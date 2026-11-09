FROM python:3.12-slim

WORKDIR /app

# تثبيت اعتمادات النظام
RUN apt-get update && apt-get install -y \
    gcc \ 
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# نسخ requirements.txt فقط أولاً (Docker layer caching)
COPY requirements.txt .

# إنشاء virtual environment وتثبيت المتطلبات
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# تثبيت dos2unix لحل مشاكل نهاية الأسطر في Windows
RUN apt-get update && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*


# نسخ باقي المشروع
COPY . .

# إنشاء المجلدات المطلوبة
RUN mkdir -p /app/staticfiles /app/media

# نسخ entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

# منفذ التشغيل
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/users/health/', timeout=5)" || exit 1

ENTRYPOINT ["/entrypoint.sh"]