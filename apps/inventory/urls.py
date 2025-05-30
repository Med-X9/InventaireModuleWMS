from django.urls import path

from apps.masterdata.views.location_views import AllWarehouseLocationListView
from .views.inventory_views import (
    InventoryListView,
    InventoryCreateView,
    InventoryDetailView,
    InventoryUpdateView,
    InventoryDeleteView,
    InventoryLaunchView,
    InventoryCancelView
)
from apps.inventory.views import InventoryWarehousesView
from .views.job_views import InventoryJobCreateView, InventoryJobRetrieveView, InventoryJobUpdateView, InventoryJobDeleteView
from .views.pda_views import InventoryPDAListView

urlpatterns = [
    # URLs pour les inventaires
    path('inventory/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/create/', InventoryCreateView.as_view(), name='inventory-create'),
    path('inventory/<int:pk>/', InventoryDetailView.as_view(), name='inventory-detail'),
    path('inventory/<int:pk>/update/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('inventory/<int:pk>/delete/', InventoryDeleteView.as_view(), name='inventory-delete'),
    path('inventory/<int:pk>/launch/', InventoryLaunchView.as_view(), name='inventory-launch'),
    path('inventory/<int:pk>/cancel/', InventoryCancelView.as_view(), name='inventory-cancel'),
    
    # URL pour les entrepôts d'un inventaire
    path('inventory/planning/<int:inventory_id>/warehouses/', InventoryWarehousesView.as_view(), name='inventory-warehouses'),
    path('inventory/planning/jobs/create/', InventoryJobCreateView.as_view(), name='inventory-job-create'),
    path('inventory/planning/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/', InventoryJobRetrieveView.as_view(), name='inventory-job-retrieve'),
    path('inventory/planning/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/update/', InventoryJobUpdateView.as_view(), name='inventory-jobs-update'),
    path('inventory/planning/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/delete/', InventoryJobDeleteView.as_view(), name='inventory-jobs-delete'),
    
    # URL pour les PDAs d'un inventaire
    path('inventory/<int:inventory_id>/pdas/', InventoryPDAListView.as_view(), name='inventory-pdas'),
        
    # # URL pour les locations d'un inventaire pour un warehouse (à partir des JobDetails)
    # path('warehouse/<int:warehouse_id>/locations/', AllWarehouseLocationListView.as_view(), name='warehouse-locations'),
]
