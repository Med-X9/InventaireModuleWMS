"""
DataSource pour différents types de sources de données.
"""
from typing import List, Dict, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
from django.db.models import QuerySet
import logging

logger = logging.getLogger(__name__)


class IDataSource(ABC):
    """Interface pour les sources de données"""
    
    @abstractmethod
    def get_data(self, **kwargs) -> Union[QuerySet, List[Dict[str, Any]]]:
        """Récupère les données"""
        pass
    
    @abstractmethod
    def get_count(self) -> int:
        """Retourne le nombre total d'éléments"""
        pass


class QuerySetDataSource(IDataSource):
    """DataSource pour QuerySet Django"""
    
    def __init__(self, queryset: QuerySet):
        self.queryset = queryset
    
    def get_data(self, **kwargs) -> QuerySet:
        """Retourne le QuerySet"""
        return self.queryset
    
    def get_count(self) -> int:
        """Compte les éléments du QuerySet"""
        return self.queryset.count()


class ListDataSource(IDataSource):
    """DataSource pour liste de dictionnaires"""
    
    def __init__(self, data_list: List[Dict[str, Any]]):
        self.data_list = data_list
    
    def get_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Retourne la liste"""
        return self.data_list
    
    def get_count(self) -> int:
        """Compte les éléments de la liste"""
        return len(self.data_list)


class CallableDataSource(IDataSource):
    """DataSource pour fonction callable"""
    
    def __init__(self, callable_func: Callable, *args, **kwargs):
        self.callable_func = callable_func
        self.args = args
        self.kwargs = kwargs
        self._cached_data: Optional[List[Dict[str, Any]]] = None
    
    def get_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Appelle la fonction et retourne les données"""
        if self._cached_data is None:
            merged_kwargs = {**self.kwargs, **kwargs}
            self._cached_data = self.callable_func(*self.args, **merged_kwargs)
        return self._cached_data
    
    def get_count(self) -> int:
        """Compte les éléments"""
        return len(self.get_data())


class DataSourceFactory:
    """Factory pour créer des DataSource"""
    
    @staticmethod
    def create(data: Union[QuerySet, List[Dict[str, Any]], Callable]) -> IDataSource:
        """
        Crée une DataSource appropriée selon le type de données.
        
        Args:
            data: QuerySet, liste de dicts, ou fonction callable
            
        Returns:
            IDataSource: DataSource appropriée
        """
        if isinstance(data, QuerySet):
            return QuerySetDataSource(data)
        elif isinstance(data, list):
            return ListDataSource(data)
        elif callable(data):
            return CallableDataSource(data)
        else:
            raise ValueError(f"Type de données non supporté: {type(data)}")

