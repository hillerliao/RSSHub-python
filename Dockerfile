FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install Python dependencies
# Official image has system dependencies, we just need python deps
RUN pip install --no-cache-dir -r requirements-full.txt && \
    playwright install chromium

# Set production environment variables
ENV FLASK_CONFIG=production
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Start app using PORT environment variable (default 5000) for compatibility with Zeabur/Heroku
CMD gunicorn -b 0.0.0.0:${PORT:-5000} main:app --timeout 120 --workers 1
