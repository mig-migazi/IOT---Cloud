FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY enrichment_service.py .

# Run the service
CMD ["python", "enrichment_service.py"]
