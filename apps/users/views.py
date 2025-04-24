from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()

class LoginView(TokenObtainPairView):
    """
    Vue pour la connexion des utilisateurs
    Retourne un token d'accès et un token de rafraîchissement
    """
    pass

class LogoutView(APIView):
    """
    Vue pour la déconnexion des utilisateurs
    Ajoute le token de rafraîchissement à la liste noire
    """
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

