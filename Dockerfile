FROM python:3.13-slim

WORKDIR /app

# Prevent Python from buffering stdout and stderr for immediate logging
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=src

# Install JavaScript runtime required by yt-dlp for solving YouTube challenges
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

# Install system dependencies: ffmpeg, libopus, and gcc for pynacl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus0 \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and files
COPY . .

# Run the bot
CMD ["python", "src/main.py"]
