"""
Exemples d'utilisation du système QueryModel pour DataTable.

Ce fichier montre comment utiliser facilement le support QueryModel dans les vues.
"""
from rest_framework.views import APIView
from apps.core.datatables.mixins import QueryModelMixin, QueryModelView
from apps.inventory.models import Inventory
from apps.inventory.serializers import InventoryDetailSerializer


# =============================================================================
# EXEMPLE 1 : Utilisation simple avec QueryModelView
# =============================================================================

class InventoryQueryModelView(QueryModelView):
    """
    Vue simple avec support QueryModel complet.
    
    Configuration minimale requise :
    - model : Modèle Django
    - serializer_class : Serializer DRF
    - column_field_mapping : Mapping colonnes QueryModel -> champs Django
    """
    
    model = Inventory
    serializer_class = InventoryDetailSerializer
    
    # Mapping des colonnes QueryModel vers les champs Django
    column_field_mapping = {
        'id': 'id',
        'reference': 'reference',
        'label': 'label',
        'date': 'date',
        'status': 'status',
        'inventory_type': 'inventory_type',
        'created_at': 'created_at',
        'account_name': 'awi_links__account__account_name',
        'warehouse_name': 'awi_links__warehouse__warehouse_name',
    }
    
    # Configuration optionnelle
    default_page_size = 100
    max_page_size = 1000
    
    def get_queryset(self):
        """Personnaliser le QuerySet si nécessaire"""
        queryset = super().get_queryset()
        # Ajouter des relations pour optimiser les requêtes
        return queryset.select_related(
            'awi_links__account',
            'awi_links__warehouse'
        )


# =============================================================================
# EXEMPLE 2 : Utilisation avec QueryModelMixin (plus de contrôle)
# =============================================================================

class InventoryQueryModelMixinView(QueryModelMixin, APIView):
    """
    Vue avec mixin QueryModel pour plus de contrôle.
    
    Permet de personnaliser complètement le comportement.
    """
    
    serializer_class = InventoryDetailSerializer
    column_field_mapping = {
        'id': 'id',
        'reference': 'reference',
        'label': 'label',
        'status': 'status',
    }
    
    def get_queryset(self):
        """QuerySet personnalisé"""
        return Inventory.objects.filter(status='active')
    
    def post(self, request, *args, **kwargs):
        """POST pour requêtes QueryModel"""
        return self.process_request(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """GET pour requêtes QueryModel"""
        return self.process_request(request, *args, **kwargs)


# =============================================================================
# EXEMPLE 3 : Avec liste de dictionnaires (depuis un service)
# =============================================================================

class InventoryResultQueryModelView(QueryModelMixin, APIView):
    """
    Vue QueryModel avec données depuis un service (liste de dicts).
    
    Utile quand les données ne viennent pas directement d'un QuerySet.
    """
    
    serializer_class = InventoryDetailSerializer
    column_field_mapping = {
        'location': 'location',
        'product': 'product',
        'final_result': 'final_result',
        'resolved': 'resolved',
    }
    
    def get_data_source(self):
        """Retourne une liste de dictionnaires depuis un service"""
        from apps.inventory.services.inventory_result_service import InventoryResultService
        
        service = InventoryResultService()
        inventory_id = self.kwargs.get('inventory_id')
        warehouse_id = self.kwargs.get('warehouse_id')
        
        # Récupérer les données depuis le service
        data_list = service.get_inventory_results_for_warehouse(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        )
        
        from apps.core.datatables.datasource import ListDataSource
        return ListDataSource(data_list)
    
    def post(self, request, *args, **kwargs):
        """POST pour requêtes QueryModel"""
        return self.process_request(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """GET pour requêtes QueryModel"""
        return self.process_request(request, *args, **kwargs)


# =============================================================================
# EXEMPLE 4 : Avec filtres personnalisés sur liste
# =============================================================================

class InventoryResultQueryModelWithFiltersView(QueryModelMixin, APIView):
    """
    Vue QueryModel avec filtres personnalisés sur liste de dictionnaires.
    
    Nécessite d'appliquer les filtres manuellement car on travaille
    avec une liste, pas un QuerySet.
    """
    
    serializer_class = InventoryDetailSerializer
    column_field_mapping = {
        'location': 'location',
        'product': 'product',
        'final_result': 'final_result',
    }
    
    def get_data_source(self):
        """Retourne une liste de dictionnaires"""
        from apps.inventory.services.inventory_result_service import InventoryResultService
        
        service = InventoryResultService()
        inventory_id = self.kwargs.get('inventory_id')
        warehouse_id = self.kwargs.get('warehouse_id')
        
        data_list = service.get_inventory_results_for_warehouse(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        )
        
        from apps.core.datatables.datasource import ListDataSource
        return ListDataSource(data_list)
    
    def process_request(self, request, *args, **kwargs):
        """
        Surcharge pour appliquer les filtres sur une liste.
        
        Pour les QuerySets, c'est automatique. Pour les listes,
        il faut appliquer les filtres manuellement.
        """
        from apps.core.datatables.models import QueryModel
        from apps.core.datatables.response import ResponseModel
        
        # Parser QueryModel
        query_model = QueryModel.from_request(request)
        
        # Récupérer les données
        data_source = self.get_data_source()
        data_list = data_source.get_data()
        
        # Appliquer les filtres manuellement (pour liste)
        filtered_data = self._apply_filters_on_list(data_list, query_model.filter_model)
        
        # Appliquer le tri manuellement (pour liste)
        sorted_data = self._apply_sort_on_list(filtered_data, query_model.sort_model)
        
        # Paginer
        start = query_model.start_row
        end = query_model.end_row or (start + self.default_page_size)
        total_count = len(sorted_data)
        paginated_data = sorted_data[start:end]
        
        # Sérialiser
        serialized_data = self.serialize_data(paginated_data)
        
        # Retourner réponse QueryModel
        response_model = ResponseModel.from_data(
            data=serialized_data,
            total_count=total_count
        )
        
        from rest_framework.response import Response
        from rest_framework import status
        return Response(response_model.to_dict(), status=status.HTTP_200_OK)
    
    def _apply_filters_on_list(self, data_list, filter_model):
        """Applique les filtres sur une liste de dictionnaires"""
        # Implémentation simplifiée - à adapter selon les besoins
        if not filter_model:
            return data_list
        
        filtered = []
        for item in data_list:
            match = True
            for col_id, filter_item in filter_model.items():
                field_name = self.column_field_mapping.get(col_id, col_id)
                value = item.get(field_name)
                
                # Logique de filtrage simplifiée
                if filter_item.filter is not None:
                    if filter_item.operator.value == "contains":
                        if filter_item.filter.lower() not in str(value).lower():
                            match = False
                            break
                    elif filter_item.operator.value == "equals":
                        if value != filter_item.filter:
                            match = False
                            break
                    # Ajouter d'autres opérateurs selon les besoins
            
            if match:
                filtered.append(item)
        
        return filtered
    
    def _apply_sort_on_list(self, data_list, sort_model):
        """Applique le tri sur une liste de dictionnaires"""
        if not sort_model:
            return data_list
        
        def sort_key(item):
            keys = []
            for sort_item in sort_model:
                field_name = self.column_field_mapping.get(
                    sort_item.col_id,
                    sort_item.col_id
                )
                value = item.get(field_name)
                if value is None:
                    value = ""
                keys.append((value, sort_item.sort.value == "desc"))
            return keys
        
        return sorted(data_list, key=sort_key)
    
    def post(self, request, *args, **kwargs):
        return self.process_request(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        return self.process_request(request, *args, **kwargs)

