"""RAG Tutorial for Beginners: a free, local RAG chatbot in Python (ADITEJUS tutorial 2026-W44-tut1).

Stack (all free, runs on a laptop): Ollama (embeddings + chat) + chromadb (local vector DB) + pypdf.
Models (studio standard, COURSE_RULEBOOK): nomic-embed-text (embeddings), qwen2.5:3b (chat). Any similar small model works.

Setup:
    ollama pull nomic-embed-text
    ollama pull qwen2.5:3b
    pip install ollama==0.6.3 chromadb==1.5.9 pypdf==6.21.2
    python3 rag_chat.py index docs/       # read + chunk + embed your files
    python3 rag_chat.py chat              # ask questions about them

STATUS: verified end-to-end on 27 Oct 2026 with a real PDF (runs in kit/tut1v/runs.json).
Scanned PDFs have no text layer: run OCR first (e.g. ocrmypdf), otherwise they are skipped.
"""
import sys, pathlib
import ollama
import chromadb
from pypdf import PdfReader

EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen2.5:3b"
DB_DIR = "rag_db"
COLLECTION = "my_docs"


def read_file(path: pathlib.Path) -> str:
    if path.suffix.lower() == ".pdf":
        # layout mode keeps the blank lines between paragraphs (plain mode drops them)
        return "\n".join(page.extract_text(extraction_mode="layout") or "" for page in PdfReader(path).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_naive(text: str, size: int = 80) -> list[str]:
    """The 'honest failure' version: fixed-size character slices that cut rules mid-sentence."""
    return [text[i:i + size] for i in range(0, len(text), size)]


def chunk_paragraphs(text: str, max_chars: int = 400, overlap: int = 1) -> list[str]:
    """The fix: split on blank lines (paragraphs), pack paragraphs up to max_chars, overlap 1 paragraph."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, cur = [], []
    for p in paras:
        if cur and sum(len(x) for x in cur) + len(p) > max_chars:
            chunks.append("\n\n".join(cur))
            cur = cur[-overlap:] if overlap else []
        cur.append(p)
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def embed(texts: list[str]) -> list[list[float]]:
    # Ollama /api/embed: `input` may be a string or a list; vectors come back L2-normalised.
    return ollama.embed(model=EMBED_MODEL, input=texts)["embeddings"]


def get_collection():
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def index(folder: str, naive: bool = False) -> None:
    col = get_collection()
    if not pathlib.Path(folder).is_dir():
        sys.exit(f"no folder called {folder!r}: put your PDFs / .txt files in it first")
    files = [p for p in pathlib.Path(folder).iterdir() if p.suffix.lower() in (".pdf", ".txt", ".md")]
    for f in files:
        try:
            text = read_file(f)
        except Exception as e:  # damaged or password-protected file
            print(f"skipped {f.name}: {e}")
            continue
        chunks = chunk_naive(text) if naive else chunk_paragraphs(text)
        if not chunks:  # e.g. a scanned PDF with no text layer
            continue
        col.delete(where={"source": f.name})  # drop this file's old chunks, so re-indexing never leaves stale ones
        col.upsert(
            ids=[f"{f.name}-{i}" for i in range(len(chunks))],
            documents=chunks,
            embeddings=embed(chunks),
            metadatas=[{"source": f.name, "chunk": i} for i in range(len(chunks))],
        )
        print(f"indexed {f.name}: {len(chunks)} chunks")


def retrieve(question: str, k: int = 3):
    col = get_collection()
    res = col.query(query_embeddings=embed([question]), n_results=k)
    return list(zip(res["documents"][0], res["metadatas"][0]))


def answer(question: str, show: bool = False) -> str:
    hits = retrieve(question)
    if show:  # print what the retriever found, so you can see WHY the answer is right or wrong
        for d, m in hits:
            print(f"  [found] {m['source']} #{m['chunk']}: {d!r}")
    context = "\n\n---\n\n".join(f"[{m['source']} #{m['chunk']}]\n{d}" for d, m in hits)
    prompt = (
        "Answer the question using ONLY the context below. "
        "If the answer is not in the context, say \"I don't know from these documents.\" "
        "Name the source file you used.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    out = ollama.chat(model=CHAT_MODEL, messages=[{"role": "user", "content": prompt}])
    return out["message"]["content"]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "chat"
    if cmd == "index":
        index(sys.argv[2] if len(sys.argv) > 2 else "docs", naive="--naive" in sys.argv)
    elif cmd == "chat":
        print("Ask about your documents (empty line to quit).")
        while (q := input("\nyou> ").strip()):
            print("bot>", answer(q, show="--show" in sys.argv))
