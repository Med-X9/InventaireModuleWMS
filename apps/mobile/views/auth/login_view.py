from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.mobile.services.auth_service import AuthService


class LoginView(APIView):
    """
    API de connexion pour l'application mobile.
    
    Authentifie un utilisateur mobile avec nom d'utilisateur et mot de passe.
    Retourne les informations de l'utilisateur et un token d'authentification.
    
    Paramètres de requête:
    - username (string): Nom d'utilisateur
    - password (string): Mot de passe
    
    Réponses:
    - 200: Connexion réussie avec données utilisateur
    - 400: Erreur de connexion (identifiants invalides)
    """
    
    def post(self, request):
        """
        Authentifie un utilisateur mobile.
        
        Args:
            request: Requête POST contenant username et password
            
        Returns:
            Response: Données utilisateur si connexion réussie, erreur sinon
        """
        auth_service = AuthService()
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        response_data, error = auth_service.login(username, password)
        
        if error:
            return Response({
                'success': False,
                'error': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(response_data, status=status.HTTP_200_OK)
