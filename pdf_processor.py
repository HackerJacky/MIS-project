"""
PDF 文件處理模組
負責讀取 PDF、清理文字、切分成語意塊
"""
import os
import re
from typing import List, Dict, Optional

import pdfplumber


# ─── 文字清理 ─────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """清理 PDF 擷取出的原始文字"""
    # 移除多餘空白（保留換行）
    text = re.sub(r'[ \t]+', ' ', text)
    # 移除超過兩個連續換行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 移除頁首頁尾常見雜訊（純數字行）
    text = re.sub(r'(?m)^\s*\d+\s*$', '', text)
    return text.strip()


# ─── PDF 讀取 ─────────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    使用 pdfplumber 逐頁讀取 PDF 文字。
    回傳合併後的全文字串，失敗時回傳 None。
    """
    pages_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    raw = page.extract_text()
                    if raw and raw.strip():
                        pages_text.append(raw)
                except Exception as e:
                    print(f"    [警告] 第 {page_num} 頁讀取失敗：{e}")
    except Exception as e:
        print(f"  [錯誤] 無法開啟 {os.path.basename(pdf_path)}：{e}")
        return None

    if not pages_text:
        return None

    return clean_text("\n\n".join(pages_text))


# ─── 文字分塊 ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 120) -> List[str]:
    """
    將長文字切成有重疊的小塊，盡量在句子邊界切割。
    中文優先找句號、英文找 . 或換行。
    """
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start  = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # 嘗試在句子邊界切割（從後往前找）
        if end < len(text):
            boundary = -1
            for sep in ['。', '！', '？', '.\n', '!\n', '?\n', '.', '!', '?', '\n', '，', ',']:
                pos = text.rfind(sep, start + overlap, end)
                if pos != -1:
                    boundary = pos + len(sep)
                    break
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()
        if len(chunk) > 30:          # 過短的塊沒有意義
            chunks.append(chunk)

        next_start = end - overlap
        if next_start <= start:      # 防止無限迴圈
            next_start = end
        start = next_start

    return chunks


# ─── 資料夾批次處理 ───────────────────────────────────────────────────────────

def process_pdf_folder(
    folder_path: str,
    chunk_size: int = 600,
    overlap:     int = 120
) -> List[Dict]:
    """
    掃描資料夾中所有 PDF，回傳文件塊串列。
    每個元素格式：
      {
        'text':         <字串>,
        'source':       <檔名>,
        'chunk_id':     <int>,
        'total_chunks': <int>
      }
    """
    pdf_files = sorted(
        f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')
    )

    if not pdf_files:
        print("⚠  未找到任何 PDF 檔案")
        return []

    print(f"📂 共找到 {len(pdf_files)} 個 PDF 檔案，開始處理…\n")
    all_documents = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"  📄 {pdf_file}")

        full_text = extract_text_from_pdf(pdf_path)
        if not full_text:
            print("     → 無法擷取文字，略過")
            continue

        chunks = chunk_text(full_text, chunk_size, overlap)
        if not chunks:
            print("     → 分塊結果為空，略過")
            continue

        for idx, chunk in enumerate(chunks):
            all_documents.append({
                'text':         chunk,
                'source':       pdf_file,
                'chunk_id':     idx,
                'total_chunks': len(chunks)
            })

        print(f"     → 產生 {len(chunks)} 塊")

    print(f"\n✅ 共建立 {len(all_documents)} 個文件塊（來自 {len(pdf_files)} 個 PDF）")
    return all_documents
