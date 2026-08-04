# Dockerfile for Flask app deployment
FROM python:3.12-slim

WORKDIR /app

# Install build dependencies and app dependencies
COPY lms/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY lms /app

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
CMD ["gunicorn", "run:app", "-b", "0.0.0.0:$PORT", "--workers", "2"]
