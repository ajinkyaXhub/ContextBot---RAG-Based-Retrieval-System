import os
import re
import PyPDF2
import docx
import chromadb
from sentence_transformers import SentenceTransformer
import pytesseract
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"

# ── Load the embedding model ──────────────────────────────────────────────────
model = SentenceTransformer('all-MiniLM-L6-v2')

# ── Connect to ChromaDB ───────────────────────────────────────────────────────
client = chromadb.PersistentClient(path="./chroma_db")


# ── Helper: Count real-looking English words ──────────────────────────────────
# Common English words to use as a real-word detector
COMMON_WORDS = set([
    "the", "and", "for", "are", "was", "this", "that", "with", "have", "from",
    "they", "been", "which", "will", "would", "could", "should", "their", "there",
    "what", "when", "where", "who", "how", "all", "each", "her", "his", "our",
    "out", "not", "but", "can", "into", "than", "then", "them", "these", "those",
    "journal", "research", "publication", "certificate", "awarded", "paper", "review",
    "international", "signed", "date", "volume", "issue", "grade", "impact", "factor",
    "open", "access", "peer", "reviewed", "editor", "chief", "acceptance", "certifies"
])

def count_real_words(text):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return sum(1 for w in words if w in COMMON_WORDS)


# ── Helper: Extract text from different file types ────────────────────────────
def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""

        # If normal extraction got little/no text, the PDF is likely image-based.
        # Fall back to OCR — convert each page to an image and read text from it.
        if len(text.strip()) < 20:
            print(f"  → No readable text found, running OCR...")
            images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
            ocr_text = ""
            for i, img in enumerate(images):
                normal_text = pytesseract.image_to_string(img)
                rotated_text = pytesseract.image_to_string(img.rotate(180))

                # Pick whichever orientation has more real-looking words
                if count_real_words(rotated_text) > count_real_words(normal_text):
                    page_text = rotated_text
                else:
                    page_text = normal_text

                ocr_text += page_text
                print(f"  → OCR processed page {i + 1}/{len(images)}")
            text = ocr_text

        return text

    elif ext == ".docx":
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        return ""


# ── Helper: Split text into chunks ───────────────────────────────────────────
def split_into_chunks(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# ── Main function: Ingest a document ─────────────────────────────────────────
def ingest_document(file_path):
    collection = client.get_or_create_collection(name="knowledge_base")
    filename = os.path.basename(file_path)
    print(f"Processing: {filename}")

    text = extract_text(file_path)
    if not text.strip():
        print(f"No text found in {filename}")
        return 0

    chunks = split_into_chunks(text)
    print(f"  → {len(chunks)} chunks created")

    embeddings = model.encode(chunks).tolist()
    print(f"  → Embeddings generated")

    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )
    print(f"  → Stored in ChromaDB")
    return len(chunks)


# ── Test it directly ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = "uploads/sample.txt"
    os.makedirs("uploads", exist_ok=True)
    with open(sample, "w") as f:
        f.write("""
        Leave Policy:
        Employees are entitled to 20 days of paid leave per year.
        Leave must be applied 2 weeks in advance.
        Sick leave is separate and allows up to 10 days per year.

        Refund Policy:
        Products can be returned within 30 days of purchase.
        Refunds are processed within 5-7 business days.
        Items must be unused and in original packaging.

        Work From Home Policy:
        Employees can work from home up to 3 days per week.
        WFH must be approved by the team lead.
        Core hours are 10am to 4pm regardless of location.
        """)
    
    count = ingest_document(sample)
    print(f"\nDone! {count} chunks stored in the database.")