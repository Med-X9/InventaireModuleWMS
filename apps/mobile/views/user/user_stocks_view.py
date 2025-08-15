from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.user_service import UserService
from apps.mobile.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    StockNotFoundException,
    DataValidationException,
    DatabaseConnectionException
)


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
