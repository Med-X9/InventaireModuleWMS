from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.inventory_service import InventoryService
from apps.mobile.exceptions import (
    InventoryNotFoundException,
    AccountNotFoundException
)


class InventoryUsersView(APIView):
    """
    API pour récupérer les utilisateurs du même compte qu'un inventaire.
    
    Permet de récupérer la liste des utilisateurs appartenant au même compte
    qu'un inventaire spécifique. Utile pour la gestion des équipes d'inventaire
    et l'affichage des utilisateurs disponibles pour les assignments.
    
    URL: /mobile/api/inventory/{inventory_id}/users/
    
    Fonctionnalités:
    - Récupération des utilisateurs du même compte
    - Validation de l'existence de l'inventaire
    - Filtrage par compte associé à l'inventaire
    - Gestion des erreurs spécifiques
    
    Paramètres d'URL:
    - inventory_id (int): ID de l'inventaire
    
    Réponses:
    - 200: Liste des utilisateurs récupérée avec succès
    - 400: ID d'inventaire invalide
    - 401: Non authentifié
    - 404: Inventaire ou compte non trouvé
    - 500: Erreur interne du serveur
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, inventory_id):
        """
        Récupère les utilisateurs du même compte qu'un inventaire.
        
        Args:
            request: Requête GET
            inventory_id: ID de l'inventaire (depuis l'URL)
            
        Returns:
            Response: Liste des utilisateurs du même compte que l'inventaire
        """
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
