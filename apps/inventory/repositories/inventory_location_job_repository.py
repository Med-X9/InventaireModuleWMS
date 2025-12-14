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
    
    def bulk_upsert(self, data_list: List[Dict[str, Any]], inventory_id: int) -> Dict[str, int]:
        """
        Effectue un upsert (update or insert) en masse pour InventoryLocationJob
        Clé unique : (inventaire_id, emplacement_id)
        
        Args:
            data_list: Liste de dictionnaires contenant les données
            inventory_id: ID de l'inventaire
            
        Returns:
            Dict contenant le nombre d'objets créés et mis à jour
        """
        if not data_list:
            return {'created': 0, 'updated': 0}
        
        # Récupérer les emplacement_ids pour cet inventaire
        emplacement_ids = [data['emplacement_id'] for data in data_list if data.get('emplacement_id')]
        
        # Récupérer les enregistrements existants
        existing_objects = InventoryLocationJob.objects.filter(
            inventaire_id=inventory_id,
            emplacement_id__in=emplacement_ids,
            is_deleted=False
        )
        
        # Créer un dictionnaire pour un accès rapide : (emplacement_id) -> InventoryLocationJob
        existing_map = {obj.emplacement_id: obj for obj in existing_objects}
        
        # Séparer les objets à créer et ceux à mettre à jour
        objects_to_create = []
        objects_to_update = []
        
        for data in data_list:
            emplacement_id = data.get('emplacement_id')
            if not emplacement_id:
                continue
            
            existing_obj = existing_map.get(emplacement_id)
            
            if existing_obj:
                # Mettre à jour l'objet existant
                for key, value in data.items():
                    setattr(existing_obj, key, value)
                objects_to_update.append(existing_obj)
            else:
                # Créer un nouvel objet
                objects_to_create.append(InventoryLocationJob(**data))
        
        # Effectuer les opérations en masse
        created_count = 0
        updated_count = 0
        
        if objects_to_create:
            created_objects = InventoryLocationJob.objects.bulk_create(objects_to_create)
            created_count = len(created_objects)
        
        if objects_to_update:
            InventoryLocationJob.objects.bulk_update(
                objects_to_update,
                ['job', 'session_1', 'session_2', 'updated_at']
            )
            updated_count = len(objects_to_update)
        
        return {
            'created': created_count,
            'updated': updated_count
        }

