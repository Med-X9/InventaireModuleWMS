from django.db.models import Q
from ..models import Inventory, Setting, Counting
from apps.inventory.exceptions.inventory_exceptions import InventoryNotFoundError
from ..interfaces.inventory_interface import IInventoryRepository
from typing import List, Dict, Any
from django.utils import timezone
from django.db import transaction

class InventoryRepository(IInventoryRepository):
    """
    Repository pour la gestion des inventaires
    """
    def get_all(self) -> List[Any]:
        """
        Récupère tous les inventaires non supprimés
        """
        return Inventory.objects.filter(is_deleted=False).order_by('-created_at')

    def get_by_id(self, inventory_id: int) -> Any:
        """
        Récupère un inventaire par son ID, en excluant les supprimés
        """
        try:
            return Inventory.objects.filter(is_deleted=False).get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas.")

    def get_by_reference(self, reference: str) -> Any:
        """
        Récupère un inventaire par sa référence, en excluant les supprimés
        """
        try:
            return Inventory.objects.filter(is_deleted=False).get(reference=reference)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec la référence {reference} n'existe pas.")

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

        return queryset.distinct().order_by('-created_at')

    def create(self, inventory_data: Dict[str, Any]) -> Any:
        """
        Crée un nouvel inventaire
        """
        with transaction.atomic():
            # Extraire les données des entrepôts et des comptages
            warehouse_ids = inventory_data.pop('warehouse', [])
            comptages = inventory_data.pop('comptages', [])
            account_id = inventory_data.pop('account_id', None)

            # S'assurer que les champs status et date sont définis
            if 'status' not in inventory_data:
                inventory_data['status'] = 'EN PREPARATION'
            if 'date' not in inventory_data:
                inventory_data['date'] = timezone.now()
            
            # S'assurer que la date de préparation est définie si le statut est EN PREPARATION
            if inventory_data.get('status') == 'EN PREPARATION' and 'en_preparation_status_date' not in inventory_data:
                inventory_data['en_preparation_status_date'] = timezone.now()

            # Créer l'objet Inventory sans sauvegarder
            inventory = Inventory(**inventory_data)
            
            # Générer la référence manuellement
            inventory.reference = inventory.generate_reference(inventory.REFERENCE_PREFIX)
            
            # Sauvegarder l'objet
            inventory.save()

            # Ajouter les liens avec les entrepôts via Setting
            for warehouse_id in warehouse_ids:
                # Créer l'objet Setting sans sauvegarder
                setting = Setting(
                    inventory=inventory,
                    warehouse_id=warehouse_id,
                    account_id=account_id
                )
                
                # Générer la référence manuellement
                setting.reference = setting.generate_reference(setting.REFERENCE_PREFIX)
                
                # Sauvegarder l'objet
                setting.save()

            # Ajouter les comptages
            for comptage in comptages:
                # Créer l'objet Counting sans sauvegarder
                counting = Counting(
                    inventory=inventory,
                    **comptage
                )
                
                # Générer la référence manuellement
                counting.reference = counting.generate_reference(counting.REFERENCE_PREFIX)
                
                # Sauvegarder l'objet
                counting.save()

            return inventory

    def update(self, inventory_id: int, inventory_data: Dict[str, Any]) -> Any:
        """
        Met à jour un inventaire
        """
        with transaction.atomic():
            inventory = self.get_by_id(inventory_id)

            # Extraire les données des entrepôts et des comptages
            warehouse_ids = inventory_data.pop('warehouse', None)
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
                    # Créer l'objet Setting sans sauvegarder
                    setting = Setting(
                        inventory=inventory,
                        warehouse_id=warehouse_id,
                        account_id=account_id
                    )
                    
                    # Générer la référence manuellement
                    setting.reference = setting.generate_reference(setting.REFERENCE_PREFIX)
                    
                    # Sauvegarder l'objet
                    setting.save()

            # Mettre à jour les comptages si fournis
            if comptages is not None:
                # Supprimer les anciens comptages
                inventory.countings.all().delete()
                # Ajouter les nouveaux comptages
                for comptage in comptages:
                    # Créer l'objet Counting sans sauvegarder
                    counting = Counting(
                        inventory=inventory,
                        **comptage
                    )
                    
                    # Générer la référence manuellement
                    counting.reference = counting.generate_reference(counting.REFERENCE_PREFIX)
                    
                    # Sauvegarder l'objet
                    counting.save()

            return inventory

    def delete(self, inventory_id: int) -> None:
        """
        Supprime un inventaire (soft delete par défaut)
        """
        self.soft_delete(inventory_id)

    def soft_delete(self, inventory_id: int) -> None:
        """
        Effectue un soft delete d'un inventaire en mettant à jour les champs is_deleted et deleted_at
        """
        inventory = self.get_by_id(inventory_id)
        inventory.is_deleted = True
        inventory.deleted_at = timezone.now()
        inventory.save()

    def hard_delete(self, inventory_id: int) -> None:
        """
        Effectue un hard delete d'un inventaire (suppression définitive de la base de données)
        """
        inventory = self.get_by_id(inventory_id)
        inventory.delete()

    def restore(self, inventory_id: int) -> Any:
        """
        Restaure un inventaire qui a été soft deleted
        """
        try:
            inventory = Inventory.objects.get(id=inventory_id, is_deleted=True)
            inventory.is_deleted = False
            inventory.deleted_at = None
            inventory.save()
            return inventory
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas ou n'est pas supprimé.")

    def get_deleted_inventories(self) -> List[Any]:
        """
        Récupère tous les inventaires soft deleted
        """
        return Inventory.objects.filter(is_deleted=True).order_by('-deleted_at')

    def get_deleted_by_id(self, inventory_id: int) -> Any:
        """
        Récupère un inventaire soft deleted par son ID
        """
        try:
            return Inventory.objects.get(id=inventory_id, is_deleted=True)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas ou n'est pas supprimé.")

    def permanent_delete(self, inventory_id: int) -> None:
        """
        Alias pour hard_delete - supprime définitivement un inventaire
        """
        self.hard_delete(inventory_id)

    def bulk_soft_delete(self, inventory_ids: List[int]) -> int:
        """
        Effectue un soft delete en masse sur plusieurs inventaires
        """
        count = Inventory.objects.filter(
            id__in=inventory_ids, 
            is_deleted=False
        ).update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        return count

    def bulk_restore(self, inventory_ids: List[int]) -> int:
        """
        Restaure en masse plusieurs inventaires soft deleted
        """
        count = Inventory.objects.filter(
            id__in=inventory_ids, 
            is_deleted=True
        ).update(
            is_deleted=False,
            deleted_at=None
        )
        return count

    def bulk_hard_delete(self, inventory_ids: List[int]) -> int:
        """
        Effectue un hard delete en masse sur plusieurs inventaires
        """
        count, _ = Inventory.objects.filter(
            id__in=inventory_ids
        ).delete()
        return count

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
            ).get(id=inventory_id, is_deleted=False)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas.")

    def get_with_related_data_by_reference(self, reference: str) -> Any:
        """
        Récupère un inventaire avec ses données associées par sa référence
        """
        try:
            return Inventory.objects.prefetch_related(
                'awi_links',
                'awi_links__account',
                'awi_links__warehouse',
                'countings'
            ).get(reference=reference, is_deleted=False)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"L'inventaire avec la référence {reference} n'existe pas.")

    def get_warehouses_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """
        Récupère tous les entrepôts associés à un inventaire
        """
        inventory = self.get_by_id(inventory_id)
        return [link.warehouse for link in inventory.awi_links.all().select_related('warehouse')]

    def get_countings_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """
        Récupère tous les comptages associés à un inventaire
        """
        inventory = self.get_by_id(inventory_id)
        return inventory.countings.all().order_by('order')

    def get_by_status(self, status: str) -> List[Any]:
        """
        Récupère les inventaires par statut
        """
        return Inventory.objects.filter(status=status, is_deleted=False).order_by('-created_at')

    def get_by_account_id(self, account_id: int) -> List[Any]:
        """
        Récupère les inventaires par compte
        """
        return Inventory.objects.filter(
            awi_links__account_id=account_id, 
            is_deleted=False
        ).distinct().order_by('-created_at')

    def get_by_warehouse_id(self, warehouse_id: int) -> List[Any]:
        """
        Récupère les inventaires par entrepôt
        """
        return Inventory.objects.filter(
            awi_links__warehouse_id=warehouse_id, 
            is_deleted=False
        ).distinct().order_by('-created_at')

    def get_active_inventories(self) -> List[Any]:
        """
        Récupère les inventaires actifs (non terminés et non clôturés)
        """
        return Inventory.objects.filter(
            status__in=['EN PREPARATION', 'EN REALISATION'],
            is_deleted=False
        ).order_by('-created_at')

    def get_completed_inventories(self) -> List[Any]:
        """
        Récupère les inventaires terminés
        """
        return Inventory.objects.filter(
            status__in=['TERMINE', 'CLOTURE'],
            is_deleted=False
        ).order_by('-created_at')

    def get_warehouse_jobs_sessions_stats(self, inventory_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques des warehouses avec count des jobs et sessions
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            List[Dict[str, Any]]: Liste avec nom warehouse, count jobs et count sessions
        """
        from django.db.models import Count, Q
        from ..models import Job, Assigment, Setting
        
        # Récupérer tous les warehouses associés à cet inventaire avec leurs statistiques
        warehouse_stats = Setting.objects.filter(
            inventory_id=inventory_id
        ).select_related('warehouse').annotate(
            jobs_count=Count(
                'warehouse__job',
                filter=Q(warehouse__job__inventory_id=inventory_id)
            ),
            sessions_count=Count(
                'warehouse__job__assigment__session',
                filter=Q(
                    warehouse__job__inventory_id=inventory_id,
                    warehouse__job__assigment__session__isnull=False,
                    warehouse__job__assigment__session__type='Mobile'
                ),
                distinct=True
            )
        )
        
        result = []
        for setting in warehouse_stats:
            result.append({
                'nom_warehouse': setting.warehouse.warehouse_name,
                'jobs_count': setting.jobs_count,
                'sessions_count': setting.sessions_count
            })
        
        return result

    def update_status(self, inventory_id: int, new_status: str) -> Any:
        """
        Met à jour le statut d'un inventaire
        """
        inventory = self.get_by_id(inventory_id)
        inventory.status = new_status
        
        # Mettre à jour la date correspondante au statut
        if new_status == 'EN PREPARATION':
            inventory.en_preparation_status_date = timezone.now()
        elif new_status == 'EN REALISATION':
            inventory.en_realisation_status_date = timezone.now()
        elif new_status == 'TERMINE':
            inventory.termine_status_date = timezone.now()
        elif new_status == 'CLOTURE':
            inventory.cloture_status_date = timezone.now()
        
        inventory.save()
        return inventory

    def exists(self, inventory_id: int) -> bool:
        """
        Vérifie si un inventaire existe
        """
        return Inventory.objects.filter(id=inventory_id, is_deleted=False).exists()

    def count_by_status(self, status: str) -> int:
        """
        Compte le nombre d'inventaires par statut
        """
        return Inventory.objects.filter(status=status, is_deleted=False).count()

    def get_recent_inventories(self, limit: int = 10) -> List[Any]:
        """
        Récupère les inventaires les plus récents
        """
        return Inventory.objects.filter(
            is_deleted=False
        ).order_by('-created_at')[:limit] 