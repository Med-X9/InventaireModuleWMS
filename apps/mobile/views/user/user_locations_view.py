from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.user_service import UserService
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
    
    def get(self, request, user_id):
        """
        Récupère les emplacements du même compte qu'un utilisateur.
        
        Args:
            request: Requête GET
            user_id: ID de l'utilisateur (depuis l'URL)
            
        Returns:
            Response: Liste des emplacements du même compte que l'utilisateur
        """
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
