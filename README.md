# 🧠 ContextBot — RAG Based AI Knowledge Retrieval Engine

## 🎯 Problem It Solves

Most companies have hundreds of documents — HR policies, SOPs, technical manuals, research papers — that nobody reads. Employees waste time searching or asking colleagues. This tool ingests all of it and gives instant, source-cited answers.

## ✨ Features

- 📄 Upload PDF, DOCX, and TXT documents
- 🔍 Semantic search — finds answers by meaning, not just keywords
- 🤖 AI-generated answers grounded in your actual documents
- 📎 Source citations — every answer shows which document it came from
- 🖼️ OCR support — reads scanned/image-based PDFs (certificates, scanned docs)
- 👁️ Document preview — click any file to open it in the browser
- 🗑️ Reset database — clear all documents and start fresh
- 💾 Persistent storage — documents survive server restarts

## 🏗️ Architecture

User uploads document
↓
Parse text (PyPDF2 / python-docx / OCR via Tesseract)
↓
Split into chunks (500 chars with 50 char overlap)
↓
Convert to vectors (sentence-transformers: all-MiniLM-L6-v2)
↓
Store in ChromaDB (local vector database)
↓
User asks a question
↓
Convert question to vector → similarity search in ChromaDB
↓
Top 15 most relevant chunks retrieved
↓
Sent to Groq (Llama 3.3 70B) as context
↓
AI generates grounded answer with source reference

## 🛠️ Tech Stack

- Frontend: React
- Backend: Python + Flask
- Vector Database: ChromaDB
- Embeddings: Sentence Transformers (all-MiniLM-L6-v2)
- LLM: Groq API (Llama 3.3 70B)
- PDF Parsing: PyPDF2
- OCR: Tesseract + pdf2image
- CORS: Flask-CORS










