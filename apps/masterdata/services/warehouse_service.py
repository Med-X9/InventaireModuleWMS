from ..models import Warehouse
from ..repositories.warehouse_repository import WarehouseRepository
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class WarehouseService:
    def __init__(self):
        self.repository = WarehouseRepository()

    @staticmethod
    def get_all_warehouses() -> List[Warehouse]:
        """
        Récupère tous les entrepôts
        
        Returns:
            List[Warehouse]: Liste des entrepôts
        """
        try:
            logger.info("Récupération de tous les entrepôts")
            warehouses = Warehouse.objects.all()
            logger.info(f"{warehouses.count()} entrepôts trouvés")
            return warehouses
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des entrepôts: {str(e)}")
            raise

    def get_warehouse_by_reference(self, reference: str) -> Optional[Warehouse]:
        """
        Récupère un entrepôt par sa référence
        
        Args:
            reference: La référence de l'entrepôt
            
        Returns:
            Warehouse: L'entrepôt trouvé ou None si non trouvé
        """
        try:
            logger.info(f"Récupération de l'entrepôt avec la référence: {reference}")
            warehouse = self.repository.get_by_reference(reference)
            logger.info(f"Entrepôt trouvé: {warehouse.warehouse_name}")
            return warehouse
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'entrepôt par référence '{reference}': {str(e)}")
            raise 