"""
Optimisations pour le module DataTables

Ce module fournit des mixins et utilitaires pour optimiser les performances
des requêtes DataTable.
"""
from typing import List, Optional, Dict, Any, Set
from django.db.models import QuerySet, ForeignKey, OneToOneField, ManyToManyField
from django.db.models.fields import TextField, BinaryField
from django.core.cache import cache
import hashlib
import logging

logger = logging.getLogger(__name__)


class OptimizedQuerySetMixin:
    """
    Mixin qui applique automatiquement select_related et prefetch_related
    pour optimiser les requêtes et éviter les problèmes N+1.
    
    UTILISATION:
        class MyView(OptimizedQuerySetMixin, QueryModelView):
            model = MyModel
            serializer_class = MySerializer
            
            # Configuration d'optimisation
            select_related_fields = ['warehouse', 'inventory']
            prefetch_related_fields = ['countings', 'job_set']
            only_fields = ['id', 'name', 'status', 'created_at']
            defer_fields = ['description', 'notes']
    """
    
    # À définir dans les vues
    select_related_fields: Optional[List[str]] = None
    prefetch_related_fields: Optional[List[str]] = None
    only_fields: Optional[List[str]] = None
    defer_fields: Optional[List[str]] = None
    
    def get_queryset(self) -> QuerySet:
        """
        Retourne un QuerySet optimisé avec select_related/prefetch_related
        
        Returns:
            QuerySet optimisé
        """
        queryset = super().get_queryset()
        
        # Appliquer select_related pour les ForeignKey
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
        
        # Appliquer prefetch_related pour les ManyToMany/Reverse FK
        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
        
        # Limiter les champs chargés (only)
        if self.only_fields:
            queryset = queryset.only(*self.only_fields)
        
        # Exclure les champs lourds (defer)
        if self.defer_fields:
            queryset = queryset.defer(*self.defer_fields)
        
        return queryset


class PaginationCacheMixin:
    """
    Mixin pour ajouter le cache au count de pagination
    
    UTILISATION:
        class MyProcessor(PaginationCacheMixin, DataTableProcessor):
            pagination_cache_timeout = 300  # 5 minutes par défaut
    """
    
    pagination_cache_timeout: int = 300  # 5 minutes par défaut
    pagination_cache_enabled: bool = True
    
    def _get_pagination_cache_key(self, request, queryset: QuerySet) -> str:
        """
        Génère une clé de cache unique pour la pagination
        
        Args:
            request: Requête HTTP
            queryset: QuerySet à paginer
            
        Returns:
            Clé de cache unique
        """
        # Créer un hash basé sur les paramètres de requête et le queryset
        query_params = dict(request.GET.items())
        query_str = str(sorted(query_params.items()))
        queryset_str = str(queryset.query)
        
        cache_data = f"{query_str}_{queryset_str}"
        cache_hash = hashlib.md5(cache_data.encode()).hexdigest()
        
        return f"datatable_count_{cache_hash}"
    
    def _get_cached_count(self, request, queryset: QuerySet) -> Optional[int]:
        """
        Récupère le count depuis le cache si disponible
        
        Args:
            request: Requête HTTP
            queryset: QuerySet à compter
            
        Returns:
            Count depuis le cache ou None
        """
        if not self.pagination_cache_enabled:
            return None
        
        cache_key = self._get_pagination_cache_key(request, queryset)
        return cache.get(cache_key)
    
    def _set_cached_count(self, request, queryset: QuerySet, count: int):
        """
        Met en cache le count
        
        Args:
            request: Requête HTTP
            queryset: QuerySet compté
            count: Nombre d'éléments
        """
        if not self.pagination_cache_enabled:
            return
        
        cache_key = self._get_pagination_cache_key(request, queryset)
        cache.set(cache_key, count, self.pagination_cache_timeout)
    
    def get_total_count(self, request, queryset: QuerySet) -> int:
        """
        Récupère le count total avec cache
        
        Args:
            request: Requête HTTP
            queryset: QuerySet à compter
            
        Returns:
            Nombre total d'éléments
        """
        # Essayer de récupérer depuis le cache
        cached_count = self._get_cached_count(request, queryset)
        if cached_count is not None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Count récupéré depuis le cache: {cached_count}")
            return cached_count
        
        # Calculer le count
        count = queryset.count()
        
        # Mettre en cache
        self._set_cached_count(request, queryset, count)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Count calculé et mis en cache: {count}")
        
        return count


def optimize_queryset(
    queryset: QuerySet,
    select_related: Optional[List[str]] = None,
    prefetch_related: Optional[List[str]] = None,
    only: Optional[List[str]] = None,
    defer: Optional[List[str]] = None
) -> QuerySet:
    """
    Fonction utilitaire pour optimiser un QuerySet
    
    Args:
        queryset: QuerySet à optimiser
        select_related: Liste de champs pour select_related
        prefetch_related: Liste de champs pour prefetch_related
        only: Liste de champs à charger uniquement
        defer: Liste de champs à exclure
        
    Returns:
        QuerySet optimisé
    """
    # Appliquer select_related en premier
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    # IMPORTANT: Ne pas utiliser only() ou defer() si select_related est déjà appliqué
    # car cela peut créer des conflits (un champ ne peut pas être à la fois différé et traversé)
    # Vérifier si le queryset a déjà des select_related appliqués
    has_existing_select_related = hasattr(queryset.query, 'select_related') and queryset.query.select_related
    
    if only and not has_existing_select_related:
        queryset = queryset.only(*only)
    elif only and has_existing_select_related:
        # Si select_related est déjà appliqué, filtrer only pour exclure les champs select_related
        select_related_fields = set(select_related or [])
        only_filtered = [field for field in only if field not in select_related_fields]
        if only_filtered:
            queryset = queryset.only(*only_filtered)
    
    if defer:
        # Exclure les champs qui sont dans select_related
        select_related_fields = set(select_related or [])
        defer_filtered = [field for field in defer if field not in select_related_fields]
        if defer_filtered:
            queryset = queryset.defer(*defer_filtered)
    
    return queryset


def auto_detect_optimizations(
    model,
    serializer_class=None,
    column_field_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, List[str]]:
    """
    Détecte automatiquement les optimisations à appliquer depuis le modèle et le serializer.
    
    Cette fonction analyse :
    1. Le modèle Django pour détecter les relations (ForeignKey, OneToOneField, ManyToManyField)
    2. Le serializer DRF pour détecter les champs utilisés
    3. Les champs lourds (TextField, BinaryField) à exclure
    4. Le column_field_mapping pour détecter les relations utilisées
    
    Args:
        model: Classe du modèle Django
        serializer_class: Classe du serializer DRF (optionnel)
        column_field_mapping: Mapping des colonnes frontend -> backend (optionnel)
        
    Returns:
        Dict avec les clés: select_related, prefetch_related, only_fields, defer_fields
    """
    if not model:
        return {
            'select_related': [],
            'prefetch_related': [],
            'only_fields': [],
            'defer_fields': []
        }
    
    select_related_fields: Set[str] = set()
    prefetch_related_fields: Set[str] = set()
    only_fields: Set[str] = set()
    defer_fields: Set[str] = set()
    
    try:
        # Analyser le modèle pour détecter les relations
        model_meta = model._meta
        
        # 1. Détecter les ForeignKey et OneToOneField (select_related)
        for field in model_meta.get_fields():
            if isinstance(field, (ForeignKey, OneToOneField)):
                # Vérifier si le champ est utilisé dans le serializer ou column_field_mapping
                field_name = field.name
                if _is_field_used(field_name, serializer_class, column_field_mapping):
                    select_related_fields.add(field_name)
                    
                    # Détecter les relations imbriquées depuis column_field_mapping
                    if column_field_mapping:
                        for col_id, mapped_field in column_field_mapping.items():
                            if mapped_field.startswith(f"{field_name}__"):
                                # Relation imbriquée détectée
                                nested_parts = mapped_field.split("__")
                                if len(nested_parts) >= 2:
                                    # Ajouter la relation directe
                                    select_related_fields.add(field_name)
                                    # Essayer d'ajouter la relation imbriquée si c'est une FK
                                    nested_field_name = nested_parts[1]
                                    try:
                                        related_model = field.related_model
                                        nested_field = related_model._meta.get_field(nested_field_name)
                                        if isinstance(nested_field, (ForeignKey, OneToOneField)):
                                            select_related_fields.add(f"{field_name}__{nested_field_name}")
                                    except:
                                        pass
            
            # 2. Détecter les ManyToManyField (prefetch_related)
            elif isinstance(field, ManyToManyField):
                if _is_field_used(field.name, serializer_class, column_field_mapping):
                    prefetch_related_fields.add(field.name)
        
        # 3. Détecter les relations inverses (reverse relations) depuis le modèle
        # Les relations inverses sont accessibles via model._meta.related_objects
        for related_object in model_meta.related_objects:
            related_name = related_object.get_accessor_name()
            if related_name and _is_field_used(related_name, serializer_class, column_field_mapping):
                prefetch_related_fields.add(related_name)
            
            # 4. Détecter les champs lourds à exclure (defer)
            elif isinstance(field, (TextField, BinaryField)):
                # Ne pas defer si le champ est utilisé
                if not _is_field_used(field.name, serializer_class, column_field_mapping):
                    defer_fields.add(field.name)
        
        # 5. Analyser le serializer pour détecter les champs utilisés
        if serializer_class:
            serializer_fields = _get_serializer_fields(serializer_class)
            # Ajouter les noms des champs du serializer à only_fields
            for field_name in serializer_fields.keys():
                only_fields.add(field_name)
            
            # Détecter les relations dans le serializer
            for field_name, field_instance in serializer_fields.items():
                # Vérifier le source du champ
                source = getattr(field_instance, 'source', field_name)
                if source and source != '*':
                    # Détecter les relations (ex: "warehouse__name")
                    if "__" in source:
                        parts = source.split("__")
                        if len(parts) >= 2:
                            relation_field = parts[0]
                            # Vérifier si c'est une relation dans le modèle
                            try:
                                model_field = model_meta.get_field(relation_field)
                                if isinstance(model_field, (ForeignKey, OneToOneField)):
                                    select_related_fields.add(relation_field)
                                    # Essayer d'ajouter la relation imbriquée
                                    if len(parts) >= 3:
                                        try:
                                            related_model = model_field.related_model
                                            nested_field = related_model._meta.get_field(parts[1])
                                            if isinstance(nested_field, (ForeignKey, OneToOneField)):
                                                select_related_fields.add(f"{relation_field}__{parts[1]}")
                                        except:
                                            pass
                            except:
                                pass
                    else:
                        # Champ direct, l'ajouter à only_fields
                        only_fields.add(source)
        
        # 6. Analyser column_field_mapping pour détecter les relations
        if column_field_mapping:
            for col_id, mapped_field in column_field_mapping.items():
                if "__" in mapped_field:
                    parts = mapped_field.split("__")
                    if len(parts) >= 2:
                        relation_field = parts[0]
                        try:
                            model_field = model_meta.get_field(relation_field)
                            if isinstance(model_field, (ForeignKey, OneToOneField)):
                                select_related_fields.add(relation_field)
                                # Ajouter la relation imbriquée si c'est aussi une FK
                                if len(parts) >= 3:
                                    try:
                                        related_model = model_field.related_model
                                        nested_field = related_model._meta.get_field(parts[1])
                                        if isinstance(nested_field, (ForeignKey, OneToOneField)):
                                            select_related_fields.add(f"{relation_field}__{parts[1]}")
                                    except:
                                        pass
                        except:
                            pass
        
        # 7. Toujours inclure le PK dans only_fields
        if only_fields and model_meta.pk:
            only_fields.add(model_meta.pk.name)
        
        # Convertir les sets en listes triées
        return {
            'select_related': sorted(list(select_related_fields)),
            'prefetch_related': sorted(list(prefetch_related_fields)),
            'only_fields': sorted(list(only_fields)) if only_fields else None,
            'defer_fields': sorted(list(defer_fields)) if defer_fields else None
        }
        
    except Exception as e:
        logger.warning(f"Erreur lors de la détection automatique des optimisations: {str(e)}")
        return {
            'select_related': [],
            'prefetch_related': [],
            'only_fields': None,
            'defer_fields': None
        }


def _is_field_used(field_name: str, serializer_class=None, column_field_mapping: Optional[Dict[str, str]] = None) -> bool:
    """
    Vérifie si un champ est utilisé dans le serializer ou le column_field_mapping.
    
    Args:
        field_name: Nom du champ à vérifier
        serializer_class: Classe du serializer DRF
        column_field_mapping: Mapping des colonnes
        
    Returns:
        True si le champ est utilisé
    """
    # Vérifier dans column_field_mapping
    if column_field_mapping:
        for mapped_field in column_field_mapping.values():
            if mapped_field == field_name or mapped_field.startswith(f"{field_name}__"):
                return True
    
    # Vérifier dans le serializer
    if serializer_class:
        try:
            serializer = serializer_class()
            if hasattr(serializer, 'fields') and field_name in serializer.fields:
                return True
            # Vérifier aussi les sources
            for field_name_serializer, field_instance in serializer.fields.items():
                if hasattr(field_instance, 'source') and field_instance.source:
                    if field_instance.source == field_name or field_instance.source.startswith(f"{field_name}__"):
                        return True
        except:
            pass
    
    return False


def _get_serializer_fields(serializer_class) -> Dict[str, Any]:
    """
    Récupère les champs du serializer.
    
    Args:
        serializer_class: Classe du serializer DRF
        
    Returns:
        Dict des champs du serializer (field_name -> field_instance)
    """
    try:
        # Créer une instance du serializer sans données
        serializer = serializer_class()
        fields = getattr(serializer, 'fields', {})
        
        # Filtrer les SerializerMethodField qui ne nécessitent pas de chargement de données
        # mais garder les autres champs
        return {
            field_name: field_instance
            for field_name, field_instance in fields.items()
            if not hasattr(field_instance, 'method_name') or field_instance.method_name is None
        }
    except Exception as e:
        logger.debug(f"Erreur lors de la récupération des champs du serializer: {str(e)}")
        return {}
