from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.inventory.views.inventory_views import InventoryCreateView
from apps.inventory.views.account_views import AccountListView
from apps.inventory.views.warehouse_views import WarehouseListView


# router = DefaultRouter()
# router.register(r'inventories', InventoryViewSet, basename='inventory')

urlpatterns = [
    path('accounts/', AccountListView.as_view(), name='account-list'),
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
    path('inventory/create/', InventoryCreateView.as_view(), name='inventory-create'),
]
