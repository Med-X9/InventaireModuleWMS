"""
Tests de compatibilité pour s'assurer que les alias et imports fonctionnent.

Ces tests vérifient que la compatibilité ascendante est maintenue.
"""
from django.test import TestCase

from apps.core.datatables.mixins import (
    ServerSideDataTableView,
    QueryModelView,
    QueryModelMixin
)
from apps.core.datatables import (
    ServerSideDataTableView as ImportedServerSide,
    QueryModelView as ImportedQueryModel,
    QueryModelMixin as ImportedMixin
)


class TestAliasCompatibility(TestCase):
    """
    Tests pour vérifier que les alias fonctionnent correctement.
    """
    
    def test_server_side_is_alias_of_query_model_view(self):
        """
        Test CRITIQUE : ServerSideDataTableView doit être un alias de QueryModelView.
        
        Ce test garantit que toutes les vues existantes qui utilisent
        ServerSideDataTableView continueront de fonctionner.
        """
        self.assertEqual(
            ServerSideDataTableView,
            QueryModelView,
            "ServerSideDataTableView doit être un alias de QueryModelView"
        )
    
    def test_server_side_has_same_methods_as_query_model_view(self):
        """Test que ServerSideDataTableView a les mêmes méthodes que QueryModelView"""
        # Vérifier les méthodes principales
        self.assertTrue(hasattr(ServerSideDataTableView, 'post'))
        self.assertTrue(hasattr(ServerSideDataTableView, 'get'))
        self.assertTrue(hasattr(ServerSideDataTableView, 'process_request'))
        self.assertTrue(hasattr(ServerSideDataTableView, 'get_queryset'))
        self.assertTrue(hasattr(ServerSideDataTableView, 'get_data_source'))
        
        # Vérifier que QueryModelView a les mêmes méthodes
        self.assertTrue(hasattr(QueryModelView, 'post'))
        self.assertTrue(hasattr(QueryModelView, 'get'))
        self.assertTrue(hasattr(QueryModelView, 'process_request'))
        self.assertTrue(hasattr(QueryModelView, 'get_queryset'))
        self.assertTrue(hasattr(QueryModelView, 'get_data_source'))
    
    def test_server_side_inherits_from_query_model_mixin(self):
        """Test que ServerSideDataTableView hérite de QueryModelMixin"""
        self.assertTrue(
            issubclass(ServerSideDataTableView, QueryModelMixin),
            "ServerSideDataTableView doit hériter de QueryModelMixin"
        )
        self.assertTrue(
            issubclass(QueryModelView, QueryModelMixin),
            "QueryModelView doit hériter de QueryModelMixin"
        )
    
    def test_imports_from_init_work(self):
        """Test que les imports depuis __init__.py fonctionnent"""
        # Vérifier que les imports depuis __init__.py fonctionnent
        self.assertEqual(ImportedServerSide, ServerSideDataTableView)
        self.assertEqual(ImportedQueryModel, QueryModelView)
        self.assertEqual(ImportedMixin, QueryModelMixin)
    
    def test_both_classes_are_same_instance(self):
        """Test que ServerSideDataTableView et QueryModelView sont la même classe"""
        # Vérifier que ce sont les mêmes objets
        self.assertIs(ServerSideDataTableView, QueryModelView)
        
        # Vérifier que les MRO (Method Resolution Order) sont identiques
        self.assertEqual(
            ServerSideDataTableView.__mro__,
            QueryModelView.__mro__
        )


class TestBackwardCompatibility(TestCase):
    """
    Tests de compatibilité ascendante pour les anciens usages.
    """
    
    def test_old_imports_still_work(self):
        """Test que les anciens imports fonctionnent toujours"""
        # Test import depuis mixins
        from apps.core.datatables.mixins import ServerSideDataTableView
        from apps.core.datatables.mixins import QueryModelMixin
        from apps.core.datatables.mixins import QueryModelView
        
        self.assertIsNotNone(ServerSideDataTableView)
        self.assertIsNotNone(QueryModelMixin)
        self.assertIsNotNone(QueryModelView)
        
        # Vérifier que l'alias fonctionne
        self.assertEqual(ServerSideDataTableView, QueryModelView)
    
    def test_import_from_init_works(self):
        """Test que l'import depuis __init__.py fonctionne"""
        # Test import depuis __init__
        from apps.core.datatables import ServerSideDataTableView
        from apps.core.datatables import QueryModelView
        from apps.core.datatables import QueryModelMixin
        
        self.assertIsNotNone(ServerSideDataTableView)
        self.assertIsNotNone(QueryModelView)
        self.assertIsNotNone(QueryModelMixin)
        
        # Vérifier que l'alias fonctionne
        self.assertEqual(ServerSideDataTableView, QueryModelView)
    
    def test_can_instantiate_view(self):
        """Test qu'on peut créer une instance de vue (sans erreur)"""
        # Test qu'on peut définir une classe héritant de ServerSideDataTableView
        class TestView(ServerSideDataTableView):
            pass
        
        # Vérifier que la classe est bien créée
        self.assertTrue(issubclass(TestView, ServerSideDataTableView))
        self.assertTrue(issubclass(TestView, QueryModelView))
        self.assertTrue(issubclass(TestView, QueryModelMixin))

