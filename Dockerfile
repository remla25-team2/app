# Use Python image
FROM python:3.10-slim

RUN apt update && apt upgrade -y && apt install -y git

# Copy files
COPY requirements.txt ./
RUN pip install --no-cache-dir  -r requirements.txt

COPY . .

# Set work directory
WORKDIR /app

# Expose the Flask port
EXPOSE 5000

CMD ["python", "app.py"]