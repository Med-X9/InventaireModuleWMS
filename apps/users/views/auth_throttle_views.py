"""
Vues d'authentification avec rate limiting pour protéger contre les attaques par force brute.
"""
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView
)
from rest_framework.throttling import AnonRateThrottle
from rest_framework.permissions import AllowAny


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """
    Vue d'obtention de token avec rate limiting.
    Limite à 5 tentatives par minute par IP pour protéger contre les attaques par force brute.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'login'  # Scope personnalisé pour le login


class ThrottledTokenRefreshView(TokenRefreshView):
    """
    Vue de rafraîchissement de token avec rate limiting.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'refresh'


class ThrottledTokenVerifyView(TokenVerifyView):
    """
    Vue de vérification de token avec rate limiting.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'verify'

