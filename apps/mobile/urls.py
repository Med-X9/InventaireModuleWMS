from django.urls import path
from . import views

app_name = "mobile"

urlpatterns = [
    # Authentification
    path("auth/login/", views.LoginView.as_view(), name="mobile_login"),
    # path("auth/jwt-login/", views.JWTLoginView.as_view(), name="mobile_jwt_login"),
    path("auth/logout/", views.LogoutView.as_view(), name="mobile_logout"),
    path(
        "auth/refresh/", views.RefreshTokenView.as_view(), name="mobile_refresh_token"
    ),
    # Synchronisation unifiée - Bonne pratique
    path(  
        "sync/data/",
        views.SyncDataView.as_view(),
        name="mobile_sync_data",
    ),
    # Liste des inventaires EN REALISATION affectés à l'utilisateur authentifié
    path(
        "inventory/",
        views.InventoryUsersView.as_view(),
        name="mobile_inventory_users",
    ),
    # Produits du même compte qu'un utilisateur
    path(
        "products/",
        views.AllProductsView.as_view(),
        name="mobile_user_products",
    ),
    # Tous les produits (sans filtre par account)
    # path(
    #     "products/all/",
    #     views.UserProductsView.as_view(),
    #     name="mobile_all_products",
    # ),
    # Stocks du même compte qu'un utilisateur
    path(
        "stocks/",
        views.UserStocksView.as_view(),
        name="mobile_user_stocks",
    ),
    # Gestion des personnes
    path(
        "persons/",
        views.PersonListView.as_view(),
        name="mobile_person_list",
    ),
    # Gestion des assignments et jobs
    path(
        "assignment/<int:assignment_id>/status/",
        views.AssignmentStatusView.as_view(),
        name="mobile_assignment_status",
    ),
    path(
        "assignment/<int:assignment_id>/block/",
        views.BlockAssignmentView.as_view(),
        name="mobile_block_assignment",
    ),
    path(
        "assignment/<int:assignment_id>/unblock/",
        views.UnblockAssignmentView.as_view(),
        name="mobile_unblock_assignment",
    ),
    path(
        "job/<int:job_id>/close/<int:assignment_id>/",
        views.CloseJobView.as_view(),
        name="mobile_close_job",
    ),
    path(
        "job/<int:job_id>/results/",
        views.JobResultsView.as_view(),
        name="mobile_job_results",
    ),
    # Jobs dont le 1er et 2ème comptage sont terminés
    path(
        "inventory/<int:inventory_id>/warehouse/<int:warehouse_id>/jobs/both-countings-terminated/",
        views.JobsWithBothCountingsTerminatedView.as_view(),
        name="mobile_jobs_both_countings_terminated",
    ),
    # Gestion des CountingDetail et NumeroSerie
    path(
        "job/<int:job_id>/counting-detail/",
        views.CountingDetailView.as_view(),
        name="mobile_counting_detail",
    ),
]
