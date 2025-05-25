# CareBridge/urls.py
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    # API Routes - All API endpoints under /api/
    path("api/", include("app.api.urls")),
    # Page Routes - Minimal page endpoints for SPA
    path("", include("app.frontend.urls")),
    # Static files
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Add Django Debug Toolbar URLs
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

# Customize admin site
admin.site.site_header = "CareBridge Administration"
admin.site.site_title = "CareBridge Admin"
admin.site.index_title = "Welcome to CareBridge Administration"
