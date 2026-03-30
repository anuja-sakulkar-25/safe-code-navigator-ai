# Use official Python slim image — smaller = faster Cloud Run startup
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (Docker caches this layer if requirements don't change)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Tell Cloud Run which port to listen on
ENV PORT=8080
EXPOSE 8080

# Command to start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]