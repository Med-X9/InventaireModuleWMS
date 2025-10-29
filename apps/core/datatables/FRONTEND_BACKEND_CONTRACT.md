# Contrat Frontend/Backend DataTable

## Vue d'ensemble

Ce document définit le contrat exact entre votre frontend Vue.js 3 + TypeScript et votre backend Django DataTable. Il spécifie les formats de requête et de réponse attendus.

## 📡 **FORMATS DE REQUÊTE BACKEND**

### 1. **Format DataTable Standard**

Votre backend Django attend ces paramètres pour les requêtes DataTable :

```typescript
interface DataTableRequest {
  // Paramètres de base DataTable
  draw: number;                    // Numéro de dessin (timestamp recommandé)
  start: number;                   // Index de début (0-based)
  length: number;                  // Nombre d'éléments par page
  
  // Recherche globale
  'search[value]': string;         // Terme de recherche
  'search[regex]': boolean;        // Recherche regex (généralement false)
  
  // Tri (support multi-colonnes)
  'order[0][column]': number;      // Index de la colonne (0-based)
  'order[0][dir]': 'asc' | 'desc'; // Direction du tri
  'order[1][column]': number;      // Tri secondaire (optionnel)
  'order[1][dir]': 'asc' | 'desc';
  // ... jusqu'à order[N]
  
  // Colonnes individuelles
  'columns[0][data]': string;      // Nom du champ
  'columns[0][name]': string;      // Nom de la colonne
  'columns[0][searchable]': boolean;
  'columns[0][orderable]': boolean;
  'columns[0][search][value]': string;
  'columns[0][search][regex]': boolean;
  // ... pour chaque colonne
  
  // Filtres personnalisés
  [key: string]: any;              // Filtres métier personnalisés
}
```

### 2. **Format REST API**

Pour les requêtes REST API classiques :

```typescript
interface RestApiRequest {
  page: number;                    // Numéro de page (1-based)
  page_size: number;               // Taille de page
  search: string;                  // Recherche globale
  ordering: string;                // Tri (ex: 'name' ou '-name')
  
  // Filtres personnalisés
  [key: string]: any;
}
```

### 3. **Filtres Avancés Supportés**

Votre backend supporte ces opérateurs de filtrage :

```typescript
interface BackendFilters {
  // Filtres de texte
  field_contains?: string;         // field__icontains
  field_startswith?: string;       // field__startswith
  field_endswith?: string;         // field__endswith
  field_exact?: string;            // field__exact
  field_iexact?: string;           // field__iexact
  field_regex?: string;            // field__regex
  field_iregex?: string;           // field__iregex
  
  // Filtres numériques
  field_gte?: number;              // field__gte
  field_lte?: number;              // field__lte
  field_gt?: number;               // field__gt
  field_lt?: number;               // field__lt
  field_range?: string;            // field__gte + field__lte (format: "min,max")
  
  // Filtres de date
  field_date?: string;             // field__date (YYYY-MM-DD)
  field_year?: number;             // field__year
  field_month?: number;            // field__month
  field_day?: number;              // field__day
  field_week?: number;             // field__week
  field_quarter?: number;          // field__quarter
  
  // Filtres de liste
  field_in?: string;               // field__in (valeurs séparées par virgules)
  field_not_in?: string;           // field__isnull=false + field__in
  
  // Filtres de nullité
  field_isnull?: boolean;          // field__isnull
  field_isempty?: boolean;         // field__isempty (pour les chaînes)
  
  // Filtres de plage de dates
  field_start?: string;            // field__gte (date de début)
  field_end?: string;              // field__lte (date de fin)
  
  // Filtres personnalisés
  [key: string]: any;
}
```

## 📤 **FORMATS DE RÉPONSE BACKEND**

### 1. **Format DataTable**

```typescript
interface DataTableResponse<T = any> {
  draw: number;                    // Même valeur que la requête
  recordsTotal: number;            // Nombre total d'enregistrements
  recordsFiltered: number;         // Nombre après filtrage
  data: T[];                       // Données sérialisées
  
  // Informations de pagination (optionnel)
  pagination?: {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
    page_size: number;
  };
  
  // Gestion d'erreurs
  error?: string;                  // Message d'erreur si applicable
}
```

### 2. **Format REST API**

```typescript
interface RestApiResponse<T = any> {
  count: number;                   // Nombre total d'enregistrements
  results: T[];                    // Données sérialisées
  
  // Navigation
  next: string | null;             // URL page suivante
  previous: string | null;         // URL page précédente
  
  // Informations de pagination (optionnel)
  pagination?: {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
    page_size: number;
  };
}
```

## 🔧 **ADAPTATION FRONTEND VUE.JS 3**

### 1. **Service de Transformation**

```typescript
// services/dataTableService.ts
export class DataTableService {
  /**
   * Transforme les paramètres frontend vers le format backend DataTable
   */
  static toDataTableParams(frontendParams: {
    page: number;
    pageSize: number;
    search?: string;
    sort?: Array<{ field: string; direction: 'asc' | 'desc' }>;
    filters?: Record<string, any>;
    columns?: Array<{ field: string; searchable: boolean; orderable: boolean }>;
  }): DataTableRequest {
    const params: any = {
      draw: Date.now(),
      start: (frontendParams.page - 1) * frontendParams.pageSize,
      length: frontendParams.pageSize,
      'search[value]': frontendParams.search || '',
      'search[regex]': false
    };

    // Tri
    if (frontendParams.sort && frontendParams.sort.length > 0) {
      frontendParams.sort.forEach((sort, index) => {
        params[`order[${index}][column]`] = this.getColumnIndex(sort.field, frontendParams.columns);
        params[`order[${index}][dir]`] = sort.direction;
      });
    }

    // Colonnes
    if (frontendParams.columns) {
      frontendParams.columns.forEach((column, index) => {
        params[`columns[${index}][data]`] = column.field;
        params[`columns[${index}][name]`] = column.field;
        params[`columns[${index}][searchable]`] = column.searchable;
        params[`columns[${index}][orderable]`] = column.orderable;
        params[`columns[${index}][search][value]`] = '';
        params[`columns[${index}][search][regex]`] = false;
      });
    }

    // Filtres personnalisés
    if (frontendParams.filters) {
      Object.assign(params, this.transformFilters(frontendParams.filters));
    }

    return params;
  }

  /**
   * Transforme les paramètres frontend vers le format REST API
   */
  static toRestApiParams(frontendParams: {
    page: number;
    pageSize: number;
    search?: string;
    sort?: Array<{ field: string; direction: 'asc' | 'desc' }>;
    filters?: Record<string, any>;
  }): RestApiRequest {
    const params: any = {
      page: frontendParams.page,
      page_size: frontendParams.pageSize
    };

    if (frontendParams.search) {
      params.search = frontendParams.search;
    }

    if (frontendParams.sort && frontendParams.sort.length > 0) {
      params.ordering = frontendParams.sort
        .map(sort => sort.direction === 'desc' ? `-${sort.field}` : sort.field)
        .join(',');
    }

    if (frontendParams.filters) {
      Object.assign(params, this.transformFilters(frontendParams.filters));
    }

    return params;
  }

  /**
   * Transforme les filtres frontend vers le format backend
   */
  private static transformFilters(filters: Record<string, any>): Record<string, any> {
    const backendFilters: Record<string, any> = {};

    Object.keys(filters).forEach(field => {
      const filter = filters[field];
      
      if (!filter || filter.value === undefined || filter.value === null || filter.value === '') {
        return;
      }

      switch (filter.operator) {
        case 'contains':
          backendFilters[`${field}_contains`] = filter.value;
          break;
        case 'startswith':
          backendFilters[`${field}_startswith`] = filter.value;
          break;
        case 'endswith':
          backendFilters[`${field}_endswith`] = filter.value;
          break;
        case 'exact':
          backendFilters[`${field}_exact`] = filter.value;
          break;
        case 'iexact':
          backendFilters[`${field}_iexact`] = filter.value;
          break;
        case 'regex':
          backendFilters[`${field}_regex`] = filter.value;
          break;
        case 'iregex':
          backendFilters[`${field}_iregex`] = filter.value;
          break;
        case 'gte':
          backendFilters[`${field}_gte`] = filter.value;
          break;
        case 'lte':
          backendFilters[`${field}_lte`] = filter.value;
          break;
        case 'gt':
          backendFilters[`${field}_gt`] = filter.value;
          break;
        case 'lt':
          backendFilters[`${field}_lt`] = filter.value;
          break;
        case 'between':
          if (filter.value2 !== undefined) {
            backendFilters[`${field}_gte`] = filter.value;
            backendFilters[`${field}_lte`] = filter.value2;
          }
          break;
        case 'range':
          if (typeof filter.value === 'string' && filter.value.includes(',')) {
            backendFilters[`${field}_range`] = filter.value;
          }
          break;
        case 'in':
          if (Array.isArray(filter.values)) {
            backendFilters[`${field}_in`] = filter.values.join(',');
          }
          break;
        case 'not_in':
          if (Array.isArray(filter.values)) {
            backendFilters[`${field}_not_in`] = filter.values.join(',');
          }
          break;
        case 'isnull':
          backendFilters[`${field}_isnull`] = filter.value;
          break;
        case 'isempty':
          backendFilters[`${field}_isempty`] = filter.value;
          break;
        case 'date':
          backendFilters[`${field}_date`] = filter.value;
          break;
        case 'year':
          backendFilters[`${field}_year`] = filter.value;
          break;
        case 'month':
          backendFilters[`${field}_month`] = filter.value;
          break;
        case 'day':
          backendFilters[`${field}_day`] = filter.value;
          break;
        case 'week':
          backendFilters[`${field}_week`] = filter.value;
          break;
        case 'quarter':
          backendFilters[`${field}_quarter`] = filter.value;
          break;
        case 'date_range':
          if (filter.start) backendFilters[`${field}_start`] = filter.start;
          if (filter.end) backendFilters[`${field}_end`] = filter.end;
          break;
        default:
          // Filtre direct si pas d'opérateur spécifique
          backendFilters[field] = filter.value;
      }
    });

    return backendFilters;
  }

  /**
   * Obtient l'index de colonne pour le tri DataTable
   */
  private static getColumnIndex(field: string, columns?: Array<{ field: string }>): number {
    if (!columns) return 0;
    const index = columns.findIndex(col => col.field === field);
    return index >= 0 ? index : 0;
  }
}
```

### 2. **Composable d'Intégration Backend**

```typescript
// composables/useBackendDataTable.ts
import { ref, computed, watch } from 'vue';
import { DataTableService } from '@/services/dataTableService';

export function useBackendDataTable<T = any>(
  endpoint: string,
  options: {
    useDataTableFormat?: boolean;  // true = DataTable, false = REST API
    autoLoad?: boolean;
    pageSize?: number;
  } = {}
) {
  const {
    useDataTableFormat = true,
    autoLoad = true,
    pageSize = 25
  } = options;

  // État réactif
  const data = ref<T[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  
  // Pagination
  const currentPage = ref(1);
  const pageSizeRef = ref(pageSize);
  const totalItems = ref(0);
  const totalPages = ref(0);
  
  // Recherche et tri
  const searchQuery = ref('');
  const sortModel = ref<Array<{ field: string; direction: 'asc' | 'desc' }>>([]);
  const filters = ref<Record<string, any>>({});
  
  // Configuration des colonnes
  const columns = ref<Array<{ field: string; searchable: boolean; orderable: boolean }>>([]);

  // Computed
  const pagination = computed(() => ({
    current_page: currentPage.value,
    total_pages: totalPages.value,
    has_next: currentPage.value < totalPages.value,
    has_previous: currentPage.value > 1,
    page_size: pageSizeRef.value,
    total: totalItems.value
  }));

  // Méthodes
  const loadData = async (): Promise<void> => {
    loading.value = true;
    error.value = null;

    try {
      const frontendParams = {
        page: currentPage.value,
        pageSize: pageSizeRef.value,
        search: searchQuery.value,
        sort: sortModel.value,
        filters: filters.value,
        columns: columns.value
      };

      const apiParams = useDataTableFormat
        ? DataTableService.toDataTableParams(frontendParams)
        : DataTableService.toRestApiParams(frontendParams);

      const url = new URL(endpoint, window.location.origin);
      Object.keys(apiParams).forEach(key => {
        if (apiParams[key] !== undefined && apiParams[key] !== null && apiParams[key] !== '') {
          url.searchParams.append(key, String(apiParams[key]));
        }
      });

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.error) {
        throw new Error(result.error);
      }

      // Traitement de la réponse selon le format
      if (useDataTableFormat) {
        data.value = result.data || [];
        totalItems.value = result.recordsTotal || 0;
        totalPages.value = Math.ceil((result.recordsTotal || 0) / pageSizeRef.value);
      } else {
        data.value = result.results || [];
        totalItems.value = result.count || 0;
        totalPages.value = Math.ceil((result.count || 0) / pageSizeRef.value);
      }

    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Erreur de chargement';
      console.error('Erreur DataTable:', err);
    } finally {
      loading.value = false;
    }
  };

  const setPage = (page: number): void => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page;
    }
  };

  const setPageSize = (size: number): void => {
    pageSizeRef.value = size;
    currentPage.value = 1;
  };

  const setSearch = (query: string): void => {
    searchQuery.value = query;
    currentPage.value = 1;
  };

  const setSort = (field: string, direction: 'asc' | 'desc'): void => {
    sortModel.value = [{ field, direction }];
  };

  const setSortModel = (newSortModel: Array<{ field: string; direction: 'asc' | 'desc' }>): void => {
    sortModel.value = newSortModel;
  };

  const setFilters = (newFilters: Record<string, any>): void => {
    filters.value = { ...filters.value, ...newFilters };
    currentPage.value = 1;
  };

  const resetFilters = (): void => {
    filters.value = {};
    searchQuery.value = '';
    currentPage.value = 1;
  };

  const refresh = (): Promise<void> => {
    return loadData();
  };

  // Watchers
  watch([currentPage, pageSizeRef, searchQuery, sortModel, filters], 
    () => {
      if (autoLoad) {
        loadData();
      }
    }, 
    { deep: true }
  );

  // Initialisation
  if (autoLoad) {
    loadData();
  }

  return {
    // État
    data,
    loading,
    error,
    pagination,
    
    // Paramètres
    currentPage,
    pageSize: pageSizeRef,
    searchQuery,
    sortModel,
    filters,
    columns,
    
    // Méthodes
    loadData,
    refresh,
    setPage,
    setPageSize,
    setSearch,
    setSort,
    setSortModel,
    setFilters,
    resetFilters
  };
}
```

### 3. **Configuration des Colonnes Compatible**

```typescript
// types/backendCompatible.ts
export interface BackendCompatibleColumn {
  field: string;                   // Nom du champ (doit correspondre au backend)
  headerName: string;              // Nom d'affichage
  dataType?: 'text' | 'number' | 'date' | 'datetime' | 'boolean' | 'select';
  sortable?: boolean;              // Peut être trié
  filterable?: boolean;            // Peut être filtré
  searchable?: boolean;            // Inclus dans la recherche globale
  
  // Configuration de filtrage
  filterConfig?: {
    operator: 'contains' | 'startswith' | 'endswith' | 'exact' | 'gte' | 'lte' | 'between' | 'in' | 'date_range';
    options?: Array<{ label: string; value: any }>;  // Pour les selects
  };
  
  // Rendu personnalisé
  valueFormatter?: (value: any, row: any) => string;
  cellRenderer?: (value: any, row: any) => string;
}

// Exemple de configuration
export const inventoryColumns: BackendCompatibleColumn[] = [
  {
    field: 'id',
    headerName: 'ID',
    dataType: 'number',
    sortable: true,
    filterable: false,
    searchable: false
  },
  {
    field: 'label',
    headerName: 'Libellé',
    dataType: 'text',
    sortable: true,
    filterable: true,
    searchable: true,
    filterConfig: {
      operator: 'contains'
    }
  },
  {
    field: 'status',
    headerName: 'Statut',
    dataType: 'select',
    sortable: true,
    filterable: true,
    searchable: false,
    filterConfig: {
      operator: 'exact',
      options: [
        { label: 'Actif', value: 'active' },
        { label: 'Inactif', value: 'inactive' },
        { label: 'En attente', value: 'pending' }
      ]
    },
    valueFormatter: (value) => {
      const statusMap = {
        active: 'Actif',
        inactive: 'Inactif',
        pending: 'En attente'
      };
      return statusMap[value] || value;
    }
  },
  {
    field: 'quantity',
    headerName: 'Quantité',
    dataType: 'number',
    sortable: true,
    filterable: true,
    searchable: false,
    filterConfig: {
      operator: 'between'
    },
    valueFormatter: (value) => new Intl.NumberFormat('fr-FR').format(value)
  },
  {
    field: 'date',
    headerName: 'Date',
    dataType: 'date',
    sortable: true,
    filterable: true,
    searchable: false,
    filterConfig: {
      operator: 'date_range'
    },
    valueFormatter: (value) => {
      if (!value) return '';
      return new Date(value).toLocaleDateString('fr-FR');
    }
  }
];
```

### 4. **Utilisation dans un Composant**

```vue
<template>
  <DataTable
    :columns="columns"
    :rowDataProp="data"
    :actions="actions"
    :serverSidePagination="true"
    :serverSideSorting="true"
    :serverSideFiltering="true"
    :currentPageProp="pagination.current_page"
    :totalPagesProp="pagination.total_pages"
    :totalItemsProp="pagination.total"
    :loading="loading"
    @pagination-changed="handlePagination"
    @sort-changed="handleSort"
    @filter-changed="handleFilter"
    @global-search-changed="handleGlobalSearch"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useBackendDataTable } from '@/composables/useBackendDataTable';
import { inventoryColumns } from '@/types/backendCompatible';

// Configuration du DataTable backend
const {
  data,
  loading,
  error,
  pagination,
  columns,
  setPage,
  setSortModel,
  setFilters,
  setSearch,
  refresh
} = useBackendDataTable('/api/inventory/datatable/', {
  useDataTableFormat: true,  // Utiliser le format DataTable
  autoLoad: true,
  pageSize: 25
});

// Configuration des colonnes
columns.value = inventoryColumns.map(col => ({
  field: col.field,
  searchable: col.searchable || false,
  orderable: col.sortable || false
}));

// Actions
const actions = [
  {
    label: 'Modifier',
    icon: 'edit',
    onClick: (row) => console.log('Edit:', row)
  },
  {
    label: 'Supprimer',
    icon: 'delete',
    color: 'danger',
    onClick: (row) => console.log('Delete:', row)
  }
];

// Handlers
const handlePagination = (params: { page: number; pageSize: number }) => {
  setPage(params.page);
};

const handleSort = (sortModel: Array<{ field: string; direction: 'asc' | 'desc' }>) => {
  setSortModel(sortModel);
};

const handleFilter = (filters: Record<string, any>) => {
  setFilters(filters);
};

const handleGlobalSearch = (search: string) => {
  setSearch(search);
};

onMounted(() => {
  console.log('DataTable initialisé avec backend');
});
</script>
```

## 🎯 **RÉSUMÉ DES ADAPTATIONS NÉCESSAIRES**

### ✅ **Ce qui est déjà compatible :**
- Structure de base des requêtes
- Formats de réponse
- Pagination
- Tri de base

### 🔧 **Ce qui doit être adapté :**
1. **Service de transformation** des filtres frontend → backend
2. **Composable d'intégration** pour la communication API
3. **Configuration des colonnes** avec mapping des champs
4. **Handlers d'événements** pour synchroniser l'état

### 🚀 **Avantages de cette approche :**
- **Type safety** complète
- **Réutilisabilité** maximale
- **Performance** optimale
- **Maintenabilité** élevée
- **Extensibilité** facile

Votre frontend Vue.js 3 + TypeScript sera parfaitement compatible avec votre backend Django DataTable ! 🎉
