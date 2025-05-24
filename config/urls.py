from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from inertia import render as inertia_render

# Main URL patterns
urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/", include("app.api.urls")),
    # Legacy app URLs (for backward compatibility during migration)
    path("legacy/", include("app.urls")),
    # Frontend routes (Inertia.js)
    path("", include("app.frontend.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "CareBridge Administration"
admin.site.site_title = "CareBridge Admin"
admin.site.index_title = "Welcome to CareBridge Administration"
