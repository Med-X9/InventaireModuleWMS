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
    compte qu'un utilisateur spécifique. Utile pour la gestion des inventaires
    et l'affichage des emplacements disponibles pour le comptage.
    
    URL: /mobile/api/user/{user_id}/locations/
    
    Fonctionnalités:
    - Récupération des emplacements du même compte
    - Validation de l'existence de l'utilisateur
    - Filtrage par compte associé à l'utilisateur
    - Gestion des erreurs spécifiques et cas d'absence d'emplacements
    
    Paramètres d'URL:
    - user_id (int): ID de l'utilisateur
    
    Réponses:
    - 200: Liste des emplacements récupérée avec succès (peut être vide)
    - 400: ID d'utilisateur invalide ou erreur de validation
    - 401: Non authentifié
    - 404: Utilisateur ou compte non trouvé
    - 500: Erreur interne du serveur ou erreur de base de données
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Récupération des emplacements utilisateur mobile",
        operation_description="Récupère la liste des emplacements appartenant au même compte qu'un utilisateur spécifique",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="ID de l'utilisateur",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
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
                description="ID d'utilisateur invalide ou erreur de validation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='ID d\'utilisateur invalide'),
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='INVALID_PARAMETER')
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
    def get(self, request, user_id):
        """
        Récupère les emplacements du même compte qu'un utilisateur.
        
        Args:
            request: Requête GET
            user_id: ID de l'utilisateur (depuis l'URL)
            
        Returns:
            Response: Liste des emplacements avec seulement les informations essentielles
        """
        try:
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
                message=f'ID d\'utilisateur invalide: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='INVALID_PARAMETER'
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
