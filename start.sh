#!/bin/bash
set -e

echo "Starting CareBridge Production Server..."

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres}; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "Database is ready!"

# Create directories
echo "Setting up directories..."
mkdir -p /app/staticfiles /app/media

# # Handle Vite manifest - create a minimal one if missing
# if [ ! -f "/app/staticfiles/manifest.json" ]; then
#     echo "Creating minimal Vite manifest..."
#     mkdir -p /app/staticfiles
#     cat > /app/staticfiles/manifest.json << 'EOF'
# {
#   "main.js": {
#     "file": "main.js",
#     "src": "main.js",
#     "isEntry": true
#   }
# }
# EOF
# fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Skip static files collection in production (serve directly from volume)
echo "Skipping static files collection..."

# Start Gunicorn
if command -v gunicorn &> /dev/null; then
    exec gunicorn \
        --bind 0.0.0.0:8000 \
        --workers ${GUNICORN_WORKERS:-3} \
        --worker-class gthread \
        --threads ${GUNICORN_THREADS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-30} \
        --log-level ${GUNICORN_LOG_LEVEL:-info} \
        --access-logfile - \
        --error-logfile - \
        CareBridge.wsgi:application
else
    echo "Gunicorn not found, using Django development server..."
    exec python manage.py runserver 0.0.0.0:8000
fi