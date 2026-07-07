from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from ingest import ingest_document, client
from query import query_knowledge_base

# Serve React frontend from Flask
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Serve React app ──────────────────────────────────────────────────────────
@app.route('/')
def serve_root():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

# ── API Routes ───────────────────────────────────────────────────────────────
@app.route("/api/", methods=["GET"])
def home():
    return jsonify({
        "message": "ContextBot Backend is running",
        "endpoints": {
            "upload": "POST /api/upload",
            "ask": "POST /api/ask",
            "files": "GET /api/files",
            "health": "GET /api/health",
            "reset": "POST /api/reset"
        }
    })

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    chunk_count = ingest_document(file_path)
    
    return jsonify({
        "message": f"Successfully ingested {file.filename}",
        "chunks": chunk_count,
        "filename": file.filename
    })

@app.route("/api/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question", "").strip()
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    result = query_knowledge_base(question)
    return jsonify({
        "answer": result["answer"],
        "sources": result["sources"]
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "running"})

@app.route("/api/reset", methods=["POST"])
def reset_database():
    client.delete_collection("knowledge_base")
    client.get_or_create_collection(name="knowledge_base")
    
    for f in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    return jsonify({"message": "Database cleared successfully"})

@app.route("/api/files", methods=["GET"])
def get_files():
    files = os.listdir(UPLOAD_FOLDER)
    files = [f for f in files if not f.startswith(".")]
    return jsonify({"files": files})

@app.route("/api/files/<filename>", methods=["GET"])
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)