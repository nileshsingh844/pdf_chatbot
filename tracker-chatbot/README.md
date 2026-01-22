---
title: PDF Chatbot with Hybrid RAG
emoji: 📄
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# PDF Chatbot - RAG-powered Document Assistant

A modern web application that allows you to upload PDF documents and chat with them using advanced RAG (Retrieval-Augmented Generation) technology.

## 🚀 Features

- **📄 PDF Upload**: Drag & drop interface with progress tracking
- **🔍 Hybrid Search**: Combines vector search and BM25 keyword search
- **🤖 AI Responses**: Powered by Groq's Llama 3.1 model
- **📖 Citations**: Automatic page references in responses
- **🌊 Streaming**: Real-time response streaming
- **🎨 Modern UI**: Responsive design with Tailwind CSS
- **🌙 Dark Mode**: Theme toggle support
- **💾 Export**: Download conversations as markdown
- **📱 Mobile**: Optimized for all devices

## 🏗️ Architecture

- **Frontend**: Next.js 14 with TypeScript
- **Backend**: FastAPI with Python
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers
- **LLM**: Groq API (Llama 3.1)
- **Search**: Hybrid (Vector + BM25)

## 🚀 Quick Start

### Local Development

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: Modern component library
- **React Dropzone**: File upload handling
- **React Markdown**: Message rendering
- **Lucide React**: Icon library

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Groq API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd tracker-chatbot
```

### 2. Configure Environment

Create a `.env` file with your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run with Docker

```bash
docker-compose up -d
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### 4. Manual Setup (Optional)

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Usage

1. **Upload a PDF**: Drag and drop a PDF file (max 100MB)
2. **Wait for processing**: The system will extract text and create embeddings
3. **Ask questions**: Type questions about the document content
4. **Get answers**: Receive responses with page citations
5. **Export conversation**: Download the chat as markdown

## API Endpoints

### Upload PDF
```http
POST /api/upload
Content-Type: multipart/form-data
```

### Chat Streaming
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What are the power requirements?",
  "session_id": "optional_session_id"
}
```

### System Stats
```http
GET /api/stats
```

### Export Conversation
```http
POST /api/export
Content-Type: multipart/form-data

session_id=your_session_id
```

### Health Check
```http
GET /api/health
```

## Configuration

### Backend Settings

Key configuration options in `backend/app/config.py`:

- **Chunk size**: 800 tokens (default)
- **Chunk overlap**: 150 tokens (default)
- **Top-k results**: 8 documents (default)
- **Similarity threshold**: 0.7 (default)
- **Hybrid alpha**: 0.5 (50% vector, 50% BM25)

### Frontend Settings

Environment variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Performance

- **PDF Processing**: <30s for 50-page documents
- **Query Response**: <3s average
- **Streaming Latency**: <50ms between chunks
- **Memory Usage**: <2GB RAM

## Development

### Project Structure

The codebase follows a modular architecture:

- **Backend modules**: Independent components for PDF processing, embeddings, search, and LLM
- **Frontend components**: Reusable React components with TypeScript
- **API layer**: Type-safe client with streaming support
- **Configuration**: Centralized settings with environment variables

### Adding Features

1. **Backend**: Add new routes in `backend/app/api/main.py`
2. **Frontend**: Create components in `frontend/components/`
3. **Types**: Update TypeScript interfaces in `frontend/lib/types.ts`
4. **Styling**: Use Tailwind CSS and shadcn/ui components

## Deployment

### Docker Production

```bash
# Build and run in production mode
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables

Production environment variables:
- `GROQ_API_KEY`: Required for LLM functionality
- `NEXT_PUBLIC_API_URL`: Frontend API endpoint
- `NODE_ENV`: Set to `production`

## Troubleshooting

### Common Issues

1. **PDF Upload Fails**
   - Check file size (max 100MB)
   - Ensure PDF contains text content
   - Verify file permissions

2. **No Search Results**
   - Check similarity threshold (try lower values)
   - Verify document was processed successfully
   - Check backend logs for errors

3. **Streaming Issues**
   - Ensure CORS is configured correctly
   - Check network connectivity
   - Verify API endpoints are accessible

### Logs

```bash
# Backend logs
docker-compose logs backend

# Frontend logs
docker-compose logs frontend

# All logs
docker-compose logs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub

---

**Built with ❤️ using modern web technologies**
