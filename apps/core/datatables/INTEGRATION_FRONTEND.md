# Documentation d'Intégration Frontend/Backend DataTable

## Vue d'ensemble

Cette documentation explique comment intégrer votre package DataTable backend Django avec votre package DataTable frontend JavaScript pour créer une solution complète de tableaux de données.

## Architecture de l'Intégration

```
Frontend (JavaScript)          Backend (Django)
┌─────────────────────┐       ┌─────────────────────┐
│   DataTable Client  │ ────► │ DataTable Server    │
│   - Configuration   │       │ - Configuration     │
│   - Requêtes AJAX   │       │ - Filtrage          │
│   - Rendu UI        │       │ - Pagination        │
│   - Interactions    │       │ - Sérialisation     │
└─────────────────────┘       └─────────────────────┘
```

## 1. Configuration Backend

### 1.1 Vue Django avec DataTable

```python
# views.py
from datatables import ServerSideDataTableView
from .models import Inventory
from .serializers import InventorySerializer
from .filters import InventoryFilter

class InventoryDataTableView(ServerSideDataTableView):
    """Vue DataTable pour les inventaires"""
    
    # Configuration du modèle
    model = Inventory
    serializer_class = InventorySerializer
    filterset_class = InventoryFilter  # Django-Filter optionnel
    
    # Configuration des champs
    search_fields = ['label', 'reference', 'description', 'status']
    order_fields = ['id', 'label', 'reference', 'date', 'status', 'quantity']
    default_order = '-date'
    
    # Configuration de pagination
    page_size = 25
    min_page_size = 5
    max_page_size = 100
    
    # Champs de filtrage automatique
    date_fields = ['date', 'created_at', 'updated_at']
    status_fields = ['status']
    
    def get_datatable_queryset(self):
        """Queryset avec optimisations"""
        return Inventory.objects.select_related('warehouse')\
                               .prefetch_related('stocks')\
                               .filter(is_deleted=False)
```

### 1.2 URL Configuration

```python
# urls.py
from django.urls import path
from .views import InventoryDataTableView

urlpatterns = [
    path('api/inventory/datatable/', 
         InventoryDataTableView.as_view(), 
         name='inventory-datatable'),
]
```

### 1.3 Sérialiseur pour DataTable

```python
# serializers.py
from rest_framework import serializers
from .models import Inventory

class InventoryDataTableSerializer(serializers.ModelSerializer):
    """Sérialiseur optimisé pour DataTable"""
    
    # Champs calculés pour le frontend
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    formatted_date = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'label', 'reference', 'description',
            'status', 'status_display', 'quantity', 
            'warehouse_name', 'formatted_date', 'actions'
        ]
    
    def get_formatted_date(self, obj):
        """Date formatée pour l'affichage"""
        if obj.date:
            return obj.date.strftime('%d/%m/%Y')
        return ''
    
    def get_actions(self, obj):
        """Boutons d'actions pour chaque ligne"""
        request = self.context.get('request')
        user = request.user if request else None
        
        actions = []
        
        # Actions selon les permissions
        if user and user.has_perm('inventory.change_inventory'):
            actions.append({
                'type': 'edit',
                'url': f'/inventory/{obj.id}/edit/',
                'icon': 'fa-edit',
                'title': 'Modifier'
            })
        
        if user and user.has_perm('inventory.delete_inventory'):
            actions.append({
                'type': 'delete',
                'url': f'/api/inventory/{obj.id}/delete/',
                'icon': 'fa-trash',
                'title': 'Supprimer',
                'confirm': True
            })
        
        actions.append({
            'type': 'view',
            'url': f'/inventory/{obj.id}/',
            'icon': 'fa-eye',
            'title': 'Voir détails'
        })
        
        return actions
```

## 2. Configuration Frontend

### 2.1 Initialisation DataTable JavaScript

```javascript
// inventory-datatable.js

class InventoryDataTable {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = this.mergeOptions(options);
        this.table = null;
        this.init();
    }
    
    mergeOptions(userOptions) {
        const defaultOptions = {
            // Configuration de base
            processing: true,
            serverSide: true,
            ajax: {
                url: '/api/inventory/datatable/',
                type: 'GET',
                data: (params) => this.buildRequestParams(params)
            },
            
            // Configuration des colonnes
            columns: [
                {
                    data: 'id',
                    name: 'id',
                    title: 'ID',
                    width: '60px',
                    searchable: false
                },
                {
                    data: 'label',
                    name: 'label', 
                    title: 'Libellé',
                    searchable: true,
                    orderable: true
                },
                {
                    data: 'reference',
                    name: 'reference',
                    title: 'Référence',
                    searchable: true,
                    orderable: true
                },
                {
                    data: 'status_display',
                    name: 'status',
                    title: 'Statut',
                    searchable: false,
                    orderable: true,
                    render: (data, type, row) => this.renderStatus(data, row.status)
                },
                {
                    data: 'quantity',
                    name: 'quantity',
                    title: 'Quantité',
                    searchable: false,
                    orderable: true,
                    render: (data) => this.formatNumber(data)
                },
                {
                    data: 'warehouse_name',
                    name: 'warehouse__name',
                    title: 'Entrepôt',
                    searchable: true,
                    orderable: false
                },
                {
                    data: 'formatted_date',
                    name: 'date',
                    title: 'Date',
                    searchable: false,
                    orderable: true,
                    width: '120px'
                },
                {
                    data: 'actions',
                    name: 'actions',
                    title: 'Actions',
                    searchable: false,
                    orderable: false,
                    width: '120px',
                    render: (data) => this.renderActions(data)
                }
            ],
            
            // Configuration de pagination
            pageLength: 25,
            lengthMenu: [[5, 10, 25, 50, 100], [5, 10, 25, 50, 100]],
            
            // Configuration de tri
            order: [[6, 'desc']], // Tri par date décroissant
            
            // Configuration de recherche
            searchDelay: 500,
            
            // Configuration d'affichage
            responsive: true,
            language: {
                url: '/static/datatables/fr.json'
            },
            
            // Callbacks
            drawCallback: () => this.onDrawCallback(),
            initComplete: () => this.onInitComplete()
        };
        
        return { ...defaultOptions, ...userOptions };
    }
    
    init() {
        this.createFilterForm();
        this.initDataTable();
        this.bindEvents();
    }
    
    initDataTable() {
        this.table = $(this.container).DataTable(this.options);
    }
    
    buildRequestParams(params) {
        // Conversion des paramètres DataTable vers le format attendu par le backend
        const requestParams = {
            // Paramètres DataTable standard
            draw: params.draw,
            start: params.start,
            length: params.length,
            'search[value]': params.search.value,
            'search[regex]': params.search.regex
        };
        
        // Paramètres de tri
        if (params.order && params.order.length > 0) {
            params.order.forEach((orderItem, index) => {
                requestParams[`order[${index}][column]`] = orderItem.column;
                requestParams[`order[${index}][dir]`] = orderItem.dir;
            });
        }
        
        // Paramètres de colonnes
        if (params.columns) {
            params.columns.forEach((column, index) => {
                requestParams[`columns[${index}][data]`] = column.data;
                requestParams[`columns[${index}][name]`] = column.name;
                requestParams[`columns[${index}][searchable]`] = column.searchable;
                requestParams[`columns[${index}][orderable]`] = column.orderable;
                requestParams[`columns[${index}][search][value]`] = column.search.value;
            });
        }
        
        // Ajouter les filtres personnalisés
        this.addCustomFilters(requestParams);
        
        return requestParams;
    }
    
    addCustomFilters(params) {
        // Récupérer les valeurs des filtres personnalisés
        const filterForm = document.getElementById('datatable-filters');
        if (filterForm) {
            const formData = new FormData(filterForm);
            
            // Filtre par statut
            const status = formData.get('status');
            if (status) {
                params['status'] = status;
            }
            
            // Filtre par plage de dates
            const dateStart = formData.get('date_start');
            const dateEnd = formData.get('date_end');
            if (dateStart) params['date_start'] = dateStart;
            if (dateEnd) params['date_end'] = dateEnd;
            
            // Filtre par entrepôt
            const warehouse = formData.get('warehouse');
            if (warehouse) {
                params['warehouse'] = warehouse;
            }
        }
    }
    
    createFilterForm() {
        const filterHtml = `
            <div id="datatable-filters" class="row mb-3">
                <div class="col-md-3">
                    <label for="status-filter">Statut</label>
                    <select id="status-filter" name="status" class="form-control">
                        <option value="">Tous les statuts</option>
                        <option value="active">Actif</option>
                        <option value="inactive">Inactif</option>
                        <option value="pending">En attente</option>
                    </select>
                </div>
                
                <div class="col-md-3">
                    <label for="date-start">Date début</label>
                    <input type="date" id="date-start" name="date_start" class="form-control">
                </div>
                
                <div class="col-md-3">
                    <label for="date-end">Date fin</label>
                    <input type="date" id="date-end" name="date_end" class="form-control">
                </div>
                
                <div class="col-md-3">
                    <label for="warehouse-filter">Entrepôt</label>
                    <select id="warehouse-filter" name="warehouse" class="form-control">
                        <option value="">Tous les entrepôts</option>
                        <!-- Options chargées dynamiquement -->
                    </select>
                </div>
                
                <div class="col-12 mt-2">
                    <button type="button" id="apply-filters" class="btn btn-primary">
                        <i class="fa fa-filter"></i> Appliquer les filtres
                    </button>
                    <button type="button" id="reset-filters" class="btn btn-secondary">
                        <i class="fa fa-times"></i> Réinitialiser
                    </button>
                </div>
            </div>
        `;
        
        // Insérer le formulaire avant le tableau
        this.container.insertAdjacentHTML('beforebegin', filterHtml);
        
        // Charger les options des select
        this.loadWarehouseOptions();
    }
    
    bindEvents() {
        // Événements pour les filtres
        document.getElementById('apply-filters').addEventListener('click', () => {
            this.table.ajax.reload();
        });
        
        document.getElementById('reset-filters').addEventListener('click', () => {
            this.resetFilters();
        });
        
        // Événements pour les actions sur les lignes
        $(this.container).on('click', '.action-btn', (e) => {
            this.handleRowAction(e);
        });
        
        // Auto-refresh optionnel
        if (this.options.autoRefresh) {
            setInterval(() => {
                this.table.ajax.reload(null, false); // false = garder la pagination
            }, this.options.autoRefresh * 1000);
        }
    }
    
    renderStatus(statusDisplay, statusValue) {
        const statusClasses = {
            'active': 'badge-success',
            'inactive': 'badge-danger', 
            'pending': 'badge-warning'
        };
        
        const cssClass = statusClasses[statusValue] || 'badge-secondary';
        return `<span class="badge ${cssClass}">${statusDisplay}</span>`;
    }
    
    renderActions(actions) {
        if (!actions || actions.length === 0) {
            return '';
        }
        
        let html = '<div class="btn-group" role="group">';
        
        actions.forEach(action => {
            const confirmAttr = action.confirm ? 
                `onclick="return confirm('Êtes-vous sûr ?')"` : '';
            
            html += `
                <button type="button" 
                        class="btn btn-sm btn-outline-primary action-btn" 
                        data-action="${action.type}"
                        data-url="${action.url}"
                        title="${action.title}"
                        ${confirmAttr}>
                    <i class="fa ${action.icon}"></i>
                </button>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    formatNumber(number) {
        if (number === null || number === undefined) return '';
        return new Intl.NumberFormat('fr-FR').format(number);
    }
    
    handleRowAction(event) {
        const button = event.currentTarget;
        const action = button.dataset.action;
        const url = button.dataset.url;
        
        switch (action) {
            case 'edit':
                window.location.href = url;
                break;
                
            case 'delete':
                this.deleteRow(url, button);
                break;
                
            case 'view':
                window.open(url, '_blank');
                break;
                
            default:
                console.warn('Action non reconnue:', action);
        }
    }
    
    deleteRow(url, button) {
        fetch(url, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                this.table.ajax.reload();
                this.showNotification('Élément supprimé avec succès', 'success');
            } else {
                throw new Error('Erreur lors de la suppression');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            this.showNotification('Erreur lors de la suppression', 'error');
        });
    }
    
    resetFilters() {
        document.getElementById('datatable-filters').reset();
        this.table.ajax.reload();
    }
    
    loadWarehouseOptions() {
        fetch('/api/warehouses/')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('warehouse-filter');
                data.results.forEach(warehouse => {
                    const option = document.createElement('option');
                    option.value = warehouse.id;
                    option.textContent = warehouse.name;
                    select.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Erreur lors du chargement des entrepôts:', error);
            });
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
    
    showNotification(message, type) {
        // Implémentation de votre système de notifications
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
    
    onDrawCallback() {
        // Callback appelé après chaque rendu du tableau
        console.log('Tableau rendu');
    }
    
    onInitComplete() {
        // Callback appelé après l'initialisation complète
        console.log('DataTable initialisé');
    }
    
    // Méthodes publiques pour l'API
    refresh() {
        this.table.ajax.reload();
    }
    
    getSelectedRows() {
        return this.table.rows('.selected').data().toArray();
    }
    
    exportData(format = 'csv') {
        const params = this.table.ajax.params();
        params.export = format;
        
        const url = `/api/inventory/datatable/?${new URLSearchParams(params)}`;
        window.open(url, '_blank');
    }
}
```

### 2.2 Utilisation dans une page HTML

```html
<!-- inventory.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Gestion des Inventaires</title>
    
    <!-- CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="card-title mb-0">
                            <i class="fa fa-boxes"></i> Gestion des Inventaires
                        </h5>
                        <div>
                            <button type="button" class="btn btn-success" onclick="inventoryTable.exportData('csv')">
                                <i class="fa fa-download"></i> Export CSV
                            </button>
                            <button type="button" class="btn btn-primary" onclick="inventoryTable.refresh()">
                                <i class="fa fa-refresh"></i> Actualiser
                            </button>
                            <a href="/inventory/create/" class="btn btn-primary">
                                <i class="fa fa-plus"></i> Nouvel inventaire
                            </a>
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <!-- Le formulaire de filtres sera inséré ici automatiquement -->
                        
                        <!-- Tableau DataTable -->
                        <table id="inventory-table" class="table table-striped table-hover">
                            <thead>
                                <!-- Les en-têtes seront générées automatiquement -->
                            </thead>
                            <tbody>
                                <!-- Les données seront chargées via AJAX -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- JavaScript -->
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Votre script DataTable -->
    <script src="/static/js/inventory-datatable.js"></script>
    
    <script>
        // Initialisation du DataTable
        const inventoryTable = new InventoryDataTable('inventory-table', {
            autoRefresh: 30, // Actualisation automatique toutes les 30 secondes
            pageLength: 50   // 50 éléments par page par défaut
        });
    </script>
</body>
</html>
```

## 3. Gestion des Erreurs

### 3.1 Côté Backend

```python
# views.py - Gestion d'erreurs améliorée
class InventoryDataTableView(ServerSideDataTableView):
    def handle_exception(self, exc):
        """Gestion personnalisée des erreurs"""
        logger.error(f"Erreur DataTable: {str(exc)}", exc_info=True)
        
        if isinstance(exc, ValidationError):
            return JsonResponse({
                'error': 'Données invalides',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
            }, status=400)
        
        elif isinstance(exc, PermissionDenied):
            return JsonResponse({
                'error': 'Accès refusé'
            }, status=403)
        
        else:
            return JsonResponse({
                'error': 'Erreur interne du serveur'
            }, status=500)
```

### 3.2 Côté Frontend

```javascript
// Gestion d'erreurs AJAX
buildRequestParams(params) {
    // ... code existant ...
    
    // Ajouter la gestion d'erreurs AJAX
    this.options.ajax.error = (xhr, error, thrown) => {
        this.handleAjaxError(xhr, error, thrown);
    };
    
    return requestParams;
}

handleAjaxError(xhr, error, thrown) {
    let message = 'Erreur lors du chargement des données';
    
    if (xhr.responseJSON && xhr.responseJSON.error) {
        message = xhr.responseJSON.error;
    } else if (xhr.status === 403) {
        message = 'Accès refusé';
    } else if (xhr.status === 500) {
        message = 'Erreur interne du serveur';
    }
    
    this.showNotification(message, 'error');
    console.error('Erreur AJAX:', { xhr, error, thrown });
}
```

## 4. Tests d'Intégration

### 4.1 Tests Backend

```python
# tests/test_datatable_integration.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

class DataTableIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.login(username='testuser', password='testpass')
        
    def test_datatable_request_format(self):
        """Test du format de requête DataTable"""
        params = {
            'draw': 1,
            'start': 0,
            'length': 10,
            'search[value]': 'test',
            'order[0][column]': 1,
            'order[0][dir]': 'asc'
        }
        
        response = self.client.get(
            reverse('inventory-datatable'),
            params
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Vérifier le format de réponse DataTable
        self.assertIn('draw', data)
        self.assertIn('recordsTotal', data)
        self.assertIn('recordsFiltered', data)
        self.assertIn('data', data)
        
    def test_rest_api_request_format(self):
        """Test du format de requête REST API"""
        params = {
            'page': 1,
            'page_size': 10,
            'search': 'test',
            'ordering': 'label'
        }
        
        response = self.client.get(
            reverse('inventory-datatable'),
            params
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Vérifier le format de réponse REST API
        self.assertIn('count', data)
        self.assertIn('results', data)
```

### 4.2 Tests Frontend (Jest)

```javascript
// tests/inventory-datatable.test.js
import InventoryDataTable from '../inventory-datatable.js';

describe('InventoryDataTable', () => {
    let mockContainer;
    
    beforeEach(() => {
        // Setup DOM mock
        mockContainer = document.createElement('table');
        mockContainer.id = 'test-table';
        document.body.appendChild(mockContainer);
    });
    
    afterEach(() => {
        document.body.removeChild(mockContainer);
    });
    
    test('should initialize with default options', () => {
        const dataTable = new InventoryDataTable('test-table');
        
        expect(dataTable.options.processing).toBe(true);
        expect(dataTable.options.serverSide).toBe(true);
        expect(dataTable.options.pageLength).toBe(25);
    });
    
    test('should build correct request parameters', () => {
        const dataTable = new InventoryDataTable('test-table');
        
        const mockParams = {
            draw: 1,
            start: 0,
            length: 10,
            search: { value: 'test', regex: false },
            order: [{ column: 1, dir: 'asc' }]
        };
        
        const requestParams = dataTable.buildRequestParams(mockParams);
        
        expect(requestParams.draw).toBe(1);
        expect(requestParams.start).toBe(0);
        expect(requestParams.length).toBe(10);
        expect(requestParams['search[value]']).toBe('test');
        expect(requestParams['order[0][column]']).toBe(1);
        expect(requestParams['order[0][dir]']).toBe('asc');
    });
});
```

## 5. Performance et Optimisations

### 5.1 Optimisations Backend

```python
# views.py - Optimisations
class OptimizedInventoryDataTableView(ServerSideDataTableView):
    def get_datatable_queryset(self):
        """Queryset optimisé avec mise en cache"""
        cache_key = f"inventory_queryset_{self.request.user.id}"
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = Inventory.objects.select_related(
                'warehouse', 'category'
            ).prefetch_related(
                'stocks', 'tags'
            ).annotate(
                stock_count=Count('stocks'),
                last_movement=Max('movements__date')
            ).filter(is_deleted=False)
            
            cache.set(cache_key, queryset, 300)  # Cache 5 minutes
        
        return queryset
```

### 5.2 Optimisations Frontend

```javascript
// Optimisations côté client
class OptimizedInventoryDataTable extends InventoryDataTable {
    constructor(containerId, options = {}) {
        super(containerId, options);
        
        // Cache des données côté client
        this.cache = new Map();
        this.cacheTimeout = 60000; // 1 minute
    }
    
    buildRequestParams(params) {
        const requestParams = super.buildRequestParams(params);
        
        // Vérifier le cache avant la requête
        const cacheKey = JSON.stringify(requestParams);
        const cachedData = this.cache.get(cacheKey);
        
        if (cachedData && Date.now() - cachedData.timestamp < this.cacheTimeout) {
            // Utiliser les données en cache
            return cachedData.params;
        }
        
        return requestParams;
    }
    
    // Debouncing pour la recherche
    setupSearchDebouncing() {
        let searchTimeout;
        
        $(this.container).on('search.dt', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.table.ajax.reload();
            }, 500);
        });
    }
}
```

## 6. Sécurité

### 6.1 Protection CSRF

```javascript
// Ajouter le token CSRF à toutes les requêtes
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
        }
    }
});

function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}
```

### 6.2 Validation côté Backend

```python
# views.py - Validation de sécurité
class SecureInventoryDataTableView(ServerSideDataTableView):
    def get_datatable_queryset(self):
        """Queryset filtré par permissions utilisateur"""
        base_queryset = super().get_datatable_queryset()
        
        # Filtrer selon les permissions utilisateur
        if not self.request.user.is_superuser:
            if self.request.user.groups.filter(name='Managers').exists():
                # Managers voient leur département
                base_queryset = base_queryset.filter(
                    warehouse__department=self.request.user.profile.department
                )
            else:
                # Utilisateurs normaux voient seulement leurs propres données
                base_queryset = base_queryset.filter(
                    created_by=self.request.user
                )
        
        return base_queryset
```

## 7. Déploiement

### 7.1 Configuration de Production

```python
# settings/production.py
# Configuration pour la production

# Cache Redis pour les DataTables
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Logging pour DataTable
LOGGING = {
    'version': 1,
    'handlers': {
        'datatable_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/datatable.log',
        },
    },
    'loggers': {
        'datatables': {
            'handlers': ['datatable_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 7.2 Configuration Nginx

```nginx
# nginx.conf - Configuration pour DataTable
location /api/inventory/datatable/ {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # Cache pour les requêtes GET
    proxy_cache datatable_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

Cette documentation vous donne une base complète pour intégrer vos deux packages DataTable. L'architecture est flexible et peut être adaptée selon vos besoins spécifiques.
