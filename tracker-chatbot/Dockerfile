FROM node:20-bullseye

# System deps for Python + build tools
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# -------------------------
# Backend install
# -------------------------
COPY backend/ /app/backend/
RUN python3 -m venv /app/backend/.venv \
 && /app/backend/.venv/bin/pip install --upgrade pip \
 && /app/backend/.venv/bin/pip install -r /app/backend/requirements.txt

# -------------------------
# Frontend install
# -------------------------
COPY frontend/ /app/frontend/
WORKDIR /app/frontend
RUN npm ci
RUN npm run build

# -------------------------
# Start script
# -------------------------
WORKDIR /app
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 7860
CMD ["/app/start.sh"]
