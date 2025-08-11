# Documentation Frontend - Opérateurs de Filtre DataTable

## 📋 Vue d'ensemble

Ce document liste tous les opérateurs de filtre disponibles pour votre frontend DataTable. Chaque opérateur peut être utilisé dans les paramètres de requête GET.

## 🔤 Opérateurs pour les Chaînes (StringFilter)

### Champs supportés : `CharField`, `TextField`, `EmailField`, `URLField`

| Opérateur | Description | Exemple | URL |
|-----------|-------------|---------|-----|
| `exact` | Correspondance exacte | `label_exact=FM5` | `GET /api/inventory/?label_exact=FM5` |
| `contains` | Contient le terme | `label_contains=FM` | `GET /api/inventory/?label_contains=FM` |
| `startswith` | Commence par | `label_startswith=FM` | `GET /api/inventory/?label_startswith=FM` |
| `endswith` | Termine par | `label_endswith=5` | `GET /api/inventory/?label_endswith=5` |
| `icontains` | Contient (insensible à la casse) | `label_icontains=fm5` | `GET /api/inventory/?label_icontains=fm5` |
| `istartswith` | Commence par (insensible à la casse) | `label_istartswith=fm` | `GET /api/inventory/?label_istartswith=fm` |
| `iendswith` | Termine par (insensible à la casse) | `label_iendswith=5` | `GET /api/inventory/?label_iendswith=5` |
| `regex` | Expression régulière | `label_regex=^FM[0-9]+$` | `GET /api/inventory/?label_regex=^FM[0-9]+$` |
| `iregex` | Expression régulière (insensible à la casse) | `label_iregex=^fm[0-9]+$` | `GET /api/inventory/?label_iregex=^fm[0-9]+$` |

### Exemples d'utilisation frontend :

```javascript
// Recherche exacte
const exactSearch = {
    'label_exact': 'FM5'
};

// Recherche contenant
const containsSearch = {
    'label_contains': 'FM'
};

// Recherche commençant par
const startsWithSearch = {
    'label_startswith': 'FM'
};

// Recherche insensible à la casse
const caseInsensitiveSearch = {
    'label_icontains': 'fm5'
};

// Expression régulière
const regexSearch = {
    'label_regex': '^FM[0-9]+$'
};
```

## 📅 Opérateurs pour les Dates (DateFilter)

### Champs supportés : `DateTimeField`, `DateField`, `TimeField`

| Opérateur | Description | Exemple | URL |
|-----------|-------------|---------|-----|
| `exact` | Date exacte | `created_at_exact=2025-07-02` | `GET /api/inventory/?created_at_exact=2025-07-02` |
| `gte` | Plus grand ou égal | `created_at_gte=2025-01-01` | `GET /api/inventory/?created_at_gte=2025-01-01` |
| `lte` | Plus petit ou égal | `created_at_lte=2025-12-31` | `GET /api/inventory/?created_at_lte=2025-12-31` |
| `gt` | Plus grand que | `created_at_gt=2025-01-01` | `GET /api/inventory/?created_at_gt=2025-01-01` |
| `lt` | Plus petit que | `created_at_lt=2025-12-31` | `GET /api/inventory/?created_at_lt=2025-12-31` |
| `range` | Plage de dates | `created_at_range=2025-01-01,2025-12-31` | `GET /api/inventory/?created_at_range=2025-01-01,2025-12-31` |
| `year` | Par année | `created_at_year=2025` | `GET /api/inventory/?created_at_year=2025` |
| `month` | Par mois | `created_at_month=7` | `GET /api/inventory/?created_at_month=7` |
| `day` | Par jour | `created_at_day=2` | `GET /api/inventory/?created_at_day=2` |
| `week` | Par semaine | `created_at_week=27` | `GET /api/inventory/?created_at_week=27` |
| `quarter` | Par trimestre | `created_at_quarter=3` | `GET /api/inventory/?created_at_quarter=3` |

### Exemples d'utilisation frontend :

```javascript
// Date exacte
const exactDate = {
    'created_at_exact': '2025-07-02'
};

// Plage de dates
const dateRange = {
    'created_at_range': '2025-01-01,2025-12-31'
};

// Date de début
const startDate = {
    'created_at_gte': '2025-01-01'
};

// Date de fin
const endDate = {
    'created_at_lte': '2025-12-31'
};

// Par année
const yearFilter = {
    'created_at_year': '2025'
};

// Par mois
const monthFilter = {
    'created_at_month': '7'
};
```

## 🔢 Opérateurs pour les Nombres (NumberFilter)

### Champs supportés : `IntegerField`, `BigIntegerField`, `DecimalField`, `FloatField`

| Opérateur | Description | Exemple | URL |
|-----------|-------------|---------|-----|
| `exact` | Valeur exacte | `id_exact=1` | `GET /api/inventory/?id_exact=1` |
| `gte` | Plus grand ou égal | `id_gte=1` | `GET /api/inventory/?id_gte=1` |
| `lte` | Plus petit ou égal | `id_lte=100` | `GET /api/inventory/?id_lte=100` |
| `gt` | Plus grand que | `id_gt=0` | `GET /api/inventory/?id_gt=0` |
| `lt` | Plus petit que | `id_lt=1000` | `GET /api/inventory/?id_lt=1000` |
| `range` | Plage de valeurs | `id_range=1,100` | `GET /api/inventory/?id_range=1,100` |

### Exemples d'utilisation frontend :

```javascript
// Valeur exacte
const exactValue = {
    'id_exact': 1
};

// Plage de valeurs
const valueRange = {
    'id_range': '1,100'
};

// Valeur minimale
const minValue = {
    'id_gte': 1
};

// Valeur maximale
const maxValue = {
    'id_lte': 100
};

// Entre deux valeurs
const betweenValues = {
    'id_gt': 0,
    'id_lt': 1000
};
```

## ✅ Opérateurs pour les Booléens (BooleanField)

### Champs supportés : `BooleanField`, `NullBooleanField`

| Opérateur | Description | Exemple | URL |
|-----------|-------------|---------|-----|
| `exact` | Valeur exacte | `is_active_exact=true` | `GET /api/inventory/?is_active_exact=true` |
| `true` | Égal à True | `is_active=true` | `GET /api/inventory/?is_active=true` |
| `false` | Égal à False | `is_active=false` | `GET /api/inventory/?is_active=false` |

### Exemples d'utilisation frontend :

```javascript
// Booléen exact
const exactBoolean = {
    'is_active_exact': true
};

// Vrai
const trueValue = {
    'is_active': true
};

// Faux
const falseValue = {
    'is_active': false
};
```

## 🔗 Opérateurs pour les Relations (ForeignKey, ManyToManyField)

### Champs supportés : `ForeignKey`, `OneToOneField`, `ManyToManyField`

| Opérateur | Description | Exemple | URL |
|-----------|-------------|---------|-----|
| `exact` | ID de la relation | `account_exact=1` | `GET /api/inventory/?account_exact=1` |
| `id_exact` | ID de la relation | `account_id_exact=1` | `GET /api/inventory/?account_id_exact=1` |
| `__field` | Champ de la relation | `account__name_contains=Company` | `GET /api/inventory/?account__name_contains=Company` |

### Exemples d'utilisation frontend :

```javascript
// Par ID de relation
const relationById = {
    'account_exact': 1
};

// Par champ de relation
const relationByField = {
    'account__name_contains': 'Company'
};

// Relation multiple
const multipleRelation = {
    'warehouses__id_exact': 1
};
```

## 🎯 Exemples d'Implémentation Frontend

### Configuration DataTable avec tous les opérateurs

```javascript
// Configuration DataTable avec filtres avancés
const dataTableConfig = {
    // Configuration de base
    url: '/api/inventory/',
    method: 'GET',
    
    // Colonnes avec filtres
    columns: [
        {
            title: 'ID',
            data: 'id',
            filterable: true,
            filterType: 'number',
            filterOperators: ['exact', 'gte', 'lte', 'gt', 'lt', 'range']
        },
        {
            title: 'Label',
            data: 'label',
            filterable: true,
            filterType: 'string',
            filterOperators: ['exact', 'contains', 'startswith', 'endswith', 'icontains', 'istartswith', 'iendswith', 'regex', 'iregex']
        },
        {
            title: 'Date de création',
            data: 'created_at',
            filterable: true,
            filterType: 'date',
            filterOperators: ['exact', 'gte', 'lte', 'gt', 'lt', 'range', 'year', 'month', 'day', 'week', 'quarter']
        },
        {
            title: 'Statut',
            data: 'status',
            filterable: true,
            filterType: 'string',
            filterOperators: ['exact', 'contains', 'icontains']
        },
        {
            title: 'Compte',
            data: 'account_name',
            filterable: true,
            filterType: 'string',
            filterOperators: ['exact', 'contains', 'startswith', 'icontains']
        }
    ],
    
    // Configuration des filtres
    filters: {
        // Filtres de chaînes
        stringFilters: ['label', 'reference', 'status', 'inventory_type'],
        stringOperators: ['exact', 'contains', 'startswith', 'endswith', 'icontains', 'istartswith', 'iendswith', 'regex', 'iregex'],
        
        // Filtres de dates
        dateFilters: ['date', 'created_at', 'updated_at'],
        dateOperators: ['exact', 'gte', 'lte', 'gt', 'lt', 'range', 'year', 'month', 'day', 'week', 'quarter'],
        
        // Filtres numériques
        numberFilters: ['id'],
        numberOperators: ['exact', 'gte', 'lte', 'gt', 'lt', 'range'],
        
        // Filtres de relations
        relationFilters: ['account__name', 'warehouse__name'],
        relationOperators: ['exact', 'contains', 'startswith', 'icontains']
    }
};
```

### Fonction de construction des paramètres de filtre

```javascript
// Fonction pour construire les paramètres de filtre
function buildFilterParams(filters) {
    const params = new URLSearchParams();
    
    // Ajouter les filtres de chaînes
    if (filters.string) {
        Object.keys(filters.string).forEach(field => {
            const filter = filters.string[field];
            if (filter.value && filter.operator) {
                params.append(`${field}_${filter.operator}`, filter.value);
            }
        });
    }
    
    // Ajouter les filtres de dates
    if (filters.date) {
        Object.keys(filters.date).forEach(field => {
            const filter = filters.date[field];
            if (filter.value && filter.operator) {
                if (filter.operator === 'range' && filter.value.start && filter.value.end) {
                    params.append(`${field}_range`, `${filter.value.start},${filter.value.end}`);
                } else {
                    params.append(`${field}_${filter.operator}`, filter.value);
                }
            }
        });
    }
    
    // Ajouter les filtres numériques
    if (filters.number) {
        Object.keys(filters.number).forEach(field => {
            const filter = filters.number[field];
            if (filter.value && filter.operator) {
                if (filter.operator === 'range' && filter.value.min && filter.value.max) {
                    params.append(`${field}_range`, `${filter.value.min},${filter.value.max}`);
                } else {
                    params.append(`${field}_${filter.operator}`, filter.value);
                }
            }
        });
    }
    
    return params;
}

// Exemple d'utilisation
const filters = {
    string: {
        label: { operator: 'contains', value: 'FM' },
        status: { operator: 'exact', value: 'EN PREPARATION' }
    },
    date: {
        created_at: { operator: 'year', value: '2025' },
        date: { operator: 'range', value: { start: '2025-01-01', end: '2025-12-31' } }
    },
    number: {
        id: { operator: 'range', value: { min: 1, max: 100 } }
    }
};

const params = buildFilterParams(filters);
console.log(params.toString());
// Résultat: label_contains=FM&status_exact=EN PREPARATION&created_at_year=2025&date_range=2025-01-01,2025-12-31&id_range=1,100
```

### Composant de filtre réutilisable

```javascript
// Composant de filtre pour chaînes
class StringFilterComponent {
    constructor(field, operators = ['exact', 'contains', 'startswith', 'endswith']) {
        this.field = field;
        this.operators = operators;
    }
    
    render() {
        return `
            <div class="filter-group">
                <label>${this.field}</label>
                <select class="operator-select">
                    ${this.operators.map(op => `<option value="${op}">${op}</option>`).join('')}
                </select>
                <input type="text" class="filter-value" placeholder="Valeur...">
            </div>
        `;
    }
    
    getFilter() {
        const operator = document.querySelector('.operator-select').value;
        const value = document.querySelector('.filter-value').value;
        
        if (value) {
            return { [`${this.field}_${operator}`]: value };
        }
        return {};
    }
}

// Composant de filtre pour dates
class DateFilterComponent {
    constructor(field, operators = ['exact', 'gte', 'lte', 'range']) {
        this.field = field;
        this.operators = operators;
    }
    
    render() {
        return `
            <div class="filter-group">
                <label>${this.field}</label>
                <select class="operator-select">
                    ${this.operators.map(op => `<option value="${op}">${op}</option>`).join('')}
                </select>
                <input type="date" class="filter-value">
                <input type="date" class="filter-value-end" style="display: none;">
            </div>
        `;
    }
    
    getFilter() {
        const operator = document.querySelector('.operator-select').value;
        const value = document.querySelector('.filter-value').value;
        const valueEnd = document.querySelector('.filter-value-end').value;
        
        if (value) {
            if (operator === 'range' && valueEnd) {
                return { [`${this.field}_range`]: `${value},${valueEnd}` };
            } else {
                return { [`${this.field}_${operator}`]: value };
            }
        }
        return {};
    }
}
```

## 📊 Tableau de Référence Rapide

| Type de Champ | Opérateurs Disponibles | Exemple Frontend |
|---------------|------------------------|------------------|
| **Chaîne** | `exact`, `contains`, `startswith`, `endswith`, `icontains`, `istartswith`, `iendswith`, `regex`, `iregex` | `{ 'label_contains': 'FM' }` |
| **Date** | `exact`, `gte`, `lte`, `gt`, `lt`, `range`, `year`, `month`, `day`, `week`, `quarter` | `{ 'created_at_year': '2025' }` |
| **Nombre** | `exact`, `gte`, `lte`, `gt`, `lt`, `range` | `{ 'id_range': '1,100' }` |
| **Booléen** | `exact`, `true`, `false` | `{ 'is_active': true }` |
| **Relation** | `exact`, `id_exact`, `__field` | `{ 'account__name_contains': 'Company' }` |

## 🚀 Intégration avec votre DataTable

1. **Ajoutez les opérateurs** dans votre configuration DataTable
2. **Utilisez la fonction `buildFilterParams`** pour construire les paramètres
3. **Implémentez les composants de filtre** pour l'interface utilisateur
4. **Testez tous les opérateurs** avec votre API

Cette documentation vous donne tous les outils nécessaires pour implémenter un système de filtrage complet dans votre frontend DataTable ! 🎯 