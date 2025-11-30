from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView
)
from .views import MobileUserListView
from .views.csrf_views import CSRFTokenView, csrf_token_simple


app_name = 'users'

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='auth_logout'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('mobile-users/', MobileUserListView.as_view(), name='mobile-users-list'),
    path('mobile-users/inventory/<int:inventory_id>/', MobileUserListView.as_view(), name='mobile-users-by-inventory'),
    
    # Endpoints CSRF
    path('csrf-token/', CSRFTokenView.as_view(), name='csrf_token'),
    path('csrf-token-simple/', csrf_token_simple, name='csrf_token_simple'),
]
