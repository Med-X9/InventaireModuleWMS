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
    
    def get_inventory_counting_tracking(self, inventory_id: int, counting_order: int, assigment_id: Optional[int] = None) -> Inventory:
        """
        Récupère un inventaire avec tous ses comptages, jobs et emplacements.
        
        Args:
            inventory_id: ID de l'inventaire à suivre
            counting_order: Ordre du comptage à filtrer (requis). Ne retourne que le comptage avec cet ordre.
            assigment_id: ID de l'assignment à filtrer (optionnel). Si fourni, ne retourne que les jobs de cet assignment.
            
        Returns:
            Inventory: Inventaire avec toutes les relations préchargées
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas ou est supprimé
        """
        try:
            inventory = self.inventory_repository.get_with_counting_tracking_data(
                inventory_id, 
                counting_order, 
                assigment_id=assigment_id
            )
            log_msg = f"Inventaire {inventory_id} récupéré avec succès pour le suivi de comptage (filtre par ordre: {counting_order}"
            if assigment_id:
                log_msg += f", filtre par assignment: {assigment_id}"
            log_msg += ")"
            logger.debug(log_msg)
            return inventory
        except InventoryNotFoundError:
            logger.error(f"Inventaire {inventory_id} non trouvé pour le suivi de comptage")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du suivi de l'inventaire {inventory_id}: {str(e)}")
            raise

