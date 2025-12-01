from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView
)
from .views import MobileUserListView
from .views.csrf_views import CSRFTokenView, csrf_token_simple
from .views.user_import_export_views import UserExportView, UserImportView


app_name = 'users'

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='auth_logout'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('mobile-users/', MobileUserListView.as_view(), name='mobile-users-list'),
    path('mobile-users/inventory/<int:inventory_id>/', MobileUserListView.as_view(), name='mobile-users-by-inventory'),
    
    # ========================================
    # URLs POUR L'IMPORT/EXPORT DES UTILISATEURS
    # ========================================
    
    path('export/', UserExportView.as_view(), name='users-export'),
    path('export/account/<int:account_id>/', UserExportView.as_view(), name='users-export-by-account'),
    path('import/', UserImportView.as_view(), name='users-import'),
    path('import/account/<int:account_id>/', UserImportView.as_view(), name='users-import-by-account'),
    
    # Endpoints CSRF
    path('csrf-token/', CSRFTokenView.as_view(), name='csrf_token'),
    path('csrf-token-simple/', csrf_token_simple, name='csrf_token_simple'),
]
