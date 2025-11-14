"""
Service pour le suivi d'un inventaire regroupé par comptages avec leurs jobs et emplacements.
"""
from typing import Optional
import logging

from ..repositories.inventory_repository import InventoryRepository
from ..exceptions.inventory_exceptions import InventoryNotFoundError
from ..models import Inventory

logger = logging.getLogger(__name__)


class CountingTrackingService:
    """
    Service responsable de la récupération des données de suivi d'inventaire.
    Gère la logique métier pour le suivi des comptages avec leurs jobs et emplacements.
    """
    
    def __init__(self, inventory_repository: Optional[InventoryRepository] = None):
        """
        Initialise le service avec un repository.
        
        Args:
            inventory_repository: Repository pour l'accès aux données d'inventaire.
                                 Si None, crée une nouvelle instance.
        """
        self.inventory_repository = inventory_repository or InventoryRepository()
    
    def get_inventory_counting_tracking(self, inventory_id: int, counting_order: int) -> Inventory:
        """
        Récupère un inventaire avec tous ses comptages, jobs et emplacements.
        
        Args:
            inventory_id: ID de l'inventaire à suivre
            counting_order: Ordre du comptage à filtrer (requis). Ne retourne que le comptage avec cet ordre.
            
        Returns:
            Inventory: Inventaire avec toutes les relations préchargées
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas ou est supprimé
        """
        try:
            inventory = self.inventory_repository.get_with_counting_tracking_data(inventory_id, counting_order)
            logger.debug(f"Inventaire {inventory_id} récupéré avec succès pour le suivi de comptage (filtre par ordre: {counting_order})")
            return inventory
        except InventoryNotFoundError:
            logger.error(f"Inventaire {inventory_id} non trouvé pour le suivi de comptage")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du suivi de l'inventaire {inventory_id}: {str(e)}")
            raise

