# 🏢 企業知識庫 RAG 系統

> MIS 學期專案 — 本地端 RAG（Retrieval-Augmented Generation）知識庫

---

## 系統架構

```
使用者問題
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Flask Web Server (app.py)                       │
│  網頁介面 + REST API                              │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  RAG Engine (rag_engine.py)                      │
│  ┌──────────────────┐   ┌───────────────────┐   │
│  │  向量檢索          │   │  Prompt 建構      │   │
│  │  (ChromaDB)       │   │  + 上下文組合     │   │
│  └──────────────────┘   └───────────────────┘   │
└────────────────────┬────────────────────────────┘
          ┌──────────┴──────────┐
          ▼                     ▼
┌──────────────────┐   ┌──────────────────────┐
│  ChromaDB        │   │  OLLAMA + gemma3     │
│  (本地向量資料庫) │   │  (本地 LLM 推論)     │
└──────────────────┘   └──────────────────────┘
          ▲
┌──────────────────┐
│  PDF Processor   │
│  (pdfplumber)    │
│  PDF → 文字塊    │
└──────────────────┘
```

---

## 技術棧

| 層次 | 工具 | 說明 |
|------|------|------|
| LLM 推論 | [OLLAMA](https://ollama.com) + gemma3 | 本地端，不需網路 |
| 嵌入模型 | sentence-transformers | 繁中/英文多語義向量 |
| 向量資料庫 | ChromaDB | 持久化本地儲存 |
| PDF 解析 | pdfplumber | 高品質文字擷取 |
| Web 框架 | Flask | REST API + 串流 SSE |
| 前端 | 純 HTML/CSS/JS | 無框架依賴 |

---

## 快速開始

### 1. 安裝 OLLAMA

前往 https://ollama.com 下載安裝，然後：

```bash
ollama pull gemma3      # 下載 gemma3 模型（約 5GB）
ollama serve            # 啟動 OLLAMA 服務
```

### 2. 安裝 Python 套件

```bash
# 方法一：執行 setup.bat（Windows 雙擊）

# 方法二：手動安裝
pip install flask pdfplumber chromadb sentence-transformers requests
```

### 3. 放入 PDF 檔案

將 PDF 檔案放入 `MIS-project/` 資料夾（已有 15 個 PDF）

### 4. 啟動系統

```bash
# 方法一：雙擊 run.bat

# 方法二：命令列
py app.py
```

### 5. 使用系統

1. 開啟瀏覽器 → http://localhost:5000
2. 點擊左側「**建立 / 重建索引**」（首次約需 2-5 分鐘）
3. 等待索引完成後，輸入問題即可查詢

---

## 檔案結構

```
MIS-project/
├── app.py              ← Flask 主程式（入口點）
├── rag_engine.py       ← RAG 核心邏輯
├── vector_store.py     ← ChromaDB 向量資料庫封裝
├── pdf_processor.py    ← PDF 讀取與分塊
├── config.py           ← 設定檔（模型、路徑等）
├── requirements.txt    ← Python 套件清單
├── setup.bat           ← 一鍵安裝（Windows）
├── run.bat             ← 一鍵啟動（Windows）
├── templates/
│   └── index.html      ← 前端網頁
├── chroma_db/          ← 向量資料庫（自動生成）
└── *.pdf               ← PDF 知識文件
```

---

## RAG 運作原理

1. **PDF 讀取**：pdfplumber 逐頁解析 PDF，保留中文文字
2. **文字分塊**：以 600 字為單位切割，保留 120 字重疊，確保語意連貫
3. **向量嵌入**：sentence-transformers 將每個文字塊轉為 768 維語意向量
4. **向量儲存**：ChromaDB 以餘弦相似度索引向量，持久化到磁碟
5. **語意搜尋**：使用者問題嵌入後，找出餘弦相似度最高的 Top-5 段落
6. **Prompt 組裝**：將檢索到的段落和問題組成完整 Prompt
7. **LLM 生成**：OLLAMA gemma3 根據 Prompt 以串流方式產生答案

---

## 設定調整（config.py）

| 設定項 | 預設值 | 說明 |
|--------|--------|------|
| `OLLAMA_MODEL` | `gemma3` | 可改為 gemma3:4b, gemma3:12b |
| `CHUNK_SIZE` | `600` | 分塊大小（字元數） |
| `CHUNK_OVERLAP` | `120` | 重疊大小（確保語意連貫） |
| `TOP_K_RESULTS` | `5` | 每次檢索的段落數 |
| `FLASK_PORT` | `5000` | Web 服務埠號 |
