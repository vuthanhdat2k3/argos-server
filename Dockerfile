# Use slim Python image
FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install CPU-only PyTorch first (smaller than default CUDA version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install remaining packages
COPY requirements.txt .
RUN pip install --no-cache-dir argostranslate>=1.9.0 \
    && rm -rf /root/.cache/pip/* \
    && rm -rf /tmp/*

# Copy only the server file
COPY server.py .

# Expose port
EXPOSE 5100

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=5100
ENV PYTHONUNBUFFERED=1

# Run server - models will be downloaded on first request
CMD ["python", "server.py"]
