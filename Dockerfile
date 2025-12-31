FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Create directory for Argos models
RUN mkdir -p /root/.local/share/argos-translate

# Expose port
EXPOSE 5100

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=5100

# Run server
CMD ["python", "server.py"]
