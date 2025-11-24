from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.users.models import UserApp


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personnalisé qui étend TokenObtainPairSerializer
    pour inclure les informations utilisateur personnalisées
    """
    
    def validate(self, attrs):
        """
        Valide les données et retourne les tokens + infos utilisateur
        """
        # Appeler la validation parent pour obtenir les tokens
        # Cette méthode lève AuthenticationFailed si les identifiants sont invalides
        # ou si l'utilisateur n'est pas actif
        data = super().validate(attrs)
        
        # Récupérer l'utilisateur authentifié (défini par super().validate())
        user = self.user
        
        # Vérification supplémentaire que l'utilisateur est actif
        # (déjà vérifié par super().validate(), mais double vérification pour sécurité)
        if not user.is_active:
            raise AuthenticationFailed(
                'Ce compte utilisateur est désactivé.',
                code='user_inactive'
            )
        
        # Formater la réponse selon le format demandé
        response_data = {
            'success': True,
            'access': str(data['access']),
            'refresh': str(data['refresh']),
            'user': {
                'user_id': user.id,
                'nom': user.nom if hasattr(user, 'nom') else '',
                'prenom': user.prenom if hasattr(user, 'prenom') else ''
            }
        }
        
        return response_data


class JWTLoginView(TokenObtainPairView):
    """
    API de connexion JWT pour l'application mobile.
    
    Authentifie un utilisateur mobile avec nom d'utilisateur et mot de passe
    et retourne un token JWT pour l'authentification des requêtes suivantes.
    Hérite de SIMPLE_JWT et retourne une réponse formatée avec les informations utilisateur.
    
    Paramètres de requête:
    - username (string): Nom d'utilisateur
    - password (string): Mot de passe
    
    Réponses:
    - 200: Connexion réussie avec token JWT et données utilisateur
    - 400: Erreur de connexion (identifiants invalides)
    - 401: Non autorisé
    - 500: Erreur interne du serveur
    """
    
    serializer_class = CustomTokenObtainPairSerializer
    
    @swagger_auto_schema(
        operation_summary="Connexion JWT utilisateur mobile",
        operation_description="Authentifie un utilisateur mobile avec JWT et retourne un token d'accès",
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
                description="Connexion JWT réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'nom': openapi.Schema(type=openapi.TYPE_STRING, example='Doe'),
                                'prenom': openapi.Schema(type=openapi.TYPE_STRING, example='John')
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
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Identifiants invalides'),
                        'details': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur interne du serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Erreur interne du serveur'),
                        'details': openapi.Schema(type=openapi.TYPE_STRING, example='Exception details')
                    }
                )
            )
        },
        tags=['Authentification Mobile']
    )
    def post(self, request, *args, **kwargs):
        """
        Gère la requête POST de connexion
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Utiliser le serializer parent pour la validation et la génération des tokens
            serializer = self.get_serializer(data=request.data)
            
            # Valider les données - AuthenticationFailed sera levée si les identifiants sont invalides
            serializer.is_valid(raise_exception=True)
            
            # Le serializer retourne déjà la réponse formatée
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
                
        except AuthenticationFailed as e:
            # Gestion spécifique des erreurs d'authentification
            logger.warning(f"Tentative de connexion échouée: {str(e)}")
            return Response({
                'success': False,
                'error': 'Identifiants invalides',
                'details': 'Nom d\'utilisateur ou mot de passe incorrect'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            # Gestion des erreurs inattendues
            logger.error(f"Erreur inattendue lors de la connexion JWT: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur',
                'details': str(e) if logger.level <= logging.DEBUG else 'Une erreur est survenue lors de la connexion'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
