# Simple alarm processor service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Copy the alarm processor
COPY alarm_processor.py /app/alarm_processor.py
WORKDIR /app

# Create non-root user
RUN useradd -m -s /bin/bash alarmuser
USER alarmuser

# Run the alarm processor
CMD ["python3", "alarm_processor.py"]
