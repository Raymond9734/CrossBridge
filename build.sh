#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js and npm if not present
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

# Install and build frontend
cd static
npm install
npm run build
cd ..

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from app.account.models import UserProfile
import os

admin_email = os.environ.get('ADMIN_EMAIL', 'admin@carebridge.com')
admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', admin_email, admin_password)
    UserProfile.objects.get_or_create(user=user, defaults={'role': 'admin'})
    print(f"Superuser created: admin/{admin_password}")
else:
    print("Superuser already exists")
EOF