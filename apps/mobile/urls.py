from django.urls import path
from . import views

app_name = "mobile"

urlpatterns = [
    # Authentification
    path("auth/login/", views.LoginView.as_view(), name="mobile_login"),
    path("auth/jwt-login/", views.JWTLoginView.as_view(), name="mobile_jwt_login"),
    path("auth/logout/", views.LogoutView.as_view(), name="mobile_logout"),
    path(
        "auth/refresh/", views.RefreshTokenView.as_view(), name="mobile_refresh_token"
    ),
    # Synchronisation unifiée - Bonne pratique
    path("sync/data/", views.SyncDataView.as_view(), name="mobile_sync_data"),
    path(
        "sync/data/user/<int:user_id>/",
        views.SyncDataView.as_view(),
        name="mobile_sync_data_by_user",
    ),
    path("sync/upload/", views.UploadDataView.as_view(), name="mobile_upload_data"),
    # Utilisateurs du même compte d'inventaire
    path(
        "inventory/<int:inventory_id>/users/",
        views.InventoryUsersView.as_view(),
        name="mobile_inventory_users",
    ),
    # Produits du même compte qu'un utilisateur
    path(
        "user/<int:user_id>/products/",
        views.UserProductsView.as_view(),
        name="mobile_user_products",
    ),
    # Locations du même compte qu'un utilisateur
    path(
        "user/<int:user_id>/locations/",
        views.UserLocationsView.as_view(),
        name="mobile_user_locations",
    ),
    # Stocks du même compte qu'un utilisateur
    path(
        "user/<int:user_id>/stocks/",
        views.UserStocksView.as_view(),
        name="mobile_user_stocks",
    ),
    # Gestion des assignments et jobs
    path(
        "user/<int:user_id>/assignment/<int:assignment_id>/status/",
        views.AssignmentStatusView.as_view(),
        name="mobile_assignment_status",
    ),
    # Gestion des CountingDetail et NumeroSerie
    path(
        "counting-detail/",
        views.CountingDetailView.as_view(),
        name="mobile_counting_detail",
    ),
]
