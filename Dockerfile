FROM python:3.12-slim

# Install system dependencies for Chrome/Chromedriver
RUN echo "deb http://mirrors.aliyun.com/debian trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian trixie-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security trixie-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    chromium chromium-driver \
    fonts-liberation libnss3 libxi6 libxcursor1 libxrandr2 libxss1 libxcomposite1 libasound2 \
    && rm -rf /var/lib/apt/lists/*



# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple && \
    playwright install --with-deps chromium

# Expose port
EXPOSE 5000

# Start app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app", "--timeout", "120", "--workers", "2"]
