"""
Tests de régression pour s'assurer que le refactoring ne casse rien.

Ces tests doivent TOUJOURS passer avant et après le refactoring.
Ils garantissent la compatibilité avec le code existant.
"""
import json
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.core.datatables.mixins import (
    ServerSideDataTableView,
    QueryModelView,
    QueryModelMixin
)
from apps.core.datatables.models import QueryModel
from apps.core.datatables.engines import FilterEngine, SortEngine, PaginationEngine
from apps.core.datatables.response import ResponseModel
from apps.core.datatables.datasource import DataSourceFactory

User = get_user_model()


class TestServerSideDataTableViewCompatibility(TestCase):
    """
    Tests de compatibilité pour ServerSideDataTableView.
    
    ServerSideDataTableView est un alias de QueryModelView.
    Ces tests vérifient que l'alias fonctionne correctement.
    """
    
    def setUp(self):
        """Configuration initiale"""
        self.factory = RequestFactory()
        self.client = APIClient()
    
    def test_server_side_is_alias_of_query_model_view(self):
        """Test que ServerSideDataTableView est bien un alias"""
        self.assertEqual(ServerSideDataTableView, QueryModelView)
    
    def test_server_side_inherits_from_query_model_mixin(self):
        """Test que ServerSideDataTableView hérite de QueryModelMixin"""
        self.assertTrue(issubclass(ServerSideDataTableView, QueryModelMixin))


class TestQueryModelParsing(TestCase):
    """
    Tests pour le parsing de QueryModel.
    
    Vérifie que tous les formats supportés fonctionnent correctement.
    """
    
    def setUp(self):
        """Configuration initiale"""
        self.factory = RequestFactory()
    
    def test_query_model_from_dict_basic(self):
        """Test parsing QueryModel depuis dictionnaire basique"""
        data = {
            "page": 1,
            "pageSize": 10,
            "search": "test"
        }
        query_model = QueryModel.from_dict(data)
        
        self.assertEqual(query_model.page, 1)
        self.assertEqual(query_model.page_size, 10)
        self.assertEqual(query_model.search, "test")
        self.assertEqual(len(query_model.sort), 0)
        self.assertEqual(len(query_model.filters), 0)
    
    def test_query_model_from_dict_with_sort(self):
        """Test parsing QueryModel avec tri"""
        data = {
            "page": 1,
            "pageSize": 10,
            "sort": [
                {"colId": "name", "sort": "asc"},
                {"colId": "date", "sort": "desc"}
            ]
        }
        query_model = QueryModel.from_dict(data)
        
        self.assertEqual(len(query_model.sort), 2)
        self.assertEqual(query_model.sort[0].col_id, "name")
        self.assertEqual(query_model.sort[0].sort.value, "asc")
        self.assertEqual(query_model.sort[1].col_id, "date")
        self.assertEqual(query_model.sort[1].sort.value, "desc")
    
    def test_query_model_from_dict_with_filters(self):
        """Test parsing QueryModel avec filtres"""
        data = {
            "page": 1,
            "pageSize": 10,
            "filters": {
                "status": ["active", "pending"],
                "name": {"type": "text", "operator": "contains", "value": "test"}
            }
        }
        query_model = QueryModel.from_dict(data)
        
        self.assertEqual(len(query_model.filters), 2)
        self.assertIn("status", query_model.filters)
        self.assertIn("name", query_model.filters)
        
        # Vérifier le filtre SET
        status_filter = query_model.filters["status"]
        self.assertEqual(status_filter.filter_type.value, "set")
        self.assertEqual(status_filter.values, ["active", "pending"])
        
        # Vérifier le filtre TEXT
        name_filter = query_model.filters["name"]
        self.assertEqual(name_filter.filter_type.value, "text")
        self.assertEqual(name_filter.operator.value, "contains")
        self.assertEqual(name_filter.filter, "test")
    
    def test_query_model_from_request_post_json(self):
        """Test parsing QueryModel depuis POST avec JSON body"""
        data = {
            "page": 2,
            "pageSize": 20,
            "search": "keyword",
            "sort": [{"colId": "id", "sort": "desc"}]
        }
        
        request = self.factory.post(
            '/api/test/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Simuler request.data (comme DRF le fait)
        request.data = data
        
        query_model = QueryModel.from_request(request)
        
        self.assertEqual(query_model.page, 2)
        self.assertEqual(query_model.page_size, 20)
        self.assertEqual(query_model.search, "keyword")
        self.assertEqual(len(query_model.sort), 1)
    
    def test_query_model_from_request_get_params(self):
        """Test parsing QueryModel depuis GET avec query params (format JSON string)"""
        request = self.factory.get(
            '/api/test/',
            {
                'page': '3',
                'pageSize': '30',
                'search': 'test',
                'sort': json.dumps([{"colId": "name", "sort": "asc"}])
            }
        )
        
        query_model = QueryModel.from_request(request)
        
        self.assertEqual(query_model.page, 3)
        self.assertEqual(query_model.page_size, 30)
        self.assertEqual(query_model.search, "test")
        self.assertEqual(len(query_model.sort), 1)
        self.assertEqual(query_model.sort[0].col_id, "name")
        self.assertEqual(query_model.sort[0].sort.value, "asc")
    
    def test_query_model_from_request_get_params_deprecated_sortby(self):
        """Test parsing QueryModel avec format déprécié sortBy/sortDir (compatibilité)"""
        request = self.factory.get(
            '/api/test/',
            {
                'page': '1',
                'pageSize': '10',
                'sortBy': 'name',
                'sortDir': 'desc'
            }
        )
        
        query_model = QueryModel.from_request(request)
        
        # Le format déprécié doit toujours fonctionner (compatibilité)
        self.assertEqual(len(query_model.sort), 1)
        self.assertEqual(query_model.sort[0].col_id, "name")
        self.assertEqual(query_model.sort[0].sort.value, "desc")


class TestFilterEngine(TestCase):
    """
    Tests pour FilterEngine.
    
    Vérifie que le moteur de filtrage fonctionne correctement.
    """
    
    def setUp(self):
        """Configuration initiale"""
        self.column_mapping = {
            'id': 'id',
            'name': 'name',
            'status': 'status',
            'price': 'price'
        }
        self.filter_engine = FilterEngine(self.column_mapping)
    
    def test_filter_engine_initialization(self):
        """Test initialisation FilterEngine"""
        self.assertIsNotNone(self.filter_engine)
        self.assertEqual(self.filter_engine.column_field_mapping, self.column_mapping)
    
    def test_filter_engine_empty_filters(self):
        """Test FilterEngine avec filtres vides"""
        from django.db.models import QuerySet
        from django.contrib.auth import get_user_model
        
        # Créer un queryset de test (vide)
        queryset = get_user_model().objects.none()
        filters = {}
        
        result = self.filter_engine.apply_filters(queryset, filters)
        
        # Le queryset ne doit pas être modifié
        self.assertEqual(result, queryset)


class TestSortEngine(TestCase):
    """
    Tests pour SortEngine.
    
    Vérifie que le moteur de tri fonctionne correctement.
    """
    
    def setUp(self):
        """Configuration initiale"""
        self.column_mapping = {
            'id': 'id',
            'name': 'name',
            'date': 'created_at'
        }
        self.sort_engine = SortEngine(self.column_mapping)
    
    def test_sort_engine_initialization(self):
        """Test initialisation SortEngine"""
        self.assertIsNotNone(self.sort_engine)
        self.assertEqual(self.sort_engine.column_field_mapping, self.column_mapping)
    
    def test_sort_engine_empty_sort(self):
        """Test SortEngine avec tri vide"""
        from django.db.models import QuerySet
        from django.contrib.auth import get_user_model
        
        queryset = get_user_model().objects.none()
        sort_model = []
        
        result = self.sort_engine.apply_sorting(queryset, sort_model)
        
        # Le queryset ne doit pas être modifié
        self.assertEqual(result, queryset)


class TestPaginationEngine(TestCase):
    """
    Tests pour PaginationEngine.
    
    Vérifie que le moteur de pagination fonctionne correctement.
    """
    
    def setUp(self):
        """Configuration initiale"""
        self.pagination_engine = PaginationEngine(
            default_page_size=20,
            max_page_size=100
        )
    
    def test_pagination_engine_initialization(self):
        """Test initialisation PaginationEngine"""
        self.assertIsNotNone(self.pagination_engine)
        self.assertEqual(self.pagination_engine.default_page_size, 20)
        self.assertEqual(self.pagination_engine.max_page_size, 100)
    
    def test_pagination_engine_respects_max_page_size(self):
        """Test que PaginationEngine respecte max_page_size"""
        from django.db.models import QuerySet
        from django.contrib.auth import get_user_model
        
        queryset = get_user_model().objects.none()
        
        # Tenter de paginer avec une taille supérieure à max
        result = self.pagination_engine.paginate(
            queryset,
            page=1,
            page_size=200  # Supérieur à max_page_size (100)
        )
        
        # La taille doit être limitée à max_page_size
        self.assertEqual(result['page_size'], 100)


class TestDataSourceFactory(TestCase):
    """
    Tests pour DataSourceFactory.
    
    Vérifie que la factory crée les bonnes sources de données.
    """
    
    def test_factory_creates_queryset_datasource(self):
        """Test création QuerySetDataSource"""
        from django.db.models import QuerySet
        from django.contrib.auth import get_user_model
        
        queryset = get_user_model().objects.all()
        data_source = DataSourceFactory.create(queryset)
        
        from apps.core.datatables.datasource import QuerySetDataSource
        self.assertIsInstance(data_source, QuerySetDataSource)
    
    def test_factory_creates_list_datasource(self):
        """Test création ListDataSource"""
        data_list = [{"id": 1, "name": "Test"}]
        data_source = DataSourceFactory.create(data_list)
        
        from apps.core.datatables.datasource import ListDataSource
        self.assertIsInstance(data_source, ListDataSource)


class TestResponseModel(TestCase):
    """
    Tests pour ResponseModel.
    
    Vérifie que le modèle de réponse fonctionne correctement.
    """
    
    def test_response_model_from_data(self):
        """Test création ResponseModel depuis données"""
        data = [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"}
        ]
        total_count = 100
        page = 1
        page_size = 20
        
        response_model = ResponseModel.from_data(
            data=data,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
        self.assertEqual(response_model.success, True)
        self.assertEqual(len(response_model.row_data), 2)
        self.assertEqual(response_model.row_count, 100)
    
    def test_response_model_to_dict(self):
        """Test conversion ResponseModel en dictionnaire"""
        data = [{"id": 1}]
        response_model = ResponseModel.from_data(
            data=data,
            total_count=1,
            page=1,
            page_size=20
        )
        
        result_dict = response_model.to_dict()
        
        self.assertIn("success", result_dict)
        self.assertIn("rowData", result_dict)
        self.assertIn("rowCount", result_dict)
        self.assertEqual(result_dict["success"], True)
        self.assertEqual(result_dict["rowCount"], 1)


class TestBackwardCompatibility(TestCase):
    """
    Tests de compatibilité ascendante.
    
    Vérifie que les anciennes façons d'utiliser le package fonctionnent toujours.
    """
    
    def test_old_imports_still_work(self):
        """Test que les anciens imports fonctionnent toujours"""
        # Ces imports doivent fonctionner
        from apps.core.datatables.mixins import ServerSideDataTableView
        from apps.core.datatables.mixins import QueryModelMixin
        from apps.core.datatables.mixins import QueryModelView
        
        self.assertIsNotNone(ServerSideDataTableView)
        self.assertIsNotNone(QueryModelMixin)
        self.assertIsNotNone(QueryModelView)
    
    def test_alias_compatibility(self):
        """Test que l'alias ServerSideDataTableView fonctionne"""
        from apps.core.datatables.mixins import ServerSideDataTableView, QueryModelView
        
        # L'alias doit pointer vers QueryModelView
        self.assertEqual(ServerSideDataTableView, QueryModelView)
        
        # Les deux doivent avoir les mêmes méthodes
        self.assertTrue(hasattr(ServerSideDataTableView, 'post'))
        self.assertTrue(hasattr(ServerSideDataTableView, 'get'))
        self.assertTrue(hasattr(QueryModelView, 'post'))
        self.assertTrue(hasattr(QueryModelView, 'get'))

