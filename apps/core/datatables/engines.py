"""
Moteurs de traitement pour QueryModel : FilterEngine, SortEngine, PaginationEngine.
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
    Moteur de filtrage qui convertit QueryModel.filters en Q() Django.
    
    Supporte tous les types de filtres :
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
        data: Union[QuerySet, List[Dict[str, Any]]],
        filter_model: Dict[str, FilterModelItem]
    ) -> Union[QuerySet, List[Dict[str, Any]]]:
        """
        Applique les filtres (filters) au queryset ou à une liste.
        
        Args:
            data: QuerySet Django ou liste de dictionnaires
            filter_model: Dictionnaire de FilterModelItem (col_id -> FilterModelItem)
            
        Returns:
            QuerySet ou liste filtrée
        """
        if not filter_model:
            return data
        
        # Si c'est une liste, utiliser apply_filters_on_list
        if isinstance(data, list):
            return self.apply_filters_on_list(data, filter_model)
        
        # Sinon, traitement QuerySet classique
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
            data = data.filter(combined_q)
        
        return data
    
    def apply_filters_on_list(
        self,
        data_list: List[Dict[str, Any]],
        filter_model: Dict[str, FilterModelItem]
    ) -> List[Dict[str, Any]]:
        """
        Applique les filtres sur une liste de dictionnaires.
        
        Args:
            data_list: Liste de dictionnaires
            filter_model: Dictionnaire de FilterModelItem
            
        Returns:
            Liste filtrée
        """
        if not filter_model:
            return data_list
        
        filtered = data_list
        
        for col_id, filter_item in filter_model.items():
            try:
                # Obtenir le nom du champ réel depuis le mapping
                field_name = self.column_field_mapping.get(col_id, col_id)
                
                # Gérer les différents types de filtres
                if filter_item.filter_type == FilterType.SET and filter_item.values:
                    # Filtre SET (valeurs multiples)
                    values = [str(v).strip() for v in filter_item.values]
                    filtered = [item for item in filtered if str(item.get(field_name, '')).strip() in values]
                
                elif filter_item.filter_type == FilterType.TEXT:
                    # Filtres texte
                    filter_value = filter_item.filter
                    if filter_value is None:
                        continue
                    
                    filter_lower = str(filter_value).lower()
                    operator = filter_item.operator
                    
                    if operator == FilterOperator.EQUALS:
                        filtered = [item for item in filtered if str(item.get(field_name, '')).strip() == str(filter_value).strip()]
                    elif operator == FilterOperator.NOT_EQUAL:
                        filtered = [item for item in filtered if str(item.get(field_name, '')).strip() != str(filter_value).strip()]
                    elif operator == FilterOperator.CONTAINS:
                        filtered = [item for item in filtered if filter_lower in str(item.get(field_name, '')).lower()]
                    elif operator == FilterOperator.NOT_CONTAINS:
                        filtered = [item for item in filtered if filter_lower not in str(item.get(field_name, '')).lower()]
                    elif operator == FilterOperator.STARTS_WITH:
                        filtered = [item for item in filtered if str(item.get(field_name, '')).lower().startswith(filter_lower)]
                    elif operator == FilterOperator.ENDS_WITH:
                        filtered = [item for item in filtered if str(item.get(field_name, '')).lower().endswith(filter_lower)]
                
                elif filter_item.filter_type == FilterType.NUMBER:
                    # Filtres numériques
                    filter_value = filter_item.filter
                    if filter_value is None:
                        continue
                    
                    try:
                        filter_num = float(filter_value)
                    except (ValueError, TypeError):
                        continue
                    
                    operator = filter_item.operator
                    
                    if operator == FilterOperator.EQUALS:
                        filtered = [item for item in filtered if self._compare_numeric(item.get(field_name), filter_num, '==')]
                    elif operator == FilterOperator.NOT_EQUAL:
                        filtered = [item for item in filtered if not self._compare_numeric(item.get(field_name), filter_num, '==')]
                    elif operator == FilterOperator.GREATER_THAN:
                        filtered = [item for item in filtered if self._compare_numeric(item.get(field_name), filter_num, '>')]
                    elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
                        filtered = [item for item in filtered if self._compare_numeric(item.get(field_name), filter_num, '>=')]
                    elif operator == FilterOperator.LESS_THAN:
                        filtered = [item for item in filtered if self._compare_numeric(item.get(field_name), filter_num, '<')]
                    elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
                        filtered = [item for item in filtered if self._compare_numeric(item.get(field_name), filter_num, '<=')]
                    elif operator == FilterOperator.IN_RANGE:
                        filter_to = filter_item.filter_to
                        if filter_to is not None:
                            try:
                                filter_to_num = float(filter_to)
                                filtered = [item for item in filtered if self._compare_numeric_range(item.get(field_name), filter_num, filter_to_num)]
                            except (ValueError, TypeError):
                                pass
                
            except Exception as e:
                logger.warning(f"Erreur lors de l'application du filtre {col_id} sur liste: {str(e)}")
                continue
        
        return filtered
    
    def _compare_numeric(self, value: Any, target: float, operator: str) -> bool:
        """Compare une valeur numérique avec un opérateur."""
        if value is None:
            return False
        try:
            num_value = float(value)
            if operator == '==':
                return num_value == target
            elif operator == '>':
                return num_value > target
            elif operator == '>=':
                return num_value >= target
            elif operator == '<':
                return num_value < target
            elif operator == '<=':
                return num_value <= target
        except (ValueError, TypeError):
            return False
        return False
    
    def _compare_numeric_range(self, value: Any, min_val: float, max_val: float) -> bool:
        """Vérifie si une valeur est dans une plage numérique."""
        if value is None:
            return False
        try:
            num_value = float(value)
            return min_val <= num_value <= max_val
        except (ValueError, TypeError):
            return False


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
        data: Union[QuerySet, List[Dict[str, Any]]],
        sort_model: List[SortModelItem]
    ) -> Union[QuerySet, List[Dict[str, Any]]]:
        """
        Applique le tri multi-colonnes au queryset ou à une liste.
        
        Args:
            data: QuerySet Django ou liste de dictionnaires
            sort_model: Liste de SortModelItem (ordre de tri)
            
        Returns:
            QuerySet ou liste triée
        """
        if not sort_model:
            return data
        
        # Si c'est une liste, utiliser apply_sorting_on_list
        if isinstance(data, list):
            return self.apply_sorting_on_list(data, sort_model)
        
        # Sinon, traitement QuerySet classique
        order_by = []
        
        for sort_item in sort_model:
            # Obtenir le nom du champ Django depuis le mapping
            col_id = sort_item.col_id
            field_name = self.column_field_mapping.get(col_id, col_id)
            
            # Log pour déboguer
            if col_id != field_name:
                logger.debug(f"Tri: {col_id} -> {field_name} (via column_field_mapping)")
            else:
                logger.debug(f"Tri: {col_id} (pas de mapping, utilisation directe)")
            
            # Ajouter le préfixe "-" pour DESC
            if sort_item.sort.value == "desc":
                field_name = f"-{field_name}"
            
            order_by.append(field_name)
        
        if order_by:
            data = data.order_by(*order_by)
        
        return data
    
    def apply_sorting_on_list(
        self,
        data_list: List[Dict[str, Any]],
        sort_model: List[SortModelItem]
    ) -> List[Dict[str, Any]]:
        """
        Applique le tri multi-colonnes sur une liste de dictionnaires.
        
        Args:
            data_list: Liste de dictionnaires
            sort_model: Liste de SortModelItem
            
        Returns:
            Liste triée
        """
        if not sort_model:
            return data_list
        
        # Construire la clé de tri multi-colonnes
        def sort_key(item):
            key_parts = []
            for sort_item in sort_model:
                col_id = sort_item.col_id
                sort_dir = sort_item.sort.value
                field_name = self.column_field_mapping.get(col_id, col_id)
                value = item.get(field_name)
                
                # Gérer les valeurs None et les types numériques
                if value is None:
                    key_parts.append((float('-inf') if sort_dir == 'asc' else float('inf'),))
                elif isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit()):
                    try:
                        num_value = float(value)
                        key_parts.append((num_value,))
                    except (ValueError, TypeError):
                        key_parts.append((str(value).lower(),))
                else:
                    key_parts.append((str(value).lower(),))
            
            return tuple(key_parts)
        
        # Trier selon toutes les colonnes
        reverse = False
        if sort_model and sort_model[0].sort.value == 'desc':
            reverse = True
        
        return sorted(data_list, key=sort_key, reverse=reverse)


class PaginationEngine:
    """
    Moteur de pagination pour pagination classique (page/pageSize).
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
        data: Union[QuerySet, List[Dict[str, Any]]],
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Pagine le queryset ou la liste avec pagination classique (page/pageSize).
        
        Args:
            data: QuerySet Django ou liste de dictionnaires
            page: Numéro de page (1-indexed)
            page_size: Taille de page
            
        Returns:
            Dict avec 'queryset' (paginated), 'total_count', 'page', 'page_size'
        """
        # Si c'est une liste, utiliser paginate_list
        if isinstance(data, list):
            return self.paginate_list(data, page, page_size)
        
        # Sinon, traitement QuerySet classique
        total_count = data.count()
        
        # Valider et limiter page_size
        if page_size > self.max_page_size:
            page_size = self.max_page_size
        
        # Calculer les indices pour le slicing (0-indexed)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # Paginer le queryset
        paginated_data = data[start_index:end_index]
        
        return {
            'queryset': paginated_data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size
        }
    
    def paginate_list(
        self,
        data_list: List[Dict[str, Any]],
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Pagine une liste de dictionnaires avec pagination classique (page/pageSize).
        
        Args:
            data_list: Liste de dictionnaires
            page: Numéro de page (1-indexed)
            page_size: Taille de page
            
        Returns:
            Dict avec 'queryset' (liste paginée), 'total_count', 'page', 'page_size'
        """
        total_count = len(data_list)
        
        # Valider et limiter page_size
        if page_size > self.max_page_size:
            page_size = self.max_page_size
        
        # Calculer les indices pour le slicing (0-indexed)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # Paginer la liste
        paginated_data = data_list[start_index:end_index]
        
        return {
            'queryset': paginated_data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size
        }

