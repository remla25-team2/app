# Use Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy files
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app/ .

# Expose the Flask port
EXPOSE 5000

CMD ["python", "app.py"]