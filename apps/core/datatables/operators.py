"""
Registry d'opérateurs pour les filtres AG-Grid.

Convertit les opérateurs AG-Grid en lookups Django ORM.
"""
from typing import Any, Optional, List
from django.db.models import Q
from .models import FilterOperator, FilterType
import logging

logger = logging.getLogger(__name__)


class OperatorRegistry:
    """
    Registry centralisé pour les opérateurs de filtres.
    
    Convertit les opérateurs AG-Grid en lookups Django ORM.
    """
    
    # Mapping opérateurs AG-Grid -> lookups Django
    OPERATOR_MAPPING = {
        FilterOperator.EQUALS: "exact",
        FilterOperator.NOT_EQUAL: "exact",  # Utilisé avec ~Q()
        FilterOperator.LESS_THAN: "lt",
        FilterOperator.LESS_THAN_OR_EQUAL: "lte",
        FilterOperator.GREATER_THAN: "gt",
        FilterOperator.GREATER_THAN_OR_EQUAL: "gte",
        FilterOperator.CONTAINS: "icontains",
        FilterOperator.NOT_CONTAINS: "icontains",  # Utilisé avec ~Q()
        FilterOperator.STARTS_WITH: "istartswith",
        FilterOperator.ENDS_WITH: "iendswith",
        FilterOperator.BLANK: "isnull",
        FilterOperator.NOT_BLANK: "isnull",  # Utilisé avec ~Q()
    }
    
    @classmethod
    def get_lookup(cls, operator: FilterOperator) -> str:
        """
        Retourne le lookup Django correspondant à l'opérateur AG-Grid.
        
        Args:
            operator: Opérateur AG-Grid
            
        Returns:
            str: Lookup Django (ex: "exact", "icontains", "lt")
        """
        return cls.OPERATOR_MAPPING.get(operator, "exact")
    
    @classmethod
    def is_negated(cls, operator: FilterOperator) -> bool:
        """
        Indique si l'opérateur doit être négé (avec ~Q()).
        
        Args:
            operator: Opérateur AG-Grid
            
        Returns:
            bool: True si l'opérateur doit être négé
        """
        negated_operators = {
            FilterOperator.NOT_EQUAL,
            FilterOperator.NOT_CONTAINS,
            FilterOperator.NOT_BLANK
        }
        return operator in negated_operators
    
    @classmethod
    def is_range_operator(cls, operator: FilterOperator) -> bool:
        """
        Indique si l'opérateur nécessite deux valeurs (range).
        
        Args:
            operator: Opérateur AG-Grid
            
        Returns:
            bool: True si c'est un opérateur de range
        """
        return operator == FilterOperator.IN_RANGE
    
    @classmethod
    def build_q_expression(
        cls,
        field_name: str,
        operator: FilterOperator,
        filter_value: Any,
        filter_to: Optional[Any] = None
    ) -> Q:
        """
        Construit une expression Q() Django depuis un opérateur AG-Grid.
        
        Args:
            field_name: Nom du champ Django
            operator: Opérateur AG-Grid
            filter_value: Valeur de filtre
            filter_to: Valeur "to" pour les ranges (optionnel)
            
        Returns:
            Q: Expression Q() Django
        """
        # Opérateur BLANK / NOT_BLANK
        if operator == FilterOperator.BLANK:
            return Q(**{f"{field_name}__isnull": True}) | Q(**{f"{field_name}": ""})
        
        if operator == FilterOperator.NOT_BLANK:
            return ~Q(**{f"{field_name}__isnull": True}) & ~Q(**{f"{field_name}": ""})
        
        # Opérateur IN_RANGE
        if operator == FilterOperator.IN_RANGE and filter_to is not None:
            lookup = cls.get_lookup(FilterOperator.GREATER_THAN_OR_EQUAL)
            q1 = Q(**{f"{field_name}__{lookup}": filter_value})
            lookup = cls.get_lookup(FilterOperator.LESS_THAN_OR_EQUAL)
            q2 = Q(**{f"{field_name}__{lookup}": filter_to})
            return q1 & q2
        
        # Opérateurs standards
        lookup = cls.get_lookup(operator)
        q_expression = Q(**{f"{field_name}__{lookup}": filter_value})
        
        # Négation si nécessaire
        if cls.is_negated(operator):
            return ~q_expression
        
        return q_expression
    
    @classmethod
    def build_set_filter_q(
        cls,
        field_name: str,
        values: List[Any]
    ) -> Q:
        """
        Construit une expression Q() pour un filtre SET (valeurs uniques).
        
        Args:
            field_name: Nom du champ Django
            values: Liste de valeurs à inclure
            
        Returns:
            Q: Expression Q() Django avec __in
        """
        if not values:
            return Q()
        
        return Q(**{f"{field_name}__in": values})

