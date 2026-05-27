@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════╗
echo ║     企業知識庫 RAG 系統 — 啟動中              ║
echo ╚══════════════════════════════════════════════╝
echo.

REM ── 尋找並啟動 OLLAMA ───────────────────────────────────────────────────────
set OLLAMA_EXE=
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe
)
if exist "C:\Program Files\Ollama\ollama.exe" (
    set OLLAMA_EXE=C:\Program Files\Ollama\ollama.exe
)

if not "%OLLAMA_EXE%"=="" (
    echo ⚙  啟動 OLLAMA 服務...
    start "OLLAMA Service" "%OLLAMA_EXE%" serve
    timeout /t 3 /nobreak >nul
    echo ✅ OLLAMA 已在背景啟動
) else (
    echo ⚠  找不到 OLLAMA，請確認已安裝並手動執行：ollama serve
    echo    下載網址：https://ollama.com
    echo.
    echo    若已安裝，也可先手動開啟另一個命令視窗執行：
    echo      ollama serve
    echo    然後重新執行本程式
    echo.
    pause
)

echo.
echo 🚀 啟動 Flask 伺服器...
echo    瀏覽器開啟：http://localhost:5000
echo.
echo    按 Ctrl+C 可關閉伺服器
echo.
cd /d "%~dp0"
py app.py
pause
