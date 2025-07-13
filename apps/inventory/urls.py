from django.urls import path

from .views.inventory_views import (
    InventoryListView,
    InventoryCreateView,
    InventoryDetailView,
    InventoryUpdateView,
    InventoryDeleteView,
    InventoryLaunchView,
    InventoryCancelView,
    InventoryTeamView,
    InventoryWarehouseStatsView,
    InventoryImportView,
    StockImportView,
)
from apps.inventory.views import InventoryWarehousesView
from .views.job_views import (
    JobCreateAPIView, 
    PendingJobsReferencesView, 
    JobRemoveEmplacementsView, 
    JobAddEmplacementsView, 
    JobDeleteView, 
    JobValidateView, 
    JobListWithLocationsView, 
    WarehouseJobsView, 
    JobReadyView, 
    JobFullDetailListView, 
    JobPendingListView, 
    JobResetAssignmentsView
)
from .views.assignment_views import (
    AssignJobsToCountingView,
    AssignResourcesToInventoryView,
    InventoryResourcesView
)
from .views.resource_assignment_views import (
    AssignResourcesToJobsView, 
    JobResourcesView, 
    RemoveResourcesFromJobView
)

urlpatterns = [
    # ========================================
    # URLs POUR LES INVENTAIRES
    # ========================================
    
    # Gestion des inventaires
    path('inventory/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/create/', InventoryCreateView.as_view(), name='inventory-create'),
    path('inventory/import/', InventoryImportView.as_view(), name='inventory-import'),
    path('inventory/<int:pk>/edit/', InventoryDetailView.as_view(), name='inventory-edit'),
    path('inventory/<int:pk>/update/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('inventory/<int:pk>/delete/', InventoryDeleteView.as_view(), name='inventory-delete'),
    path('inventory/<int:pk>/launch/', InventoryLaunchView.as_view(), name='inventory-launch'),
    path('inventory/<int:pk>/cancel/', InventoryCancelView.as_view(), name='inventory-cancel'),
    path('inventory/<int:pk>/detail/', InventoryTeamView.as_view(), name='inventory-detail'),
    
    # Statistiques et données des inventaires
    path('inventory/<int:inventory_id>/warehouse-stats/', InventoryWarehouseStatsView.as_view(), name='inventory-warehouse-stats'),
    path('inventory/<int:inventory_id>/stocks/import/', StockImportView.as_view(), name='stock-import'),
    path('inventory/planning/<int:inventory_id>/warehouses/', InventoryWarehousesView.as_view(), name='inventory-warehouses'),
    
    # ========================================
    # URLs POUR LES JOBS
    # ========================================
    
    # Création et gestion des jobs
    path('inventory/planning/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/create/', JobCreateAPIView.as_view(), name='inventory-jobs-create'),
    path('inventory/<int:warehouse_id>/pending-jobs/', PendingJobsReferencesView.as_view(), name='pending-jobs-references'),
    path('inventory/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/', WarehouseJobsView.as_view(), name='warehouse-jobs'),
    
    # Actions sur les jobs
    path('jobs/validate/', JobValidateView.as_view(), name='jobs-validate'),
    path('jobs/delete/', JobDeleteView.as_view(), name='job-delete'),
    path('jobs/ready/', JobReadyView.as_view(), name='jobs-ready'),
    path('jobs/reset-assignments/', JobResetAssignmentsView.as_view(), name='job-reset-assignments'),
    
    # Gestion des emplacements des jobs
    path('jobs/<int:job_id>/remove-emplacements/', JobRemoveEmplacementsView.as_view(), name='job-remove-emplacements'),
    path('jobs/<int:job_id>/add-emplacements/', JobAddEmplacementsView.as_view(), name='job-add-emplacements'),
    
    # Consultation des jobs
    path('jobs/list/', JobListWithLocationsView.as_view(), name='jobs-list-with-locations'),
    path('jobs/valid/warehouse/<int:warehouse_id>/inventory/<int:inventory_id>/', JobFullDetailListView.as_view(), name='valid-jobs-by-warehouse-inventory'),
    path('jobs/pending/', JobPendingListView.as_view(), name='jobs-pending'),
    
    # ========================================
    # URLs POUR L'AFFECTATION DES JOBS
    # ========================================
    
    path('inventory/<int:inventory_id>/assign-jobs/', AssignJobsToCountingView.as_view(), name='assign-jobs-to-counting'),
    
    # ========================================
    # URLs POUR L'AFFECTATION DES RESSOURCES AUX JOBS
    # ========================================
    
    path('inventory/assign-resources/', AssignResourcesToJobsView.as_view(), name='assign-resources-to-jobs'),
    path('jobs/<int:job_id>/resources/', JobResourcesView.as_view(), name='get-job-resources'),
    path('jobs/<int:job_id>/remove-resources/', RemoveResourcesFromJobView.as_view(), name='remove-resources-from-job'),
    
    # ========================================
    # URLs POUR L'AFFECTATION DES RESSOURCES AUX INVENTAIRES
    # ========================================
    
    path('inventory/<int:inventory_id>/assign-resources-inventory/', AssignResourcesToInventoryView.as_view(), name='assign-resources-to-inventory'),
    path('inventory/<int:inventory_id>/resources/', InventoryResourcesView.as_view(), name='get-inventory-resources'),
]
