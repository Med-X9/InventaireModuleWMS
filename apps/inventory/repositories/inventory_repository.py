from django.db.models import Q
from ..models import Inventory, Setting, Counting
from apps.inventory.exceptions.inventory_exceptions import InventoryNotFoundError
from ..interfaces.inventory_interface import IInventoryRepository
from typing import List, Dict, Any
from django.utils import timezone

class InventoryRepository(IInventoryRepository):
    """
    Repository pour la gestion des inventaires
    """
    def get_all(self) -> List[Any]:
        """
        Récupère tous les inventaires non supprimés
        """
        return Inventory.objects.filter(is_deleted=False)

    def get_by_id(self, inventory_id: int) -> Any:
        """
        Récupère un inventaire par son ID, en excluant les supprimés
        """
        try:
            return Inventory.objects.filter(is_deleted=False).get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas.")

    def get_by_filters(self, filters_dict: Dict[str, Any]) -> List[Any]:
        """
        Récupère les inventaires selon les filtres, en excluant les supprimés
        """
        queryset = Inventory.objects.filter(is_deleted=False)

        # Filtrage par statut
        if 'status' in filters_dict:
            queryset = queryset.filter(status=filters_dict['status'])

        # Filtrage par date de début
        if 'date_start' in filters_dict:
            queryset = queryset.filter(date__gte=filters_dict['date_start'])

        # Filtrage par date de fin
        if 'date_end' in filters_dict:
            queryset = queryset.filter(date__lte=filters_dict['date_end'])

        # Filtrage par label
        if 'label' in filters_dict:
            queryset = queryset.filter(label__icontains=filters_dict['label'])

        # Filtrage par compte
        if 'account_id' in filters_dict:
            queryset = queryset.filter(awi_links__account_id=filters_dict['account_id'])

        # Filtrage par entrepôt
        if 'warehouse_id' in filters_dict:
            queryset = queryset.filter(awi_links__warehouse_id=filters_dict['warehouse_id'])

        # Filtrage par mode de comptage
        if 'counting_mode' in filters_dict:
            queryset = queryset.filter(countings__count_mode=filters_dict['counting_mode'])

        return queryset.distinct()

    def create(self, inventory_data: Dict[str, Any]) -> Any:
        """
        Crée un nouvel inventaire
        """
        # Extraire les données des entrepôts et des comptages
        warehouse_ids = inventory_data.pop('warehouse_ids', [])
        comptages = inventory_data.pop('comptages', [])
        account_id = inventory_data.pop('account_id', None)

        # S'assurer que les champs status et pending_status_date sont définis
        if 'status' not in inventory_data:
            inventory_data['status'] = 'PENDING'
        if 'pending_status_date' not in inventory_data:
            inventory_data['pending_status_date'] = timezone.now()

        # Créer l'inventaire
        inventory = Inventory.objects.create(**inventory_data)

        # Ajouter les liens avec les entrepôts via Setting
        for warehouse_id in warehouse_ids:
            Setting.objects.create(
                inventory=inventory,
                warehouse_id=warehouse_id,
                account_id=account_id
            )

        # Ajouter les comptages
        for comptage in comptages:
            Counting.objects.create(
                inventory=inventory,
                **comptage
            )

        return inventory

    def update(self, inventory_id: int, inventory_data: Dict[str, Any]) -> Any:
        """
        Met à jour un inventaire
        """
        inventory = self.get_by_id(inventory_id)

        # Extraire les données des entrepôts et des comptages
        warehouse_ids = inventory_data.pop('warehouse_ids', None)
        comptages = inventory_data.pop('comptages', None)
        account_id = inventory_data.pop('account_id', None)

        # Mettre à jour les champs de base
        for key, value in inventory_data.items():
            setattr(inventory, key, value)
        inventory.save()

        # Mettre à jour les entrepôts si fournis
        if warehouse_ids is not None:
            # Supprimer les anciennes associations
            inventory.awi_links.all().delete()
            # Ajouter les nouvelles associations
            for warehouse_id in warehouse_ids:
                Setting.objects.create(
                    inventory=inventory,
                    warehouse_id=warehouse_id,
                    account_id=account_id
                )

        # Mettre à jour les comptages si fournis
        if comptages is not None:
            # Supprimer les anciens comptages
            inventory.countings.all().delete()
            # Ajouter les nouveaux comptages
            for comptage in comptages:
                Counting.objects.create(
                    inventory=inventory,
                    **comptage
                )

        return inventory

    def delete(self, inventory_id: int) -> None:
        """
        Effectue un soft delete d'un inventaire en mettant à jour les champs is_deleted et deleted_at
        """
        inventory = self.get_by_id(inventory_id)
        inventory.is_deleted = True
        inventory.deleted_at = timezone.now()
        inventory.save()

    def get_with_related_data(self, inventory_id: int) -> Any:
        """
        Récupère un inventaire avec ses données associées
        """
        try:
            return Inventory.objects.prefetch_related(
                'awi_links',
                'awi_links__account',
                'awi_links__warehouse',
                'countings'
            ).get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas.")

    def get_warehouses_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """
        Récupère tous les entrepôts associés à un inventaire
        """
        inventory = self.get_by_id(inventory_id)
        return [link.warehouse for link in inventory.awi_links.all().select_related('warehouse')] 