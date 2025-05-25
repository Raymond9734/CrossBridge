#!/bin/bash
set -e

echo "🔧 Handling Django migrations..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
python manage.py check --database default

# Handle migrations with conflict resolution
handle_migrations() {
    # Check if there are unapplied migrations
    if python manage.py showmigrations --plan | grep -q "\[ \]"; then
        echo "📝 Found unapplied migrations"
        
        # Try normal migration first
        if ! python manage.py migrate --noinput; then
            echo "⚠️  Migration failed, resolving conflicts..."
            
            # Try fake-initial for existing tables
            python manage.py migrate --fake-initial --noinput || true
            
            # Try migration again
            if ! python manage.py migrate --noinput; then
                echo "🔨 Creating fresh migrations..."
                
                # Remove migration files (keep __init__.py)
                find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
                find . -path "*/migrations/*.pyc" -delete
                
                # Create fresh migrations
                python manage.py makemigrations --noinput
                python manage.py migrate --noinput
            fi
        fi
    else
        echo "✅ All migrations are up to date"
    fi
}

# Run migration handling
handle_migrations

echo "✅ Migrations complete!"

# Execute the provided command or default to runserver
if [ $# -eq 0 ]; then
    exec python manage.py runserver 0.0.0.0:8000
else
    exec "$@"
fi