from typing import Any, List, Dict
from django.db import transaction
from apps.masterdata.models import InventoryLocationJob
from ..interfaces.inventory_location_job_interface import IInventoryLocationJobRepository


class InventoryLocationJobRepository(IInventoryLocationJobRepository):
    """
    Repository pour la gestion des InventoryLocationJob
    """
    
    def create(self, data: Dict[str, Any]) -> Any:
        """
        Crée un nouvel InventoryLocationJob
        
        Args:
            data: Dictionnaire contenant les données (inventaire, emplacement, job, session_1, session_2)
            
        Returns:
            InventoryLocationJob: L'objet créé
        """
        return InventoryLocationJob.objects.create(**data)
    
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[Any]:
        """
        Crée plusieurs InventoryLocationJob en une seule opération
        
        Args:
            data_list: Liste de dictionnaires contenant les données
            
        Returns:
            List[InventoryLocationJob]: Liste des objets créés
        """
        objects = [InventoryLocationJob(**data) for data in data_list]
        return InventoryLocationJob.objects.bulk_create(objects)
    
    def get_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """
        Récupère tous les InventoryLocationJob pour un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            List[InventoryLocationJob]: Liste des objets
        """
        return InventoryLocationJob.objects.filter(
            inventaire_id=inventory_id,
            is_deleted=False
        ).select_related('inventaire', 'emplacement')
    
    def delete_by_inventory_id(self, inventory_id: int) -> int:
        """
        Supprime tous les InventoryLocationJob pour un inventaire (soft delete)
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            int: Nombre d'objets supprimés
        """
        from django.utils import timezone
        
        count = InventoryLocationJob.objects.filter(
            inventaire_id=inventory_id,
            is_deleted=False
        ).update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        return count

