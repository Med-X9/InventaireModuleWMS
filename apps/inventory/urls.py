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
from .views.job_views import JobCreateAPIView, PendingJobsReferencesView, JobRemoveEmplacementsView, JobAddEmplacementsView, JobDeleteView, JobValidateView, JobListWithLocationsView, WarehouseJobsView, JobReadyView, JobFullDetailListView, JobPendingListView, JobResetAssignmentsView
from .views.assignment_views import AssignJobsToCountingView, AssignmentRulesView, AssignmentsBySessionView
from .views.resource_assignment_views import AssignResourcesToJobsView, JobResourcesView, RemoveResourcesFromJobView

urlpatterns = [
    # URLs pour les inventaires
    path('inventory/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/create/', InventoryCreateView.as_view(), name='inventory-create'),
    path('inventory/import/', InventoryImportView.as_view(), name='inventory-import'),
    path('inventory/<int:pk>/edit/', InventoryDetailView.as_view(), name='inventory-edit'),
    path('inventory/<int:pk>/update/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('inventory/<int:pk>/delete/', InventoryDeleteView.as_view(), name='inventory-delete'),
    path('inventory/<int:pk>/launch/', InventoryLaunchView.as_view(), name='inventory-launch'),
    path('inventory/<int:pk>/cancel/', InventoryCancelView.as_view(), name='inventory-cancel'),
    path('inventory/<int:pk>/detail/', InventoryTeamView.as_view(), name='inventory-detail'),
    
    # URL pour les statistiques des warehouses d'un inventaire
    path('inventory/<int:inventory_id>/warehouse-stats/', InventoryWarehouseStatsView.as_view(), name='inventory-warehouse-stats'),
    # URL pour l'importation de stocks
    path('inventory/<int:inventory_id>/stocks/import/', StockImportView.as_view(), name='stock-import'),
    
    # URL pour les entrepôts d'un inventaire
    path('inventory/planning/<int:inventory_id>/warehouses/', InventoryWarehousesView.as_view(), name='inventory-warehouses'),
    path('inventory/planning/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/create/', JobCreateAPIView.as_view(), name='inventory-jobs-create'),
    
    # URL pour récupérer les jobs en attente
    path('inventory/<int:warehouse_id>/pending-jobs/', PendingJobsReferencesView.as_view(), name='pending-jobs-references'),
    
    # URL pour récupérer tous les jobs d'un warehouse
    path('inventory/<int:warehouse_id>/jobs/', WarehouseJobsView.as_view(), name='warehouse-jobs'),
    
    # URL pour valider des jobs
    path('jobs/validate/', JobValidateView.as_view(), name='jobs-validate'),
    
    
    
    # URL pour supprimer définitivement un job
    path('jobs/delete/', JobDeleteView.as_view(), name='job-delete'),
    
    # URL pour supprimer des emplacements d'un job
    path('jobs/<int:job_id>/remove-emplacements/', JobRemoveEmplacementsView.as_view(), name='job-remove-emplacements'),
    
    # URL pour ajouter des emplacements à un job
    path('jobs/<int:job_id>/add-emplacements/', JobAddEmplacementsView.as_view(), name='job-add-emplacements'),
    
    # URL pour les PDAs d'un inventaire
    # path('inventory/<int:inventory_id>/pdas/', InventoryPDAListView.as_view(), name='inventory-pdas'),
    
    # Nouvelle API pour lister tous les jobs avec détails
    path('jobs/list/', JobListWithLocationsView.as_view(), name='jobs-list-with-locations'),
    
    # URLs pour l'affectation des jobs
    path('inventory/<int:inventory_id>/assign-jobs/', AssignJobsToCountingView.as_view(), name='assign-jobs-to-counting'),
    path('assignment-rules/', AssignmentRulesView.as_view(), name='assignment-rules'),
    path('session/<int:session_id>/assignments/', AssignmentsBySessionView.as_view(), name='assignments-by-session'),
    
    # URLs pour l'affectation des ressources aux jobs
    path('jobs/assign-resources/', AssignResourcesToJobsView.as_view(), name='assign-resources-to-jobs'),
    path('jobs/<int:job_id>/resources/', JobResourcesView.as_view(), name='get-job-resources'),
    path('jobs/<int:job_id>/remove-resources/', RemoveResourcesFromJobView.as_view(), name='remove-resources-from-job'),

    # URL pour marquer un job comme prêt
    path('jobs/ready/', JobReadyView.as_view(), name='jobs-ready'),

    # Nouvelle URL pour les jobs validés d'un entrepôt et d'un inventaire spécifique
    path('jobs/valid/warehouse/<int:warehouse_id>/inventory/<int:inventory_id>/', JobFullDetailListView.as_view(), name='valid-jobs-by-warehouse-inventory'),
    
    # URL pour lister les jobs en attente
    path('jobs/pending/', JobPendingListView.as_view(), name='jobs-pending'),
    
    # URL pour remettre les assignements de jobs en attente
    path('jobs/reset-assignments/', JobResetAssignmentsView.as_view(), name='job-reset-assignments'),
    

    
]
