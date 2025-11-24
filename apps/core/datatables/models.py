"""
Modèles de données compatibles AG-Grid pour DataTable.

Ce module fournit les modèles de données nécessaires pour supporter
les fonctionnalités AG-Grid : sortModel, filterModel, etc.
"""
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class SortDirection(str, Enum):
    """Direction de tri compatible AG-Grid"""
    ASC = "asc"
    DESC = "desc"


class FilterType(str, Enum):
    """Types de filtres compatibles AG-Grid"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SET = "set"  # Pour les filtres avec valeurs uniques
    CUSTOM = "custom"


class FilterOperator(str, Enum):
    """Opérateurs de filtres compatibles AG-Grid"""
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
    Modèle de tri compatible AG-Grid (sortModel)
    
    Exemple AG-Grid:
    {
        "colId": "age",
        "sort": "asc"
    }
    """
    col_id: str  # Identifiant de la colonne
    sort: SortDirection  # Direction : "asc" ou "desc"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire compatible AG-Grid"""
        return {
            "colId": self.col_id,
            "sort": self.sort.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SortModelItem':
        """Crée depuis un dictionnaire AG-Grid"""
        return cls(
            col_id=data.get("colId", data.get("col_id", "")),
            sort=SortDirection(data.get("sort", "asc"))
        )


@dataclass
class FilterModelItem:
    """
    Modèle de filtre compatible AG-Grid (filterModel)
    
    Exemple AG-Grid:
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
        """Convertit en dictionnaire compatible AG-Grid"""
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
        """Crée depuis un dictionnaire AG-Grid"""
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
    Modèle de requête complet compatible AG-Grid.
    
    Contient sortModel et filterModel comme dans AG-Grid.
    
    Exemple:
    {
        "sortModel": [
            {"colId": "age", "sort": "asc"},
            {"colId": "name", "sort": "desc"}
        ],
        "filterModel": {
            "age": {"filterType": "number", "type": "greaterThan", "filter": 30},
            "name": {"filterType": "text", "type": "contains", "filter": "John"}
        }
    }
    """
    sort_model: List[SortModelItem] = field(default_factory=list)
    filter_model: Dict[str, FilterModelItem] = field(default_factory=dict)
    start_row: int = 0  # Pour infinite scroll
    end_row: Optional[int] = None  # Pour infinite scroll
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire compatible AG-Grid"""
        result = {
            "sortModel": [item.to_dict() for item in self.sort_model],
            "filterModel": {
                col_id: item.to_dict() 
                for col_id, item in self.filter_model.items()
            },
            "startRow": self.start_row,
        }
        
        if self.end_row is not None:
            result["endRow"] = self.end_row
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryModel':
        """Crée depuis un dictionnaire AG-Grid"""
        sort_model = [
            SortModelItem.from_dict(item) 
            for item in data.get("sortModel", [])
        ]
        
        filter_model = {
            col_id: FilterModelItem.from_dict(item)
            for col_id, item in data.get("filterModel", {}).items()
        }
        
        return cls(
            sort_model=sort_model,
            filter_model=filter_model,
            start_row=data.get("startRow", data.get("start_row", 0)),
            end_row=data.get("endRow", data.get("end_row"))
        )
    
    @classmethod
    def from_request(cls, request) -> 'QueryModel':
        """
        Crée depuis une requête HTTP (format AG-Grid ou DataTable standard)
        
        Supporte deux formats :
        1. Format AG-Grid JSON (POST body ou GET params)
        2. Format DataTable standard (GET params)
        """
        # Essayer format AG-Grid (JSON dans body ou GET)
        if hasattr(request, 'data') and request.data:
            # POST avec JSON
            if isinstance(request.data, dict):
                return cls.from_dict(request.data)
        
        # Essayer GET params au format AG-Grid
        if request.GET.get('sortModel') or request.GET.get('filterModel'):
            # Parser depuis query params (JSON string)
            import json
            data = {}
            if request.GET.get('sortModel'):
                data['sortModel'] = json.loads(request.GET.get('sortModel'))
            if request.GET.get('filterModel'):
                data['filterModel'] = json.loads(request.GET.get('filterModel'))
            if request.GET.get('startRow'):
                data['startRow'] = int(request.GET.get('startRow'))
            if request.GET.get('endRow'):
                data['endRow'] = int(request.GET.get('endRow'))
            return cls.from_dict(data)
        
        # Fallback : format DataTable standard
        sort_model = []
        order_index = 0
        while f'order[{order_index}][column]' in request.GET:
            column_index = int(request.GET.get(f'order[{order_index}][column]', 0))
            direction = request.GET.get(f'order[{order_index}][dir]', 'asc')
            # Nécessite mapping column_index -> col_id (à faire dans la vue)
            order_index += 1
        
        return cls(
            sort_model=sort_model,
            filter_model={},
            start_row=int(request.GET.get('start', 0)),
            end_row=None
        )

