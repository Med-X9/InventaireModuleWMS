from ..models import Warehouse
from typing import List
import logging

logger = logging.getLogger(__name__)

class WarehouseService:
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