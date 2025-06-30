"""
Service pour la gestion des comptages d'inventaire.
"""
from typing import Dict, Any, List
from django.utils import timezone
from ..interfaces.counting_interface import ICountingService
from ..repositories import InventoryRepository
from ..exceptions import CountingValidationError
from ..models import Counting, Inventory

class CountingService(ICountingService):
    """Service pour la gestion des comptages d'inventaire."""
    
    def __init__(self, repository: InventoryRepository = None):
        self.repository = repository or InventoryRepository()
    
    def validate_counting_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données d'un comptage.
        
        Args:
            data: Les données à valider
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        errors = []
        
        if not data.get('order'):
            errors.append("L'ordre du comptage est obligatoire")
        
        if not data.get('count_mode'):
            errors.append("Le mode de comptage est obligatoire")
        else:
            valid_modes = ["Liste d'emplacement", "Liste emplacement et article", "Etat de stock", "Hybride"]
            if data['count_mode'] not in valid_modes:
                errors.append(f"Mode de comptage invalide: {data['count_mode']}")
        
        # Validation des champs selon le mode de comptage
        count_mode = data.get('count_mode')
        unit_scanned = data.get('unit_scanned', False)
        entry_quantity = data.get('entry_quantity', False)
        stock_situation = data.get('stock_situation', False)
        is_variant = data.get('is_variant', False)
        quantity_show = data.get('quantity_show', False)

        if count_mode == "Liste d'emplacement":
            if not (unit_scanned or entry_quantity):
                errors.append("Pour le mode 'Liste d'emplacement', au moins un des champs unit_scanned ou entry_quantity doit être true")
            if unit_scanned and entry_quantity:
                errors.append("Pour le mode 'Liste d'emplacement', un seul des champs unit_scanned ou entry_quantity doit être true")
            if stock_situation:
                errors.append("Pour le mode 'Liste d'emplacement', le champ stock_situation doit être false")
            if is_variant:
                errors.append("Pour le mode 'Liste d'emplacement', le champ is_variant doit être false")
            if quantity_show:
                errors.append("Pour le mode 'Liste d'emplacement', le champ quantity_show doit être false")
                
        elif count_mode == "Etat de stock":
            if not stock_situation:
                errors.append("Pour le mode 'Etat de stock', le champ stock_situation doit être true")
            if unit_scanned:
                errors.append("Pour le mode 'Etat de stock', le champ unit_scanned doit être false")
            if entry_quantity:
                errors.append("Pour le mode 'Etat de stock', le champ entry_quantity doit être false")
            if is_variant:
                errors.append("Pour le mode 'Etat de stock', le champ is_variant doit être false")
            if quantity_show:
                errors.append("Pour le mode 'Liste d'emplacement', le champ quantity_show doit être false")
                
        elif count_mode == "Liste emplacement et article":
            if unit_scanned:
                errors.append("Pour le mode 'Liste emplacement et article', le champ unit_scanned doit être false")
            if entry_quantity:
                errors.append("Pour le mode 'Liste emplacement et article', le champ entry_quantity doit être false")
            if stock_situation:
                errors.append("Pour le mode 'Liste emplacement et article', le champ stock_situation doit être false")
            # if not is_variant:
            #     errors.append("Pour le mode 'Liste emplacement et article', le champ is_variant doit être true")
                
        elif count_mode == "Hybride":
            if unit_scanned:
                errors.append("Pour le mode 'Hybride', le champ unit_scanned doit être false")
            if entry_quantity:
                errors.append("Pour le mode 'Hybride', le champ entry_quantity doit être false")
            if stock_situation:
                errors.append("Pour le mode 'Hybride', le champ stock_situation doit être false")
            if quantity_show:
                errors.append("Pour le mode 'Liste d'emplacement', le champ quantity_show doit être false")
            
        
        if errors:
            raise CountingValidationError(" | ".join(errors))

    def validate_countings_consistency(self, comptages: List[Dict[str, Any]]) -> None:
        """
        Valide la cohérence des modes de comptage entre les comptages.
        
        Args:
            comptages: Liste des comptages à valider
            
        Raises:
            CountingValidationError: Si les modes de comptage ne sont pas cohérents
        """
        if len(comptages) < 3:
            return

        # Trier les comptages par ordre
        sorted_comptages = sorted(comptages, key=lambda x: x.get('order', 0))
        
        # Vérifier le mode du troisième comptage
        third_counting = sorted_comptages[2]
        first_counting = sorted_comptages[0]
        second_counting = sorted_comptages[1]

        # Si le premier comptage est en mode "Etat de stock"
        if first_counting.get('count_mode') == "Etat de stock":
            # Le troisième comptage doit avoir le même mode que le deuxième
            if third_counting.get('count_mode') != second_counting.get('count_mode'):
                raise CountingValidationError(
                    "Si le premier comptage est en mode 'Etat de stock', "
                    "le troisième comptage doit avoir le même mode que le deuxième comptage"
                )
        else:
            # Sinon, le troisième comptage doit avoir le même mode que le premier ou le deuxième
            valid_modes = [first_counting.get('count_mode'), second_counting.get('count_mode')]
            if third_counting.get('count_mode') not in valid_modes:
                raise CountingValidationError(
                    f"Le troisième comptage doit avoir le même mode que le premier ({first_counting.get('count_mode')}) "
                    f"ou le deuxième comptage ({second_counting.get('count_mode')}). "
                    f"Mode actuel: {third_counting.get('count_mode')}"
                )
    
    def create_counting(self, data: Dict[str, Any]) -> Counting:
        """
        Crée un nouveau comptage.
        
        Args:
            data: Les données du comptage
            
        Returns:
            Counting: Le comptage créé
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        # Validation des données
        self.validate_counting_data(data)
        
        # Création du comptage
        counting = Counting.objects.create(
            inventory_id=data['inventory_id'],
            order=data['order'],
            count_mode=data['count_mode'],
            status='PENDING',
            unit_scanned=data.get('unit_scanned', False),
            entry_quantity=data.get('entry_quantity', False),
            stock_situation=data.get('stock_situation', False),
            is_variant=data.get('is_variant', False)
        )
        
        return counting

    def create_countings(self, inventory_id: int, comptages_data: List[Dict[str, Any]]) -> List[Counting]:
        """
        Crée plusieurs comptages pour un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            comptages_data: Liste des données des comptages
            
        Returns:
            List[Counting]: Liste des comptages créés
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        # Validation de la cohérence des modes de comptage
        self.validate_countings_consistency(comptages_data)
        
        countings = []
        for comptage_data in comptages_data:
            comptage_data['inventory_id'] = inventory_id
            counting = self.create_counting(comptage_data)
            countings.append(counting)
        
        return countings
    
    def update_counting_status(self, counting_id: int, status: str) -> Counting:
        """
        Met à jour le statut d'un comptage.
        
        Args:
            counting_id: L'ID du comptage
            status: Le nouveau statut
            
        Returns:
            Counting: Le comptage mis à jour
            
        Raises:
            CountingValidationError: Si le statut est invalide
        """
        try:
            counting = Counting.objects.get(id=counting_id)
        except Counting.DoesNotExist:
            raise CountingValidationError("Le comptage spécifié n'existe pas")
        
        valid_statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
        if status not in valid_statuses:
            raise CountingValidationError(f"Statut invalide. Doit être l'un des suivants: {', '.join(valid_statuses)}")
        
        counting.status = status
        counting.save()
        
        return counting 