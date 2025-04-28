"""
Repositories pour l'application inventory.
"""
from typing import List, Optional
from django.db import models
from .interfaces import IInventoryRepository
from .models import Inventory
from .exceptions import InventoryNotFoundError

class InventoryRepository(IInventoryRepository):
    """Repository pour les inventaires."""
    
    def get_by_id(self, inventory_id: int) -> Inventory:
        """Récupère un inventaire par son ID."""
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"Inventory with id {inventory_id} not found")
    
    def get_all(self) -> List[Inventory]:
        """Récupère tous les inventaires."""
        return list(Inventory.objects.all().order_by('-created_at'))
    
    def get_by_reference(self, reference: str) -> Optional[Inventory]:
        """Récupère un inventaire par sa référence."""
        try:
            return Inventory.objects.get(reference=reference)
        except Inventory.DoesNotExist:
            return None
    
    def create(self, **kwargs) -> Inventory:
        """Crée un nouvel inventaire."""
        return Inventory.objects.create(**kwargs)
    
    def update(self, inventory: Inventory, **kwargs) -> Inventory:
        """Met à jour un inventaire."""
        for key, value in kwargs.items():
            setattr(inventory, key, value)
        inventory.save()
        return inventory 