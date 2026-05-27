@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════╗
echo ║     企業知識庫 RAG 系統 — 安裝套件             ║
echo ╚══════════════════════════════════════════════╝
echo.
echo [1/3] 升級 pip...
py -m pip install --upgrade pip --quiet

echo [2/3] 安裝必要套件（首次約需 3-10 分鐘）...
py -m pip install flask pdfplumber chromadb sentence-transformers requests

echo.
echo [3/3] 確認 OLLAMA 已安裝並拉取 gemma3 模型...
echo       若尚未安裝 OLLAMA，請前往 https://ollama.com 下載
echo       然後執行：ollama pull gemma3
echo.
echo ✅ 安裝完成！請執行 run.bat 啟動系統
echo.
pause
