FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY backend/requirements.txt /app/backend/requirements.txt
COPY requirements.txt /app/requirements.txt

# Install all Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
RUN pip install --no-cache-dir streamlit>=1.35.0 requests>=2.32.0

# Copy entire project
COPY . /app

# Create data directories
RUN mkdir -p /app/backend/data/uploads \
             /app/backend/data/db \
             /app/backend/data/faiss

# Expose ports
EXPOSE 7860
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting FastAPI backend..."\n\
cd /app && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --app-dir /app &\n\
sleep 5\n\
echo "Starting Streamlit frontend..."\n\
cd /app && python -m streamlit run app.py \
  --server.port 7860 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/bin/bash", "/app/start.sh"]
