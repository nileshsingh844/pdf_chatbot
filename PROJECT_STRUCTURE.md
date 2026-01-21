# PDF Chatbot Project Structure

## Overview
A comprehensive PDF chatbot system with FastAPI backend and Next.js frontend, featuring hybrid search (vector + keyword), PDF processing, and intelligent question answering.

## Directory Structure

```
DoCScanner/
├── tracker-chatbot/                    # Main application directory
│   ├── backend/                        # Python FastAPI backend
│   │   ├── app/                        # Core application modules
│   │   │   ├── api/                    # API endpoints
│   │   │   │   └── main.py            # FastAPI routes and endpoints
│   │   │   ├── config.py               # Configuration settings
│   │   │   ├── knowledge_base/         # Vector database and embeddings
│   │   │   │   ├── embedder.py         # Text embedding logic
│   │   │   │   └── vector_store.py     # ChromaDB vector operations
│   │   │   ├── llm/                    # Language model integration
│   │   │   │   ├── groq_client.py      # Groq API client
│   │   │   │   └── prompt_templates.py # RAG prompt templates
│   │   │   ├── pdf_processor/          # PDF processing pipeline
│   │   │   │   ├── chunker.py          # Text chunking strategies
│   │   │   │   └── parser.py           # PDF text extraction
│   │   │   └── retrieval/              # Search and retrieval
│   │   │       └── hybrid_search.py    # Vector + keyword hybrid search
│   │   ├── data/                       # Data storage
│   │   │   └── chroma_db/             # ChromaDB vector database
│   │   ├── Dockerfile                  # Backend Docker configuration
│   │   ├── requirements.txt            # Python dependencies
│   │   ├── simple_main.py             # Main application entry point
│   │   └── minimal_main.py            # Minimal test version
│   ├── frontend/                       # Next.js React frontend
│   │   ├── app/                        # Next.js App Router
│   │   │   ├── globals.css            # Global styles
│   │   │   ├── layout.tsx             # Root layout component
│   │   │   └── page.tsx               # Main page component
│   │   ├── components/                 # React components
│   │   │   ├── chat/                   # Chat-related components
│   │   │   │   └── chat-interface.tsx # Main chat UI
│   │   │   ├── pdf/                    # PDF-related components
│   │   │   │   └── pdf-upload.tsx     # PDF upload interface
│   │   │   ├── settings/              # Settings components
│   │   │   └── ui/                     # Reusable UI components
│   │   ├── lib/                        # Utility libraries
│   │   │   ├── api.ts                  # API client functions
│   │   │   ├── types.ts                # TypeScript type definitions
│   │   │   └── utils.ts                # Utility functions
│   │   ├── Dockerfile                  # Frontend Docker configuration
│   │   ├── package.json               # Node.js dependencies
│   │   ├── tsconfig.json              # TypeScript configuration
│   │   ├── tailwind.config.js         # Tailwind CSS configuration
│   │   └── next.config.js             # Next.js configuration
│   ├── docker-compose.yml              # Multi-container Docker setup
│   ├── .env                           # Environment variables
│   ├── README.md                      # Project documentation
│   └── quectel-5g-lte-advanced-module-product-overview.pdf # Sample PDF for testing
└── data/                              # Shared data directory
    ├── chroma_db/                     # Vector database storage
    └── uploads/                       # Uploaded PDF files
```

## Core Components

### Backend Architecture

#### 1. API Layer (`app/api/main.py`)
- **Health Check**: `/api/health` - Service status monitoring
- **PDF Upload**: `/api/upload` - PDF file processing and storage
- **Chat Interface**: `/api/chat` - Question answering with streaming responses
- **Document Management**: `/api/documents` - Document listing and management

#### 2. Knowledge Base (`app/knowledge_base/`)
- **Vector Store**: ChromaDB integration for vector storage and retrieval
- **Embedder**: Text embedding using sentence-transformers
- **Document Processing**: PDF chunking and vectorization pipeline

#### 3. LLM Integration (`app/llm/`)
- **Groq Client**: Integration with Groq API for LLM responses
- **Prompt Templates**: RAG (Retrieval-Augmented Generation) prompt engineering
- **Response Generation**: Context-aware answer generation

#### 4. PDF Processing (`app/pdf_processor/`)
- **Parser**: PDF text extraction using PyPDF2
- **Chunker**: Intelligent text chunking with overlap strategies
- **Preprocessing**: Text cleaning and normalization

#### 5. Retrieval System (`app/retrieval/`)
- **Hybrid Search**: Combination of vector search and keyword search
- **Ranking**: Result ranking and relevance scoring
- **Context Assembly**: Context preparation for LLM

### Frontend Architecture

#### 1. App Router (`app/`)
- **Layout**: Root layout with navigation and providers
- **Page**: Main application page with chat interface
- **Global Styles**: Tailwind CSS and custom styling

#### 2. Components (`components/`)
- **Chat Interface**: Real-time chat with streaming responses
- **PDF Upload**: Drag-and-drop PDF upload interface
- **UI Components**: Reusable UI elements with shadcn/ui

#### 3. Libraries (`lib/`)
- **API Client**: Type-safe API communication
- **Type Definitions**: TypeScript interfaces and types
- **Utilities**: Helper functions and utilities

## Key Features

### 1. Hybrid Search System
- **Vector Search**: Semantic similarity using embeddings
- **Keyword Search**: Traditional text search
- **Ranking Fusion**: Combined relevance scoring

### 2. PDF Processing Pipeline
- **Multi-format Support**: PDF, DOCX, TXT files
- **Intelligent Chunking**: Context-aware text segmentation
- **Metadata Extraction**: Document structure and content analysis

### 3. Real-time Chat
- **Streaming Responses**: Real-time answer streaming
- **Session Management**: Conversation history tracking
- **Context Preservation**: Multi-turn conversation support

### 4. RAG Architecture
- **Retrieval**: Relevant document chunk retrieval
- **Augmentation**: Context enhancement with retrieved content
- **Generation**: LLM-powered answer generation

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: ChromaDB (vector database)
- **LLM**: Groq API
- **Embeddings**: Sentence Transformers
- **PDF Processing**: PyPDF2
- **Container**: Docker

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **HTTP Client**: Fetch API
- **Container**: Docker

## Configuration

### Environment Variables (`.env`)
```
# Backend Configuration
GROQ_API_KEY=your_groq_api_key
CHROMA_DB_PATH=./data/chroma_db
UPLOAD_DIR=./data/uploads

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Docker Setup
- **Backend Dockerfile**: Python environment with dependencies
- **Frontend Dockerfile**: Node.js environment with Next.js build
- **Docker Compose**: Multi-service orchestration

## Data Flow

1. **PDF Upload**: User uploads PDF → Backend processes → Text extraction → Chunking → Embedding → Vector storage
2. **Question Processing**: User question → Hybrid search → Context retrieval → LLM generation → Streaming response
3. **Session Management**: Conversation history → Context preservation → Multi-turn support

## Development Setup

### Backend
```bash
cd tracker-chatbot/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python simple_main.py
```

### Frontend
```bash
cd tracker-chatbot/frontend
npm install
npm run dev
```

### Docker
```bash
cd tracker-chatbot
docker-compose up --build
```

## Testing

### Health Checks
- Backend: `curl http://localhost:8000/api/health`
- Frontend: `curl http://localhost:3000`

### Sample Test
```bash
# Upload PDF
curl -X POST -F "file=@sample.pdf" http://localhost:8000/api/upload

# Ask Question
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are the key features?"}'
```

## Deployment

### Production Considerations
- **Environment Variables**: Secure API key management
- **Database Persistence**: Persistent volume for ChromaDB
- **Scaling**: Horizontal scaling with load balancers
- **Monitoring**: Health checks and logging
- **Security**: CORS configuration and authentication

## Performance Optimization

### Backend
- **Vector Indexing**: Optimized ChromaDB configuration
- **Caching**: Response and embedding caching
- **Batch Processing**: Efficient PDF processing
- **Async Operations**: Non-blocking I/O operations

### Frontend
- **Code Splitting**: Dynamic component loading
- **Image Optimization**: Next.js image optimization
- **Bundle Analysis**: Optimized bundle sizes
- **Caching**: API response caching

## Monitoring and Logging

### Backend Logs
- **Application Logs**: Structured logging with levels
- **API Logs**: Request/response tracking
- **Error Logs**: Exception handling and reporting

### Frontend Monitoring
- **Performance Metrics**: Core Web Vitals
- **Error Tracking**: Client-side error reporting
- **User Analytics**: Usage patterns and insights
