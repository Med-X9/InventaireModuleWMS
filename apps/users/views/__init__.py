# This file makes the views directory a Python package 

from .auth_views import LoginView, LogoutView
from .user_views import MobileUserListView

__all__ = ['LoginView', 'LogoutView', 'MobileUserListView'] 