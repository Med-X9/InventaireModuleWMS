"""
URL configuration for the project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.i18n import set_language
from django.conf import settings
from django.conf.urls.static import static
from .api_info import api_info

schema_view = get_schema_view(
    openapi.Info(
        title=api_info['title'],
        default_version=api_info['version'],
        description=api_info['description'],
        contact=openapi.Contact(
            name=api_info['contact']['name'],
            email=api_info['contact']['email']
        ),
        license=openapi.License(
            name=api_info['license']['name'],
            url=api_info['license']['url']
        ),
        terms_of_service=api_info['termsOfService'],
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('web/api/', include('apps.inventory.urls')),
        path('mobile/api/', include('apps.mobile.urls')),
        path('api/auth/', include('apps.users.urls')),
        path('masterdata/api/', include('apps.masterdata.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('web/api/', include('apps.inventory.urls')),
    path('mobile/api/', include('apps.mobile.urls')),
    path('api/auth/', include('apps.users.urls')),
    path('masterdata/api/', include('apps.masterdata.urls')),
    path('set_language/', set_language, name='set_language'),
    
    # Documentation API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Ajout des URLs pour les fichiers statiques et médias en mode développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
