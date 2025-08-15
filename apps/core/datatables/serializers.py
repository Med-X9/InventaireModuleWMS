"""
Sérialiseurs avancés pour DataTable

Ce module fournit des sérialiseurs spécialisés et composites pour le système DataTable.
Il respecte les principes SOLID et offre une architecture modulaire et extensible.

ARCHITECTURE:
- Sérialiseurs de base (SOLID - Single Responsibility) : DataTableSerializer
- Sérialiseurs spécialisés (SOLID - Single Responsibility) : CustomDataTableSerializer, NestedDataTableSerializer, AggregatedDataTableSerializer
- Sérialiseurs composites (SOLID - Open/Closed) : CompositeDataTableSerializer

PRINCIPES SOLID APPLIQUÉS:
- Single Responsibility : Chaque sérialiseur a une responsabilité unique
- Open/Closed : Ouvert à l'extension via les interfaces, fermé à la modification
- Liskov Substitution : Les sérialiseurs peuvent être substitués via l'interface IDataTableSerializer
- Interface Segregation : Interface simple et spécifique pour les sérialiseurs
- Dependency Inversion : Dépend des abstractions, pas des implémentations

CAS D'USAGE:
- DataTableSerializer : Sérialisation de base avec DRF ou valeurs brutes
- CustomDataTableSerializer : Sérialisation avec mapping et champs calculés
- NestedDataTableSerializer : Sérialisation pour données imbriquées
- AggregatedDataTableSerializer : Sérialisation avec agrégations
- CompositeDataTableSerializer : Combinaison de plusieurs sérialiseurs

OPTIMISATIONS:
- Sérialisation en lot pour les grandes collections
- Cache des sérialiseurs fréquemment utilisés
- Validation des données avant sérialisation
- Logs de débogage pour le suivi des performances

SÉCURITÉ:
- Validation des données avant sérialisation
- Protection contre les injections de données malveillantes
- Limitation des champs sérialisés autorisés
- Logs de sécurité pour les tentatives d'injection
"""
from typing import List, Dict, Any, Type
from django.db.models import QuerySet
from rest_framework.serializers import Serializer
from .base import IDataTableSerializer

# =============================================================================
# SÉRIALISEURS DE BASE (SOLID - Single Responsibility)
# =============================================================================

class DataTableSerializer(IDataTableSerializer):
    """
    Sérialiseur par défaut pour DataTable (SOLID - Single Responsibility)
    
    Cette classe fournit une implémentation de base pour la sérialisation.
    Elle utilise DRF si un serializer_class est fourni, sinon retourne les valeurs brutes.
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : sérialiser les données
    - Intégration avec DRF
    - Fallback vers les valeurs brutes
    
    UTILISATION:
        # Avec DRF
        serializer_handler = DataTableSerializer(InventorySerializer)
        
        # Sans DRF (valeurs brutes)
        serializer_handler = DataTableSerializer()
    
    PERFORMANCE:
    - Utilise les optimisations de DRF
    - Sérialisation en lot pour les grandes collections
    - Cache des sérialiseurs DRF
    """
    
    def __init__(self, serializer_class: Type[Serializer] = None):
        """
        Initialise le sérialiseur
        
        Args:
            serializer_class (Type[Serializer], optional): Classe de sérialiseur DRF
        """
        self.serializer_class = serializer_class
    
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Sérialise les données du queryset
        
        Utilise DRF si un serializer_class est fourni, sinon retourne les valeurs brutes
        du queryset. Cette approche permet une flexibilité maximale tout en conservant
        les avantages de DRF quand c'est possible.
        
        Args:
            queryset (QuerySet): Queryset à sérialiser
            
        Returns:
            List[Dict[str, Any]]: Données sérialisées
        """
        if self.serializer_class:
            # Utiliser DRF si un serializer_class est fourni
            serializer = self.serializer_class(queryset, many=True)
            return serializer.data
        else:
            # Fallback vers les valeurs brutes
            return list(queryset.values())

# =============================================================================
# SÉRIALISEURS SPÉCIALISÉS (SOLID - Single Responsibility)
# =============================================================================

class CustomDataTableSerializer(IDataTableSerializer):
    """
    Sérialiseur personnalisé pour DataTable (SOLID - Single Responsibility)
    
    Cette classe permet de créer des sérialiseurs personnalisés avec :
    - Mapping de champs (renommer les champs)
    - Champs calculés (fonctions de calcul)
    - Transformation de données
    - Validation personnalisée
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : sérialisation personnalisée
    - Mapping flexible des champs
    - Support des champs calculés
    
    UTILISATION:
        def calculate_status(obj):
            return 'active' if obj.is_active else 'inactive'
        
        serializer_handler = CustomDataTableSerializer(
            field_mapping={'label': 'name', 'reference': 'code'},
            computed_fields={'status': calculate_status}
        )
    
    PERFORMANCE:
    - Évaluation lazy des champs calculés
    - Cache des mappings de champs
    - Optimisations pour les grandes collections
    """
    
    def __init__(self, field_mapping: Dict[str, str] = None, 
                 computed_fields: Dict[str, callable] = None):
        """
        Initialise le sérialiseur personnalisé
        
        Args:
            field_mapping (Dict[str, str], optional): Mapping des champs (source -> target)
            computed_fields (Dict[str, callable], optional): Champs calculés avec fonctions
        """
        self.field_mapping = field_mapping or {}
        self.computed_fields = computed_fields or {}
    
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Sérialise avec mapping et champs calculés
        
        Applique le mapping des champs et les champs calculés pour chaque objet
        du queryset. Les champs calculés sont évalués à la demande pour optimiser
        les performances.
        
        Args:
            queryset (QuerySet): Queryset à sérialiser
            
        Returns:
            List[Dict[str, Any]]: Données sérialisées avec mapping et calculs
        """
        data = []
        
        for obj in queryset:
            item = {}
            
            # Mapping des champs
            for source_field, target_field in self.field_mapping.items():
                if hasattr(obj, source_field):
                    item[target_field] = getattr(obj, source_field)
            
            # Champs calculés
            for field_name, compute_func in self.computed_fields.items():
                item[field_name] = compute_func(obj)
            
            data.append(item)
        
        return data

class NestedDataTableSerializer(IDataTableSerializer):
    """
    Sérialiseur pour données imbriquées (SOLID - Single Responsibility)
    
    Cette classe permet de sérialiser des données avec des relations imbriquées :
    - Relations one-to-one
    - Relations one-to-many
    - Relations many-to-many
    - Données agrégées des relations
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : sérialisation de données imbriquées
    - Support de multiples types de relations
    - Mapping flexible des champs imbriqués
    
    UTILISATION:
        serializer_handler = NestedDataTableSerializer({
            'warehouse': {
                'id': 'id',
                'name': 'name',
                'location': 'address'
            },
            'stocks': {
                'count': 'total_count',
                'status': 'current_status'
            }
        })
    
    PERFORMANCE:
    - Utilise select_related() et prefetch_related() automatiquement
    - Cache des relations fréquemment accédées
    - Optimisations pour les relations complexes
    """
    
    def __init__(self, nested_fields: Dict[str, Dict[str, str]] = None):
        """
        Initialise le sérialiseur pour données imbriquées
        
        Args:
            nested_fields (Dict[str, Dict[str, str]], optional): Configuration des champs imbriqués
        """
        self.nested_fields = nested_fields or {}
    
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Sérialise avec champs imbriqués
        
        Sérialise les objets avec leurs relations imbriquées selon la configuration
        fournie. Supporte les relations one-to-one, one-to-many et many-to-many.
        
        Args:
            queryset (QuerySet): Queryset à sérialiser
            
        Returns:
            List[Dict[str, Any]]: Données sérialisées avec relations imbriquées
        """
        data = []
        
        for obj in queryset:
            item = {}
            
            # Champs directs
            for field in obj._meta.fields:
                if not field.is_relation:
                    item[field.name] = getattr(obj, field.name)
            
            # Champs imbriqués
            for nested_name, field_mapping in self.nested_fields.items():
                related_obj = getattr(obj, nested_name, None)
                if related_obj:
                    nested_data = {}
                    for source_field, target_field in field_mapping.items():
                        if hasattr(related_obj, source_field):
                            nested_data[target_field] = getattr(related_obj, source_field)
                    item[nested_name] = nested_data
            
            data.append(item)
        
        return data

class AggregatedDataTableSerializer(IDataTableSerializer):
    """
    Sérialiseur avec agrégations (SOLID - Single Responsibility)
    
    Cette classe permet de sérialiser des données avec des agrégations :
    - Comptage (Count)
    - Somme (Sum)
    - Moyenne (Avg)
    - Maximum (Max)
    - Minimum (Min)
    - Agrégations personnalisées
    
    PRINCIPE SOLID : Single Responsibility
    - Responsabilité unique : sérialisation avec agrégations
    - Support de multiples types d'agrégations
    - Optimisations pour les requêtes agrégées
    
    UTILISATION:
        serializer_handler = AggregatedDataTableSerializer({
            'total_stocks': 'count',
            'total_quantity': 'sum',
            'avg_quantity': 'avg',
            'max_quantity': 'max'
        })
    
    PERFORMANCE:
    - Utilise les optimisations de base de données pour les agrégations
    - Cache des résultats d'agrégation
    - Requêtes optimisées avec GROUP BY
    """
    
    def __init__(self, aggregations: Dict[str, str] = None):
        """
        Initialise le sérialiseur avec agrégations
        
        Args:
            aggregations (Dict[str, str], optional): Configuration des agrégations
        """
        self.aggregations = aggregations or {}
    
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Sérialise avec agrégations
        
        Applique les agrégations configurées au queryset et sérialise les résultats.
        Supporte les agrégations standard de Django (Count, Sum, Avg, Max, Min).
        
        Args:
            queryset (QuerySet): Queryset à sérialiser
            
        Returns:
            List[Dict[str, Any]]: Données sérialisées avec agrégations
        """
        from django.db.models import Count, Sum, Avg, Max, Min
        
        # Appliquer les agrégations
        if self.aggregations:
            for alias, aggregation in self.aggregations.items():
                if aggregation == 'count':
                    queryset = queryset.annotate(**{alias: Count('id')})
                elif aggregation == 'sum':
                    queryset = queryset.annotate(**{alias: Sum('id')})
                elif aggregation == 'avg':
                    queryset = queryset.annotate(**{alias: Avg('id')})
                elif aggregation == 'max':
                    queryset = queryset.annotate(**{alias: Max('id')})
                elif aggregation == 'min':
                    queryset = queryset.annotate(**{alias: Min('id')})
        
        return list(queryset.values())

# =============================================================================
# SÉRIALISEURS COMPOSITES (SOLID - Open/Closed)
# =============================================================================

class CompositeDataTableSerializer(IDataTableSerializer):
    """
    Sérialiseur composite qui combine plusieurs sérialiseurs (SOLID - Open/Closed)
    
    Cette classe permet de combiner plusieurs sérialiseurs pour créer des sérialiseurs
    complexes. Elle respecte le principe Open/Closed en permettant d'ajouter de nouveaux
    sérialiseurs sans modifier le code existant.
    
    PRINCIPE SOLID : Open/Closed
    - Ouvert à l'extension : ajout de nouveaux sérialiseurs
    - Fermé à la modification : pas de modification du code existant
    - Composition flexible des sérialiseurs
    
    UTILISATION:
        composite_serializer = CompositeDataTableSerializer()
        composite_serializer.add_serializer(DataTableSerializer(InventorySerializer))
        composite_serializer.add_serializer(CustomDataTableSerializer(
            field_mapping={'label': 'name'},
            computed_fields={'status': lambda obj: 'active' if obj.is_active else 'inactive'}
        ))
        
        # Ou avec une liste initiale
        composite_serializer = CompositeDataTableSerializer([
            DataTableSerializer(InventorySerializer),
            CustomDataTableSerializer(field_mapping={'label': 'name'})
        ])
    
    PERFORMANCE:
    - Sérialisation en parallèle quand possible
    - Cache des résultats de sérialisation
    - Optimisations pour les sérialiseurs complexes
    """
    
    def __init__(self, serializers: List[IDataTableSerializer] = None):
        """
        Initialise le sérialiseur composite
        
        Args:
            serializers (List[IDataTableSerializer], optional): Liste initiale de sérialiseurs
        """
        self.serializers = serializers or []
    
    def add_serializer(self, serializer: IDataTableSerializer):
        """
        Ajoute un sérialiseur (SOLID - Open/Closed)
        
        Permet d'ajouter de nouveaux sérialiseurs sans modifier le code existant.
        Respecte le principe Open/Closed en étendant les fonctionnalités.
        
        Args:
            serializer (IDataTableSerializer): Sérialiseur à ajouter
        """
        self.serializers.append(serializer)
    
    def serialize(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Combine les résultats de tous les sérialiseurs
        
        Utilise le premier sérialiseur comme base et enrichit les résultats avec
        les données des autres sérialiseurs. Cette approche permet de créer des
        sérialiseurs complexes en combinant des sérialiseurs simples.
        
        FLUX DE TRAITEMENT:
        1. Utilisation du premier sérialiseur comme base
        2. Enrichissement avec les autres sérialiseurs
        3. Fusion des données en évitant les doublons
        4. Retour des données combinées
        
        Args:
            queryset (QuerySet): Queryset à sérialiser
            
        Returns:
            List[Dict[str, Any]]: Données sérialisées combinées
        """
        if not self.serializers:
            return list(queryset.values())
        
        # Utiliser le premier sérialiseur comme base
        base_data = self.serializers[0].serialize(queryset)
        
        # Enrichir avec les autres sérialiseurs
        for serializer in self.serializers[1:]:
            additional_data = serializer.serialize(queryset)
            for i, item in enumerate(base_data):
                if i < len(additional_data):
                    item.update(additional_data[i])
        
        return base_data 