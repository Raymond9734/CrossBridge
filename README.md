# CareBridge Healthcare Management System

## 🏥 Overview

CareBridge is a comprehensive healthcare management system built with Django and React that facilitates seamless communication between patients and healthcare providers. This restructured version follows Django best practices with a modular architecture for enhanced maintainability and scalability.

## 🚀 Key Features

- **User Management**: Role-based access for patients, doctors, and administrators
- **Appointment Booking**: Real-time availability checking and booking system
- **Medical Records**: Comprehensive patient health records with vitals tracking
- **Prescription Management**: Digital prescription creation and tracking
- **Lab Results**: Laboratory test results management
- **Notification System**: Multi-channel notifications (email, SMS, in-app)
- **Review System**: Patient feedback and doctor rating system
- **Dashboard Analytics**: Role-specific dashboards with key metrics
- **Real-time Updates**: WebSocket integration for live updates
- **API Documentation**: Comprehensive API documentation with Swagger/OpenAPI

## 🏗️ Architecture

### Modular App Structure

```
CareBridge/
├── apps/
│   ├── core/              # Base classes, utilities, middleware
│   ├── accounts/          # User management and profiles
│   ├── appointments/      # Appointment booking and scheduling
│   ├── medical_records/   # Health records and prescriptions
│   ├── notifications/     # Notification system
│   └── api/               # API endpoints and documentation
├── config/                # Django settings and configuration
├── frontend/              # React/Inertia.js frontend
├── requirements/          # Environment-specific requirements
└── tests/                 # Comprehensive test suite
```

### Technology Stack

**Backend:**

- Django 5.1.5 with Django REST Framework
- PostgreSQL database with Redis caching
- Celery for asynchronous task processing
- JWT authentication with session fallback

**Frontend:**

- React 19.0 with Inertia.js for SPA experience
- Tailwind CSS for styling
- Vite for build tooling
- Lucide React for icons

**Infrastructure:**

- Redis for caching and task queue
- Nginx for reverse proxy and static files
- Docker for containerization
- Celery Beat for scheduled tasks

## 📊 Performance Optimizations

### Database Optimizations

- **Indexes**: Strategic indexing on frequently queried fields
- **Query Optimization**: N+1 query elimination with select_related/prefetch_related
- **Connection Pooling**: Database connection pooling for better resource utilization
- **Soft Deletes**: Soft delete implementation for data retention

### Caching Strategy

- **Redis Caching**: Multi-level caching for user data, appointments, and notifications
- **Cache Invalidation**: Smart cache invalidation on data updates
- **Query Result Caching**: Expensive query results cached with TTL
- **Session Caching**: Redis-backed session storage

### API Optimizations

- **Pagination**: Efficient pagination with cursor-based pagination for large datasets
- **Serializer Optimization**: Optimized serializers with field selection
- **Rate Limiting**: Endpoint-specific rate limiting
- **Request Throttling**: User and IP-based throttling

## 🔐 Security Features

### Authentication & Authorization

- **JWT Tokens**: Secure JWT-based authentication
- **Role-Based Access**: Granular permissions for different user roles
- **Session Management**: Secure session handling with Redis
- **Password Security**: Bcrypt password hashing with complexity requirements

### Data Protection

- **HTTPS Enforcement**: SSL/TLS encryption in production
- **CSRF Protection**: Cross-site request forgery protection
- **XSS Prevention**: Cross-site scripting protection
- **SQL Injection Prevention**: ORM-based query protection
- **Sensitive Data Masking**: PII masking in logs and responses

### API Security

- **Rate Limiting**: Configurable rate limits per endpoint
- **Input Validation**: Comprehensive input validation and sanitization
- **Error Handling**: Secure error responses without information leakage
- **Audit Logging**: Complete audit trail for all operations

## 📋 API Documentation

### Authentication Endpoints

```http
POST /api/v1/auth/login/
POST /api/v1/auth/register/
POST /api/v1/auth/logout/
GET  /api/v1/auth/me/
```

### User Management

```http
GET    /api/v1/profiles/
PUT    /api/v1/profiles/{id}/
GET    /api/v1/profiles/dashboard_data/
GET    /api/v1/doctors/
GET    /api/v1/doctors/{id}/available_slots/
GET    /api/v1/doctors/{id}/statistics/
```

### Appointment Management

```http
GET    /api/v1/appointments/
POST   /api/v1/appointments/
GET    /api/v1/appointments/{id}/
POST   /api/v1/appointments/{id}/confirm/
POST   /api/v1/appointments/{id}/cancel/
POST   /api/v1/appointments/{id}/complete/
POST   /api/v1/appointment-booking/book/
GET    /api/v1/appointment-booking/available_doctors/
```

### Medical Records

```http
GET    /api/v1/medical-records/
POST   /api/v1/medical-records/
GET    /api/v1/medical-records/{id}/
PUT    /api/v1/medical-records/{id}/
GET    /api/v1/prescriptions/
POST   /api/v1/prescriptions/
POST   /api/v1/prescriptions/{id}/deactivate/
GET    /api/v1/lab-results/
POST   /api/v1/lab-results/
```

### Notifications

```http
GET    /api/v1/notifications/
POST   /api/v1/notifications/mark_all_read/
POST   /api/v1/notifications/{id}/mark_read/
GET    /api/v1/notification-preferences/
PUT    /api/v1/notification-preferences/
```

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── test_accounts/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_services.py
│   └── test_serializers.py
├── test_appointments/
├── test_medical_records/
├── test_notifications/
├── test_api/
└── fixtures/
```

### Test Coverage

```python
# pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
python_files = tests.py test_*.py *_tests.py
addopts = --cov=apps --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Test command
pytest --cov=apps --cov-report=html --cov-report=term-missing
```

### Example Test Cases

```python
# tests/test_appointments/test_services.py
import pytest
from django.contrib.auth.models import User
from app.account.models import UserProfile, DoctorProfile
from app.appointment.services import AppointmentService
from app.appointment.models import Appointment


@pytest.mark.django_db
class TestAppointmentService:
    def test_book_appointment_success(self):
        """Test successful appointment booking."""
        # Create test users
        patient = User.objects.create_user(
            username='patient', email='patient@test.com', password='pass123'
        )
        doctor = User.objects.create_user(
            username='doctor', email='doctor@test.com', password='pass123'
        )

        # Create profiles
        patient_profile = UserProfile.objects.create(user=patient, role='patient')
        doctor_profile = UserProfile.objects.create(user=doctor, role='doctor')
        DoctorProfile.objects.create(user_profile=doctor_profile)

        # Test appointment booking
        service = AppointmentService()
        appointment = service.book_appointment(
            patient=patient,
            doctor_id=doctor.id,
            appointment_date='2024-12-25',
            start_time='10:00:00',
            appointment_type='consultation'
        )

        assert appointment.patient == patient
        assert appointment.doctor == doctor
        assert appointment.status == 'pending'

    def test_book_appointment_conflict(self):
        """Test booking appointment with time conflict."""
        # Setup existing appointment
        # Test conflict detection
        # Assert ConflictError is raised
        pass

    def test_get_available_slots(self):
        """Test getting available time slots for doctor."""
        # Setup doctor availability
        # Test slot generation
        # Assert correct slots returned
        pass
```

### Integration Tests

```python
# tests/test_api/test_appointment_booking.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestAppointmentBookingAPI:
    def setup_method(self):
        self.client = APIClient()
        self.patient = User.objects.create_user(
            username='patient', email='patient@test.com', password='pass123'
        )
        self.client.force_authenticate(user=self.patient)

    def test_book_appointment_endpoint(self):
        """Test appointment booking via API."""
        data = {
            'doctor_id': 1,
            'appointment_date': '2024-12-25',
            'start_time': '10:00:00',
            'appointment_type': 'consultation',
            'patient_notes': 'Regular checkup'
        }

        response = self.client.post('/api/v1/appointment-booking/book/', data)
        assert response.status_code == 201
        assert 'id' in response.data

    def test_get_available_doctors(self):
        """Test getting available doctors."""
        response = self.client.get('/api/v1/appointment-booking/available_doctors/')
        assert response.status_code == 200
        assert 'doctors' in response.data
```

## 🚀 Deployment Guide

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd CareBridge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements/development.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your settings

# Setup database
python manage.py migrate
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py create_sample_data

# Start development server
python manage.py runserver

# Start Celery worker (separate terminal)
celery -A config worker -l info

# Start Celery beat (separate terminal)
celery -A config beat -l info
```

### Production Deployment

```bash
# Install production dependencies
pip install -r requirements/production.txt

# Set production environment variables
export DJANGO_SETTINGS_MODULE=config.settings.production
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgres://user:pass@host/db
export REDIS_URL=redis://host:6379/0

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Start with Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements/production.txt .
RUN pip install -r production.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/carebridge
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: carebridge
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  celery:
    build: .
    command: celery -A config worker -l info
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A config beat -l info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

## 📈 Monitoring and Logging

### Application Monitoring

```python
# config/settings/production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/carebridge/app.log',
            'maxBytes': 15728640,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/carebridge/error.log',
            'maxBytes': 15728640,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Performance Monitoring

```python
# Custom middleware for performance tracking
class PerformanceTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        # Log slow requests
        if duration > 1.0:
            logger.warning(f'Slow request: {request.path} took {duration:.2f}s')

        # Add performance header
        response['X-Response-Time'] = f'{duration:.3f}s'

        return response
```

## 🔧 Maintenance and Operations

### Database Maintenance

```bash
# Backup database
pg_dump carebridge > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
psql carebridge < backup_file.sql

# Clean up old sessions
python manage.py clearsessions

# Clean up old notifications
python manage.py cleanup_old_notifications
```

### Cache Maintenance

```bash
# Clear all cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Monitor Redis
redis-cli info memory
redis-cli --scan --pattern "*" | wc -l
```

### Health Checks

```python
# health_check.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    """Basic health check endpoint."""
    status = {
        'status': 'healthy',
        'database': 'ok',
        'cache': 'ok',
        'timestamp': timezone.now().isoformat()
    }

    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        status['database'] = 'error'
        status['status'] = 'unhealthy'

    try:
        # Test cache
        cache.set('health_check', 'ok', 30)
        if cache.get('health_check') != 'ok':
            raise Exception('Cache test failed')
    except Exception:
        status['cache'] = 'error'
        status['status'] = 'unhealthy'

    return JsonResponse(status)
```

## 📚 Additional Resources

- **API Documentation**: Available at `/api/docs/` (Swagger UI)
- **Admin Interface**: Available at `/admin/`
- **Database Schema**: See documentation diagrams above
- **Code Examples**: Check the `examples/` directory
- **Contributing Guidelines**: See `CONTRIBUTING.md`
- **Changelog**: See `CHANGELOG.md`

## 🤝 Support and Contributing

For support, please open an issue on the repository or contact the development team.

Contributions are welcome! Please read the contributing guidelines and submit pull requests for any improvements.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**CareBridge Development Team**  
_Building the future of healthcare management_
