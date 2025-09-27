from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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
    
    @swagger_auto_schema(
        operation_summary="Connexion utilisateur mobile",
        operation_description="Authentifie un utilisateur mobile avec nom d'utilisateur et mot de passe",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Nom d\'utilisateur',
                    example='john.doe'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Mot de passe',
                    example='password123'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Connexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'nom': openapi.Schema(type=openapi.TYPE_STRING, example='Doe'),
                                'prenom': openapi.Schema(type=openapi.TYPE_STRING, example='John'),
                                'username': openapi.Schema(type=openapi.TYPE_STRING, example='john.doe')
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Erreur de connexion",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Identifiants invalides')
                    }
                )
            )
        },
        tags=['Authentification Mobile']
    )
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
