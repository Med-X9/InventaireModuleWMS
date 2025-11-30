"""
Mixins pour QueryModel uniquement.

Ce module fournit des mixins pour intégrer facilement
les fonctionnalités QueryModel dans les vues Django REST Framework.

PRINCIPES DRY/SOLID:
- DRY (Don't Repeat Yourself) : Réutilisation maximale du code
- SOLID : Séparation des responsabilités et extensibilité
- Interface cohérente pour toutes les vues QueryModel

FONCTIONNALITÉS:
- Mixin réutilisable pour les vues QueryModel
- Support automatique des requêtes QueryModel (POST JSON ou GET query params)
- Configuration flexible et extensible
- Intégration transparente avec Django REST Framework
- Support des QuerySets et listes de dictionnaires

UTILISATION RAPIDE:
    class MyListView(QueryModelMixin, APIView):
        model = MyModel
        serializer_class = MySerializer
        column_field_mapping = {
            'id': 'id',
            'name': 'name',
            'age': 'age'
        }
        
        def get_queryset(self):
            return MyModel.objects.all()
    
    La vue supporte automatiquement:
    - Tri multi-colonnes (sort ou sortBy/sortDir)
    - Filtres complexes (filters)
    - Pagination classique (page/pageSize)
    - Recherche globale (search)
    - Format de réponse QueryModel
"""

import logging
from typing import List, Dict, Any, Optional, Union
from django.http import HttpRequest
from django.db.models import QuerySet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class QueryModelMixin:
    """
    Mixin pour ajouter le support QueryModel à une vue.
    
    Ce mixin est spécialisé pour le format QueryModel uniquement (page, pageSize, search, sort, filters).
    
    USAGE SIMPLE:
    
    class MyView(QueryModelMixin, APIView):
        model = MyModel
        serializer_class = MySerializer
        column_field_mapping = {
            'id': 'id',
            'name': 'name',
            'age': 'age'
        }
        
        def get_queryset(self):
            return MyModel.objects.all()
    
    La vue supporte automatiquement:
    - Tri multi-colonnes (sort ou sortBy/sortDir)
    - Filtres complexes (filters)
    - Pagination classique (page/pageSize)
    - Recherche globale (search)
    - Format de réponse QueryModel
    """
    
    # Configuration requise
    serializer_class: Optional[type] = None
    column_field_mapping: Dict[str, str] = {}  # col_id -> field_name
    
    # Configuration optionnelle
    default_page_size: int = 100
    max_page_size: int = 1000
    search_fields: List[str] = []  # Champs pour la recherche globale
    
    def get_queryset(self) -> QuerySet:
        """
        Retourne le QuerySet de base.
        
        À surcharger dans la vue pour personnaliser le QuerySet.
        """
        if hasattr(self, 'model'):
            return self.model.objects.all()
        raise NotImplementedError(
            "Vous devez soit définir 'model' soit surcharger 'get_queryset()'"
        )
    
    def get_data_source(self):
        """
        Retourne la source de données.
        
        Par défaut, utilise get_queryset(). Peut être surchargé pour
        utiliser une liste de dictionnaires ou une fonction callable.
        """
        from .datasource import DataSourceFactory
        queryset = self.get_queryset()
        return DataSourceFactory.create(queryset)
    
    def get_column_field_mapping(self) -> Dict[str, str]:
        """
        Retourne le mapping colonnes -> champs Django.
        
        Par défaut, utilise self.column_field_mapping.
        Peut être surchargé pour un mapping dynamique.
        """
        return getattr(self, 'column_field_mapping', {})
    
    def get_serializer_class(self) -> type:
        """Retourne la classe de serializer"""
        if self.serializer_class is None:
            raise NotImplementedError(
                "Vous devez définir 'serializer_class'"
            )
        return self.serializer_class
    
    def serialize_data(
        self,
        data: Union[QuerySet, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Sérialise les données avec le serializer.
        
        Args:
            data: QuerySet ou liste de dictionnaires
            
        Returns:
            Liste de dictionnaires sérialisés
        """
        serializer_class = self.get_serializer_class()
        
        if isinstance(data, QuerySet):
            # QuerySet -> utiliser many=True
            serializer = serializer_class(data, many=True)
            return serializer.data
        elif isinstance(data, list):
            # Liste de dicts -> sérialiser chaque élément
            serializer = serializer_class(data, many=True)
            return serializer.data
        else:
            # Convertir en liste si nécessaire
            data_list = list(data) if hasattr(data, '__iter__') else [data]
            serializer = serializer_class(data_list, many=True)
            return serializer.data
    
    def process_request(
        self,
        request: HttpRequest,
        *args,
        **kwargs
    ) -> Response:
        """
        Traite une requête complète au format QueryModel.
        
        FLUX:
        1. Parser QueryModel depuis la requête (page, pageSize, search, sort, filters)
        2. Récupérer la source de données
        3. Appliquer la recherche globale (search)
        4. Appliquer les filtres (FilterEngine)
        5. Appliquer le tri (SortEngine)
        6. Paginer (PaginationEngine avec page/pageSize)
        7. Sérialiser les données
        8. Retourner ResponseModel
        
        Args:
            request: Requête HTTP
            *args, **kwargs: Arguments additionnels
            
        Returns:
            Response DRF avec format QueryModel
        """
        from .models import QueryModel
        from .engines import FilterEngine, SortEngine, PaginationEngine
        from .response import ResponseModel
        
        try:
            # 1. Parser QueryModel
            query_model = QueryModel.from_request(request)
            
            # 2. Récupérer la source de données
            data_source = self.get_data_source()
            data = data_source.get_data()
            
            # 3. Appliquer la recherche globale si présente (nouveau format)
            if query_model.search:
                search_clean = query_model.search.strip()
                if search_clean:
                    # Utiliser search_fields si défini, sinon utiliser tous les champs du mapping
                    search_fields = getattr(self, 'search_fields', [])
                    if not search_fields:
                        # Fallback : utiliser tous les champs du column_field_mapping
                        search_fields = list(self.get_column_field_mapping().values())
                    
                    if isinstance(data, QuerySet):
                        # Recherche sur QuerySet
                        from django.db.models import Q
                        search_query = Q()
                        for field in search_fields:
                            try:
                                search_query |= Q(**{f"{field}__icontains": search_clean})
                            except Exception:
                                # Ignorer les champs invalides
                                continue
                        if search_query:
                            data = data.filter(search_query)
                    else:
                        # Recherche sur liste de dictionnaires
                        filtered_data = []
                        for item in data:
                            match_found = False
                            # Chercher dans les champs configurés
                            for field in search_fields:
                                value = item.get(field)
                                if value is not None and search_clean.lower() in str(value).lower():
                                    filtered_data.append(item)
                                    match_found = True
                                    break
                            # Si pas trouvé dans les champs configurés, chercher dans tous les champs
                            if not match_found:
                                for key, value in item.items():
                                    if value is not None and search_clean.lower() in str(value).lower():
                                        filtered_data.append(item)
                                        break
                        data = filtered_data
            
            # 4. Appliquer les filtres (QuerySet ou liste)
            column_mapping = self.get_column_field_mapping()
            filter_engine = FilterEngine(column_mapping)
            data = filter_engine.apply_filters(data, query_model.filters)
            
            # 5. Appliquer le tri (QuerySet ou liste)
            column_mapping = self.get_column_field_mapping()
            sort_engine = SortEngine(column_mapping)
            data = sort_engine.apply_sorting(data, query_model.sort)
            
            # 6. Paginer (QuerySet ou liste)
            pagination_engine = PaginationEngine(
                default_page_size=self.default_page_size,
                max_page_size=self.max_page_size
            )
            pagination_result = pagination_engine.paginate(
                data,
                page=query_model.page,
                page_size=query_model.page_size
            )
            paginated_data = pagination_result['queryset']
            total_count = pagination_result['total_count']
            
            # 7. Sérialiser
            serialized_data = self.serialize_data(paginated_data)
            
            # 8. Retourner ResponseModel avec le nouveau format
            response_model = ResponseModel.from_data(
                data=serialized_data,
                total_count=total_count,
                page=query_model.page,
                page_size=query_model.page_size
            )
            
            return Response(response_model.to_dict(), status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement QueryModel: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": f"Erreur lors du traitement: {str(e)}",
                    "rowData": [],
                    "rowCount": 0
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QueryModelView(QueryModelMixin, APIView):
    """
    Vue complète avec support QueryModel.
    
    Cette classe est spécialisée pour le format QueryModel uniquement.
    
    USAGE:
    
    class MyView(QueryModelView):
        model = MyModel
        serializer_class = MySerializer
        column_field_mapping = {
            'id': 'id',
            'name': 'name'
        }
    
    La vue expose automatiquement:
    - POST /api/my-view/ (avec QueryModel dans le body)
    - GET /api/my-view/?page=1&pageSize=10&search=...&sort=...&filters=... (format QueryModel)
    """
    
    def post(self, request, *args, **kwargs):
        """
        POST pour requêtes QueryModel (format JSON dans body).
        
        Body attendu:
        {
            "page": 1,
            "pageSize": 10,
            "search": "ink",
            "sort": [{"colId": "name", "sort": "asc"}],
            "filters": {
                "status": ["active", "pending"],
                "category": {"type": "text", "operator": "contains", "value": "ink"}
            }
        }
        """
        return self.process_request(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """
        GET pour requêtes QueryModel (format query params).
        
        Query params:
        - page: int (numéro de page, 1-indexed)
        - pageSize: int (taille de page)
        - search: string (recherche globale)
        - sort: JSON string (array de {colId, sort}) ou sortBy/sortDir pour tri simple
        - filters: JSON string (dict de filtres)
        """
        return self.process_request(request, *args, **kwargs)


# =============================================================================
# ALIAS DE COMPATIBILITÉ
# =============================================================================

# Alias pour compatibilité avec le code existant
# ServerSideDataTableView est maintenant un alias de QueryModelView
ServerSideDataTableView = QueryModelView
