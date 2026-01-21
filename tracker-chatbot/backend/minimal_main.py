from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import time
import os
import asyncio

app = FastAPI(title="PDF Chatbot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    type: str
    content: str
    session_id: Optional[str] = None

class UploadResponse(BaseModel):
    message: str
    document_id: str
    page_count: int
    chunk_count: int

# In-memory storage for demo
sessions = {}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "PDF Chatbot API is running"}

@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Mock PDF upload endpoint"""
    
    # Validate file type
    if not file.filename or not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate file size (100MB limit)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
    
    # Mock processing
    await asyncio.sleep(1)  # Simulate processing time
    
    return UploadResponse(
        message=f"PDF '{file.filename}' uploaded and processed successfully",
        document_id=f"doc_{int(time.time())}",
        page_count=25,  # Mock page count
        chunk_count=42  # Mock chunk count
    )

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """Mock chat endpoint with streaming response"""
    
    async def generate_mock_response():
        # Simulate processing delay
        await asyncio.sleep(0.5)
        
        # Send initial response
        yield f"data: {json.dumps({'type': 'content', 'content': 'This is a mock response from PDF chatbot. '})}\n\n"
        
        await asyncio.sleep(0.3)
        yield f"data: {json.dumps({'type': 'content', 'content': 'The full PDF processing features are not available in this minimal mode. '})}\n\n"
        
        await asyncio.sleep(0.3)
        yield f"data: {json.dumps({'type': 'content', 'content': 'Please install the full ML dependencies to enable actual PDF parsing and RAG functionality. '})}\n\n"
        
        await asyncio.sleep(0.3)
        yield f"data: {json.dumps({'type': 'content', 'content': 'Your question was: \"' + request.message + '\"'})}\n\n"
        
        # Send completion
        session_id = request.session_id or f"session_{int(time.time())}"
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
    
    return StreamingResponse(
        generate_mock_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
        }
    )

@app.get("/api/stats")
async def get_stats():
    """Mock stats endpoint"""
    return {
        "documents_processed": 1,
        "total_chunks": 42,
        "active_sessions": len(sessions),
        "system_status": "minimal_mode"
    }

@app.post("/api/export")
async def export_conversation():
    """Mock export endpoint"""
    return {"message": "Export functionality not available in minimal mode"}

@app.delete("/api/reset")
async def reset_system():
    """Mock reset endpoint"""
    sessions.clear()
    return {"message": "System reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
