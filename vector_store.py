"""
向量資料庫模組 (ChromaDB)
負責嵌入向量的儲存與語意檢索
"""
import os
# 抑制 Windows 上的 symlinks 警告（不影響功能）
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer

from config import (
    VECTOR_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)


class VectorStore:
    """
    封裝 ChromaDB + sentence-transformers 的向量儲存與查詢。
    ChromaDB 持久化存放於 ./chroma_db，重啟後資料不會流失。
    """

    def __init__(self):
        print(f"🔧 初始化向量資料庫 → {VECTOR_DB_PATH}")
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)

        self._client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

        print(f"📦 載入嵌入模型：{EMBEDDING_MODEL}")
        print("   （首次執行會自動下載模型，約 470 MB，請稍候…）")
        self._embedder = SentenceTransformer(EMBEDDING_MODEL)

        self._col = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},   # 使用餘弦相似度
        )
        print(f"✅ 向量資料庫就緒，目前存有 {self._col.count()} 筆資料\n")

    # ─── 新增 / 更新文件 ──────────────────────────────────────────────────────

    def add_documents(self, documents: List[Dict], batch_size: int = 64) -> None:
        """
        將文件塊嵌入後寫入 ChromaDB。
        使用 upsert 以避免重複 ID 錯誤。
        """
        if not documents:
            print("⚠  沒有文件可新增")
            return

        texts     = [d['text']   for d in documents]
        ids       = [self._make_id(d) for d in documents]
        metadatas = [
            {'source': d['source'], 'chunk_id': str(d['chunk_id'])}
            for d in documents
        ]

        print(f"🧮 產生 {len(texts)} 個嵌入向量…")
        embeddings = self._embedder.encode(
            texts,
            show_progress_bar=True,
            batch_size=32
        ).tolist()

        print("💾 寫入向量資料庫…")
        for i in range(0, len(texts), batch_size):
            self._col.upsert(
                documents  = texts[i : i + batch_size],
                ids        = ids[i : i + batch_size],
                metadatas  = metadatas[i : i + batch_size],
                embeddings = embeddings[i : i + batch_size],
            )
        print(f"✅ 已寫入 {len(documents)} 筆，資料庫共 {self._col.count()} 筆\n")

    # ─── 語意搜尋 ─────────────────────────────────────────────────────────────

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        對查詢字串做語意搜尋，回傳最相關的 n_results 筆。
        每筆格式：{'text': ..., 'source': ..., 'score': ...}
        """
        total = self._col.count()
        if total == 0:
            return []

        n = min(n_results, total)
        query_vec = self._embedder.encode([query]).tolist()

        result = self._col.query(
            query_embeddings = query_vec,
            n_results        = n,
        )

        hits = []
        if result['documents']:
            for i, text in enumerate(result['documents'][0]):
                meta  = result['metadatas'][0][i]
                dist  = result['distances'][0][i] if result.get('distances') else 1.0
                score = round(1.0 - dist, 4)      # 轉換為相似度 (越高越相關)
                hits.append({
                    'text':   text,
                    'source': meta.get('source', '未知來源'),
                    'score':  score,
                })
        return hits

    # ─── 工具函式 ─────────────────────────────────────────────────────────────

    def count(self) -> int:
        return self._col.count()

    def clear(self) -> None:
        """清空整個集合（重新索引前呼叫）"""
        self._client.delete_collection(COLLECTION_NAME)
        self._col = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print("🗑  已清空向量資料庫")

    @staticmethod
    def _make_id(doc: Dict) -> str:
        """產生不含特殊字元的唯一 ID"""
        src = doc['source'].replace(' ', '_').replace('.', '_')
        return f"{src}__{doc['chunk_id']}"
