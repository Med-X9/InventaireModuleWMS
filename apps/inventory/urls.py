from django.urls import path
from . import views  # ou from apps.inventory import views

from apps.inventory.views import AccountListView,WarehouseListView
urlpatterns = [
    path('accounts/', AccountListView.as_view(), name='account-list'),
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
]
