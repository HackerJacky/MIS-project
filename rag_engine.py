"""
RAG 核心引擎
整合 PDF 處理、向量檢索、OLLAMA 問答
"""
import json
import os
from typing import Generator, List, Dict, Tuple

import requests

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    PDF_FOLDER,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS,
)
from pdf_processor import process_pdf_folder
from vector_store  import VectorStore


class RAGEngine:
    """
    RAG（Retrieval-Augmented Generation）引擎
    流程：問題 → 向量檢索相關段落 → 組成 Prompt → OLLAMA 生成答案
    """

    def __init__(self):
        self.vs = VectorStore()

    # ─── 索引 PDF ────────────────────────────────────────────────────────────

    def index_pdfs(self) -> Dict:
        """掃描 PDF_FOLDER，建立（或重建）向量索引"""
        pdf_files = [
            f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')
        ]
        if not pdf_files:
            return {'status': 'error', 'message': '找不到任何 PDF 檔案'}

        self.vs.clear()
        docs = process_pdf_folder(PDF_FOLDER, CHUNK_SIZE, CHUNK_OVERLAP)

        if not docs:
            return {'status': 'error', 'message': '無法從 PDF 擷取文字'}

        self.vs.add_documents(docs)
        return {
            'status':      'success',
            'message':     f'成功索引 {len(pdf_files)} 個 PDF，共 {len(docs)} 塊',
            'pdf_count':   len(pdf_files),
            'chunk_count': len(docs),
        }

    # ─── 一次性問答（非串流） ────────────────────────────────────────────────

    def query(self, question: str) -> Tuple[str, List[Dict]]:
        """回傳 (answer_str, sources_list)"""
        if self.vs.count() == 0:
            return (
                "⚠ 知識庫尚未建立，請先點擊「建立索引」按鈕。",
                []
            )

        hits    = self.vs.search(question, TOP_K_RESULTS)
        context = self._build_context(hits)
        prompt  = self._build_prompt(question, context)
        answer  = self._ollama_generate(prompt)

        sources = [
            {'source': h['source'], 'excerpt': h['text'][:300], 'score': h['score']}
            for h in hits
        ]
        return answer, sources

    # ─── 串流問答（Server-Sent Events 用） ──────────────────────────────────

    def query_stream(
        self, question: str
    ) -> Generator[str, None, None]:
        """
        生成器：依序 yield SSE 格式字串
          data: {"type":"sources", "data":[...]}
          data: {"type":"token",   "data":"..."}
          data: {"type":"done"}
        """
        if self.vs.count() == 0:
            yield _sse({'type': 'error', 'data': '⚠ 知識庫尚未建立，請先點擊「建立索引」。'})
            return

        hits    = self.vs.search(question, TOP_K_RESULTS)
        sources = [
            {'source': h['source'], 'excerpt': h['text'][:300], 'score': h['score']}
            for h in hits
        ]
        yield _sse({'type': 'sources', 'data': sources})

        context = self._build_context(hits)
        prompt  = self._build_prompt(question, context)

        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json    = {'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': True},
                stream  = True,
                timeout = OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()

            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                try:
                    chunk = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue

                token = chunk.get('response', '')
                if token:
                    yield _sse({'type': 'token', 'data': token})

                if chunk.get('done'):
                    break

        except requests.exceptions.ConnectionError:
            yield _sse({'type': 'error',
                        'data': '❌ 無法連接 OLLAMA，請確認已執行 `ollama serve`'})
        except requests.exceptions.Timeout:
            yield _sse({'type': 'error', 'data': '❌ OLLAMA 回應逾時，請稍後再試'})
        except Exception as e:
            yield _sse({'type': 'error', 'data': f'❌ 發生錯誤：{e}'})

        yield _sse({'type': 'done'})

    # ─── 系統狀態 ────────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """回傳系統狀態 JSON"""
        ollama_ok = False
        models    = []
        try:
            r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if r.status_code == 200:
                ollama_ok = True
                data = r.json()
                models = [m['name'] for m in data.get('models', [])]
        except Exception:
            pass

        pdf_files = sorted(
            f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')
        )
        return {
            'ollama_ok':     ollama_ok,
            'ollama_model':  OLLAMA_MODEL,
            'models':        models,
            'doc_count':     self.vs.count(),
            'pdf_files':     pdf_files,
            'pdf_count':     len(pdf_files),
            'indexed':       self.vs.count() > 0,
        }

    # ─── 內部輔助 ────────────────────────────────────────────────────────────

    @staticmethod
    def _build_context(hits: List[Dict]) -> str:
        parts = []
        for i, h in enumerate(hits, 1):
            parts.append(
                f"【參考資料 {i}】（來源：{h['source']}，相關度：{h['score']}）\n{h['text']}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        return f"""<context>
{context}
</context>

根據以上參考資料，請用繁體中文回答以下問題。
- 直接給出答案，不要重複問題
- 條列重點，清楚說明
- 若資料不足請說明

問題：{question}

回答：""""

    @staticmethod
    def _ollama_generate(prompt: str) -> str:
        """非串流版（給 /api/query 用）"""
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json    = {'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False},
                timeout = OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json().get('response', '（無回應）')
        except requests.exceptions.ConnectionError:
            return '❌ 無法連接 OLLAMA，請確認已執行 `ollama serve`'
        except Exception as e:
            return f'❌ 發生錯誤：{e}'


# ─── 工具函式 ─────────────────────────────────────────────────────────────────

def _sse(obj: dict) -> str:
    """格式化為 Server-Sent Events 字串"""
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"
