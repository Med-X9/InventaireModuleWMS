from django.urls import path

from apps.masterdata.views.location_views import AllWarehouseLocationListView
from .views.inventory_views import (
    InventoryListView,
    InventoryCreateView,
    InventoryDetailView,
    InventoryUpdateView,
    InventoryDeleteView,
    InventoryLaunchView,
    InventoryCancelView,
    InventoryTeamView
)
from apps.inventory.views import InventoryWarehousesView
from .views.job_views import JobCreateAPIView, PendingJobsReferencesView, JobRemoveEmplacementsView, JobAddEmplacementsView, JobDeleteView, JobValidateView, JobListWithLocationsView, WarehouseJobsView
from .views.assignment_views import assign_jobs_to_counting, get_assignment_rules
# from .views.pda_views import InventoryPDAListView

urlpatterns = [
    # URLs pour les inventaires
    path('inventory/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/create/', InventoryCreateView.as_view(), name='inventory-create'),
    path('inventory/<int:pk>/edit/', InventoryDetailView.as_view(), name='inventory-edit'),
    path('inventory/<int:pk>/update/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('inventory/<int:pk>/delete/', InventoryDeleteView.as_view(), name='inventory-delete'),
    path('inventory/<int:pk>/launch/', InventoryLaunchView.as_view(), name='inventory-launch'),
    path('inventory/<int:pk>/cancel/', InventoryCancelView.as_view(), name='inventory-cancel'),
    path('inventory/<int:pk>/detail/', InventoryTeamView.as_view(), name='inventory-detail'),
    
    # URL pour les entrepôts d'un inventaire
    path('inventory/planning/<int:inventory_id>/warehouses/', InventoryWarehousesView.as_view(), name='inventory-warehouses'),
    path('inventory/planning/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/create/', JobCreateAPIView.as_view(), name='inventory-jobs-create'),
    
    # URL pour récupérer les jobs en attente
    path('warehouse/<int:warehouse_id>/pending-jobs/', PendingJobsReferencesView.as_view(), name='pending-jobs-references'),
    
    # URL pour récupérer tous les jobs d'un warehouse
    path('warehouse/<int:warehouse_id>/jobs/', WarehouseJobsView.as_view(), name='warehouse-jobs'),
    
    # URL pour valider des jobs
    path('jobs/validate/', JobValidateView.as_view(), name='jobs-validate'),
    
    # URL pour supprimer définitivement un job
    path('job/<int:job_id>/delete/', JobDeleteView.as_view(), name='job-delete'),
    
    # URL pour supprimer des emplacements d'un job
    path('job/<int:job_id>/remove-emplacements/', JobRemoveEmplacementsView.as_view(), name='job-remove-emplacements'),
    
    # URL pour ajouter des emplacements à un job
    path('job/<int:job_id>/add-emplacements/', JobAddEmplacementsView.as_view(), name='job-add-emplacements'),
    
    # URL pour les PDAs d'un inventaire
    # path('inventory/<int:inventory_id>/pdas/', InventoryPDAListView.as_view(), name='inventory-pdas'),
    
    # Nouvelle API pour lister tous les jobs avec détails
    path('jobs/list/', JobListWithLocationsView.as_view(), name='jobs-list-with-locations'),
    
    # URLs pour l'affectation des jobs
    path('assign-jobs/', assign_jobs_to_counting, name='assign-jobs-to-counting'),
    path('assignment-rules/', get_assignment_rules, name='assignment-rules'),
]
