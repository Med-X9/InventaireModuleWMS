from django.urls import path
from . import views  # ou from apps.inventory import views
from django.conf.urls.i18n import set_language


urlpatterns = [
    # Exemple de route
    path('set_language/', set_language, name='set_language'),
]
