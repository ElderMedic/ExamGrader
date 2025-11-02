FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for screenshot functionality
RUN apt-get update && apt-get install -y \
    libx11-dev \
    libxrandr-dev \
    libxi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY exam_grader ./exam_grader
COPY main.py .

# Create directories for outputs
RUN mkdir -p /app/screenshots /app/results

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "main.py", "--help"]
