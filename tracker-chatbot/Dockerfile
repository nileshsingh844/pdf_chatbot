FROM python:3.9-slim

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy requirements and install Python dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend package.json and install Node.js dependencies
COPY --chown=user frontend/package*.json ./frontend/
RUN cd frontend && npm install

# Copy application code
COPY --chown=user . .

# Build Next.js frontend
RUN cd frontend && npm run build

# Create data directories with proper permissions
RUN mkdir -p ./data/uploads ./data/chroma_db
RUN chmod 755 ./data/uploads ./data/chroma_db

# Expose HF Space port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

# Start the application
CMD ["./start.sh"]
