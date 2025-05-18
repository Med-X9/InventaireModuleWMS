from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

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
            return Response(
                {"message": "Déconnexion réussie"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Erreur lors de la déconnexion"},
                status=status.HTTP_400_BAD_REQUEST
            ) 