FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code and templates
COPY app.py .
COPY templates/ templates/

# Expose port
EXPOSE 5000

# Run the service
CMD ["python", "app.py"]
