"""
Flask Web Server
RAG的REST API 與前端網頁
"""
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

from rag_engine import RAGEngine
from config     import FLASK_HOST, FLASK_PORT

app = Flask(__name__)
rag = RAGEngine()


@app.route('/')
def index():
    return render_template('index.html')


# ─── API 路由 ─────────────────────────────────────────────────────────────────

@app.route('/api/status', methods=['GET'])
def api_status():
    """取得系統狀態（OLLAMA 連線、已索引文件數…）"""
    return jsonify(rag.get_status())


@app.route('/api/index', methods=['POST'])
def api_index():
    """觸發 PDF 索引（較耗時，請耐心等候）"""
    result = rag.index_pdfs()
    return jsonify(result)


@app.route('/api/query', methods=['POST'])
def api_query():
    """串流問答 — 使用 Server-Sent Events 即時回傳 LLM 輸出"""
    data     = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()

    if not question:
        return jsonify({'error': '請輸入問題'}), 400

    def generate():
        yield from rag.query_stream(question)

    return Response(
        stream_with_context(generate()),
        mimetype = 'text/event-stream',
        headers  = {
            'Cache-Control':    'no-cache',
            'X-Accel-Buffering': 'no',   # 停用 Nginx 緩衝（若有 Proxy）
        },
    )


# ─── 啟動 ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 55)
    print("  🏢 企業知識庫 RAG 系統")
    print("=" * 55)
    print(f"  網址：http://localhost:{FLASK_PORT}")
    print(f"  模型：{__import__('config').OLLAMA_MODEL}")
    print("  確認 OLLAMA 已啟動：ollama serve")
    print("=" * 55)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)
