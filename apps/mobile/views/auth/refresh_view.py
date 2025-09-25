from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.mobile.services.auth_service import AuthService


class RefreshTokenView(APIView):
    """
    API de rafraîchissement de token pour l'application mobile.
    
    Permet de renouveler un token d'authentification expiré en utilisant
    un refresh token valide. Évite à l'utilisateur de se reconnecter
    fréquemment pendant l'utilisation de l'application.
    
    Paramètres de requête:
    - refresh_token (string): Token de rafraîchissement valide
    
    Réponses:
    - 200: Token rafraîchi avec succès
    - 400: Refresh token invalide ou expiré
    - 401: Non autorisé
    """
    
    def post(self, request):
        """
        Rafraîchit un token d'authentification.
        
        Args:
            request: Requête POST contenant le refresh_token
            
        Returns:
            Response: Nouveau token d'accès si rafraîchissement réussi, erreur sinon
        """
        auth_service = AuthService()
        
        refresh_token = request.data.get('refresh_token')
        
        response_data, error = auth_service.refresh_token(refresh_token)
        
        if error:
            return Response({
                'success': False,
                'error': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(response_data, status=status.HTTP_200_OK)
