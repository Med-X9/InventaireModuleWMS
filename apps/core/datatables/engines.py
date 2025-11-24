"""
Moteurs de traitement pour AG-Grid : FilterEngine, SortEngine, PaginationEngine.
"""
from typing import List, Dict, Any, Optional, Union
from django.db.models import QuerySet, Q
from django.core.paginator import Paginator
from .models import QueryModel, SortModelItem, FilterModelItem, FilterType, FilterOperator
from .operators import OperatorRegistry
import logging

logger = logging.getLogger(__name__)


class FilterEngine:
    """
    Moteur de filtrage qui convertit QueryModel.filterModel en Q() Django.
    
    Supporte tous les types de filtres AG-Grid :
    - Text filters (contains, startsWith, etc.)
    - Number filters (equals, greaterThan, etc.)
    - Date filters (equals, inRange, etc.)
    - Set filters (unique values)
    """
    
    def __init__(self, column_field_mapping: Optional[Dict[str, str]] = None):
        """
        Initialise le moteur de filtrage.
        
        Args:
            column_field_mapping: Mapping col_id -> field_name Django
                                 Si None, utilise col_id directement comme field_name
        """
        self.column_field_mapping = column_field_mapping or {}
    
    def apply_filters(
        self,
        queryset: QuerySet,
        filter_model: Dict[str, FilterModelItem]
    ) -> QuerySet:
        """
        Applique les filtres du filterModel au queryset.
        
        Args:
            queryset: QuerySet Django
            filter_model: Dictionnaire de FilterModelItem (col_id -> FilterModelItem)
            
        Returns:
            QuerySet: QuerySet filtré
        """
        if not filter_model:
            return queryset
        
        q_objects = []
        
        for col_id, filter_item in filter_model.items():
            try:
                # Obtenir le nom du champ Django
                field_name = self.column_field_mapping.get(col_id, col_id)
                
                # Construire l'expression Q()
                if filter_item.filter_type == FilterType.SET and filter_item.values:
                    # Filtre SET (valeurs uniques)
                    q_expr = OperatorRegistry.build_set_filter_q(
                        field_name,
                        filter_item.values
                    )
                elif filter_item.operator == FilterOperator.IN_RANGE and filter_item.filter_to is not None:
                    # Filtre range
                    q_expr = OperatorRegistry.build_q_expression(
                        field_name,
                        filter_item.operator,
                        filter_item.filter,
                        filter_item.filter_to
                    )
                else:
                    # Filtre standard
                    q_expr = OperatorRegistry.build_q_expression(
                        field_name,
                        filter_item.operator,
                        filter_item.filter
                    )
                
                if q_expr:
                    q_objects.append(q_expr)
                    
            except Exception as e:
                logger.warning(
                    f"Erreur lors de l'application du filtre {col_id}: {str(e)}"
                )
                continue
        
        # Combiner tous les filtres avec AND
        if q_objects:
            combined_q = q_objects[0]
            for q_obj in q_objects[1:]:
                combined_q &= q_obj
            queryset = queryset.filter(combined_q)
        
        return queryset


class SortEngine:
    """
    Moteur de tri multi-colonnes compatible AG-Grid.
    
    Supporte le tri sur plusieurs colonnes simultanément.
    """
    
    def __init__(self, column_field_mapping: Optional[Dict[str, str]] = None):
        """
        Initialise le moteur de tri.
        
        Args:
            column_field_mapping: Mapping col_id -> field_name Django
        """
        self.column_field_mapping = column_field_mapping or {}
    
    def apply_sorting(
        self,
        queryset: QuerySet,
        sort_model: List[SortModelItem]
    ) -> QuerySet:
        """
        Applique le tri multi-colonnes au queryset.
        
        Args:
            queryset: QuerySet Django
            sort_model: Liste de SortModelItem (ordre de tri)
            
        Returns:
            QuerySet: QuerySet trié
        """
        if not sort_model:
            return queryset
        
        order_by = []
        
        for sort_item in sort_model:
            # Obtenir le nom du champ Django
            field_name = self.column_field_mapping.get(
                sort_item.col_id,
                sort_item.col_id
            )
            
            # Ajouter le préfixe "-" pour DESC
            if sort_item.sort.value == "desc":
                field_name = f"-{field_name}"
            
            order_by.append(field_name)
        
        if order_by:
            queryset = queryset.order_by(*order_by)
        
        return queryset


class PaginationEngine:
    """
    Moteur de pagination pour infinite scroll (compatible AG-Grid).
    
    Supporte startRow/endRow pour le scroll infini.
    """
    
    def __init__(
        self,
        default_page_size: int = 100,
        max_page_size: int = 1000
    ):
        """
        Initialise le moteur de pagination.
        
        Args:
            default_page_size: Taille de page par défaut
            max_page_size: Taille maximale autorisée
        """
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
    
    def paginate(
        self,
        queryset: QuerySet,
        start_row: int = 0,
        end_row: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Pagine le queryset pour infinite scroll.
        
        Args:
            queryset: QuerySet Django
            start_row: Index de début (inclusif)
            end_row: Index de fin (exclusif, optionnel)
            
        Returns:
            Dict avec 'queryset' (paginated), 'total_count', 'start_row', 'end_row'
        """
        total_count = queryset.count()
        
        # Calculer end_row si non fourni
        if end_row is None:
            end_row = start_row + self.default_page_size
        
        # Limiter la taille de page
        page_size = end_row - start_row
        if page_size > self.max_page_size:
            page_size = self.max_page_size
            end_row = start_row + page_size
        
        # Paginer le queryset
        paginated_queryset = queryset[start_row:end_row]
        
        return {
            'queryset': paginated_queryset,
            'total_count': total_count,
            'start_row': start_row,
            'end_row': end_row,
            'page_size': page_size
        }

