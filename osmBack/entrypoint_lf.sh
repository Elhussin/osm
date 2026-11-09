#!/bin/bash
set -e

# Load virtual environment
source /app/venv/bin/activate

echo "Waiting for PostgreSQL..."
python << 'END'
import os
import sys
import time
import psycopg2

max_retries = 5
retry = 0

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

while retry < max_retries:
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.close()
        print("PostgreSQL is ready!")
        sys.exit(0)
    except psycopg2.OperationalError:
        retry += 1
        print(f"PostgreSQL is unavailable - sleeping (attempt {retry}/{max_retries})")
        time.sleep(2)

print("Could not connect to PostgreSQL")
sys.exit(1)
END

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear


echo "Checking for custom command..."
if [ "$#" -gt 0 ]; then
    echo "Executing custom command: $@"
    exec "$@"
else
    echo "Starting Gunicorn..."
    exec gunicorn optics_tenant.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --threads 2 \
        --worker-class gthread \
        --worker-tmp-dir /dev/shm \
        --log-level info \
        --access-logfile - \
        --error-logfile - \
        --timeout 120 \
        --graceful-timeout 30 \
        --keep-alive 5
fi
