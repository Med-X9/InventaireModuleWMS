from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView, TokenBlacklistView, TokenObtainPairView
from .views import MobileUserListView

app_name = 'users'

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='auth_logout'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('mobile-users/', MobileUserListView.as_view(), name='mobile-users-list'),
    path('mobile-users/inventory/<int:inventory_id>/', MobileUserListView.as_view(), name='mobile-users-by-inventory'),
]
