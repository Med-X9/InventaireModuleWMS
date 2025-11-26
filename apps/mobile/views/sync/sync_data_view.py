from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.mobile.services.sync_service import SyncService
from apps.mobile.utils import success_response, error_response
from apps.mobile.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    SyncDataException
)


class SyncDataView(APIView):
    """
    API de synchronisation intelligente pour l'application mobile.
    
    Récupère toutes les données nécessaires en une seule requête pour optimiser
    les performances de l'application mobile. Inclut les inventaires, comptages,
    jobs, assignments, produits, emplacements et stocks.
    
    Comportement:
    - Récupère l'utilisateur depuis le token d'authentification
    - Récupère les inventaires du même compte que l'utilisateur connecté
    
    Paramètres de requête:
    - inventory_id (int, optionnel): ID d'inventaire spécifique à synchroniser
    
    Réponses:
    - 200: Données de synchronisation récupérées avec succès
    - 400: Paramètre invalide ou erreur de synchronisation
    - 401: Non authentifié
    - 404: Utilisateur ou compte non trouvé
    - 500: Erreur interne du serveur
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Synchronisation des données mobile",
        operation_description="Récupère toutes les données nécessaires en une seule requête pour optimiser les performances de l'application mobile",
        manual_parameters=[
            openapi.Parameter(
                'inventory_id',
                openapi.IN_QUERY,
                description="ID d'inventaire spécifique à synchroniser",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Données de synchronisation récupérées avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'inventories': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Liste des inventaires actifs"
                        ),
                        'countings': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Liste des comptages associés"
                        ),
                        'jobs': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Liste des jobs"
                        ),
                        'assignments': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Liste des assignments"
                        ),
                        'products': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Liste des produits"
                        ),
                        'locations': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Liste des emplacements"
                        ),
                        'stocks': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Liste des stocks"
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Paramètre invalide ou erreur de synchronisation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Paramètre invalide'),
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
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='NOT_FOUND')
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
        tags=['Synchronisation Mobile']
    )
    def get(self, request):
        """
        Récupère toutes les données de synchronisation pour l'utilisateur connecté.
        
        Args:
            request: Requête GET avec paramètres optionnels
            - L'utilisateur est récupéré automatiquement depuis le token d'authentification
            
        Returns:
            Response: Données complètes de synchronisation incluant:
                - inventaires actifs
                - comptages associés
                - jobs et assignments
                - produits et emplacements
                - stocks disponibles
        """
        try:
            # Récupérer l'utilisateur depuis le token d'authentification
            target_user_id = request.user.id
            print(f"user_id depuis token: {target_user_id}")
            
            sync_service = SyncService()
            
            # Récupérer les paramètres de synchronisation
            # inventory_id = request.GET.get('inventory_id')
            
            response_data = sync_service.sync_data(target_user_id)
            
            return success_response(
                data=response_data,
                message="Données synchronisées avec succès"
            )
            
        except (UserNotFoundException, AccountNotFoundException) as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='NOT_FOUND'
            )
        except ValueError as e:
            return error_response(
                message=f'Paramètre invalide: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='INVALID_PARAMETER'
            )
        except SyncDataException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='SYNC_ERROR'
            )
        except Exception as e:
            print(f"Erreur inattendue dans SyncDataView: {str(e)}")
            return error_response(
                message='Erreur interne du serveur',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type='INTERNAL_ERROR'
            )
