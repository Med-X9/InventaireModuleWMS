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
    - Tri multi-colonnes (sort)
    - Filtres complexes (filters)
    - Pagination classique (page/pageSize)
    - Recherche globale (search)
    - Format de réponse QueryModel
"""

import logging
from typing import List, Dict, Any, Optional, Union
from django.http import HttpRequest, HttpResponse
from django.db.models import QuerySet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .optimizations import optimize_queryset

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
    column_field_mapping: Dict[str, str] = {}  # col_id -> field_name (optionnel, auto-détecté si vide)
    
    # Configuration optionnelle avec valeurs par défaut améliorées
    default_page_size: int = 20  # Taille de page par défaut (au lieu de 100)
    max_page_size: int = 100     # Taille maximale (au lieu de 1000)
    search_fields: List[str] = []  # Champs pour la recherche globale (auto-détecté si vide)
    # Configuration optionnelle pour les options de filtres avancés (type Excel)
    # Exemple :
    #   datatable_filter_options = {
    #       "client": "client__name",
    #       "status": "status",
    #   }
    # Utilisé par get_distinct_filter_values() et les vues dédiées aux options de filtre.
    datatable_filter_options: Dict[str, str] = {}
    
    # Virtual scrolling : si True, la réponse JSON inclut startRow et endRow (indices 0-based du bloc).
    include_block_indices: bool = False
    
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
        
        OPTIMISATIONS:
        - Les optimisations doivent être définies explicitement via :
          - select_related_fields : Liste de champs pour select_related()
          - prefetch_related_fields : Liste de champs pour prefetch_related()
          - only_fields : Liste de champs à charger uniquement
          - defer_fields : Liste de champs à exclure
        
        Exemple:
            class MyView(QueryModelView):
                model = MyModel
                serializer_class = MySerializer
                select_related_fields = ['category', 'author']
                prefetch_related_fields = ['tags', 'comments']
        """
        from .datasource import DataSourceFactory
        
        queryset = self.get_queryset()

        # Vérifier si la vue a défini explicitement des optimisations
        has_explicit_optimizations = (
            hasattr(self, 'select_related_fields') or
            hasattr(self, 'prefetch_related_fields') or
            hasattr(self, 'only_fields') or
            hasattr(self, 'defer_fields')
        )
        
        if has_explicit_optimizations:
            # Appliquer les optimisations explicites
            queryset = optimize_queryset(
                queryset,
                select_related=getattr(self, 'select_related_fields', None),
                prefetch_related=getattr(self, 'prefetch_related_fields', None),
                only=getattr(self, 'only_fields', None),
                defer=getattr(self, 'defer_fields', None),
            )
        # Sinon, retourner le queryset tel quel (pas d'optimisation automatique)

        return DataSourceFactory.create(queryset)
    
    def get_column_field_mapping(self) -> Dict[str, str]:
        """
        Retourne le mapping colonnes -> champs Django.
        
        Fusion intelligente : auto-détection + mappings explicites.
        
        Stratégie :
        1. Auto-détecter depuis le serializer (tous les champs)
        2. Fusionner avec column_field_mapping explicite (écrase l'auto-détection)
        3. Résultat : mapping complet avec personnalisations
        
        Avantage : Définir seulement les champs personnalisés !
        
        Exemple :
            # Au lieu de 20 lignes pour 20 champs :
            column_field_mapping = {
                'id': 'id',
                'name': 'name',
                # ... 18 autres lignes identiques
            }
            
            # Maintenant, seulement les champs personnalisés :
            column_field_mapping = {
                'account_name': 'awi_links__account__account_name',  # Seulement les relations
                'warehouse_name': 'awi_links__warehouse__warehouse_name'
            }
            # Les 18 autres champs sont auto-détectés depuis le serializer !
        
        Returns:
            Dict[str, str]: Mapping col_id -> field_name Django (fusionné)
        """
        # Étape 1 : Auto-détection depuis le serializer
        auto_mapping = {}
        try:
            serializer_class = self.get_serializer_class()
            if serializer_class:
                auto_mapping = self._auto_detect_mapping_from_serializer(serializer_class)
                if auto_mapping and logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Auto-détection du column_field_mapping depuis {serializer_class.__name__}: "
                        f"{len(auto_mapping)} champs détectés"
                    )
        except (NotImplementedError, AttributeError):
            # Serializer non disponible, continuer
            pass
        
        # Étape 2 : Récupérer les mappings explicites (personnalisations)
        explicit_mapping = getattr(self, 'column_field_mapping', {})
        
        # Étape 3 : Fusionner (mappings explicites écrasent l'auto-détection)
        if explicit_mapping:
            # Fusion : auto-détection + personnalisations
            merged_mapping = {**auto_mapping, **explicit_mapping}
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Fusion du mapping : {len(auto_mapping)} auto-détectés + "
                    f"{len(explicit_mapping)} personnalisés = {len(merged_mapping)} total"
                )
            
            return merged_mapping
        
        # Si pas de mapping explicite, retourner l'auto-détection
        if auto_mapping:
            return auto_mapping
        
        # Fallback : mapping vide (utiliser col_id directement)
        return {}
    
    def get_search_fields(self) -> List[str]:
        """
        Retourne les champs utilisés pour la recherche globale.
        
        Par défaut retourne l'attribut de classe search_fields.
        Peut être surchargé dans la vue pour un comportement dynamique.
        """
        return getattr(self, 'search_fields', [])
    
    def _auto_detect_mapping_from_serializer(self, serializer_class: type) -> Dict[str, str]:
        """
        Auto-détecte le mapping colonnes -> champs depuis le serializer.
        
        Parcourt les champs du serializer et crée un mapping :
        - col_id = nom du champ dans le serializer
        - field_name = source du champ (si défini) ou nom du champ
        
        Args:
            serializer_class: Classe du serializer DRF
            
        Returns:
            Dict[str, str]: Mapping col_id -> field_name Django
        """
        mapping = {}
        
        try:
            # Créer une instance du serializer sans données
            serializer = serializer_class()
            fields = getattr(serializer, 'fields', {})
            
            for field_name, field_instance in fields.items():
                # Utiliser le nom du champ comme col_id
                col_id = field_name
                
                # Déterminer le field_name Django réel
                # Si le champ a un 'source', utiliser le source
                if hasattr(field_instance, 'source') and field_instance.source:
                    field_name_django = field_instance.source
                else:
                    # Sinon, utiliser le nom du champ directement
                    field_name_django = field_name
                
                # Ajouter au mapping
                mapping[col_id] = field_name_django
                
        except Exception as e:
            logger.warning(
                f"Erreur lors de l'auto-détection du mapping depuis {serializer_class.__name__}: {str(e)}"
            )
        
        return mapping
    
    def get_distinct_filter_values(self, field_key: str) -> List[Any]:
        """
        Retourne les valeurs distinctes pour un champ de filtre configuré.
        
        Cette méthode est conçue pour les filtres "Excel-like" où l'on affiche
        toutes les valeurs possibles d'une colonne (même si elles ne sont pas
        présentes sur la page actuelle).
        
        Configuration côté vue :
            class InventoryListView(QueryModelView):
                model = Inventory
                serializer_class = InventoryDetailSerializer
                
                # Colonnes exposées pour les filtres avancés
                datatable_filter_options = {
                    "client": "client__name",
                    "status": "status",
                    "warehouse": "warehouse__warehouse_name",
                }
        
        Args:
            field_key: Nom de la colonne côté frontend (ex: "client", "status").
        
        Returns:
            List[Any]: Liste des valeurs distinctes ordonnées.
        """
        # Récupérer le mapping des colonnes filtrables
        options_mapping = getattr(self, "datatable_filter_options", {}) or {}
        field_path = options_mapping.get(field_key)
        
        if not field_path:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Aucun mapping trouvé pour le filtre avancé '{field_key}' "
                    f"dans datatable_filter_options de {self.__class__.__name__}."
                )
            return []
        
        queryset = self.get_queryset()
        
        try:
            # Utiliser values_list + distinct() pour récupérer toutes les valeurs uniques
            values_qs = (
                queryset.values_list(field_path, flat=True)
                .order_by(field_path)
                .distinct()
            )
            # Retourner une simple liste (sérialisable en JSON)
            return list(values_qs)
        except Exception as e:
            # On log l'erreur mais on ne lève pas d'exception ici pour ne pas
            # casser l'API principale si l'endpoint de métadonnées est utilisé.
            logger.warning(
                f"Erreur lors de la récupération des valeurs distinctes pour "
                f"'{field_key}' ({field_path}) dans {self.__class__.__name__}: {e}"
            )
            return []
    
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
        1. Vérifier si export demandé (export=excel ou export=csv)
        2. Parser QueryModel depuis la requête (page, pageSize, search, sort, filters)
        3. Récupérer la source de données
        4. Appliquer la recherche globale (search)
        5. Appliquer les filtres (FilterEngine)
        6. Appliquer le tri (SortEngine)
        7. Si export : exporter TOUTES les données (sans pagination) et retourner fichier
        8. Sinon : Paginer et retourner ResponseModel JSON
        
        Args:
            request: Requête HTTP
            *args, **kwargs: Arguments additionnels
            
        Returns:
            Response DRF avec format QueryModel (JSON) ou fichier (Excel/CSV)
        """
        from .models import QueryModel
        from .engines import FilterEngine, SortEngine, PaginationEngine
        from .response import ResponseModel
        from .exporters import export_manager
        
        try:
            # 1. Vérifier si export demandé
            export_format = request.GET.get('export')
            if not export_format:
                # Essayer de récupérer depuis request.data si disponible
                try:
                    if hasattr(request, 'data') and isinstance(request.data, dict):
                        export_format = request.data.get('export')
                except Exception:
                    # request.data peut lever une exception si le body n'est pas du JSON valide
                    # Dans ce cas, ignorer et continuer sans export
                    pass
            
            # 2. Parser QueryModel
            query_model = QueryModel.from_request(request)
            
            # 3. Récupérer la source de données
            data_source = self.get_data_source()
            data = data_source.get_data()
            
            # 4. Appliquer la recherche globale si présente
            if query_model.search:
                search_clean = query_model.search.strip()
                if search_clean:
                    # Récupérer les champs de recherche (auto-détecté si vide)
                    search_fields = self.get_search_fields()
                    
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
            
            # 5. Appliquer les filtres (QuerySet ou liste)
            column_mapping = self.get_column_field_mapping()
            filter_engine = FilterEngine(column_mapping)
            data = filter_engine.apply_filters(data, query_model.filters)
            
            # 6. Appliquer le tri (QuerySet ou liste)
            column_mapping = self.get_column_field_mapping()
            if not column_mapping:
                logger.warning(
                    f"column_field_mapping est vide pour {self.__class__.__name__}. "
                    "Le tri peut échouer si des colonnes utilisent des relations Django."
                )
            sort_engine = SortEngine(column_mapping)
            data = sort_engine.apply_sorting(data, query_model.sort)
            
            # 7. Si export demandé : exporter TOUTES les données (sans pagination)
            if export_format:
                serializer_class = self.get_serializer_class()
                filename = getattr(self, 'export_filename', 'export')
                
                if isinstance(data, list):
                    # Pour les listes : sérialiser puis exporter
                    if serializer_class:
                        serializer = serializer_class(data, many=True)
                        serialized_data = [dict(item) for item in serializer.data]
                    else:
                        serialized_data = data
                    
                    return self._export_from_list(serialized_data, export_format, filename)
                else:
                    # QuerySet : utiliser export_manager normalement
                    return export_manager.export(
                        format_name=export_format,
                        queryset=data,
                        serializer_class=serializer_class,
                        filename=filename
                    )
            
            # 8. Sinon : Paginer et retourner JSON
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
            
            # 9. Sérialiser
            serialized_data = self.serialize_data(paginated_data)
            
            # 10. Retourner ResponseModel avec le nouveau format
            response_model = ResponseModel.from_data(
                data=serialized_data,
                total_count=total_count,
                page=query_model.page,
                page_size=query_model.page_size
            )
            
            return Response(
                response_model.to_dict(include_block_indices=getattr(self, 'include_block_indices', False)),
                status=status.HTTP_200_OK
            )
            
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
    
    def _export_from_list(self, data_list: List[Dict[str, Any]], export_format: str, filename: str) -> HttpResponse:
        """
        Exporte depuis une liste de dictionnaires.
        
        Args:
            data_list: Liste de dictionnaires à exporter
            export_format: Format d'export ('excel' ou 'csv')
            filename: Nom du fichier
            
        Returns:
            HttpResponse avec le fichier
        """
        from django.http import HttpResponse
        import csv
        
        # Import conditionnel pour openpyxl
        try:
            from openpyxl import Workbook
            OPENPYXL_AVAILABLE = True
        except ImportError:
            OPENPYXL_AVAILABLE = False
        
        try:
            if export_format.lower() in ['excel', 'xlsx']:
                # Vérifier que openpyxl est disponible
                if not OPENPYXL_AVAILABLE:
                    return HttpResponse(
                        "openpyxl n'est pas installé. Installez-le avec: pip install openpyxl",
                        content_type='text/plain',
                        status=500
                    )
                
                # Export Excel depuis liste
                wb = Workbook()
                ws = wb.active
                
                if not data_list:
                    ws.append(["Aucune donnée à exporter"])
                else:
                    # En-têtes
                    headers = list(data_list[0].keys())
                    ws.append(headers)
                    
                    # Données
                    for row_data in data_list:
                        row = [row_data.get(header, '') for header in headers]
                        ws.append(row)
                
                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
                wb.save(response)
                return response
                
            elif export_format.lower() == 'csv':
                # Export CSV depuis liste
                response = HttpResponse(content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
                
                if not data_list:
                    writer = csv.writer(response)
                    writer.writerow(["Aucune donnée à exporter"])
                else:
                    headers = list(data_list[0].keys())
                    writer = csv.DictWriter(response, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(data_list)
                
                return response
            else:
                return HttpResponse(
                    f"Format d'export non supporté: {export_format}",
                    content_type='text/plain',
                    status=400
                )
        except ImportError as e:
            logger.error(f"Module manquant pour export {export_format}: {str(e)}", exc_info=True)
            return HttpResponse(
                f"Module manquant pour l'export {export_format}. Installez openpyxl pour Excel.",
                content_type='text/plain',
                status=500
            )
        except Exception as e:
            logger.error(f"Erreur export depuis liste: {str(e)}", exc_info=True)
            return HttpResponse(
                f"Erreur lors de l'export: {str(e)}",
                content_type='text/plain',
                status=500
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
    
    def get_filter_options(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        Endpoint générique pour récupérer les valeurs distinctes d'un filtre.
        
        Cet endpoint permet d'implémenter facilement des filtres avancés
        "type Excel" côté frontend.
        
        Utilisation dans urls.py :
        
            path(
                "inventories/filter-options/",
                InventoryListView.as_view(action=\"filter-options\"),
                name=\"inventory-filter-options\",
            )
        
        Requête :
            GET /api/inventories/filter-options/?field=client
        
        Paramètres :
            - field : nom de la colonne côté frontend (clé de datatable_filter_options)
        
        Réponse :
            - 200 OK : liste des valeurs distinctes
            - 400 BAD REQUEST : si le paramètre 'field' est manquant
        """
        field_key = request.GET.get("field")
        
        if not field_key:
            return Response(
                {"detail": "Le paramètre 'field' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        values = self.get_distinct_filter_values(field_key)
        return Response(values, status=status.HTTP_200_OK)
    
    def get(self, request, *args, **kwargs):
        """
        GET pour requêtes QueryModel (format query params).
        
        Query params:
        - page: int (numéro de page, 1-indexed)
        - pageSize: int (taille de page)
        - search: string (recherche globale)
        - sort: JSON string (array de {colId, sort})
        - filters: JSON string (dict de filtres)
        """
        return self.process_request(request, *args, **kwargs) 


# =============================================================================
# ALIAS DE COMPATIBILITÉ
# =============================================================================

# Alias pour compatibilité avec le code existant
# ServerSideDataTableView est maintenant un alias de QueryModelView
ServerSideDataTableView = QueryModelView
