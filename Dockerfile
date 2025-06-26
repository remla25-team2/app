# Use Python image
FROM python:3.10-slim AS builder

LABEL org.opencontainers.image.source https://github.com/remla25-team2/app

# clean up to reduce image size by avoiding apt cache in image.
RUN apt update && apt upgrade -y && apt install -y git && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Copy files
COPY requirements.txt ./
RUN pip install --no-cache-dir  -r requirements.txt

# For multi stage
FROM python:3.10-slim AS production

LABEL org.opencontainers.image.source https://github.com/remla25-team2/app

COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Set work directory
WORKDIR /app

# Expose the Flask port
EXPOSE 5000

CMD ["python", "app.py"]