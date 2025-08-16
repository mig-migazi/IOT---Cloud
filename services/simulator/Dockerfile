FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY smart_breaker_simulator.py .

# Run the service
CMD ["python", "smart_breaker_simulator.py"]
