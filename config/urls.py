from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/masterdata/', include('apps.masterdata.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
] 