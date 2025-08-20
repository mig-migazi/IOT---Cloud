FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (if needed for health checks)
EXPOSE 8080

# Run the bridge service
CMD ["python3", "app.py"]
