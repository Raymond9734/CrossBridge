# Frontend build stage
FROM node:18-alpine AS frontend-build
WORKDIR /app

# Copy package.json and install node dependencies
COPY package*.json ./
RUN npm install

# Copy frontend source code
COPY app/static/src ./app/static/src
COPY vite.config.js ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Build frontend assets
RUN npm run build

# Python production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=CareBridge.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Copy built frontend assets
COPY --from=frontend-build /app/app/static/dist ./app/static/dist

# Create necessary directories (no chown)
RUN mkdir -p /app/staticfiles /app/media

# Run collectstatic as root
RUN python manage.py collectstatic --noinput

# Copy and make startup script executable (no chown)
COPY start.sh .
RUN chmod +x start.sh

# No user switch, run as root
# USER appuser  <-- removed

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/system/health_check/ || exit 1

CMD ["./start.sh"]
