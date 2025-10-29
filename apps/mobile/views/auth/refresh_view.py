from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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
    permission_classes = [AllowAny]  # Pas d'authentification requise pour le refresh token
    
    @swagger_auto_schema(
        operation_summary="Rafraîchissement de token mobile",
        operation_description="Renouvelle un token d'authentification expiré en utilisant un refresh token valide",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh_token'],
            properties={
                'refresh_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Token de rafraîchissement valide',
                    example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Token rafraîchi avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...')
                    }
                )
            ),
            400: openapi.Response(
                description="Refresh token invalide ou expiré",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Refresh token invalide')
                    }
                )
            ),
            401: openapi.Response(
                description="Non autorisé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Token is invalid or expired')
                    }
                )
            )
        },
        tags=['Authentification Mobile']
    )
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
