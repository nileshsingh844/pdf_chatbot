# PDF Chatbot - Hugging Face Space Deployment

## 🚀 Production Setup

This repository is configured for Hugging Face Docker Space deployment with Next.js frontend and FastAPI backend.

## 📋 Architecture

- **Frontend**: Next.js on port 7860 (public)
- **Backend**: FastAPI on port 8000 (internal)
- **API Proxy**: Next.js rewrites `/api/* → http://127.0.0.1:8000/api/*`

## 🔧 HF Space Configuration

### Space Settings
- **Type**: Docker Space
- **Port**: 7860
- **Hardware**: CPU (recommended for Groq API)
- **Public**: Yes

### Required Secrets
Add these in your HF Space settings:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

### Optional Environment Variables
```bash
# Backend Configuration
CHROMA_DB_PATH=./data/chroma_db
UPLOAD_DIR=./data/uploads

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📁 Repository Structure

```
tracker-chatbot/
├── Dockerfile              # Multi-service container setup
├── start.sh                # Startup script
├── backend/                # FastAPI Python backend
├── frontend/               # Next.js TypeScript frontend
├── README.md               # Project documentation
├── README_HF_SPACE.md      # This deployment guide
└── .env.example            # Environment variables template
```

## 🐳 Docker Setup

The Dockerfile builds a single container running both services:

1. **Backend Setup**: Python venv with dependencies
2. **Frontend Build**: Next.js production build
3. **Startup**: Backend (background) + Frontend (main)

### Build Process
```dockerfile
# Install Python dependencies
COPY backend/ /app/backend/
RUN python3 -m venv /app/backend/.venv
RUN pip install -r requirements.txt

# Build Next.js frontend
COPY frontend/ /app/frontend/
RUN npm ci && npm run build

# Start both services
CMD ["/app/start.sh"]
```

## 🔄 API Proxy Configuration

Next.js rewrites API calls to backend:

```javascript
// frontend/next.config.js
async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: "http://127.0.0.1:8000/api/:path*",
    },
  ];
}
```

This allows frontend to call:
- `fetch("/api/health")` → FastAPI health check
- `fetch("/api/chat")` → FastAPI chat endpoint
- `fetch("/api/upload")` → FastAPI PDF upload

## 🌐 CORS Configuration

Backend allows requests from HF Space:

```python
# backend/app/config.py
cors_origins: list = [
  "http://localhost:3000", 
  "http://localhost:7860", 
  "http://127.0.0.1:7860"
]
```

## 🚀 Deployment Steps

### 1. Create HF Space
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose **Docker** as SDK
4. Set **Space name** and **Hardware**
5. Clone the repository

### 2. Push Code
```bash
git clone https://huggingface.co/spaces/your-username/your-space-name
cd your-space-name
# Copy your tracker-chatbot files
git add .
git commit -m "Initial deployment"
git push
```

### 3. Configure Secrets
1. Go to your Space settings
2. Add `GROQ_API_KEY` in "Repository Secrets"
3. Restart the Space

### 4. Monitor Build
- HF will automatically build the Docker image
- Check the "Logs" tab for build progress
- Once built, the Space will be publicly accessible

## 🔍 API Endpoints

### Health Check
```bash
GET /api/health
```

### PDF Upload
```bash
POST /api/upload
Content-Type: multipart/form-data
```

### Chat Interface
```bash
POST /api/chat
Content-Type: application/json
{
  "message": "What are the key features?",
  "session_id": "user_session_123"
}
```

### Document Management
```bash
GET /api/documents     # List documents
DELETE /api/documents/{id}  # Delete document
```

## 📱 Features

- **📄 PDF Upload**: Drag & drop with progress tracking
- **🔍 Hybrid Search**: Vector + BM25 keyword search
- **🤖 AI Responses**: Groq Llama 3.1 integration
- **📖 Citations**: Automatic page references
- **🌊 Streaming**: Real-time response streaming
- **🎨 Modern UI**: Responsive design with Tailwind CSS
- **🌙 Dark Mode**: Theme toggle support
- **💾 Export**: Download conversations as markdown
- **📱 Mobile**: Optimized for all devices

## 🛠️ Development

### Local Development
```bash
# Backend
cd tracker-chatbot/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python simple_main.py

# Frontend (separate terminal)
cd tracker-chatbot/frontend
npm install
npm run dev
```

### Docker Local Testing
```bash
cd tracker-chatbot
docker build -t pdf-chatbot .
docker run -p 7860:7860 -e GROQ_API_KEY=your_key pdf-chatbot
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Build Failures
- Check Docker logs for specific errors
- Ensure all dependencies are in requirements.txt
- Verify Node.js and Python versions

#### 2. API Connection Issues
- Verify Next.js rewrites in next.config.js
- Check CORS origins in backend config
- Ensure backend is running on port 8000

#### 3. Environment Variables
- Add secrets in HF Space settings
- Verify variable names match exactly
- Restart space after adding secrets

#### 4. File Upload Issues
- Check file size limits in backend config
- Verify upload directory permissions
- Monitor backend logs for errors

### Debug Commands
```bash
# Check backend health
curl http://localhost:8000/api/health

# Check frontend build
cd frontend && npm run build

# Docker logs
docker logs <container_id>
```

## 📊 Performance

### Optimizations
- **Backend**: Async processing, efficient chunking
- **Frontend**: Code splitting, image optimization
- **Database**: ChromaDB vector indexing
- **API**: Response streaming, caching

### Resource Requirements
- **CPU**: 2+ cores recommended
- **Memory**: 4GB+ RAM
- **Storage**: 10GB+ for documents
- **Network**: Stable internet for Groq API

## 🔒 Security

### Best Practices
- Use HF Space secrets for API keys
- Implement rate limiting if needed
- Validate file uploads on backend
- Use HTTPS in production
- Monitor API usage and logs

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📈 Monitoring

### Health Checks
- Backend: `/api/health` endpoint
- Frontend: Application loading
- Database: ChromaDB connection status

### Logging
- Backend logs: FastAPI uvicorn logs
- Frontend logs: Next.js build logs
- System logs: Docker container logs

### Metrics to Track
- Response times
- Error rates
- User sessions
- Document processing times
- API usage patterns

## 🎯 Next Steps

### Potential Enhancements
1. **Authentication**: User login system
2. **Database**: PostgreSQL for user data
3. **Caching**: Redis for performance
4. **Monitoring**: Prometheus + Grafana
5. **Scaling**: Load balancer setup
6. **CI/CD**: Automated testing and deployment

### Production Considerations
- Domain customization
- SSL certificates
- Backup strategies
- Disaster recovery
- Performance monitoring
- User analytics

---

## 🎉 Ready for Production

Your PDF Chatbot is now configured for Hugging Face Space deployment with:

✅ **Docker Multi-Service Setup**
✅ **API Proxy Configuration**
✅ **CORS Security**
✅ **Environment Variables**
✅ **Production Optimizations**
✅ **Monitoring & Logging**

Deploy to Hugging Face Spaces and start chatting with your PDFs!
