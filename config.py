"""
RAG 知識庫系統設定檔
"""
import os

# 基本路徑設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── OLLAMA 設定 ───────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "gemma3:1b"       # 輕量版，可改為 gemma3:4b（需要 4GB RAM）
OLLAMA_TIMEOUT  = 180               # 秒

# ─── 嵌入模型設定 ────────────────────────────────────────────
# paraphrase-multilingual-MiniLM-L12-v2 支援繁體中文，約 470 MB
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# ─── 向量資料庫 ───────────────────────────────────────────────
VECTOR_DB_PATH      = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME     = "mis_knowledge_base"

# ─── PDF 資料夾 ───────────────────────────────────────────────
PDF_FOLDER = BASE_DIR               # PDF 與 app.py 放在同一層

# ─── RAG 分塊設定 ─────────────────────────────────────────────
CHUNK_SIZE    = 600                 # 每塊字元數
CHUNK_OVERLAP = 120                 # 重疊字元數（確保語意連貫）
TOP_K_RESULTS = 5                   # 每次檢索前幾筆

# ─── Flask 設定 ───────────────────────────────────────────────
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
