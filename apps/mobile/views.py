from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.auth_service import AuthService
from apps.mobile.services.sync_service import SyncService
from apps.mobile.services.inventory_service import InventoryService
from apps.mobile.services.user_service import UserService
from apps.mobile.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    ProductNotFoundException,
    LocationNotFoundException,
    StockNotFoundException,
    InventoryNotFoundException,
    DatabaseConnectionException,
    DataValidationException,
    SyncDataException,
    UploadDataException
)

# Create your views here.

class LoginView(APIView):
    """API de connexion mobile"""
    
    def post(self, request):
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


class LogoutView(APIView):
    """API de déconnexion mobile"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        auth_service = AuthService()
        response_data = auth_service.logout()
        return Response(response_data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """API de refresh token"""
    
    def post(self, request):
        auth_service = AuthService()
        
        refresh_token = request.data.get('refresh_token')
        
        response_data, error = auth_service.refresh_token(refresh_token)
        
        if error:
            return Response({
                'success': False,
                'error': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(response_data, status=status.HTTP_200_OK)


class SyncDataView(APIView):
    """
    API de synchronisation intelligente - Bonne pratique
    Récupère toutes les données nécessaires en une seule requête
    Si user_id est fourni dans l'URL, récupère les inventaires du même compte que cet utilisateur
    Sinon, récupère tous les inventaires en réalisation
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        try:
            sync_service = SyncService()
            
            # Récupérer les paramètres de synchronisation
            inventory_id = request.GET.get('inventory_id')
            
            # Si user_id est fourni dans l'URL, utiliser cet utilisateur
            # Sinon, utiliser l'utilisateur connecté
            if user_id:
                target_user_id = user_id
            else:
                target_user_id = request.user.id
            
            response_data = sync_service.sync_data(target_user_id, inventory_id)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except (UserNotFoundException, AccountNotFoundException) as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Paramètre invalide: {str(e)}',
                'error_type': 'INVALID_PARAMETER'
            }, status=status.HTTP_400_BAD_REQUEST)
        except SyncDataException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'SYNC_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur inattendue dans SyncDataView: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur',
                'error_type': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UploadDataView(APIView):
    """
    API d'upload unifiée - Bonne pratique
    Traite tous les types d'uploads en une seule requête
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            sync_service = SyncService()
            
            sync_id = request.data.get('sync_id')
            if not sync_id:
                return Response({
                    'success': False,
                    'error': 'sync_id requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            countings = request.data.get('countings', [])
            assignments = request.data.get('assignments', [])
            
            response_data = sync_service.upload_data(sync_id, countings, assignments)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Données invalides: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except UploadDataException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur inattendue dans UploadDataView: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InventoryUsersView(APIView):
    """
    API pour récupérer les utilisateurs du même compte qu'un inventaire
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, inventory_id):
        try:
            inventory_service = InventoryService()
            
            response_data = inventory_service.get_inventory_users(inventory_id)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except InventoryNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'INVENTORY_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except AccountNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'ACCOUNT_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'ID d\'inventaire invalide: {str(e)}',
                'error_type': 'INVALID_PARAMETER'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur inattendue dans InventoryUsersView: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur',
                'error_type': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserInventoriesView(APIView):
    """
    API pour récupérer les inventaires du même compte qu'un utilisateur
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user_service = UserService()
            
            response_data = user_service.get_user_inventories(user_id)
            
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
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'ID d\'utilisateur invalide: {str(e)}',
                'error_type': 'INVALID_PARAMETER'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur inattendue dans UserInventoriesView: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur',
                'error_type': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProductsView(APIView):
    """
    API pour récupérer les produits du même compte qu'un utilisateur
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
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


class UserLocationsView(APIView):
    """
    API pour récupérer les locations du même compte qu'un utilisateur
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user_service = UserService()
            
            response_data = user_service.get_user_locations(user_id)
            
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
        except LocationNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'NO_LOCATIONS_FOUND',
                'data': {
                    'locations': []
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
            print(f"Erreur inattendue dans UserLocationsView: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': f'Erreur interne du serveur: {str(e)}',
                'error_type': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserStocksView(APIView):
    """
    API pour récupérer les stocks du même compte qu'un utilisateur
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user_service = UserService()
            
            response_data = user_service.get_user_stocks(user_id)
            
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
        except StockNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'NO_STOCKS_FOUND',
                'data': {
                    'stocks': []
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
            print(f"Erreur inattendue dans UserStocksView: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': f'Erreur interne du serveur: {str(e)}',
                'error_type': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
