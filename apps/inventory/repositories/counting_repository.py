from django.db.models import Q, Max, Sum, F, IntegerField
from django.db.models.functions import Cast
from ..models import Counting, CountingDetail, Inventory
from apps.inventory.exceptions.counting_exceptions import CountingNotFoundError
from ..interfaces.counting_interface import ICountingRepository
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db import transaction


class CountingRepository(ICountingRepository):
    """
    Repository pour la gestion des comptages
    """
    
    def get_all(self) -> List[Any]:
        """
        Récupère tous les comptages
        """
        return Counting.objects.all().order_by('-created_at')

    def get_by_id(self, counting_id: int) -> Any:
        """
        Récupère un comptage par son ID
        """
        try:
            return Counting.objects.get(id=counting_id)
        except Counting.DoesNotExist:
            raise CountingNotFoundError(f"Le comptage avec l'ID {counting_id} n'existe pas.")

    def get_by_filters(self, filters_dict: Dict[str, Any]) -> List[Any]:
        """
        Récupère les comptages selon les filtres
        """
        queryset = Counting.objects.all()

        # Filtrage par inventaire
        if 'inventory_id' in filters_dict:
            queryset = queryset.filter(inventory_id=filters_dict['inventory_id'])

        # Filtrage par mode de comptage
        if 'count_mode' in filters_dict:
            queryset = queryset.filter(count_mode=filters_dict['count_mode'])

        # Filtrage par ordre
        if 'order' in filters_dict:
            queryset = queryset.filter(order=filters_dict['order'])

        # Filtrage par unit_scanned
        if 'unit_scanned' in filters_dict:
            queryset = queryset.filter(unit_scanned=filters_dict['unit_scanned'])

        # Filtrage par entry_quantity
        if 'entry_quantity' in filters_dict:
            queryset = queryset.filter(entry_quantity=filters_dict['entry_quantity'])

        # Filtrage par is_variant
        if 'is_variant' in filters_dict:
            queryset = queryset.filter(is_variant=filters_dict['is_variant'])

        # Filtrage par n_lot
        if 'n_lot' in filters_dict:
            queryset = queryset.filter(n_lot=filters_dict['n_lot'])

        # Filtrage par n_serie
        if 'n_serie' in filters_dict:
            queryset = queryset.filter(n_serie=filters_dict['n_serie'])

        # Filtrage par dlc
        if 'dlc' in filters_dict:
            queryset = queryset.filter(dlc=filters_dict['dlc'])

        # Filtrage par show_product
        if 'show_product' in filters_dict:
            queryset = queryset.filter(show_product=filters_dict['show_product'])

        # Filtrage par stock_situation
        if 'stock_situation' in filters_dict:
            queryset = queryset.filter(stock_situation=filters_dict['stock_situation'])

        # Filtrage par quantity_show
        if 'quantity_show' in filters_dict:
            queryset = queryset.filter(quantity_show=filters_dict['quantity_show'])

        return queryset.distinct().order_by('-created_at')

    def create(self, counting_data: Dict[str, Any]) -> Any:
        """
        Crée un nouveau comptage
        """
        with transaction.atomic():
            # Récupération de l'inventaire
            inventory_id = counting_data.get('inventory_id')
            if not inventory_id:
                raise CountingNotFoundError("L'ID de l'inventaire est obligatoire")
            
            try:
                inventory = Inventory.objects.get(id=inventory_id)
            except Inventory.DoesNotExist:
                raise CountingNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas")
            
            # Création du comptage
            counting = Counting(
                inventory=inventory,
                **counting_data
            )
            
            # Générer la référence manuellement
            counting.reference = counting.generate_reference(counting.REFERENCE_PREFIX)
            
            # Sauvegarder l'objet
            counting.save()
            
            return counting

    def update(self, counting_id: int, counting_data: Dict[str, Any]) -> Any:
        """
        Met à jour un comptage
        """
        with transaction.atomic():
            counting = self.get_by_id(counting_id)
            
            # Mise à jour des champs
            for key, value in counting_data.items():
                if hasattr(counting, key):
                    setattr(counting, key, value)
            
            counting.save()
            return counting

    def delete(self, counting_id: int) -> None:
        """
        Supprime un comptage
        """
        counting = self.get_by_id(counting_id)
        counting.delete()

    def get_by_inventory_id(self, inventory_id: int) -> List[Any]:
        """
        Récupère tous les comptages d'un inventaire
        """
        return Counting.objects.filter(
            inventory_id=inventory_id
        ).order_by('order')

    def get_by_count_mode(self, count_mode: str) -> List[Any]:
        """
        Récupère les comptages par mode de comptage
        """
        return Counting.objects.filter(
            count_mode=count_mode
        ).order_by('-created_at')

    def get_with_related_data(self, counting_id: int) -> Any:
        """
        Récupère un comptage avec ses données associées
        """
        try:
            return Counting.objects.select_related(
                'inventory'
            ).prefetch_related(
                'countingdetail_set'
            ).get(id=counting_id)
        except Counting.DoesNotExist:
            raise CountingNotFoundError(f"Le comptage avec l'ID {counting_id} n'existe pas.")
    
    def get_by_inventory_and_order(self, inventory_id: int, order: int) -> Optional[Counting]:
        """
        Récupère un comptage par inventaire et ordre.
        """
        return Counting.objects.filter(inventory_id=inventory_id, order=order).first()

    # Méthodes spécialisées supplémentaires

    def get_by_inventory_and_mode(self, inventory_id: int, count_mode: str) -> List[Any]:
        """
        Récupère les comptages d'un inventaire par mode de comptage
        """
        return Counting.objects.filter(
            inventory_id=inventory_id,
            count_mode=count_mode
        ).order_by('order')

    def get_by_order_range(self, inventory_id: int, min_order: int, max_order: int) -> List[Any]:
        """
        Récupère les comptages d'un inventaire dans une plage d'ordre
        """
        return Counting.objects.filter(
            inventory_id=inventory_id,
            order__gte=min_order,
            order__lte=max_order
        ).order_by('order')

    def get_enabled_countings(self, inventory_id: int) -> List[Any]:
        """
        Récupère les comptages activés d'un inventaire
        """
        return Counting.objects.filter(
            inventory_id=inventory_id
        ).order_by('order')

    def get_counting_details(self, counting_id: int) -> List[Any]:
        """
        Récupère les détails d'un comptage
        """
        counting = self.get_by_id(counting_id)
        return counting.countingdetail_set.all().order_by('-created_at')

    def count_by_mode(self, inventory_id: int) -> Dict[str, int]:
        """
        Compte le nombre de comptages par mode pour un inventaire
        """
        countings = Counting.objects.filter(inventory_id=inventory_id)
        result = {}
        for counting in countings:
            mode = counting.count_mode
            result[mode] = result.get(mode, 0) + 1
        return result

    def get_next_order(self, inventory_id: int) -> int:
        """
        Récupère le prochain ordre disponible pour un inventaire
        """
        max_order = Counting.objects.filter(
            inventory_id=inventory_id
        ).aggregate(
            max_order=Max('order')
        )['max_order']
        
        return (max_order or 0) + 1

    def reorder_countings(self, inventory_id: int) -> None:
        """
        Réordonne les comptages d'un inventaire
        """
        countings = Counting.objects.filter(
            inventory_id=inventory_id
        ).order_by('order')
        
        for index, counting in enumerate(countings, 1):
            counting.order = index
            counting.save()

    def duplicate_counting(self, counting_id: int) -> Any:
        """
        Duplique un comptage
        """
        with transaction.atomic():
            original = self.get_by_id(counting_id)
            
            # Créer une copie
            counting_data = {
                'inventory': original.inventory,
                'count_mode': original.count_mode,
                'unit_scanned': original.unit_scanned,
                'entry_quantity': original.entry_quantity,
                'is_variant': original.is_variant,
                'n_lot': original.n_lot,
                'n_serie': original.n_serie,
                'dlc': original.dlc,
                'show_product': original.show_product,
                'stock_situation': original.stock_situation,
                'quantity_show': original.quantity_show,
                'order': self.get_next_order(original.inventory.id)
            }
            
            # Créer l'objet Counting sans sauvegarder
            counting = Counting(**counting_data)
            
            # Générer la référence manuellement
            counting.reference = counting.generate_reference(counting.REFERENCE_PREFIX)
            
            # Sauvegarder l'objet
            counting.save()
            
            return counting

    def bulk_create(self, countings_data: List[Dict[str, Any]]) -> List[Any]:
        """
        Crée plusieurs comptages en une seule opération
        """
        with transaction.atomic():
            countings = []
            for data in countings_data:
                # Créer l'objet Counting sans sauvegarder
                counting = Counting(**data)
                
                # Générer la référence manuellement
                counting.reference = counting.generate_reference(counting.REFERENCE_PREFIX)
                
                # Sauvegarder l'objet
                counting.save()
                
                countings.append(counting)
            return countings

    def bulk_update(self, countings_data: List[Dict[str, Any]]) -> int:
        """
        Met à jour plusieurs comptages en une seule opération
        """
        with transaction.atomic():
            count = 0
            for data in countings_data:
                counting_id = data.pop('id')
                try:
                    counting = self.get_by_id(counting_id)
                    for key, value in data.items():
                        if hasattr(counting, key):
                            setattr(counting, key, value)
                    counting.save()
                    count += 1
                except CountingNotFoundError:
                    continue
            return count 

    def get_inventory_results_by_warehouse(
        self,
        inventory_id: int,
        warehouse_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les quantités inventoriées agrégées par entrepôt, emplacement,
        produit (le cas échéant) et ordre de comptage.

        Args:
            inventory_id: Identifiant de l'inventaire ciblé.
            warehouse_id: Identifiant de l'entrepôt à filtrer (optionnel).

        Returns:
            Liste de dictionnaires contenant les quantités agrégées.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Log initial pour débogage
        logger.debug(f"🔍 Récupération des résultats pour inventory_id={inventory_id}, warehouse_id={warehouse_id}")
        
        # Vérifier d'abord combien de CountingDetail existent pour cet inventaire
        all_counting_details = CountingDetail.objects.filter(
            counting__inventory_id=inventory_id
        )
        logger.debug(f"📊 Nombre total de CountingDetail pour inventory_id={inventory_id}: {all_counting_details.count()}")
        
        queryset = CountingDetail.objects.filter(
            counting__inventory_id=inventory_id
        )

        if warehouse_id is not None:
            # Vérifier combien de CountingDetail existent avant le filtre warehouse
            before_warehouse_filter = queryset.count()
            logger.debug(f"📊 Nombre de CountingDetail avant filtre warehouse: {before_warehouse_filter}")
            
            queryset = queryset.filter(job__warehouse_id=warehouse_id)
            
            # Vérifier combien de CountingDetail existent après le filtre warehouse
            after_warehouse_filter = queryset.count()
            logger.debug(f"📊 Nombre de CountingDetail après filtre warehouse_id={warehouse_id}: {after_warehouse_filter}")
            
            # Si aucun résultat, vérifier les jobs pour cet entrepôt
            if after_warehouse_filter == 0:
                from ..models import Job
                jobs_count = Job.objects.filter(
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id
                ).count()
                logger.warning(f"⚠️ Aucun CountingDetail trouvé. Nombre de jobs pour inventory_id={inventory_id}, warehouse_id={warehouse_id}: {jobs_count}")
                
                # Vérifier les countings pour cet inventaire
                from ..models import Counting
                countings = Counting.objects.filter(inventory_id=inventory_id)
                logger.debug(f"📊 Nombre de Counting pour inventory_id={inventory_id}: {countings.count()}")
                for counting in countings:
                    logger.debug(f"   - Counting id={counting.id}, order={counting.order}, count_mode={counting.count_mode}")

        # Sous-requêtes pour récupérer les infos d'EcartComptage (final_result, id)
        # Un EcartComptage est identifié par (product_id, location_id, inventory_id)
        # via ComptageSequence qui lie CountingDetail à EcartComptage
        from django.db.models import OuterRef, Subquery
        from ..models import ComptageSequence
        
        # Récupérer directement le final_result de l'EcartComptage via ComptageSequence.
        base_ecart_qs = ComptageSequence.objects.filter(
            counting_detail__product_id=OuterRef('product_id'),
            counting_detail__location_id=OuterRef('location_id'),
            counting_detail__counting__inventory_id=OuterRef('counting__inventory_id')
        ).order_by('-sequence_number').select_related('ecart_comptage')

        final_result_subquery = base_ecart_qs.values('ecart_comptage__final_result')[:1]
        ecart_id_subquery = base_ecart_qs.values('ecart_comptage_id')[:1]
        resolved_subquery = base_ecart_qs.values('ecart_comptage__resolved')[:1]
        
        annotated_queryset = queryset.annotate(
            warehouse_id_alias=F('job__warehouse_id'),
            warehouse_reference_alias=F('job__warehouse__reference'),
            warehouse_name_alias=F('job__warehouse__warehouse_name'),
            location_reference_alias=F('location__location_reference'),
            location_code_alias=F('location__reference'),
            counting_order_alias=F('counting__order'),
            product_reference_alias=F('product__reference'),
            product_barcode_alias=F('product__Barcode'),
            product_description_alias=F('product__Short_Description'),
            product_internal_code_alias=F('product__Internal_Product_Code'),
            job_reference_alias=F('job__reference'),
            final_result_alias=Subquery(final_result_subquery),
            ecart_id_alias=Subquery(ecart_id_subquery),
            resolved_alias=Subquery(resolved_subquery),
        )

        aggregated_queryset = annotated_queryset.values(
            'warehouse_id_alias',
            'warehouse_reference_alias',
            'warehouse_name_alias',
            'location_id',
            'location_reference_alias',
            'location_code_alias',
            'counting_order_alias',
            'product_id',
            'product_reference_alias',
            'product_barcode_alias',
            'product_description_alias',
            'product_internal_code_alias',
            'job_id',
            'ecart_id_alias',
            'resolved_alias',
        ).annotate(
            total_quantity=Sum('quantity_inventoried'),
            # Prendre le final_result (sera le même pour tous les CountingDetail d'une même combinaison)
            final_result_agg=Max('final_result_alias'),
            # Prendre le resolved (sera le même pour tous les CountingDetail d'une même combinaison)
            # Cast en entier car PostgreSQL ne supporte pas MAX() sur les booléens
            resolved_agg=Max(Cast('resolved_alias', IntegerField()))
        ).order_by(
            'warehouse_id_alias',
            'job_id',
            'location_reference_alias',
            'product_reference_alias',
            'counting_order_alias',
        )

        result_list = list(aggregated_queryset)
        logger.debug(f"✅ Nombre de résultats agrégés retournés: {len(result_list)}")
        
        return result_list