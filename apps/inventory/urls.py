from django.urls import path

from .views.inventory_views import (
    InventoryListView,
    InventoryCreateView,
    InventoryDuplicateView,
    InventoryDetailView,
    InventoryDetailByReferenceView,
    InventoryUpdateView,
    InventoryDeleteView,
    InventoryLaunchView,
    InventoryCancelView,
    InventoryCompleteView,
    InventoryCloseView,
    InventoryTeamView,
    InventoryWarehouseStatsView,
    InventoryResultByWarehouseView,
    InventoryImportView,
    StockImportView,
    InventoryOrderingTestView,
)
from apps.inventory.views import InventoryWarehousesView, AccountWarehousesView


from .views.job_views import JobCreateAPIView, PendingJobsReferencesView, JobRemoveEmplacementsView, JobAddEmplacementsView, JobDeleteView, JobValidateView, JobListWithLocationsView, WarehouseJobsView, JobReadyView, JobFullDetailListView, JobPendingListView, JobResetAssignmentsView, JobBatchAssignmentView, JobTransferView, JobProgressByCountingView, InventoryProgressByCountingView
from .views.ecart_comptage_views import EcartComptageUpdateFinalResultView, EcartComptageResolveView
from .views.assignment_views import AssignJobsToCountingView, AssignResourcesToInventoryView, InventoryResourcesView, SessionAssignmentsView
from .views.resource_assignment_views import AssignResourcesToJobsView, JobResourcesView, RemoveResourcesFromJobView
from .views.counting_tracking_views import InventoryCountingTrackingView, JobDetailTrackingView
from .views.counting_views import CountingLaunchView
from .views.pdf_views import InventoryJobsPdfView, JobAssignmentPdfView

urlpatterns = [
    # ========================================
    # URLs POUR LES INVENTAIRES
    # ========================================
    
    # Gestion des inventaires
    path('inventory/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/test-ordering/', InventoryOrderingTestView.as_view(), name='inventory-test-ordering'),
    path('inventory/create/', InventoryCreateView.as_view(), name='inventory-create'),
    path('inventory/<int:pk>/duplicate/', InventoryDuplicateView.as_view(), name='inventory-duplicate'),
    path('inventory/import/', InventoryImportView.as_view(), name='inventory-import'),
    path('inventory/<int:pk>/edit/', InventoryDetailView.as_view(), name='inventory-edit'),
    path('inventory/by-reference/<str:reference>/', InventoryDetailByReferenceView.as_view(), name='inventory-by-reference'),
    path('inventory/<int:pk>/update/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('inventory/<int:pk>/delete/', InventoryDeleteView.as_view(), name='inventory-delete'),
    path('inventory/<int:pk>/launch/', InventoryLaunchView.as_view(), name='inventory-launch'),
    path('inventory/<int:pk>/cancel/', InventoryCancelView.as_view(), name='inventory-cancel'),
    path('inventory/<int:pk>/complete/', InventoryCompleteView.as_view(), name='inventory-complete'),
    path('inventory/<int:pk>/close/', InventoryCloseView.as_view(), name='inventory-close'),
    path('inventory/<int:pk>/detail/', InventoryTeamView.as_view(), name='inventory-detail'),
    
    # Statistiques et données des inventaires
    path('inventory/<int:inventory_id>/warehouse-stats/', InventoryWarehouseStatsView.as_view(), name='inventory-warehouse-stats'),
    path('inventory/<int:inventory_id>/warehouses/<int:warehouse_id>/results/', InventoryResultByWarehouseView.as_view(), name='inventory-warehouse-results'),
    path('inventory/<int:inventory_id>/stocks/import/', StockImportView.as_view(), name='stock-import'),
    path('inventory/planning/<int:inventory_id>/warehouses/', InventoryWarehousesView.as_view(), name='inventory-warehouses'),
    path('inventory/account/<int:account_id>/warehouses/', AccountWarehousesView.as_view(), name='account-warehouses'),
    
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
    path('jobs/launch-counting/', CountingLaunchView.as_view(), name='job-launch-counting'),
    
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
    path('inventory/session/<int:session_id>/assignments/', SessionAssignmentsView.as_view(), name='session-assignments'),
    path('inventory/assign-jobs-manual/', JobBatchAssignmentView.as_view(), name='assign-jobs-manual'),
    # URL pour transférer les jobs par comptage
    path('jobs/transfer/', JobTransferView.as_view(), name='job-transfer'),
    
    # URLs pour l'avancement des emplacements par job et par counting
    path('jobs/<int:job_id>/progress-by-counting/', JobProgressByCountingView.as_view(), name='job-progress-by-counting'),
    path('inventory/<int:inventory_id>/progress-by-counting/', InventoryProgressByCountingView.as_view(), name='inventory-progress-by-counting'),
    
    # ========================================
    # URL POUR LE SUIVI DES COMPTAGES
    # ========================================
    
    # API pour le suivi d'un inventaire regroupé par comptages avec jobs et emplacements
    path('inventory/<int:inventory_id>/counting-tracking/', InventoryCountingTrackingView.as_view(), name='inventory-counting-tracking'),
    # API DataTable pour récupérer les JobDetail avec Assignment (filtres: warehouse_id, inventory_id, counting_order)
    path('job-details/tracking/', JobDetailTrackingView.as_view(), name='job-detail-tracking'),
    
    # ========================================
    # URL POUR LA GENERATION DE PDF
    # ========================================
    
    # API pour generer le PDF des jobs d'inventaire (tous les comptages)
    path('inventory/<int:inventory_id>/jobs/pdf/', InventoryJobsPdfView.as_view(), name='inventory-jobs-pdf'),
    # API pour generer le PDF d'un job/assignment/equipe specifique
    path('jobs/<int:job_id>/assignments/<int:assignment_id>/pdf/', JobAssignmentPdfView.as_view(), name='job-assignment-pdf'),
    
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
    
    # ========================================
    # URLs POUR LES ECARTS DE COMPTAGE
    # ========================================

    # API pour modifier le résultat final d'un EcartComptage (nécessite au moins 2 séquences)
    path(
        'ecarts-comptage/<int:ecart_id>/final-result/',
        EcartComptageUpdateFinalResultView.as_view(),
        name='ecart-comptage-update-final-result',
    ),
    # API pour marquer un EcartComptage comme résolu (nécessite au moins 2 séquences et un résultat final)
    path(
        'ecarts-comptage/<int:ecart_id>/resolve/',
        EcartComptageResolveView.as_view(),
        name='ecart-comptage-resolve',
    ),
]
