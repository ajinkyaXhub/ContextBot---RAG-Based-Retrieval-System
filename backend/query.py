import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
import os

# ── Load the same embedding model ─────────────────────────────────────────────
model = SentenceTransformer('all-MiniLM-L6-v2')

# ── Connect to ChromaDB ───────────────────────────────────────────────────────
client = chromadb.PersistentClient(path="./chroma_db")

# ── Configure Gemini (new SDK) ────────────────────────────────────────────────


GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY)

# ── Main query function ───────────────────────────────────────────────────────
def query_knowledge_base(question):
    collection = client.get_or_create_collection(name="knowledge_base")
    # Step 1: Convert the question to a vector
    question_vector = model.encode([question]).tolist()

    # Step 2: Search ChromaDB for the 5 most similar chunks
    results = collection.query(
        query_embeddings=question_vector,
        n_results=25
    )

    # Step 3: Extract the matching chunks and their sources
    chunks = results["documents"][0]
    sources = [m["source"] for m in results["metadatas"][0]]

    # Step 4: Build a prompt for Gemini
    
    context = "\n\n".join([f"[From {sources[i]}]:\n{chunks[i]}" for i in range(len(chunks))])
    
    prompt = f"""You are a helpful company knowledge base assistant.
Answer the question using ONLY the context provided below.
If asked to list items, list ALL items you find in the context — do not summarize or truncate.
If the answer is not in the context, say "I couldn't find that in the documents."
Always mention which document the answer came from.

Context:
{context}

Question: {question}

Answer:"""

    # Step 5: Send to Gemini and get the answer
    response = groq_client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}]
)
    answer = response.choices[0].message.content

    # Step 6: Return answer + unique sources used
    unique_sources = list(set(sources))
    return {
        "answer": answer,
        "sources": unique_sources
    }


# ── Test it directly ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    questions = [
        "How many days of leave do employees get?",
        "What is the refund policy?",
        "Can employees work from home?"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        result = query_knowledge_base(q)
        print(f"A: {result['answer']}")
        print(f"Sources: {result['sources']}")