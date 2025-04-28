"""
Service pour la gestion des inventaires.
"""
from typing import Dict, Any, List
from django.utils import timezone
from ..interfaces import IInventoryService
from ..repositories import InventoryRepository
from ..exceptions import InventoryValidationError
from ..models import Inventory, Setting, Counting
from django.db import IntegrityError
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

class InventoryService(IInventoryService):
    """Service pour la gestion des inventaires."""
    
    def __init__(self, repository: InventoryRepository = None):
        self.repository = repository or InventoryRepository()
    
    def validate_inventory_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données d'un inventaire.
        
        Args:
            data: Les données à valider
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        errors = []
        
        if not data.get('label'):
            errors.append("Le label est obligatoire")
        
        if not data.get('date'):
            errors.append("La date est obligatoire")
        
        if not data.get('account'):
            errors.append("Le compte est obligatoire")
        
        if not data.get('warehouse'):
            errors.append("Au moins un entrepôt est obligatoire")
        
        comptages = data.get('comptages', [])
        if not comptages:
            errors.append("Les comptages sont obligatoires")
        else:
            # Validation des comptages
            counting_errors = self._validate_countings(comptages)
            if counting_errors:
                errors.extend(counting_errors)
            
            mode_errors = self.validate_counting_modes(comptages)
            if mode_errors:
                errors.extend(mode_errors)
        
        if errors:
            raise InventoryValidationError(" | ".join(errors))
    
    def _validate_countings(self, countings: List[Dict[str, Any]]) -> List[str]:
        """
        Valide les données des comptages.
        
        Args:
            countings: Liste des données de comptage
            
        Returns:
            List[str]: Liste des erreurs de validation
        """
        errors = []
        
        for i, counting in enumerate(countings, 1):
            if not counting.get('order'):
                errors.append(f"Comptage {i}: L'ordre du comptage est obligatoire")
            
            if not counting.get('count_mode'):
                errors.append(f"Comptage {i}: Le mode de comptage est obligatoire")
            
            # Validation des champs selon le mode de comptage
            count_mode = counting.get('count_mode')
            unit_scanned = counting.get('unit_scanned', False)
            entry_quantity = counting.get('entry_quantity', False)
            stock_situation = counting.get('stock_situation', False)
            is_variant = counting.get('is_variant', False)
            
            if count_mode == "Liste d'emplacement":
                if not unit_scanned and not entry_quantity:
                    errors.append(f"Comptage {i}: Pour le mode 'Liste d'emplacement', un des champs unit_scanned ou entry_quantity doit être true")
                if unit_scanned and entry_quantity:
                    errors.append(f"Comptage {i}: Pour le mode 'Liste d'emplacement', un seul des champs unit_scanned ou entry_quantity doit être true")
                if stock_situation:
                    errors.append(f"Comptage {i}: Pour le mode 'Liste d'emplacement', le champ stock_situation doit être false")
                if is_variant:
                    errors.append(f"Comptage {i}: Pour le mode 'Liste d'emplacement', le champ is_variant doit être false")
                    
            elif count_mode == "Etat de stock":
                if not stock_situation:
                    errors.append(f"Comptage {i}: Pour le mode 'Etat de stock', le champ stock_situation doit être true")
                if unit_scanned:
                    errors.append(f"Comptage {i}: Pour le mode 'Etat de stock', le champ unit_scanned doit être false")
                if entry_quantity:
                    errors.append(f"Comptage {i}: Pour le mode 'Etat de stock', le champ entry_quantity doit être false")
                if is_variant:
                    errors.append(f"Comptage {i}: Pour le mode 'Etat de stock', le champ is_variant doit être false")
                    
            elif count_mode == "Liste emplacement et article":
                if unit_scanned:
                    errors.append(f"Comptage {i}: Pour le mode 'Liste emplacement et article', le champ unit_scanned doit être false")
                if entry_quantity:
                    errors.append(f"Comptage {i}: Pour le mode 'Liste emplacement et article', le champ entry_quantity doit être false")
                if stock_situation:
                    errors.append(f"Comptage {i}: Pour le mode 'Liste emplacement et article', le champ stock_situation doit être false")
                    
            elif count_mode == "Hybride":
                if unit_scanned:
                    errors.append(f"Comptage {i}: Pour le mode 'Hybride', le champ unit_scanned doit être false")
                if entry_quantity:
                    errors.append(f"Comptage {i}: Pour le mode 'Hybride', le champ entry_quantity doit être false")
                if stock_situation:
                    errors.append(f"Comptage {i}: Pour le mode 'Hybride', le champ stock_situation doit être false")
                if is_variant:
                    errors.append(f"Comptage {i}: Pour le mode 'Hybride', le champ is_variant doit être false")
        
        return errors
    
    def create_inventory(self, data: Dict[str, Any]) -> Inventory:
        """
        Crée un nouvel inventaire.
        
        Args:
            data: Les données de l'inventaire
            
        Returns:
            Inventory: L'inventaire créé
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        # Validation complète des données avant toute création
        self.validate_inventory_data(data)
        
        # Extraction des données
        label = data['label']
        date = data['date']
        account_id = data['account']
        warehouse_ids = data['warehouse']
        comptages_data = data['comptages']
        
        try:
            # Création de l'inventaire
            inventory = self.repository.create(
                label=label,
                date=date,
                status='PENDING',
                pending_status_date=timezone.now()
            )
            
            # Création des liens entre l'inventaire et les entrepôts
            for warehouse_id in warehouse_ids:
                Setting.objects.create(
                    account_id=account_id,
                    warehouse_id=warehouse_id,
                    inventory=inventory
                )
            
            # Création des comptages
            for comptage_data in comptages_data:
                Counting.objects.create(
                    inventory=inventory,
                    **comptage_data
                )
            
            return inventory
            
        except IntegrityError as e:
            # En cas d'erreur d'intégrité, on supprime l'inventaire s'il a été créé
            if 'inventory' in locals():
                inventory.delete()
            # On log l'erreur détaillée dans le terminal
            logger.error(f"Erreur d'intégrité lors de la création de l'inventaire: {str(e)}")
            # On relance uniquement les erreurs de validation
            raise InventoryValidationError("Erreur de validation des données")
        except Exception as e:
            # En cas d'erreur, on supprime l'inventaire s'il a été créé
            if 'inventory' in locals():
                inventory.delete()
            # On log l'erreur détaillée dans le terminal
            logger.error(f"Erreur inattendue lors de la création de l'inventaire: {str(e)}")
            raise InventoryValidationError("Une erreur inattendue s'est produite")

    @staticmethod
    def validate_counting_modes(comptages) -> List[str]:
        """
        Valide les modes de comptage
        
        Returns:
            List[str]: Liste des erreurs de validation
        """
        errors = []
        
        if len(comptages) < 3:
            errors.append("Il doit y avoir au moins 3 comptages")
        else:
            first_mode = comptages[0]['count_mode']
            second_mode = comptages[1]['count_mode']
            third_mode = comptages[2]['count_mode']

            if first_mode == "Etat de stock":
                if third_mode != second_mode:
                    errors.append("Le mode du troisième comptage doit être identique au deuxième quand le premier est 'Etat de stock'")
            else:
                if third_mode != first_mode and third_mode != second_mode:
                    errors.append("Le mode du troisième comptage doit être identique au premier ou au deuxième")
        
        return errors 