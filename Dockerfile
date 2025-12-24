FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install Python dependencies
# Official image has system dependencies, we just need python deps
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# Expose port
EXPOSE 5000

# Start app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app", "--timeout", "120", "--workers", "1"]
