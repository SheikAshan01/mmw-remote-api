# Use base image with apt support
FROM python:3.11-slim

# Install system packages (av related)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavdevice-dev libavfilter-dev libavformat-dev \
    libavcodec-dev libavutil-dev libswscale-dev libswresample-dev \
    pkg-config build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
