from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.auth_service import AuthService


class LogoutView(APIView):
    """
    API de déconnexion pour l'application mobile.
    
    Permet à l'utilisateur mobile de se déconnecter de manière sécurisée.
    Invalide la session et nettoie les données d'authentification.
    
    Fonctionnalités:
    - Déconnexion sécurisée de l'utilisateur
    - Invalidation de la session
    - Nettoyage des données d'authentification
    - Retour de confirmation de déconnexion
    
    Réponses:
    - 200: Déconnexion réussie
    - 401: Non authentifié
    - 500: Erreur interne du serveur
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Déconnecte l'utilisateur mobile.
        
        Args:
            request: Requête POST de déconnexion
            
        Returns:
            Response: Confirmation de déconnexion
        """
        auth_service = AuthService()
        response_data = auth_service.logout()
        return Response(response_data, status=200)
