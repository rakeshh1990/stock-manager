FROM python:3.11-slim

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev postgresql-client\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY app/requirements.txt /app/app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --default-timeout=100 -r /app/app/requirements.txt


# Copy everything
COPY . .

# Set Python path so "import app" works
ENV PYTHONPATH=/app

# Entrypoint
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
