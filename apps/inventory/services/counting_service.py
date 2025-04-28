"""
Service pour la gestion des comptages d'inventaire.
"""
from typing import Dict, Any, List
from django.utils import timezone
from ..interfaces import ICountingService
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
        if not data.get('inventory_id'):
            raise CountingValidationError("L'ID de l'inventaire est obligatoire")
        
        if not data.get('order'):
            raise CountingValidationError("L'ordre du comptage est obligatoire")
        
        if not data.get('count_mode'):
            raise CountingValidationError("Le mode de comptage est obligatoire")
        
        # Vérification de l'existence de l'inventaire
        try:
            inventory = self.repository.get_by_id(data['inventory_id'])
            if inventory.status != 'PENDING':
                raise CountingValidationError("L'inventaire n'est pas en statut PENDING")
        except Inventory.DoesNotExist:
            raise CountingValidationError("L'inventaire spécifié n'existe pas")
        
        # Validation des champs selon le mode de comptage
        count_mode = data.get('count_mode')
        unit_scanned = data.get('unit_scanned', False)
        entry_quantity = data.get('entry_quantity', False)
        stock_situation = data.get('stock_situation', False)
        is_variant = data.get('is_variant', False)
        
        if count_mode == "Liste d'emplacement":
            if not (unit_scanned or entry_quantity):
                raise CountingValidationError("Pour le mode 'Liste d'emplacement', au moins un des champs unit_scanned ou entry_quantity doit être true")
            if stock_situation:
                raise CountingValidationError("Pour le mode 'Liste d'emplacement', le champ stock_situation doit être false")
            if is_variant:
                raise CountingValidationError("Pour le mode 'Liste d'emplacement', le champ is_variant doit être false")
                
        elif count_mode == "Etat de stock":
            if not stock_situation:
                raise CountingValidationError("Pour le mode 'Etat de stock', le champ stock_situation doit être true")
            if unit_scanned:
                raise CountingValidationError("Pour le mode 'Etat de stock', le champ unit_scanned doit être false")
            if entry_quantity:
                raise CountingValidationError("Pour le mode 'Etat de stock', le champ entry_quantity doit être false")
            if is_variant:
                raise CountingValidationError("Pour le mode 'Etat de stock', le champ is_variant doit être false")
                
        elif count_mode == "Liste emplacement et article":
            if unit_scanned:
                raise CountingValidationError("Pour le mode 'Liste emplacement et article', le champ unit_scanned doit être false")
            if entry_quantity:
                raise CountingValidationError("Pour le mode 'Liste emplacement et article', le champ entry_quantity doit être false")
            if stock_situation:
                raise CountingValidationError("Pour le mode 'Liste emplacement et article', le champ stock_situation doit être false")
                
        elif count_mode == "Hybride":
            if unit_scanned:
                raise CountingValidationError("Pour le mode 'Hybride', le champ unit_scanned doit être false")
            if entry_quantity:
                raise CountingValidationError("Pour le mode 'Hybride', le champ entry_quantity doit être false")
            if stock_situation:
                raise CountingValidationError("Pour le mode 'Hybride', le champ stock_situation doit être false")
            if is_variant:
                raise CountingValidationError("Pour le mode 'Hybride', le champ is_variant doit être false")
    
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
            pending_status_date=timezone.now(),
            unit_scanned=data.get('unit_scanned', False),
            entry_quantity=data.get('entry_quantity', False),
            stock_situation=data.get('stock_situation', False),
            is_variant=data.get('is_variant', False)
        )
        
        return counting
    
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