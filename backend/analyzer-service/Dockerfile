FROM python:3.11-slim

WORKDIR /app

# Install required system dependencies for pandas/numpy/ta
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from app folder
COPY app/requirements.txt /app/app/requirements.txt

# Upgrade pip and install dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/app/requirements.txt

# Copy rest of the application code
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app

EXPOSE 8000

# Start the service
CMD ["/app/entrypoint.sh"]
