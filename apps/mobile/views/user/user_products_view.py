from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.mobile.services.user_service import UserService
from apps.mobile.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    ProductNotFoundException,
    DataValidationException,
    DatabaseConnectionException
)


class UserProductsView(APIView):
    """
    API pour récupérer les produits du même compte qu'un utilisateur.
    
    Permet de récupérer la liste des produits appartenant au même compte
    qu'un utilisateur spécifique. Utile pour la gestion des inventaires
    et l'affichage des produits disponibles pour le comptage.
    
    URL: /mobile/api/user/{user_id}/products/
    
    Fonctionnalités:
    - Récupération des produits du même compte
    - Validation de l'existence de l'utilisateur
    - Filtrage par compte associé à l'utilisateur
    - Gestion des erreurs spécifiques et cas d'absence de produits
    
    Paramètres d'URL:
    - user_id (int): ID de l'utilisateur
    
    Réponses:
    - 200: Liste des produits récupérée avec succès (peut être vide)
    - 400: ID d'utilisateur invalide ou erreur de validation
    - 401: Non authentifié
    - 404: Utilisateur ou compte non trouvé
    - 500: Erreur interne du serveur ou erreur de base de données
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Récupération des produits utilisateur mobile",
        operation_description="Récupère la liste des produits appartenant au même compte qu'un utilisateur spécifique",
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
                description="Liste des produits récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'products': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                    description="Liste des produits du même compte"
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
        Récupère les produits du même compte qu'un utilisateur.
        
        Args:
            request: Requête GET
            user_id: ID de l'utilisateur (depuis l'URL)
            
        Returns:
            Response: Liste des produits du même compte que l'utilisateur
        """
        try:
            user_service = UserService()
            
            response_data = user_service.get_user_products(user_id)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except UserNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'USER_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except AccountNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'ACCOUNT_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except ProductNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'NO_PRODUCTS_FOUND',
                'data': {
                    'products': []
                }
            }, status=status.HTTP_200_OK)  # Retourner 200 avec liste vide
        except DataValidationException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'VALIDATION_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseConnectionException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'DATABASE_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'ID d\'utilisateur invalide: {str(e)}',
                'error_type': 'INVALID_PARAMETER'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur inattendue dans UserProductsView: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': f'Erreur interne du serveur: {str(e)}',
                'error_type': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
