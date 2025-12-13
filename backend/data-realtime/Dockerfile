FROM python:3.10-slim

# ------------------------------------------------------
# 1️⃣ Install system dependencies for Chrome
# ------------------------------------------------------
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    ca-certificates \
    fonts-liberation \
    libglib2.0-0 \
    libnss3 \
    libgdk-pixbuf-2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libxcursor1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------
# 2️⃣ Add Google Chrome repository
# ------------------------------------------------------
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | \
    gpg --dearmor -o /usr/share/keyrings/google.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google.gpg] https://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list

# ------------------------------------------------------
# 3️⃣ Install Chrome Stable & ChromeDriver
# ------------------------------------------------------
# ❗ Mac M1/M2/M3 → Docker ARM64 → Chrome chỉ có build AMD64
#   Vì vậy phải dùng Chromium thay thế
RUN apt-get update && apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------
# 4️⃣ Working directory
# ------------------------------------------------------
WORKDIR /app
COPY . .

# ------------------------------------------------------
# 5️⃣ Install Python dependencies
# ------------------------------------------------------
RUN pip install --upgrade pip setuptools wheel && pip install .

# ------------------------------------------------------
# 6️⃣ Environment for Selenium
# ------------------------------------------------------
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER=/usr/bin/chromedriver
ENV DISPLAY=:99

# ------------------------------------------------------
# 7️⃣ Run WebSocket server
# ------------------------------------------------------
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
CMD ["python", "-u", "websocket_server.py"]