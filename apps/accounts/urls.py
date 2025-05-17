from django.urls import path
from .views.user_views import MobileUserListView

urlpatterns = [
    path('mobile-users/', MobileUserListView.as_view(), name='mobile-users-list'),
] 