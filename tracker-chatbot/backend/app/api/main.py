from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import os
import tempfile
import logging
from datetime import datetime

# Import our modules
from ..config import settings
from ..pdf_processor.parser import PDFParser
from ..pdf_processor.chunker import SemanticChunker
from ..knowledge_base.embedder import Embedder
from ..knowledge_base.vector_store import VectorStore
from ..retrieval.hybrid_search import HybridSearcher
from ..llm.groq_client import GroqClient
from ..llm.prompt_templates import SYSTEM_PROMPT, WELCOME_MESSAGE, ERROR_FALLBACK_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Chatbot API",
    description="RAG-based PDF chatbot with hybrid search",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (initialized on startup)
pdf_parser = None
chunker = None
embedder = None
vector_store = None
hybrid_searcher = None
groq_client = None

# In-memory session storage
sessions = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    type: str
    content: str
    timestamp: datetime


class UploadResponse(BaseModel):
    status: str
    filename: str
    page_count: int
    chunk_count: int
    processing_time: float


class StatsResponse(BaseModel):
    document_count: int
    total_chunks: int
    vector_store_stats: Dict[str, Any]
    search_stats: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global pdf_parser, chunker, embedder, vector_store, hybrid_searcher, groq_client
    
    logger.info("Starting PDF Chatbot API...")
    
    try:
        # Create directories
        os.makedirs(settings.upload_dir, exist_ok=True)
        os.makedirs(settings.temp_dir, exist_ok=True)
        os.makedirs(settings.vector_db.persist_directory, exist_ok=True)
        
        # Initialize components
        pdf_parser = PDFParser()
        chunker = SemanticChunker(
            chunk_size=settings.pdf.chunk_size,
            chunk_overlap=settings.pdf.chunk_overlap
        )
        embedder = Embedder(
            model_name=settings.embedding.model,
            batch_size=settings.embedding.batch_size,
            device=settings.embedding.device,
            normalize_embeddings=settings.embedding.normalize_embeddings
        )
        vector_store = VectorStore(
            persist_directory=settings.vector_db.persist_directory,
            collection_name=settings.vector_db.collection_name
        )
        hybrid_searcher = HybridSearcher(
            vector_store=vector_store,
            embedder=embedder,
            alpha=settings.retrieval.hybrid_alpha,
            rrf_k=settings.retrieval.rrf_k
        )
        logger.info(f"GROQ_API_KEY loaded: {bool(settings.groq.api_key)}")
        
        # Fail fast if API key is missing
        if not settings.groq.api_key:
            raise RuntimeError("GROQ_API_KEY is missing. Add it in HF Secrets and restart Space.")
            
        groq_client = GroqClient(
            api_key=settings.groq.api_key,
            model=settings.groq.model,
            temperature=settings.groq.temperature,
            max_tokens=settings.groq.max_tokens,
            max_retries=settings.groq.max_retries,
            retry_delay=settings.groq.retry_delay
        )
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        raise


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "PDF Chatbot API is running", "version": "1.0.0"}


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    try:
        vector_stats = vector_store.get_stats()
        search_stats = hybrid_searcher.get_search_stats()
        
        return StatsResponse(
            document_count=vector_stats.get('document_count', 0),
            total_chunks=search_stats.get('indexed_documents', 0),
            vector_store_stats=vector_stats,
            search_stats=search_stats
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if file.size > settings.pdf.max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds {settings.pdf.max_size_mb}MB limit"
        )
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Parse PDF
        logger.info(f"Parsing PDF: {file.filename}")
        pdf_content = pdf_parser.parse_pdf(temp_file_path)
        
        # Chunk content
        logger.info("Chunking content...")
        chunks = chunker.chunk_document(pdf_content)
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = embedder.embed_texts(chunk_texts)
        
        # Prepare documents for indexing
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                'content': chunk.content,
                'embedding': embeddings[i] if i < len(embeddings) else [],
                'metadata': {
                    'page_number': chunk.page_number,
                    'chunk_id': chunk.chunk_id,
                    'category': chunk.category,
                    'filename': file.filename,
                    'source': pdf_content.metadata.get('title', file.filename)
                }
            }
            documents.append(doc)
        
        # Index documents
        logger.info("Indexing documents...")
        hybrid_searcher.index_documents(documents)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        logger.info(f"Successfully processed {file.filename} in {processing_time:.2f}s")
        
        return UploadResponse(
            status="success",
            filename=file.filename,
            page_count=pdf_content.metadata.get('page_count', 0),
            chunk_count=len(chunks),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF {file.filename}: {str(e)}")
        
        # Clean up temp file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with SSE streaming."""
    async def generate_response():
        try:
            # Get or create session
            session_id = request.session_id or f"session_{datetime.now().timestamp()}"
            if session_id not in sessions:
                sessions[session_id] = {'messages': [], 'created_at': datetime.now()}
            
            session = sessions[session_id]
            
            # Add user message to session
            session['messages'].append({
                'role': 'user',
                'content': request.message,
                'timestamp': datetime.now()
            })
            
            # Search for relevant documents
            search_results = hybrid_searcher.search(
                query=request.message,
                top_k=settings.retrieval.top_k,
                threshold=settings.retrieval.threshold
            )
            
            if not search_results:
                # No relevant documents found
                yield f"data: {json.dumps({'type': 'content', 'content': ERROR_FALLBACK_PROMPT})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"
                return
            
            # Prepare context
            context_parts = []
            for result in search_results:
                page_num = result.get('metadata', {}).get('page_number', 'Unknown')
                content = result.get('content', '')
                context_parts.append(f"(Page {page_num}) {content}")
            
            context = "\n\n".join(context_parts)
            
            # Create RAG prompt
            rag_prompt = groq_client.create_rag_prompt(context, request.message)
            
            # Prepare messages for Groq
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": rag_prompt}
            ]
            
            # Stream response from Groq
            full_response = ""
            async for chunk in groq_client.stream_chat(messages):
                if chunk['type'] == 'content':
                    full_response += chunk['content']
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk['content']})}\n\n"
                elif chunk['type'] == 'done':
                    # Add assistant message to session
                    session['messages'].append({
                        'role': 'assistant',
                        'content': full_response,
                        'timestamp': datetime.now()
                    })
                    yield f"data: {json.dumps({'type': 'done', 'content': '', 'session_id': session_id})}\n\n"
                    return
                elif chunk['type'] == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'content': chunk['content']})}\n\n"
                    return
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.post("/api/export")
async def export_conversation(session_id: str = Form(...)):
    """Export conversation as markdown."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        messages = session['messages']
        
        # Generate markdown
        markdown = "# Conversation Export\n\n"
        markdown += f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown += f"Total messages: {len(messages)}\n\n"
        markdown += "---\n\n"
        
        for msg in messages:
            role = msg['role'].title()
            content = msg['content']
            timestamp = msg['timestamp'].strftime('%H:%M:%S')
            
            markdown += f"## {role} ({timestamp})\n\n"
            markdown += f"{content}\n\n"
            markdown += "---\n\n"
        
        # Return as file download
        from fastapi.responses import Response
        
        return Response(
            content=markdown,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=conversation_{session_id}.md"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/reset")
async def reset_session(session_id: Optional[str] = None):
    """Reset session or clear all data."""
    try:
        if session_id:
            # Reset specific session
            if session_id in sessions:
                del sessions[session_id]
            return {"message": f"Session {session_id} reset"}
        else:
            # Clear all data
            sessions.clear()
            hybrid_searcher.clear_index()
            return {"message": "All data cleared"}
            
    except Exception as e:
        logger.error(f"Error resetting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check component health
        vector_healthy = vector_store.is_healthy()
        embedder_healthy = embedder.is_model_loaded()
        groq_validation = groq_client.validate_api_key()
        groq_healthy = groq_validation.get("ok", False)
        
        overall_health = all([vector_healthy, embedder_healthy, groq_healthy])
        
        return {
            "status": "healthy" if overall_health else "unhealthy",
            "components": {
                "vector_store": vector_healthy,
                "embedder": embedder_healthy,
                "groq_client": {
                    "healthy": groq_healthy,
                    "reason": groq_validation.get("reason", "Unknown")
                }
            },
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.debug
    )
