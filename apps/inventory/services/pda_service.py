from apps.inventory.models import Assigment, Inventory 
from apps.inventory.exceptions.pda_exceptions import PdaNotFoundError
import logging

logger = logging.getLogger(__name__)

class PDAService:
    @staticmethod
    def get_inventory_pdas(inventory_id):
        """
        Récupère tous les PDAs associés à un inventaire
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            list: Liste des PDAs
            
        Raises:
            PDANotFoundError: Si l'inventaire n'existe pas
        """
        try:
            logger.info(f"Récupération des PDAs pour l'inventaire {inventory_id}")
            
            # Vérifier si l'inventaire existe
            if not Inventory.objects.filter(id=inventory_id).exists():
                logger.error(f"Inventaire {inventory_id} non trouvé")
                raise PdaNotFoundError(f"Inventaire {inventory_id} non trouvé")
            
            # Récupérer les PDAs
            pdas = Assigment.objects.filter(job__inventory_id=inventory_id)
            logger.info(f"{pdas.count()} PDAs trouvés pour l'inventaire {inventory_id}")
            
            return pdas
            
        except PdaNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des PDAs: {str(e)}")
            raise PdaNotFoundError(f"Erreur lors de la récupération des PDAs: {str(e)}") 