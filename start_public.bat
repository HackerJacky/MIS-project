@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║   企業知識庫 RAG 系統 — 公開分享模式（報告用）        ║
echo ╚══════════════════════════════════════════════════════╝
echo.

REM ── 啟動 OLLAMA ────────────────────────────────────────
echo [1/3] 啟動 OLLAMA...
start "OLLAMA" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
timeout /t 3 /nobreak >nul
echo       ✅ OLLAMA 已啟動

REM ── 啟動 Flask ─────────────────────────────────────────
echo [2/3] 啟動 Flask 伺服器...
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
start "Flask" cmd /c "cd /d %~dp0 && py app.py"
echo       ✅ Flask 啟動中（約 15 秒後就緒）
timeout /t 15 /nobreak >nul

REM ── 啟動 ngrok ─────────────────────────────────────────
echo [3/3] 建立公開網址...
echo.
echo ════════════════════════════════════════════
echo   請看「ngrok」視窗裡的 Forwarding 網址
echo   例如：https://xxxx-xxx.ngrok-free.app
echo   把這個網址傳給老師 / 同學即可！
echo ════════════════════════════════════════════
echo.
start "ngrok" "C:\ngrok\ngrok.exe" http 5000

pause
