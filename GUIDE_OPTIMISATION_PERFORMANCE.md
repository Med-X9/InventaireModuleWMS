# 🚀 GUIDE D'OPTIMISATION DES PERFORMANCES

## Vue d'ensemble

Ce guide présente des recommandations concrètes pour améliorer les performances de chaque application Django du projet InventaireModuleWMS.

---

## 📦 APPLICATION: INVENTORY

### 🔴 Problèmes identifiés

1. **Requêtes N+1 potentielles** dans certains repositories
2. **Absence de cache** pour les données fréquemment consultées
3. **Pas d'indexation** sur certains champs fréquemment filtrés
4. **Sérialisation lourde** avec beaucoup de relations imbriquées
5. **Transactions longues** dans certains services

### ✅ Recommandations d'optimisation

#### 1. Optimisation des requêtes dans les repositories

**Problème**: Certaines méthodes ne utilisent pas `select_related` ou `prefetch_related`.

**Solution**: Ajouter des optimisations dans `inventory_repository.py`:

```python
# apps/inventory/repositories/inventory_repository.py

def get_all(self) -> List[Any]:
    """Récupère tous les inventaires avec relations préchargées"""
    return Inventory.objects.filter(is_deleted=False)\
        .select_related('account')\
        .prefetch_related('awi_links__warehouse')\
        .order_by('-created_at')

def get_by_id(self, inventory_id: int) -> Any:
    """Récupère un inventaire avec toutes ses relations"""
    try:
        return Inventory.objects.filter(is_deleted=False)\
            .select_related('account')\
            .prefetch_related(
                'awi_links__warehouse',
                'countings',
                'setting_set'
            )\
            .get(id=inventory_id)
    except Inventory.DoesNotExist:
        raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas.")
```

#### 2. Ajout de cache pour les données fréquemment consultées

**Solution**: Implémenter un cache Redis pour les inventaires actifs:

```python
# apps/inventory/services/inventory_service.py

from django.core.cache import cache
from django.conf import settings

class InventoryService:
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def get_active_inventories_cached(self):
        """Récupère les inventaires actifs avec cache"""
        cache_key = 'active_inventories'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            inventories = self.repository.get_all()
            serialized = InventorySerializer(inventories, many=True).data
            cache.set(cache_key, serialized, self.CACHE_TIMEOUT)
            return serialized
        
        return cached_data
    
    def invalidate_inventory_cache(self, inventory_id=None):
        """Invalide le cache des inventaires"""
        cache.delete('active_inventories')
        if inventory_id:
            cache.delete(f'inventory_{inventory_id}')
```

#### 3. Optimisation des index de base de données

**Solution**: Créer une migration pour ajouter des index:

```python
# apps/inventory/migrations/0012_add_performance_indexes.py

from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0011_comptagesequence_reference'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_inventory_status_deleted ON inventory_inventory(status, is_deleted);",
            reverse_sql="DROP INDEX IF EXISTS idx_inventory_status_deleted;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_job_inventory_warehouse ON inventory_job(inventory_id, warehouse_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_job_inventory_warehouse;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_job_status ON inventory_job(status);",
            reverse_sql="DROP INDEX IF EXISTS idx_job_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_assignment_job_counting ON inventory_assigment(job_id, counting_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_assignment_job_counting;"
        ),
    ]
```

#### 4. Optimisation de la pagination

**Solution**: Utiliser `cursor pagination` pour les grandes listes:

```python
# apps/inventory/views/inventory_views.py

from rest_framework.pagination import CursorPagination

class InventoryCursorPagination(CursorPagination):
    page_size = 50
    ordering = '-created_at'
    page_size_query_param = 'page_size'
    max_page_size = 200
```

#### 5. Optimisation des serializers avec `to_representation`

**Solution**: Utiliser `Prefetch` dans les serializers:

```python
# apps/inventory/serializers/inventory_serializer.py

class InventoryDetailSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        # Précharger les relations avant la sérialisation
        instance = Inventory.objects.prefetch_related(
            'countings',
            'awi_links__warehouse',
            'setting_set'
        ).get(id=instance.id)
        
        return super().to_representation(instance)
```

#### 6. Utilisation de `bulk_create` et `bulk_update`

**Solution**: Optimiser les opérations en masse:

```python
# apps/inventory/services/job_service.py

@transaction.atomic
def create_multiple_jobs(self, jobs_data):
    """Crée plusieurs jobs en une seule transaction"""
    jobs = [Job(**data) for data in jobs_data]
    created_jobs = Job.objects.bulk_create(jobs, batch_size=100)
    return created_jobs

@transaction.atomic
def update_multiple_jobs_status(self, job_ids, status):
    """Met à jour le statut de plusieurs jobs"""
    Job.objects.filter(id__in=job_ids).update(status=status)
```

#### 7. Ajout de monitoring avec Django Debug Toolbar (dev) et Sentry (prod)

**Solution**: Configurer le monitoring:

```python
# project/settings/base.py

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Pour la production
import sentry_sdk
sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    traces_sample_rate=0.1,
)
```

### 📊 Métriques de performance attendues

- **Réduction des requêtes DB**: 70-80% (de 50+ à 5-10 requêtes par page)
- **Temps de réponse**: < 200ms pour les listes, < 100ms pour les détails
- **Throughput**: +300% de requêtes par seconde

---

## 📦 APPLICATION: MASTERDATA

### 🔴 Problèmes identifiés

1. **21 modèles** avec beaucoup de relations - risque de requêtes N+1
2. **Peu d'optimisations** dans les repositories
3. **Pas de cache** pour les données de référence
4. **Requêtes lourdes** pour les emplacements non affectés

### ✅ Recommandations d'optimisation

#### 1. Optimisation des requêtes pour les emplacements

**Solution**: Améliorer `UnassignedLocationsView`:

```python
# apps/masterdata/views/location_views.py

class UnassignedLocationsView(ServerSideDataTableView):
    def get_datatable_queryset(self):
        """Optimisé avec seulement les champs nécessaires"""
        warehouse_id = self.kwargs.get('warehouse_id')
        account_id = self.kwargs.get('account_id')
        inventory_id = self.kwargs.get('inventory_id')

        # Utiliser values_list pour éviter de charger tous les objets
        assigned_location_ids = JobDetail.objects.filter(
            job__inventory_id=inventory_id,
            location_id__isnull=False,
        ).values_list('location_id', flat=True)

        queryset = Location.objects.filter(
            is_active=True,
            sous_zone__zone__warehouse_id=warehouse_id,
            regroupement__account_id=account_id,
        ).exclude(id__in=assigned_location_ids)\
         .select_related(
             'sous_zone',
             'sous_zone__zone',
             'sous_zone__zone__warehouse',
             'location_type',
             'regroupement',
             'regroupement__account',
         )\
         .prefetch_related(
             'stock_set__product__Product_Family'
         )\
         .only(
             'id', 'location_reference', 'sous_zone', 
             'location_type', 'regroupement'
         )

        return queryset
```

#### 2. Cache pour les données de référence

**Solution**: Mettre en cache les warehouses, zones, produits:

```python
# apps/masterdata/services/warehouse_service.py

from django.core.cache import cache

class WarehouseService:
    CACHE_TIMEOUT = 3600  # 1 heure pour les données de référence
    
    def get_all_cached(self):
        """Récupère tous les warehouses avec cache"""
        cache_key = 'all_warehouses'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            warehouses = self.repository.get_all()
            serialized = WarehouseSerializer(warehouses, many=True).data
            cache.set(cache_key, serialized, self.CACHE_TIMEOUT)
            return serialized
        
        return cached_data
    
    def invalidate_cache(self):
        """Invalide le cache des warehouses"""
        cache.delete('all_warehouses')
```

#### 3. Optimisation des index pour les recherches fréquentes

**Solution**: Ajouter des index composites:

```python
# apps/masterdata/migrations/0009_add_performance_indexes.py

from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('masterdata', '0008_...'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_location_active_warehouse ON masterdata_location(is_active, sous_zone_id) WHERE is_active = true;",
            reverse_sql="DROP INDEX IF EXISTS idx_location_active_warehouse;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_stock_location_product ON masterdata_stock(location_id, product_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_stock_location_product;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_family_status ON masterdata_product(Product_Family_id, Product_Status);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_family_status;"
        ),
    ]
```

#### 4. Utilisation de `annotate` pour éviter les requêtes multiples

**Solution**: Calculer les statistiques en une seule requête:

```python
# apps/masterdata/services/location_service.py

from django.db.models import Count, Q

def get_locations_with_stats(self, warehouse_id):
    """Récupère les emplacements avec statistiques en une requête"""
    return Location.objects.filter(
        sous_zone__zone__warehouse_id=warehouse_id,
        is_active=True
    ).select_related('sous_zone', 'location_type')\
     .annotate(
         total_stocks=Count('stock_set'),
         active_stocks=Count('stock_set', filter=Q(stock_set__quantity_available__gt=0))
     )
```

#### 5. Optimisation des imports en masse

**Solution**: Utiliser `bulk_create` avec `ignore_conflicts`:

```python
# apps/masterdata/services/import_service.py

def import_products_bulk(self, products_data):
    """Importe les produits en masse de manière optimisée"""
    products = [Product(**data) for data in products_data]
    
    # Utiliser bulk_create avec ignore_conflicts pour éviter les erreurs
    created = Product.objects.bulk_create(
        products, 
        batch_size=500,
        ignore_conflicts=True
    )
    
    return created
```

### 📊 Métriques de performance attendues

- **Réduction des requêtes DB**: 60-70%
- **Temps de réponse**: < 150ms pour les listes
- **Cache hit rate**: > 80% pour les données de référence

---

## 📦 APPLICATION: MOBILE

### 🔴 Problèmes identifiés

1. **Synchronisation lourde** - beaucoup de données transférées
2. **Pas de pagination** pour les grandes listes
3. **Pas de compression** des réponses
4. **Requêtes multiples** pour la synchronisation

### ✅ Recommandations d'optimisation

#### 1. Optimisation de la synchronisation

**Solution**: Implémenter une synchronisation incrémentale:

```python
# apps/mobile/services/sync_service.py

class SyncService:
    def sync_data_incremental(self, user_id, last_sync_timestamp=None):
        """Synchronise uniquement les données modifiées depuis la dernière sync"""
        if last_sync_timestamp:
            # Synchronisation incrémentale
            inventories = Inventory.objects.filter(
                status='EN REALISATION',
                updated_at__gte=last_sync_timestamp
            ).select_related('account')\
             .prefetch_related('countings')
        else:
            # Synchronisation complète
            inventories = self.repository.get_inventories_by_user_assignments(user_id)
        
        # Utiliser only() pour limiter les champs retournés
        jobs = Job.objects.filter(
            inventory__in=inventories,
            status__in=['TRANSFERT', 'ENTAME']
        ).only(
            'id', 'reference', 'status', 'inventory_id', 
            'warehouse_id', 'created_at', 'updated_at'
        ).prefetch_related('jobdetail_set__location')
        
        return {
            'inventories': InventorySerializer(inventories, many=True).data,
            'jobs': JobSerializer(jobs, many=True).data,
            'sync_timestamp': timezone.now().isoformat()
        }
```

#### 2. Pagination pour les grandes listes

**Solution**: Ajouter une pagination cursor:

```python
# apps/mobile/views/user/user_products_view.py

from rest_framework.pagination import CursorPagination

class MobileCursorPagination(CursorPagination):
    page_size = 100
    ordering = '-id'
    page_size_query_param = 'page_size'
    max_page_size = 500

class UserProductsView(APIView):
    pagination_class = MobileCursorPagination
    
    def get(self, request, user_id):
        products = self.get_queryset(user_id)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(products, request)
        
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
```

#### 3. Compression des réponses

**Solution**: Activer la compression Gzip:

```python
# project/settings/base.py

MIDDLEWARE = [
    # ... autres middlewares
    'django.middleware.gzip.GZipMiddleware',  # Ajouter en premier
    # ...
]

# Ou utiliser nginx pour la compression
```

#### 4. Optimisation des serializers mobiles

**Solution**: Créer des serializers légers pour mobile:

```python
# apps/mobile/serializers/light_serializers.py

class LightProductSerializer(serializers.ModelSerializer):
    """Serializer léger pour mobile - seulement les champs essentiels"""
    class Meta:
        model = Product
        fields = ('id', 'reference', 'Short_Description', 'Barcode')
        read_only_fields = fields

class LightLocationSerializer(serializers.ModelSerializer):
    """Serializer léger pour les emplacements"""
    class Meta:
        model = Location
        fields = ('id', 'location_reference', 'sous_zone_id')
        read_only_fields = fields
```

#### 5. Cache pour les données statiques

**Solution**: Mettre en cache les produits et emplacements:

```python
# apps/mobile/services/user_service.py

from django.core.cache import cache

class UserService:
    def get_user_products_cached(self, user_id):
        """Récupère les produits avec cache"""
        cache_key = f'user_{user_id}_products'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            products = self.repository.get_user_products(user_id)
            serialized = LightProductSerializer(products, many=True).data
            cache.set(cache_key, serialized, 1800)  # 30 minutes
            return serialized
        
        return cached_data
```

#### 6. Optimisation des uploads

**Solution**: Utiliser des transactions batch pour les uploads:

```python
# apps/mobile/services/counting_detail_service.py

from django.db import transaction

@transaction.atomic
def bulk_create_counting_details(self, details_data, batch_size=100):
    """Crée plusieurs counting details en batch"""
    counting_details = []
    
    for data in details_data:
        counting_details.append(CountingDetail(**data))
        
        if len(counting_details) >= batch_size:
            CountingDetail.objects.bulk_create(counting_details)
            counting_details = []
    
    if counting_details:
        CountingDetail.objects.bulk_create(counting_details)
```

### 📊 Métriques de performance attendues

- **Taille des réponses**: -60% avec compression et serializers légers
- **Temps de synchronisation**: -50% avec sync incrémentale
- **Bande passante**: -70% avec pagination et cache

---

## 📦 APPLICATION: USERS

### 🔴 Problèmes identifiés

1. **Pas de repository pattern** - accès direct aux modèles
2. **Pas de cache** pour les tokens
3. **Pas de rate limiting** avancé

### ✅ Recommandations d'optimisation

#### 1. Implémentation du repository pattern

**Solution**: Créer un repository pour les utilisateurs:

```python
# apps/users/repositories/user_repository.py

from typing import Optional
from ..models import UserApp

class UserRepository:
    """Repository pour l'accès aux données utilisateurs"""
    
    def get_by_id(self, user_id: int) -> Optional[UserApp]:
        """Récupère un utilisateur par ID"""
        try:
            return UserApp.objects.select_related().get(id=user_id)
        except UserApp.DoesNotExist:
            return None
    
    def get_by_username(self, username: str) -> Optional[UserApp]:
        """Récupère un utilisateur par username"""
        try:
            return UserApp.objects.select_related().get(username=username)
        except UserApp.DoesNotExist:
            return None
    
    def get_mobile_users_by_inventory(self, inventory_id: int):
        """Récupère les utilisateurs mobiles pour un inventaire"""
        return UserApp.objects.filter(
            type='MOBILE',
            # Ajouter la logique de filtrage par inventaire
        ).select_related()
```

#### 2. Cache pour les tokens JWT

**Solution**: Utiliser Redis pour le cache des tokens:

```python
# apps/users/services/auth_service.py

from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

class AuthService:
    TOKEN_CACHE_TIMEOUT = 3600  # 1 heure
    
    def generate_tokens_cached(self, user):
        """Génère des tokens avec cache"""
        cache_key = f'user_tokens_{user.id}'
        cached_tokens = cache.get(cache_key)
        
        if cached_tokens:
            return cached_tokens
        
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        cache.set(cache_key, tokens, self.TOKEN_CACHE_TIMEOUT)
        return tokens
```

#### 3. Optimisation du rate limiting

**Solution**: Utiliser django-ratelimit avec Redis:

```python
# apps/users/views/auth_throttle_views.py

from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='post')
class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Vue avec rate limiting optimisé"""
    pass
```

### 📊 Métriques de performance attendues

- **Temps de réponse auth**: < 50ms
- **Cache hit rate**: > 90% pour les tokens
- **Réduction des requêtes DB**: 80% pour les authentifications

---

## 🔧 OPTIMISATIONS GLOBALES

### 1. Configuration de la base de données

```python
# project/settings/base.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30 secondes
        },
        'CONN_MAX_AGE': 600,  # Réutiliser les connexions
    }
}
```

### 2. Configuration du cache Redis

```python
# project/settings/base.py

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'inventaire',
        'TIMEOUT': 300,
    }
}
```

### 3. Middleware de performance

```python
# project/middleware/performance.py

import time
from django.utils.deprecation import MiddlewareMixin

class PerformanceMiddleware(MiddlewareMixin):
    """Middleware pour mesurer les performances"""
    
    def process_request(self, request):
        request._start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            response['X-Process-Time'] = f'{duration:.3f}'
            
            # Logger les requêtes lentes (> 1 seconde)
            if duration > 1.0:
                import logging
                logger = logging.getLogger('performance')
                logger.warning(
                    f'Slow request: {request.path} took {duration:.3f}s'
                )
        
        return response
```

### 4. Monitoring avec Django Silk (développement)

```python
# project/settings/dev.py

INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

# URLs pour Silk
if DEBUG:
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
```

### 5. Optimisation des migrations

```python
# Créer des index en parallèle
# Utiliser RunPython pour les migrations complexes
# Éviter les migrations qui bloquent la table entière
```

---

## 📈 PLAN D'IMPLÉMENTATION

### Phase 1: Optimisations critiques (Semaine 1-2)
1. ✅ Ajouter `select_related` et `prefetch_related` dans tous les repositories
2. ✅ Créer les index de base de données essentiels
3. ✅ Implémenter le cache Redis pour les données fréquentes

### Phase 2: Optimisations importantes (Semaine 3-4)
1. ✅ Optimiser les serializers avec `only()` et `defer()`
2. ✅ Implémenter la pagination cursor
3. ✅ Ajouter la compression Gzip

### Phase 3: Optimisations avancées (Semaine 5-6)
1. ✅ Synchronisation incrémentale pour mobile
2. ✅ Monitoring et profiling
3. ✅ Optimisation des transactions

---

## 🧪 TESTS DE PERFORMANCE

### Outils recommandés

1. **Django Debug Toolbar** - Pour le développement
2. **Django Silk** - Profiling avancé
3. **Locust** - Tests de charge
4. **Apache Bench (ab)** - Tests simples
5. **New Relic / Datadog** - Monitoring production

### Script de test de charge

```python
# tests/performance/test_load.py

from locust import HttpUser, task, between

class InventoryUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def list_inventories(self):
        self.client.get("/web/api/inventory/")
    
    @task(2)
    def get_inventory_detail(self):
        self.client.get("/web/api/inventory/1/edit/")
    
    @task(1)
    def list_jobs(self):
        self.client.get("/web/api/jobs/list/")
```

---

## 📝 CHECKLIST D'OPTIMISATION

### Pour chaque endpoint:
- [ ] Utilise `select_related` pour les ForeignKey
- [ ] Utilise `prefetch_related` pour les ManyToMany et reverse ForeignKey
- [ ] Utilise `only()` pour limiter les champs chargés
- [ ] Pagination implémentée pour les listes
- [ ] Cache configuré si les données changent rarement
- [ ] Index de base de données sur les champs filtrés
- [ ] Compression activée
- [ ] Monitoring configuré

---

*Guide créé le: $(date)*
*Version: 1.0*


