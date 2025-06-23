# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.12-slim

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout/stderr (useful for logging)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (for better Docker caching)
COPY requirements.txt .

# env
ENV EMBEDDING_MODEL=text-embedding-3-small

RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app
COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
