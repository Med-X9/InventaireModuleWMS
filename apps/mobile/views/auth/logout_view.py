from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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
    
    @swagger_auto_schema(
        operation_summary="Déconnexion utilisateur mobile",
        operation_description="Déconnecte l'utilisateur mobile de manière sécurisée",
        security=[{'Bearer': []}],
        responses={
            200: openapi.Response(
                description="Déconnexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Déconnexion réussie')
                    }
                )
            ),
            401: openapi.Response(
                description="Non authentifié",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Authentication credentials were not provided.')
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur interne du serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Erreur interne du serveur')
                    }
                )
            )
        },
        tags=['Authentification Mobile']
    )
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
