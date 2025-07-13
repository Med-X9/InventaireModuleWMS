from typing import Dict, Any, List, Optional
from django.db import transaction
from ..interfaces.inventory_resource_interface import IInventoryResourceRepository
from ..models import Inventory, InventoryDetailRessource
from apps.masterdata.models import Ressource

class InventoryResourceRepository(IInventoryResourceRepository):
    """Repository pour l'affectation des ressources aux inventaires"""
    
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Récupère un inventaire par son ID"""
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            return None
    
    def get_resource_by_id(self, resource_id: int) -> Optional[Ressource]:
        """Récupère une ressource par son ID"""
        try:
            return Ressource.objects.get(id=resource_id)
        except Ressource.DoesNotExist:
            return None
    
    def get_existing_inventory_resource(self, inventory_id: int, resource_id: int) -> Optional[InventoryDetailRessource]:
        """Récupère une affectation ressource-inventaire existante"""
        try:
            return InventoryDetailRessource.objects.get(inventory_id=inventory_id, ressource_id=resource_id)
        except InventoryDetailRessource.DoesNotExist:
            return None
    
    def create_inventory_resource(self, assignment_data: Dict[str, Any]) -> InventoryDetailRessource:
        """Crée une nouvelle affectation ressource-inventaire"""
        return InventoryDetailRessource.objects.create(**assignment_data)
    
    def update_inventory_resource(self, inventory_resource: InventoryDetailRessource, **kwargs) -> None:
        """Met à jour une affectation ressource-inventaire"""
        for key, value in kwargs.items():
            setattr(inventory_resource, key, value)
        inventory_resource.save()
    
    def get_inventory_resources(self, inventory_id: int) -> List[InventoryDetailRessource]:
        """Récupère toutes les ressources affectées à un inventaire"""
        return list(InventoryDetailRessource.objects.filter(inventory_id=inventory_id).select_related('ressource'))
    
    def delete_inventory_resources(self, inventory_id: int, resource_ids: List[int]) -> int:
        """Supprime des affectations ressource-inventaire"""
        deleted_count, _ = InventoryDetailRessource.objects.filter(
            inventory_id=inventory_id,
            ressource_id__in=resource_ids
        ).delete()
        return deleted_count 