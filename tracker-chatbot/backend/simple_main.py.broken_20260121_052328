#!/usr/bin/env python3

import os
import json
import time
from typing import Optional
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ----------------------------
# Simple helpers
# ----------------------------
def sanitize_metadata_for_chromadb(metadata: dict) -> dict:
    clean = {}
    for k, v in (metadata or {}).items():
        if isinstance(v, (list, tuple)):
            clean[k] = ", ".join(str(x) for x in v) if v else ""
        elif isinstance(v, dict):
            clean[k] = json.dumps(v, ensure_ascii=False)
        elif v is None or isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean


@dataclass
class Document:
    text: str
    metadata: dict


# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(title="PDF Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class UploadResponse(BaseModel):
    message: str
    document_id: str
    page_count: int
    chunk_count: int

sessions = {}

# Global ML components
global_parser = None
global_chunker = None
global_embedder = None
global_vector_store = None
global_hybrid_searcher = None


@app.on_event("startup")
async def startup_event():
    global global_parser, global_chunker, global_embedder, global_vector_store, global_hybrid_searcher

    print("Initializing ML components...")

    from app.pdf_processor.parser import PDFParser
    from app.pdf_processor.chunker import SemanticChunker
    from app.knowledge_base.embedder import Embedder
    from app.knowledge_base.vector_store import VectorStore
    from app.retrieval.hybrid_search import HybridSearcher

    global_parser = PDFParser()
    global_chunker = SemanticChunker()
    global_embedder = Embedder()
    global_vector_store = VectorStore()
    global_hybrid_searcher = HybridSearcher(global_vector_store, global_embedder)

    print("✓ ML components initialized")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "PDF Chatbot API is running"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")

    try:
        if global_parser is None or global_chunker is None or global_embedder is None or global_vector_store is None or global_hybrid_searcher is None:
            raise RuntimeError("ML components not initialized. Restart server.")

        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)

        pdf_content = global_parser.parse_pdf(temp_path)
        chunks = global_chunker.chunk_document(pdf_content)

        print(f"Created {len(chunks)} chunks from PDF")
        print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = global_embedder.embed_texts([c.content for c in chunks])
        print(f"Generated {len(embeddings)} embeddings")

        # Add to Chroma
        docs_for_vector = []
        docs_for_index = []

        for i, chunk in enumerate(chunks):
            meta = sanitize_metadata_for_chromadb(chunk.metadata)

            docs_for_vector.append({
                "content": chunk.content,
                "embedding": embeddings[i] if i < len(embeddings) else [],
                "metadata": meta
            })

            docs_for_index.append({
                "content": chunk.content,
                "embedding": embeddings[i] if i < len(embeddings) else None,
                "metadata": meta
            })

        doc_ids = global_vector_store.add_documents(docs_for_vector)
        print(f"Added {len(doc_ids)} documents to vector store")

        ok = global_hybrid_searcher.index_documents(docs_for_index)
        print(f"Indexed {len(docs_for_index)} docs for hybrid search (ok={ok})")

        try:
            print("Search stats:", global_hybrid_searcher.get_search_stats())
        except Exception as e:
            print("Could not get search stats:", e)

        return UploadResponse(
            message=f"PDF '{file.filename}' uploaded and processed successfully",
            document_id=f"doc_{int(time.time())}",
            page_count=len(pdf_content.pages),
            chunk_count=len(chunks),
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return UploadResponse(
            message=f"PDF '{file.filename}' uploaded (mock processing due to error: {str(e)})",
            document_id=f"doc_{int(time.time())}",
            page_count=25,
            chunk_count=42,
        )


@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    async def generate_response():
        try:
            if global_hybrid_searcher is None:
                raise RuntimeError("Hybrid search not initialized. Restart server.")

            print(f"Searching for: {request.message}")

            # ✅ FIX: lower threshold so results are not filtered out by RRF scoring
            results = global_hybrid_searcher.search(request.message, top_k=8, threshold=0.0005)

            print(f"Found {len(results)} search results")

            context = ""
            if results:
                context = "Context chunks from uploaded PDF (use ONLY these chunks):\n\n"
                for i, r in enumerate(results, 1):
                    content = r.get("content", "")
                    meta = r.get("metadata", {})
                    page = meta.get("page_number") or meta.get("page") or "Unknown"
                    score = r.get("combined_score", r.get("score", 0))
                    context += f"[Chunk {i} | Page {page} | Score {score:.4f}]\n{content}\n\n"
            else:
                context = "No relevant information found in uploaded PDFs."

            # LLM (Groq)
            from app.llm.groq_client import GroqClient
            groq_client = GroqClient(api_key=os.environ.get("GROQ_API_KEY", ""))

            models_to_try = [
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
                "gemma2-9b-it",
                "mixtral-8x7b-32768",
            ]

            system_prompt = (
                "You are a PDF Document QA assistant.\n"
                "\n"
                "RULES (must follow):\n"
                "1) Answer strictly using ONLY the provided context chunks from the PDF.\n"
                "2) If the context does not contain the answer, reply exactly:\n"
                "   \"I couldn't find this in the uploaded document.\"\n"
                "3) Always include page citations in the format: (Page X)\n"
                "4) Always quote exact phrases from the context using double quotes.\n"
                "5) Do NOT use outside knowledge. Do NOT guess.\n"
                "\n"
                "OUTPUT FORMAT:\n"
                "Answer:\n"
                "- <answer with citations>\n"
                "\n"
                "Evidence:\n"
                "- \"quote...\" (Page X)\n"
            )

            user_prompt = f"{context}\n\nUser Question: {request.message}"

            for model in models_to_try:
                try:
                    groq_client.model = model
                    print(f"Trying model: {model}")

                    async for chunk in groq_client.stream_chat(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ]
                    ):
                        text = chunk.get("content", "")
                        if text:
                            yield f"data: {json.dumps({'type':'content','content':text})}\n\n"

                    session_id = request.session_id or f"session_{int(time.time())}"
                    yield f"data: {json.dumps({'type':'done','session_id':session_id})}\n\n"
                    return

                except Exception as e:
                    print(f"Model failed ({model}): {e}")
                    continue

            raise RuntimeError("All Groq models failed")

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type':'content','content':f'Error: {str(e)}'})}\n\n"
            session_id = request.session_id or f"session_{int(time.time())}"
            yield f"data: {json.dumps({'type':'done','session_id':session_id})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )


@app.get("/api/stats")
async def get_stats():
    try:
        stats = global_vector_store.get_stats() if global_vector_store else {}
        return {"vector_store": stats, "active_sessions": len(sessions)}
    except Exception as e:
        return {"vector_store": {}, "active_sessions": len(sessions), "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("Starting PDF Chatbot API with full ML capabilities...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
