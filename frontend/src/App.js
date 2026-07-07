import { useState, useRef, useEffect } from "react";

const API = "https://contextbot-backend.onrender.com";

function TypingDots() {
  return (
    <div style={styles.typingBubble}>
      <div style={styles.typingDots}>
        <span style={{ ...styles.dot, animationDelay: "0s" }} />
        <span style={{ ...styles.dot, animationDelay: "0.2s" }} />
        <span style={{ ...styles.dot, animationDelay: "0.4s" }} />
      </div>
    </div>
  );
}

function FileIcon({ name }) {
  const ext = name.split(".").pop().toLowerCase();
  const icons = { pdf: "📕", docx: "📘", txt: "📄", doc: "📘" };
  return <span>{icons[ext] || "📄"}</span>;
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello! Upload your company documents and I'll answer any questions about them.",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [resetting, setResetting] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    fetch(`${API}/files`)
      .then(res => res.json())
      .then(data => setUploadedFiles(data.files || []))
      .catch(() => {});
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = "";

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API}/upload`, { method: "POST", body: formData });
      const data = await res.json();
      setUploadedFiles((prev) => [...prev, data.filename]);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `✅ Indexed "${data.filename}" — ${data.chunks} chunks stored. Ask me anything about it.`,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "❌ Upload failed. Make sure the Flask server is running on port 5000." },
      ]);
    } finally {
      setUploading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim() || loading) return;

    const q = question.trim();
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer, sources: data.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "❌ Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleReset = async () => {
    if (!window.confirm("Clear all documents and chat history?")) return;
    setResetting(true);
    try {
      await fetch(`${API}/reset`, { method: "POST" });
      setUploadedFiles([]);
      setMessages([
        { role: "assistant", text: "Database cleared. Upload new documents to get started." },
      ]);
    } catch {
      alert("Reset failed.");
    } finally {
      setResetting(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 4px; }
        textarea:focus { border-color: #2563eb !important; }
      `}</style>

      <div style={styles.container}>
        <div style={styles.sidebar}>
          <div style={styles.logo}>🧠 KnowledgeBase</div>
          <p style={styles.sidebarLabel}>DOCUMENTS</p>

          <label style={{
            ...styles.uploadBtn,
            opacity: uploading ? 0.6 : 1,
            cursor: uploading ? "not-allowed" : "pointer"
          }}>
            {uploading ? "⏳ Uploading..." : "+ Upload Document"}
            <input
              type="file"
              accept=".pdf,.txt,.docx"
              onChange={handleUpload}
              style={{ display: "none" }}
              disabled={uploading}
            />
          </label>

          <div style={styles.fileList}>
            {uploadedFiles.length === 0 ? (
              <p style={styles.noFiles}>No documents yet</p>
            ) : (
              uploadedFiles.map((f, i) => (
                <div
                  key={i}
                  style={styles.fileItem}
                  onClick={() => window.open(`${API}/files/${encodeURIComponent(f)}`, "_blank")}
                  title="Click to preview"
                >
                  <FileIcon name={f} />
                  <span style={styles.fileName}>{f}</span>
                  <span style={styles.openIcon}>↗</span>
                </div>
              ))
            )}
          </div>

          <div style={styles.sidebarFooter}>
            {uploadedFiles.length > 0 && (
              <button onClick={handleReset} disabled={resetting} style={styles.resetBtn}>
                {resetting ? "Clearing..." : "🗑 Clear All Documents"}
              </button>
            )}
            <p style={styles.footerText}>Powered by Groq + ChromaDB</p>
          </div>
        </div>

        <div style={styles.main}>
          <div style={styles.header}>
            <p style={styles.headerTitle}>Company Knowledge Assistant</p>
            <p style={styles.headerSub}>
              {uploadedFiles.length === 0
                ? "Upload a document to get started"
                : `${uploadedFiles.length} document${uploadedFiles.length > 1 ? "s" : ""} indexed`}
            </p>
          </div>

          <div style={styles.chatWindow}>
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  ...styles.messageWrapper,
                  justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                  animation: "fadeIn 0.2s ease",
                }}
              >
                {msg.role === "assistant" && <div style={styles.avatar}>🧠</div>}
                <div style={{
                  ...styles.messageBubble,
                  background: msg.role === "user" ? "#2563eb" : "#1a1a1a",
                  borderRadius: msg.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                  border: msg.role === "assistant" ? "1px solid #2a2a2a" : "none",
                }}>
                  <p style={styles.messageText}>{msg.text}</p>
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={styles.sourceTag}>📎 {msg.sources.join(", ")}</div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ ...styles.messageWrapper, justifyContent: "flex-start" }}>
                <div style={styles.avatar}>🧠</div>
                <TypingDots />
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div style={styles.inputArea}>
            <div style={styles.inputRow}>
              <textarea
                ref={inputRef}
                style={styles.input}
                placeholder="Ask a question about your documents..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={loading}
              />
              <button
                style={{
                  ...styles.sendBtn,
                  opacity: loading || !question.trim() ? 0.4 : 1,
                  cursor: loading || !question.trim() ? "not-allowed" : "pointer",
                }}
                onClick={handleAsk}
                disabled={loading || !question.trim()}
              >
                ↑
              </button>
            </div>
            <p style={styles.hint}>Press Enter to send · Shift+Enter for new line</p>
          </div>
        </div>
      </div>
    </>
  );
}

const styles = {
  container: { display: "flex", height: "100vh", background: "#0f0f0f" },
  sidebar: {
    width: "260px", background: "#111", borderRight: "1px solid #1e1e1e",
    display: "flex", flexDirection: "column", padding: "24px 16px", gap: "10px",
  },
  logo: { fontSize: "18px", fontWeight: "700", color: "#fff", marginBottom: "4px" },
  sidebarLabel: { fontSize: "10px", color: "#444", fontWeight: "700", letterSpacing: "1.5px", marginTop: "8px" },
  uploadBtn: {
    display: "block", background: "#2563eb", color: "#fff",
    padding: "10px 14px", borderRadius: "8px", fontSize: "13px",
    fontWeight: "600", textAlign: "center", transition: "opacity 0.2s",
  },
  fileList: { flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "4px", marginTop: "4px" },
  noFiles: { color: "#333", fontSize: "12px", marginTop: "4px" },
  fileItem: {
  background: "#1a1a1a", padding: "8px 10px", borderRadius: "6px",
  fontSize: "12px", color: "#888", display: "flex", alignItems: "center", gap: "6px",
  cursor: "pointer", transition: "background 0.15s",
},
fileName: {
  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1,
},
openIcon: {
  fontSize: "12px", color: "#444", flexShrink: 0,
},
  sidebarFooter: { borderTop: "1px solid #1e1e1e", paddingTop: "12px", display: "flex", flexDirection: "column", gap: "8px" },
  resetBtn: {
    background: "transparent", border: "1px solid #2a2a2a", color: "#666",
    padding: "8px 12px", borderRadius: "6px", fontSize: "12px", cursor: "pointer",
    textAlign: "left",
  },
  footerText: { fontSize: "11px", color: "#333" },
  main: { flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" },
  header: {
    padding: "16px 24px", borderBottom: "1px solid #1a1a1a",
    display: "flex", flexDirection: "column", gap: "2px",
  },
  headerTitle: { fontSize: "15px", fontWeight: "600", color: "#e8e8e8" },
  headerSub: { fontSize: "12px", color: "#555" },
  chatWindow: {
    flex: 1, overflowY: "auto", padding: "24px",
    display: "flex", flexDirection: "column", gap: "16px",
  },
  messageWrapper: { display: "flex", alignItems: "flex-end", gap: "8px" },
  avatar: { fontSize: "20px", flexShrink: 0, marginBottom: "2px" },
  messageBubble: { maxWidth: "65%", padding: "12px 16px" },
  messageText: { fontSize: "14px", lineHeight: "1.7", color: "#e0e0e0", whiteSpace: "pre-wrap" },
  sourceTag: {
    marginTop: "8px", fontSize: "11px", color: "#555",
    borderTop: "1px solid #2a2a2a", paddingTop: "6px",
  },
  inputArea: { padding: "16px 24px", borderTop: "1px solid #1a1a1a", background: "#0f0f0f" },
  inputRow: { display: "flex", gap: "8px", alignItems: "flex-end" },
  input: {
    flex: 1, background: "#1a1a1a", border: "1px solid #2a2a2a",
    borderRadius: "10px", padding: "12px 16px", color: "#e8e8e8",
    fontSize: "14px", resize: "none", outline: "none", fontFamily: "inherit",
    lineHeight: "1.5", transition: "border-color 0.2s",
  },
  sendBtn: {
    background: "#2563eb", color: "#fff", border: "none",
    borderRadius: "10px", width: "44px", height: "44px",
    fontSize: "20px", cursor: "pointer", flexShrink: 0,
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  hint: { fontSize: "11px", color: "#333", marginTop: "8px" },
  typingBubble: {
    background: "#1a1a1a", border: "1px solid #2a2a2a",
    borderRadius: "18px 18px 18px 4px", padding: "14px 18px",
  },
  typingDots: { display: "flex", gap: "4px", alignItems: "center" },
  dot: {
    width: "6px", height: "6px", borderRadius: "50%",
    background: "#555", display: "inline-block",
    animation: "bounce 1.2s infinite",
  },
};
