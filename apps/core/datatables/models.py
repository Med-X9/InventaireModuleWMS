"""
Modèles de données pour QueryModel.

Ce module fournit les modèles de données nécessaires pour supporter
les fonctionnalités QueryModel : page, pageSize, search, sort, filters.
"""
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SortDirection(str, Enum):
    """Direction de tri"""
    ASC = "asc"
    DESC = "desc"


class FilterType(str, Enum):
    """Types de filtres"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SET = "set"  # Pour les filtres avec valeurs uniques
    CUSTOM = "custom"


class FilterOperator(str, Enum):
    """Opérateurs de filtres"""
    EQUALS = "equals"
    NOT_EQUAL = "notEqual"
    LESS_THAN = "lessThan"
    LESS_THAN_OR_EQUAL = "lessThanOrEqual"
    GREATER_THAN = "greaterThan"
    GREATER_THAN_OR_EQUAL = "greaterThanOrEqual"
    IN_RANGE = "inRange"
    CONTAINS = "contains"
    NOT_CONTAINS = "notContains"
    STARTS_WITH = "startsWith"
    ENDS_WITH = "endsWith"
    BLANK = "blank"
    NOT_BLANK = "notBlank"


@dataclass
class SortModelItem:
    """
    Modèle de tri (sort)
    
    Exemple:
    {
        "colId": "age",
        "sort": "asc"
    }
    """
    col_id: str  # Identifiant de la colonne
    sort: SortDirection  # Direction : "asc" ou "desc"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "colId": self.col_id,
            "sort": self.sort.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SortModelItem':
        """Crée depuis un dictionnaire"""
        if not isinstance(data, dict):
            # Si data n'est pas un dict, utiliser des valeurs par défaut
            return cls(
                col_id="",
                sort=SortDirection("asc")
            )

        return cls(
            col_id=data.get("colId", data.get("col_id", "")),
            sort=SortDirection(data.get("sort", "asc"))
        )


@dataclass
class FilterModelItem:
    """
    Modèle de filtre (filters)
    
    Exemple:
    {
        "colId": "age",
        "filterType": "number",
        "type": "greaterThan",
        "filter": 30
    }
    """
    col_id: str  # Identifiant de la colonne
    filter_type: FilterType = FilterType.TEXT
    operator: FilterOperator = FilterOperator.EQUALS
    filter: Optional[Union[str, int, float, List[Any]]] = None
    filter_to: Optional[Union[str, int, float]] = None  # Pour inRange
    values: Optional[List[Any]] = None  # Pour SET filter
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        result = {
            "colId": self.col_id,
            "filterType": self.filter_type.value,
            "type": self.operator.value,
        }
        
        if self.filter is not None:
            result["filter"] = self.filter
        
        if self.filter_to is not None:
            result["filterTo"] = self.filter_to
        
        if self.values is not None:
            result["values"] = self.values
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterModelItem':
        """Crée depuis un dictionnaire"""
        return cls(
            col_id=data.get("colId", data.get("col_id", "")),
            filter_type=FilterType(data.get("filterType", data.get("filter_type", "text"))),
            operator=FilterOperator(data.get("type", data.get("operator", "equals"))),
            filter=data.get("filter"),
            filter_to=data.get("filterTo", data.get("filter_to")),
            values=data.get("values")
        )


@dataclass
class QueryModel:
    """
    Modèle de requête QueryModel (format standard).
    
    Format de requête standard :
    {
        "page": 1,
        "pageSize": 10,
        "search": "ink",
        "sort": [
            {"colId": "category", "sort": "asc"},
            {"colId": "created_at", "sort": "desc"}
        ],
        "filters": {
            "status": ["active", "pending"],  // Format simple (array)
            "category": {"type": "text", "operator": "contains", "value": "ink"},
            "price": {"type": "number", "operator": "gte", "value": 10}
        }
    }
    
    Note: Le format sortBy/sortDir est déprécié. Utilisez "sort" (array) à la place.
    """
    page: int = 1
    page_size: int = 10
    search: Optional[str] = None
    sort: List[SortModelItem] = field(default_factory=list)  # Tri multiple
    filters: Dict[str, FilterModelItem] = field(default_factory=dict)  # Filtres
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour le nouveau format"""
        result = {
            "page": self.page,
            "pageSize": self.page_size,
        }
        
        if self.search:
            result["search"] = self.search
        
        if self.sort:
            result["sort"] = [item.to_dict() for item in self.sort]
        
        if self.filters:
            result["filters"] = {
                col_id: item.to_dict() 
                for col_id, item in self.filters.items()
            }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryModel':
        """
        Crée depuis un dictionnaire (format standard uniquement).

        Format attendu :
        - page, pageSize, search, sort (array), filters
        
        Note: Le format sortBy/sortDir est déprécié mais toujours supporté pour compatibilité.
        """
        # Vérifier que data est bien un dictionnaire
        if not isinstance(data, dict):
            # Si data n'est pas un dict, retourner un QueryModel par défaut
            return cls()

        # Format standard : sort (array)
        sort_list = data.get("sort", [])
        
        # Compatibilité ascendante : support sortBy/sortDir (déprécié)
        if not sort_list and data.get("sortBy"):
            logger.warning(
                "Le format sortBy/sortDir est déprécié. "
                "Utilisez 'sort': [{'colId': '...', 'sort': '...'}] à la place."
            )
            # Convertir format déprécié en format standard
            sort_list = [{
                "colId": data.get("sortBy"),
                "sort": data.get("sortDir", "asc")
            }]
        
        # Créer le modèle de tri en filtrant les éléments mal formés
        sort_model = []
        for item in sort_list:
            if isinstance(item, dict):
                sort_model.append(SortModelItem.from_dict(item))
            else:
                logger.warning(f"Élément de tri ignoré (type invalide): {type(item)}")
        
        # Convertir nouveau format de filtres vers FilterModelItem
        filters_dict = data.get("filters", {})
        filter_model = {}

        # Validation : s'assurer que filters_dict est un dictionnaire
        if not isinstance(filters_dict, dict):
            # Si c'est une string, essayer de la parser en JSON
            if isinstance(filters_dict, str):
                try:
                    import json
                    filters_dict = json.loads(filters_dict)
                except (json.JSONDecodeError, TypeError, ValueError):
                    logger.warning(f"Filtres malformés reçus (string non JSON) : {filters_dict}. Ignoré.")
                    filters_dict = {}
            else:
                logger.warning(f"Filtres malformés reçus (type {type(filters_dict)}) : {filters_dict}. Ignoré.")
                filters_dict = {}

        # Maintenant filters_dict est garanti d'être un dictionnaire
        for col_id, filter_data in filters_dict.items():
            try:
                filter_model[col_id] = cls._convert_new_filter_format(col_id, filter_data)
            except Exception as e:
                logger.warning(f"Erreur lors du traitement du filtre '{col_id}': {e}. Filtre ignoré.")
                continue
        
        return cls(
            page=data.get("page", 1),
            page_size=data.get("pageSize", data.get("page_size", 10)),
            search=data.get("search"),
            sort=sort_model,
            filters=filter_model
        )
    
    @staticmethod
    def _convert_new_filter_format(col_id: str, filter_data: Union[Dict[str, Any], List[Any]]) -> FilterModelItem:
        """
        Convertit le nouveau format de filtre vers FilterModelItem.
        
        Supporte plusieurs formats :
        - Format simple (array) : ["active", "pending"] -> filtre multi
        - Format complet (object) :
          - {"type": "multi", "values": ["active", "pending"]}
          - {"type": "text", "operator": "contains", "value": "ink"}
          - {"type": "number", "operator": "gte", "value": 10}
          - {"type": "boolean", "value": true}
          - {"type": "date", "operator": "range", "from": "2025-01-01", "to": "2025-11-30"}
        """
        # Si c'est une liste, convertir en format multi
        if isinstance(filter_data, list):
            return FilterModelItem(
                col_id=col_id,
                filter_type=FilterType.SET,
                operator=FilterOperator.EQUALS,
                values=filter_data
            )
        
        # Sinon, c'est un dictionnaire
        filter_type_str = filter_data.get("type", "text")
        
        # Mapper les types
        type_mapping = {
            "multi": FilterType.SET,
            "text": FilterType.TEXT,
            "number": FilterType.NUMBER,
            "date": FilterType.DATE,
            "boolean": FilterType.TEXT  # Traiter comme texte pour l'instant
        }
        filter_type = type_mapping.get(filter_type_str, FilterType.TEXT)
        
        # Mapper les opérateurs
        operator_mapping = {
            "contains": FilterOperator.CONTAINS,
            "gte": FilterOperator.GREATER_THAN_OR_EQUAL,
            "lte": FilterOperator.LESS_THAN_OR_EQUAL,
            "gt": FilterOperator.GREATER_THAN,
            "lt": FilterOperator.LESS_THAN,
            "eq": FilterOperator.EQUALS,
            "neq": FilterOperator.NOT_EQUAL,
            "range": FilterOperator.IN_RANGE,
            "startsWith": FilterOperator.STARTS_WITH,
            "endsWith": FilterOperator.ENDS_WITH
        }
        operator_str = filter_data.get("operator", "equals")
        operator = operator_mapping.get(operator_str, FilterOperator.EQUALS)
        
        # Extraire les valeurs
        if filter_type == FilterType.SET:
            # Filtre multi : {"type": "multi", "values": [...]}
            values = filter_data.get("values", [])
            return FilterModelItem(
                col_id=col_id,
                filter_type=filter_type,
                operator=FilterOperator.EQUALS,
                values=values
            )
        elif operator == FilterOperator.IN_RANGE:
            # Filtre range : {"type": "date", "operator": "range", "from": "...", "to": "..."}
            filter_value = filter_data.get("from") or filter_data.get("value")
            filter_to = filter_data.get("to")
            return FilterModelItem(
                col_id=col_id,
                filter_type=filter_type,
                operator=operator,
                filter=filter_value,
                filter_to=filter_to
            )
        else:
            # Filtre standard : {"type": "text", "operator": "contains", "value": "ink"}
            filter_value = filter_data.get("value")
            return FilterModelItem(
                col_id=col_id,
                filter_type=filter_type,
                operator=operator,
                filter=filter_value
            )
    
    @classmethod
    def from_request(cls, request) -> 'QueryModel':
        """
        Crée depuis une requête HTTP (format standard).
        
        Supporte :
        - POST avec JSON body : page, pageSize, search, sort (array), filters
        - GET avec query params : page, pageSize, search, sort (JSON string), filters (JSON string)
        
        Note: Le format sortBy/sortDir est déprécié mais toujours supporté pour compatibilité.
        """
        import json

        # PRIORITÉ 1 : POST avec JSON body (format recommandé)
        if hasattr(request, 'data') and request.data:
            if isinstance(request.data, dict):
                # Vérifier si request.data contient des données QueryModel pertinentes
                if any(key in request.data for key in ['page', 'pageSize', 'search', 'sort', 'filters']):
                    return cls.from_dict(request.data)

        # PRIORITÉ 2 : Essayer request.body pour les requêtes avec body JSON
        # ⚠️ ATTENTION: Ne pas accéder à request.body si les données ont déjà été lues par DRF
        if hasattr(request, '_load_data_called') and not request._load_data_called:
            try:
                if hasattr(request, 'body') and request.body:
                    body_data = json.loads(request.body)
                    if isinstance(body_data, dict) and any(key in body_data for key in ['page', 'pageSize', 'search', 'sort', 'filters']):
                        return cls.from_dict(body_data)
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                # Body n'est pas du JSON valide ou erreur d'attribut, ignorer
                pass
        
        # PRIORITÉ 3 : GET params (format JSON string pour sort et filters)
        data = {
            "page": int(request.GET.get('page', 1)),
            "pageSize": int(request.GET.get('pageSize', request.GET.get('page_size', 10))),
        }
        
        if request.GET.get('search'):
            data['search'] = request.GET.get('search')
        
        # Format standard : sort comme JSON string
        if request.GET.get('sort'):
            try:
                sort_value = request.GET.get('sort')
                # Si c'est déjà une liste (depuis POST body), utiliser directement
                if isinstance(sort_value, list):
                    data['sort'] = sort_value
                else:
                    # Sinon, parser comme JSON string
                    data['sort'] = json.loads(sort_value)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Format de tri invalide dans GET params: {e}. Tri ignoré.")
                data['sort'] = []
        
        # Compatibilité ascendante : support sortBy/sortDir (déprécié)
        elif request.GET.get('sortBy'):
            logger.warning(
                "Le format sortBy/sortDir dans GET params est déprécié. "
                "Utilisez 'sort' (JSON string) à la place."
            )
            data['sortBy'] = request.GET.get('sortBy')
            data['sortDir'] = request.GET.get('sortDir', 'asc')
        
        # Format standard : filters comme JSON string
        if request.GET.get('filters'):
            try:
                filter_value = request.GET.get('filters')
                if isinstance(filter_value, dict):
                    data['filters'] = filter_value
                else:
                    data['filters'] = json.loads(filter_value)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Format de filtres invalide dans GET params: {e}. Filtres ignorés.")
                data['filters'] = {}
        
        return cls.from_dict(data)

