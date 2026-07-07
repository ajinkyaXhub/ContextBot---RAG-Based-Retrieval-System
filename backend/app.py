import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from ingest import ingest_document, client
from query import query_knowledge_base
from flask import send_from_directory

app = Flask(__name__)
CORS(app)  # Allows React (running on port 3000) to talk to Flask (port 5000)

UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "ContextBot Backend is running",
        "endpoints": {
            "upload": "POST /upload",
            "ask": "POST /ask",
            "files": "GET /files",
            "health": "GET /health",
            "reset": "POST /reset"
        }
    })
# ── Route 1: Upload a document ────────────────────────────────────────────────
# React sends a file here → we save it → we ingest it into ChromaDB
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Save the file to uploads folder
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Ingest it into ChromaDB
    chunk_count = ingest_document(file_path)

    return jsonify({
        "message": f"Successfully ingested {file.filename}",
        "chunks": chunk_count,
        "filename": file.filename
    })


# ── Route 2: Ask a question ───────────────────────────────────────────────────
# React sends a question here → we search ChromaDB → we call Groq → we return answer
@app.route("/ask", methods=["POST"])
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


# ── Route 3: Health check ─────────────────────────────────────────────────────
# Just to confirm the server is running
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"})


# ── Route 4: Reset the database ───────────────────────────────────────────────
@app.route("/reset", methods=["POST"])
def reset_database():
    global collection
    client.delete_collection("knowledge_base")
    collection = client.get_or_create_collection(name="knowledge_base")

    for f in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(file_path):
            os.remove(file_path)

    return jsonify({"message": "Database cleared successfully"})

@app.route("/files", methods=["GET"])
def get_files():
    files = os.listdir(UPLOAD_FOLDER)
    files = [f for f in files if not f.startswith(".")]
    return jsonify({"files": files})



@app.route("/files/<filename>", methods=["GET"])
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)