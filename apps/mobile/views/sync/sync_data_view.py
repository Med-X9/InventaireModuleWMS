from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.sync_service import SyncService
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
    - Si user_id est fourni dans l'URL, récupère les inventaires du même compte que cet utilisateur
    - Sinon, récupère tous les inventaires en réalisation
    
    Paramètres d'URL:
    - user_id (int, optionnel): ID de l'utilisateur pour la synchronisation
    
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
    
    def get(self, request, user_id=None):
        """
        Récupère toutes les données de synchronisation pour un utilisateur.
        
        Args:
            request: Requête GET avec paramètres optionnels
            user_id: ID de l'utilisateur (optionnel, utilise l'utilisateur connecté si non fourni)
            
        Returns:
            Response: Données complètes de synchronisation incluant:
                - inventaires actifs
                - comptages associés
                - jobs et assignments
                - produits et emplacements
                - stocks disponibles
        """
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
