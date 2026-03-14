from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.mobile.services.user_service import UserService
from apps.mobile.utils import success_response, error_response
from apps.mobile.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    LocationNotFoundException,
    DataValidationException,
    DatabaseConnectionException
)


class UserLocationsView(APIView):
    """
    API pour récupérer les emplacements du même compte qu'un utilisateur.
    
    Permet de récupérer la liste des emplacements (locations) appartenant au même
    compte de l'utilisateur connecté. Utile pour la gestion des inventaires
    et l'affichage des emplacements disponibles pour le comptage.
    
    URL: /mobile/api/locations/
    
    Fonctionnalités:
    - Récupération des emplacements du même compte
    - L'utilisateur est récupéré automatiquement depuis le token d'authentification
    - Filtrage par compte associé à l'utilisateur connecté
    - Gestion des erreurs spécifiques et cas d'absence d'emplacements
    
    Réponses:
    - 200: Liste des emplacements récupérée avec succès (peut être vide)
    - 400: Erreur de validation
    - 401: Non authentifié
    - 404: Utilisateur ou compte non trouvé
    - 500: Erreur interne du serveur ou erreur de base de données
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Récupération des emplacements utilisateur mobile",
        operation_description="Récupère la liste des emplacements appartenant au même compte de l'utilisateur connecté (récupéré depuis le token)",
        responses={
            200: openapi.Response(
                description="Liste des emplacements récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Emplacements récupérés avec succès'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'locations': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'web_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=4146),
                                            'location_reference': openapi.Schema(type=openapi.TYPE_STRING, example='00100'),
                                            'location_name': openapi.Schema(type=openapi.TYPE_STRING, example='00100'),
                                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                                        }
                                    ),
                                    description="Liste des emplacements du même compte"
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Erreur de validation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Erreur de validation'),
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='VALIDATION_ERROR')
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
            404: openapi.Response(
                description="Utilisateur ou compte non trouvé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Utilisateur non trouvé'),
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='USER_NOT_FOUND')
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
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='INTERNAL_ERROR')
                    }
                )
            )
        },
        security=[{'Bearer': []}],
        tags=['Utilisateur Mobile']
    )
    def get(self, request):
        """
        Récupère les emplacements du même compte de l'utilisateur connecté.
        
        Args:
            request: Requête GET
            - L'utilisateur est récupéré automatiquement depuis le token d'authentification
            
        Returns:
            Response: Liste des emplacements avec seulement les informations essentielles
        """
        try:
            # Récupérer l'utilisateur depuis le token d'authentification
            user_id = request.user.id
            print(f"user_id depuis token: {user_id}")
            
            user_service = UserService()
            
            response_data = user_service.get_user_locations(user_id)
            
            # Extraire seulement les informations demandées de chaque location
            locations = []
            if response_data and 'data' in response_data and 'locations' in response_data['data']:
                for location in response_data['data']['locations']:
                    locations.append({
                        'web_id': location.get('web_id'),
                        'location_reference': location.get('location_reference'),
                        'location_name': location.get('location_name'),
                        'created_at': location.get('created_at'),
                        'updated_at': location.get('updated_at')
                    })
            
            # Retourner avec success_response mais seulement les locations dans data
            return success_response(
                data={'locations': locations},
                message="Emplacements récupérés avec succès"
            )
            
        except UserNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='USER_NOT_FOUND'
            )
        except AccountNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='ACCOUNT_NOT_FOUND'
            )
        except LocationNotFoundException as e:
            return success_response(
                data={'locations': []},
                message="Emplacements récupérés avec succès"
            )
        except DataValidationException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='VALIDATION_ERROR'
            )
        except DatabaseConnectionException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type='DATABASE_ERROR'
            )
        except ValueError as e:
            return error_response(
                message=f'Erreur de validation: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='VALIDATION_ERROR'
            )
        except Exception as e:
            print(f"Erreur inattendue dans UserLocationsView: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            return error_response(
                message="Erreur interne du serveur",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type='INTERNAL_ERROR'
            )
