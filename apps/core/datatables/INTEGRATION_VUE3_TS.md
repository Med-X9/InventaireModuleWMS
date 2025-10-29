# Documentation d'Intégration Vue.js 3 + TypeScript

## Vue d'ensemble

Cette documentation explique comment intégrer votre package DataTable backend Django avec votre package DataTable frontend Vue.js 3 + TypeScript pour créer une solution complète de tableaux de données.

## Architecture de l'Intégration

```
Frontend (Vue.js 3 + TS)       Backend (Django)
┌─────────────────────────┐   ┌─────────────────────┐
│   DataTable Component   │──►│ DataTable Server    │
│   - Composition API     │   │ - Configuration     │
│   - Reactive State      │   │ - Filtrage          │
│   - TypeScript Types    │   │ - Pagination        │
│   - Composables         │   │ - Sérialisation     │
└─────────────────────────┘   └─────────────────────┘
```

## 1. Types TypeScript

### 1.1 Types de Base

```typescript
// types/datatable.ts

export interface DataTableColumn {
  data: string;
  name: string;
  title: string;
  width?: string;
  searchable?: boolean;
  orderable?: boolean;
  render?: (data: any, type: string, row: any) => string;
  className?: string;
}

export interface DataTableOrder {
  column: number;
  dir: 'asc' | 'desc';
}

export interface DataTableSearch {
  value: string;
  regex: boolean;
}

export interface DataTableParams {
  draw: number;
  start: number;
  length: number;
  search: DataTableSearch;
  order: DataTableOrder[];
  columns: DataTableColumn[];
}

export interface DataTableResponse<T = any> {
  draw: number;
  recordsTotal: number;
  recordsFiltered: number;
  data: T[];
  pagination?: {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
    page_size: number;
  };
  error?: string;
}

export interface RestApiResponse<T = any> {
  count: number;
  results: T[];
  next: string | null;
  previous: string | null;
  pagination?: {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
    page_size: number;
  };
}

export interface DataTableConfig {
  processing?: boolean;
  serverSide?: boolean;
  pageLength?: number;
  lengthMenu?: number[][];
  order?: [number, 'asc' | 'desc'][];
  searchDelay?: number;
  autoRefresh?: number;
  responsive?: boolean;
  language?: {
    url?: string;
    [key: string]: any;
  };
}

export interface DataTableFilters {
  status?: string;
  date_start?: string;
  date_end?: string;
  warehouse?: string | number;
  [key: string]: any;
}

export interface ActionButton {
  type: string;
  url: string;
  icon: string;
  title: string;
  confirm?: boolean;
  permission?: string;
}

export interface InventoryItem {
  id: number;
  label: string;
  reference: string;
  description?: string;
  status: 'active' | 'inactive' | 'pending';
  status_display: string;
  quantity: number;
  warehouse_name: string;
  formatted_date: string;
  actions: ActionButton[];
  created_at: string;
  updated_at: string;
}
```

### 1.2 Types pour les Composables

```typescript
// types/composables.ts

export interface UseDataTableOptions {
  endpoint: string;
  config?: Partial<DataTableConfig>;
  initialFilters?: DataTableFilters;
  autoLoad?: boolean;
}

export interface UseDataTableReturn<T = any> {
  // État réactif
  data: Ref<T[]>;
  loading: Ref<boolean>;
  error: Ref<string | null>;
  pagination: Ref<{
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
    page_size: number;
    total: number;
  }>;
  
  // Paramètres de requête
  currentPage: Ref<number>;
  pageSize: Ref<number>;
  searchQuery: Ref<string>;
  sortColumn: Ref<string>;
  sortDirection: Ref<'asc' | 'desc'>;
  filters: Ref<DataTableFilters>;
  
  // Méthodes
  loadData: () => Promise<void>;
  refresh: () => Promise<void>;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setSearch: (query: string) => void;
  setSort: (column: string, direction: 'asc' | 'desc') => void;
  setFilters: (newFilters: Partial<DataTableFilters>) => void;
  resetFilters: () => void;
  exportData: (format: 'csv' | 'excel' | 'pdf') => void;
}
```

## 2. Composable Principal

### 2.1 useDataTable Composable

```typescript
// composables/useDataTable.ts

import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue';
import type { Ref } from 'vue';
import { useApi } from './useApi';
import type { 
  UseDataTableOptions, 
  UseDataTableReturn, 
  DataTableResponse,
  DataTableFilters,
  DataTableParams
} from '@/types/datatable';

export function useDataTable<T = any>(
  options: UseDataTableOptions
): UseDataTableReturn<T> {
  
  // État réactif
  const data = ref<T[]>([]) as Ref<T[]>;
  const loading = ref(false);
  const error = ref<string | null>(null);
  const pagination = ref({
    current_page: 1,
    total_pages: 1,
    has_next: false,
    has_previous: false,
    page_size: options.config?.pageLength || 25,
    total: 0
  });
  
  // Paramètres de requête
  const currentPage = ref(1);
  const pageSize = ref(options.config?.pageLength || 25);
  const searchQuery = ref('');
  const sortColumn = ref('');
  const sortDirection = ref<'asc' | 'desc'>('asc');
  const filters = ref<DataTableFilters>(options.initialFilters || {});
  
  // Configuration par défaut
  const defaultConfig: DataTableConfig = {
    processing: true,
    serverSide: true,
    pageLength: 25,
    lengthMenu: [[5, 10, 25, 50, 100], [5, 10, 25, 50, 100]],
    order: [[0, 'desc']],
    searchDelay: 500,
    responsive: true,
    ...options.config
  };
  
  // API composable
  const { get, post } = useApi();
  
  // Auto-refresh timer
  let refreshTimer: NodeJS.Timeout | null = null;
  
  // Watchers pour les paramètres
  watch([currentPage, pageSize, searchQuery, sortColumn, sortDirection, filters], 
    () => {
      if (options.autoLoad !== false) {
        loadData();
      }
    }, 
    { deep: true }
  );
  
  // Construction des paramètres de requête
  const buildRequestParams = (): DataTableParams & Record<string, any> => {
    const params: any = {
      // Paramètres DataTable standard
      draw: Date.now(), // Utiliser timestamp comme draw
      start: (currentPage.value - 1) * pageSize.value,
      length: pageSize.value,
      'search[value]': searchQuery.value,
      'search[regex]': false
    };
    
    // Paramètres de tri
    if (sortColumn.value) {
      params['order[0][column]'] = sortColumn.value;
      params['order[0][dir]'] = sortDirection.value;
    }
    
    // Filtres personnalisés
    Object.keys(filters.value).forEach(key => {
      const value = filters.value[key];
      if (value !== null && value !== undefined && value !== '') {
        params[key] = value;
      }
    });
    
    return params;
  };
  
  // Chargement des données
  const loadData = async (): Promise<void> => {
    loading.value = true;
    error.value = null;
    
    try {
      const params = buildRequestParams();
      const response = await get<DataTableResponse<T>>(options.endpoint, { params });
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      data.value = response.data || [];
      pagination.value = {
        current_page: currentPage.value,
        total_pages: Math.ceil(response.recordsTotal / pageSize.value),
        has_next: (currentPage.value * pageSize.value) < response.recordsTotal,
        has_previous: currentPage.value > 1,
        page_size: pageSize.value,
        total: response.recordsTotal
      };
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Erreur lors du chargement';
      console.error('Erreur DataTable:', err);
    } finally {
      loading.value = false;
    }
  };
  
  // Actualisation
  const refresh = async (): Promise<void> => {
    await loadData();
  };
  
  // Navigation
  const setPage = (page: number): void => {
    if (page >= 1 && page <= pagination.value.total_pages) {
      currentPage.value = page;
    }
  };
  
  const setPageSize = (size: number): void => {
    pageSize.value = size;
    currentPage.value = 1; // Reset à la première page
  };
  
  // Recherche
  const setSearch = (query: string): void => {
    searchQuery.value = query;
    currentPage.value = 1; // Reset à la première page
  };
  
  // Tri
  const setSort = (column: string, direction: 'asc' | 'desc'): void => {
    sortColumn.value = column;
    sortDirection.value = direction;
  };
  
  // Filtres
  const setFilters = (newFilters: Partial<DataTableFilters>): void => {
    filters.value = { ...filters.value, ...newFilters };
    currentPage.value = 1; // Reset à la première page
  };
  
  const resetFilters = (): void => {
    filters.value = {};
    searchQuery.value = '';
    currentPage.value = 1;
  };
  
  // Export
  const exportData = async (format: 'csv' | 'excel' | 'pdf'): Promise<void> => {
    try {
      const params = { ...buildRequestParams(), export: format };
      const url = `${options.endpoint}?${new URLSearchParams(params).toString()}`;
      window.open(url, '_blank');
    } catch (err) {
      error.value = 'Erreur lors de l\'export';
      console.error('Erreur export:', err);
    }
  };
  
  // Auto-refresh
  const setupAutoRefresh = (): void => {
    if (defaultConfig.autoRefresh && defaultConfig.autoRefresh > 0) {
      refreshTimer = setInterval(() => {
        refresh();
      }, defaultConfig.autoRefresh * 1000);
    }
  };
  
  const clearAutoRefresh = (): void => {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  };
  
  // Lifecycle
  onMounted(() => {
    if (options.autoLoad !== false) {
      loadData();
    }
    setupAutoRefresh();
  });
  
  onUnmounted(() => {
    clearAutoRefresh();
  });
  
  return {
    // État réactif
    data,
    loading,
    error,
    pagination,
    
    // Paramètres de requête
    currentPage,
    pageSize,
    searchQuery,
    sortColumn,
    sortDirection,
    filters,
    
    // Méthodes
    loadData,
    refresh,
    setPage,
    setPageSize,
    setSearch,
    setSort,
    setFilters,
    resetFilters,
    exportData
  };
}
```

### 2.2 Composable API

```typescript
// composables/useApi.ts

import { ref } from 'vue';
import type { Ref } from 'vue';

interface ApiOptions {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

interface RequestConfig {
  params?: Record<string, any>;
  headers?: Record<string, string>;
  timeout?: number;
}

export function useApi(options: ApiOptions = {}) {
  const loading = ref(false);
  const error = ref<string | null>(null);
  
  const defaultOptions: ApiOptions = {
    baseURL: '',
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
    ...options
  };
  
  // Récupérer le token CSRF
  const getCSRFToken = (): string => {
    const token = document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value;
    return token || '';
  };
  
  // Construire l'URL complète
  const buildUrl = (endpoint: string, params?: Record<string, any>): string => {
    const url = new URL(endpoint, defaultOptions.baseURL || window.location.origin);
    
    if (params) {
      Object.keys(params).forEach(key => {
        const value = params[key];
        if (value !== null && value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    
    return url.toString();
  };
  
  // Requête générique
  const request = async <T = any>(
    method: string,
    endpoint: string,
    config: RequestConfig & { body?: any } = {}
  ): Promise<T> => {
    loading.value = true;
    error.value = null;
    
    try {
      const url = method === 'GET' ? buildUrl(endpoint, config.params) : endpoint;
      
      const headers = {
        ...defaultOptions.headers,
        ...config.headers
      };
      
      // Ajouter le token CSRF pour les requêtes modifiant les données
      if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
        headers['X-CSRFToken'] = getCSRFToken();
      }
      
      const fetchOptions: RequestInit = {
        method: method.toUpperCase(),
        headers,
        credentials: 'same-origin'
      };
      
      if (config.body) {
        fetchOptions.body = JSON.stringify(config.body);
      }
      
      const response = await fetch(url, fetchOptions);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text() as any;
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur de requête';
      error.value = errorMessage;
      throw err;
    } finally {
      loading.value = false;
    }
  };
  
  // Méthodes HTTP
  const get = <T = any>(endpoint: string, config?: RequestConfig): Promise<T> =>
    request<T>('GET', endpoint, config);
  
  const post = <T = any>(endpoint: string, body?: any, config?: RequestConfig): Promise<T> =>
    request<T>('POST', endpoint, { ...config, body });
  
  const put = <T = any>(endpoint: string, body?: any, config?: RequestConfig): Promise<T> =>
    request<T>('PUT', endpoint, { ...config, body });
  
  const patch = <T = any>(endpoint: string, body?: any, config?: RequestConfig): Promise<T> =>
    request<T>('PATCH', endpoint, { ...config, body });
  
  const del = <T = any>(endpoint: string, config?: RequestConfig): Promise<T> =>
    request<T>('DELETE', endpoint, config);
  
  return {
    loading,
    error,
    get,
    post,
    put,
    patch,
    delete: del
  };
}
```

## 3. Composant DataTable Principal

### 3.1 DataTable.vue

```vue
<!-- components/DataTable.vue -->
<template>
  <div class="datatable-container">
    <!-- En-tête avec titre et actions -->
    <div class="datatable-header">
      <div class="datatable-title">
        <slot name="title">
          <h5><i :class="titleIcon"></i> {{ title }}</h5>
        </slot>
      </div>
      
      <div class="datatable-actions">
        <slot name="actions">
          <button 
            @click="exportData('csv')" 
            class="btn btn-success btn-sm"
            :disabled="loading"
          >
            <i class="fa fa-download"></i> Export CSV
          </button>
          
          <button 
            @click="refresh()" 
            class="btn btn-primary btn-sm"
            :disabled="loading"
          >
            <i class="fa fa-refresh" :class="{ 'fa-spin': loading }"></i> 
            Actualiser
          </button>
        </slot>
      </div>
    </div>
    
    <!-- Formulaire de filtres -->
    <DataTableFilters
      v-if="showFilters"
      :filters="filters"
      :loading="loading"
      @update:filters="setFilters"
      @reset="resetFilters"
    />
    
    <!-- Barre de recherche -->
    <div class="datatable-search" v-if="showSearch">
      <div class="row align-items-center mb-3">
        <div class="col-md-6">
          <div class="input-group">
            <input
              v-model="searchQuery"
              type="text"
              class="form-control"
              placeholder="Rechercher..."
              :disabled="loading"
            />
            <button class="btn btn-outline-secondary" type="button">
              <i class="fa fa-search"></i>
            </button>
          </div>
        </div>
        
        <div class="col-md-6 text-end">
          <select 
            v-model="pageSize" 
            class="form-select form-select-sm d-inline-block w-auto"
            :disabled="loading"
          >
            <option v-for="size in pageSizeOptions" :key="size" :value="size">
              {{ size }} par page
            </option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- Tableau -->
    <div class="table-responsive">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.name"
              :style="{ width: column.width }"
              :class="column.className"
            >
              <div 
                class="th-content"
                :class="{ 'sortable': column.orderable }"
                @click="column.orderable ? handleSort(column.name) : null"
              >
                {{ column.title }}
                
                <span v-if="column.orderable && sortColumn === column.name" class="sort-indicator">
                  <i :class="sortDirection === 'asc' ? 'fa fa-sort-up' : 'fa fa-sort-down'"></i>
                </span>
                <span v-else-if="column.orderable" class="sort-indicator">
                  <i class="fa fa-sort text-muted"></i>
                </span>
              </div>
            </th>
          </tr>
        </thead>
        
        <tbody>
          <!-- État de chargement -->
          <tr v-if="loading">
            <td :colspan="columns.length" class="text-center py-4">
              <div class="spinner-border spinner-border-sm me-2"></div>
              Chargement en cours...
            </td>
          </tr>
          
          <!-- État d'erreur -->
          <tr v-else-if="error">
            <td :colspan="columns.length" class="text-center py-4 text-danger">
              <i class="fa fa-exclamation-triangle me-2"></i>
              {{ error }}
            </td>
          </tr>
          
          <!-- Aucune donnée -->
          <tr v-else-if="data.length === 0">
            <td :colspan="columns.length" class="text-center py-4 text-muted">
              <i class="fa fa-inbox me-2"></i>
              Aucune donnée disponible
            </td>
          </tr>
          
          <!-- Données -->
          <tr v-else v-for="row in data" :key="getRowKey(row)">
            <td
              v-for="column in columns"
              :key="column.name"
              :class="column.className"
            >
              <component
                v-if="column.component"
                :is="column.component"
                :data="getColumnValue(row, column.data)"
                :row="row"
                :column="column"
                @action="handleRowAction"
              />
              
              <div
                v-else-if="column.render"
                v-html="column.render(getColumnValue(row, column.data), 'display', row)"
              ></div>
              
              <span v-else>
                {{ getColumnValue(row, column.data) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Pagination -->
    <DataTablePagination
      v-if="showPagination && pagination.total > 0"
      :pagination="pagination"
      :loading="loading"
      @update:page="setPage"
    />
    
    <!-- Informations -->
    <div class="datatable-info mt-2">
      <small class="text-muted">
        Affichage de {{ startRecord }} à {{ endRecord }} sur {{ pagination.total }} éléments
        <span v-if="searchQuery"> (filtré)</span>
      </small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue';
import { useDataTable } from '@/composables/useDataTable';
import DataTableFilters from './DataTableFilters.vue';
import DataTablePagination from './DataTablePagination.vue';
import type { 
  DataTableColumn, 
  DataTableFilters as FiltersType,
  UseDataTableOptions
} from '@/types/datatable';

// Props
interface Props {
  endpoint: string;
  columns: DataTableColumn[];
  title?: string;
  titleIcon?: string;
  showFilters?: boolean;
  showSearch?: boolean;
  showPagination?: boolean;
  config?: UseDataTableOptions['config'];
  initialFilters?: FiltersType;
  rowKey?: string;
  pageSizeOptions?: number[];
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Tableau de données',
  titleIcon: 'fa fa-table',
  showFilters: true,
  showSearch: true,
  showPagination: true,
  rowKey: 'id',
  pageSizeOptions: () => [5, 10, 25, 50, 100]
});

// Emits
const emit = defineEmits<{
  rowAction: [action: string, row: any];
  dataLoaded: [data: any[]];
  error: [error: string];
}>();

// DataTable composable
const {
  data,
  loading,
  error,
  pagination,
  currentPage,
  pageSize,
  searchQuery,
  sortColumn,
  sortDirection,
  filters,
  loadData,
  refresh,
  setPage,
  setPageSize,
  setSearch,
  setSort,
  setFilters,
  resetFilters,
  exportData
} = useDataTable({
  endpoint: props.endpoint,
  config: props.config,
  initialFilters: props.initialFilters
});

// Computed
const startRecord = computed(() => {
  if (pagination.value.total === 0) return 0;
  return (currentPage.value - 1) * pageSize.value + 1;
});

const endRecord = computed(() => {
  const end = currentPage.value * pageSize.value;
  return Math.min(end, pagination.value.total);
});

// Méthodes
const getRowKey = (row: any): string | number => {
  return row[props.rowKey] || row.id || Math.random();
};

const getColumnValue = (row: any, dataPath: string): any => {
  return dataPath.split('.').reduce((obj, key) => obj?.[key], row);
};

const handleSort = (column: string): void => {
  if (sortColumn.value === column) {
    // Inverser la direction si même colonne
    const newDirection = sortDirection.value === 'asc' ? 'desc' : 'asc';
    setSort(column, newDirection);
  } else {
    // Nouvelle colonne, commencer par asc
    setSort(column, 'asc');
  }
};

const handleRowAction = (action: string, row: any): void => {
  emit('rowAction', action, row);
};

// Watchers
watch(data, (newData) => {
  emit('dataLoaded', newData);
});

watch(error, (newError) => {
  if (newError) {
    emit('error', newError);
  }
});

// Exposer les méthodes pour l'accès depuis le parent
defineExpose({
  refresh,
  loadData,
  exportData,
  setFilters,
  resetFilters,
  data,
  loading,
  error,
  pagination
});
</script>

<style scoped>
.datatable-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 1.5rem;
}

.datatable-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.datatable-title h5 {
  margin: 0;
  color: #495057;
}

.datatable-actions {
  display: flex;
  gap: 0.5rem;
}

.th-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.th-content.sortable {
  cursor: pointer;
  user-select: none;
}

.th-content.sortable:hover {
  background-color: rgba(0,0,0,0.05);
}

.sort-indicator {
  margin-left: 0.5rem;
  opacity: 0.7;
}

.table th {
  background-color: #f8f9fa;
  border-top: none;
  font-weight: 600;
  color: #495057;
}

.table td {
  vertical-align: middle;
}

.datatable-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 768px) {
  .datatable-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .datatable-actions {
    justify-content: center;
  }
}
</style>
```

### 3.2 Composant de Filtres

```vue
<!-- components/DataTableFilters.vue -->
<template>
  <div class="datatable-filters">
    <form @submit.prevent="applyFilters" class="row g-3 mb-3">
      <!-- Filtre par statut -->
      <div class="col-md-3">
        <label for="status-filter" class="form-label">Statut</label>
        <select 
          id="status-filter" 
          v-model="localFilters.status" 
          class="form-select"
          :disabled="loading"
        >
          <option value="">Tous les statuts</option>
          <option value="active">Actif</option>
          <option value="inactive">Inactif</option>
          <option value="pending">En attente</option>
        </select>
      </div>
      
      <!-- Filtre par date de début -->
      <div class="col-md-3">
        <label for="date-start" class="form-label">Date début</label>
        <input 
          id="date-start"
          v-model="localFilters.date_start" 
          type="date" 
          class="form-control"
          :disabled="loading"
        />
      </div>
      
      <!-- Filtre par date de fin -->
      <div class="col-md-3">
        <label for="date-end" class="form-label">Date fin</label>
        <input 
          id="date-end"
          v-model="localFilters.date_end" 
          type="date" 
          class="form-control"
          :disabled="loading"
        />
      </div>
      
      <!-- Filtre par entrepôt -->
      <div class="col-md-3">
        <label for="warehouse-filter" class="form-label">Entrepôt</label>
        <select 
          id="warehouse-filter" 
          v-model="localFilters.warehouse" 
          class="form-select"
          :disabled="loading"
        >
          <option value="">Tous les entrepôts</option>
          <option 
            v-for="warehouse in warehouses" 
            :key="warehouse.id" 
            :value="warehouse.id"
          >
            {{ warehouse.name }}
          </option>
        </select>
      </div>
      
      <!-- Boutons d'action -->
      <div class="col-12">
        <button 
          type="submit" 
          class="btn btn-primary"
          :disabled="loading"
        >
          <i class="fa fa-filter"></i> Appliquer les filtres
        </button>
        
        <button 
          type="button" 
          @click="resetFilters" 
          class="btn btn-secondary ms-2"
          :disabled="loading"
        >
          <i class="fa fa-times"></i> Réinitialiser
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';
import { useApi } from '@/composables/useApi';
import type { DataTableFilters } from '@/types/datatable';

// Props
interface Props {
  filters: DataTableFilters;
  loading: boolean;
}

const props = defineProps<Props>();

// Emits
const emit = defineEmits<{
  'update:filters': [filters: DataTableFilters];
  reset: [];
}>();

// État local
const localFilters = reactive<DataTableFilters>({ ...props.filters });
const warehouses = ref<Array<{ id: number; name: string }>>([]);

// API
const { get } = useApi();

// Méthodes
const applyFilters = (): void => {
  emit('update:filters', { ...localFilters });
};

const resetFilters = (): void => {
  Object.keys(localFilters).forEach(key => {
    localFilters[key] = '';
  });
  emit('reset');
};

const loadWarehouses = async (): Promise<void> => {
  try {
    const response = await get<{ results: Array<{ id: number; name: string }> }>('/api/warehouses/');
    warehouses.value = response.results || [];
  } catch (error) {
    console.error('Erreur lors du chargement des entrepôts:', error);
  }
};

// Watchers
watch(() => props.filters, (newFilters) => {
  Object.assign(localFilters, newFilters);
}, { deep: true });

// Lifecycle
onMounted(() => {
  loadWarehouses();
});
</script>

<style scoped>
.datatable-filters {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}
</style>
```

### 3.3 Composant de Pagination

```vue
<!-- components/DataTablePagination.vue -->
<template>
  <nav aria-label="Pagination du tableau">
    <ul class="pagination justify-content-center mb-0">
      <!-- Bouton Précédent -->
      <li class="page-item" :class="{ disabled: !pagination.has_previous || loading }">
        <button
          class="page-link"
          @click="goToPage(pagination.current_page - 1)"
          :disabled="!pagination.has_previous || loading"
        >
          <i class="fa fa-chevron-left"></i>
          <span class="d-none d-sm-inline"> Précédent</span>
        </button>
      </li>
      
      <!-- Pages -->
      <li
        v-for="page in visiblePages"
        :key="page"
        class="page-item"
        :class="{ active: page === pagination.current_page, disabled: loading }"
      >
        <button
          v-if="page !== '...'"
          class="page-link"
          @click="goToPage(page as number)"
          :disabled="loading"
        >
          {{ page }}
        </button>
        <span v-else class="page-link">...</span>
      </li>
      
      <!-- Bouton Suivant -->
      <li class="page-item" :class="{ disabled: !pagination.has_next || loading }">
        <button
          class="page-link"
          @click="goToPage(pagination.current_page + 1)"
          :disabled="!pagination.has_next || loading"
        >
          <span class="d-none d-sm-inline">Suivant </span>
          <i class="fa fa-chevron-right"></i>
        </button>
      </li>
    </ul>
    
    <!-- Informations de pagination -->
    <div class="pagination-info text-center mt-2">
      <small class="text-muted">
        Page {{ pagination.current_page }} sur {{ pagination.total_pages }}
      </small>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue';

// Props
interface Props {
  pagination: {
    current_page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
    page_size: number;
    total: number;
  };
  loading: boolean;
  maxVisiblePages?: number;
}

const props = withDefaults(defineProps<Props>(), {
  maxVisiblePages: 7
});

// Emits
const emit = defineEmits<{
  'update:page': [page: number];
}>();

// Computed
const visiblePages = computed(() => {
  const { current_page, total_pages } = props.pagination;
  const maxVisible = props.maxVisiblePages;
  const pages: (number | string)[] = [];
  
  if (total_pages <= maxVisible) {
    // Afficher toutes les pages
    for (let i = 1; i <= total_pages; i++) {
      pages.push(i);
    }
  } else {
    // Logique pour afficher les pages avec ellipses
    const halfVisible = Math.floor(maxVisible / 2);
    
    if (current_page <= halfVisible + 1) {
      // Début : 1, 2, 3, 4, 5, ..., last
      for (let i = 1; i <= maxVisible - 2; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total_pages);
    } else if (current_page >= total_pages - halfVisible) {
      // Fin : 1, ..., n-4, n-3, n-2, n-1, n
      pages.push(1);
      pages.push('...');
      for (let i = total_pages - (maxVisible - 3); i <= total_pages; i++) {
        pages.push(i);
      }
    } else {
      // Milieu : 1, ..., current-1, current, current+1, ..., last
      pages.push(1);
      pages.push('...');
      for (let i = current_page - 1; i <= current_page + 1; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total_pages);
    }
  }
  
  return pages;
});

// Méthodes
const goToPage = (page: number): void => {
  if (page >= 1 && page <= props.pagination.total_pages && !props.loading) {
    emit('update:page', page);
  }
};
</script>

<style scoped>
.pagination-info {
  margin-top: 0.5rem;
}

.page-link {
  border: 1px solid #dee2e6;
  color: #6c757d;
}

.page-item.active .page-link {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.page-item.disabled .page-link {
  color: #6c757d;
  pointer-events: none;
  cursor: auto;
  background-color: #fff;
  border-color: #dee2e6;
}
</style>
```

## 4. Composant d'Actions

### 4.1 DataTableActions.vue

```vue
<!-- components/DataTableActions.vue -->
<template>
  <div class="btn-group" role="group">
    <button
      v-for="action in visibleActions"
      :key="action.type"
      type="button"
      class="btn btn-sm"
      :class="getActionClass(action)"
      :title="action.title"
      @click="handleAction(action)"
      :disabled="loading"
    >
      <i :class="action.icon"></i>
      <span v-if="showLabels" class="ms-1">{{ action.title }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ActionButton } from '@/types/datatable';

// Props
interface Props {
  actions: ActionButton[];
  row: any;
  loading?: boolean;
  showLabels?: boolean;
  userPermissions?: string[];
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  showLabels: false,
  userPermissions: () => []
});

// Emits
const emit = defineEmits<{
  action: [action: string, row: any, actionData: ActionButton];
}>();

// Computed
const visibleActions = computed(() => {
  return props.actions.filter(action => {
    // Vérifier les permissions si spécifiées
    if (action.permission && props.userPermissions.length > 0) {
      return props.userPermissions.includes(action.permission);
    }
    return true;
  });
});

// Méthodes
const getActionClass = (action: ActionButton): string => {
  const baseClasses = ['btn-outline-primary'];
  
  switch (action.type) {
    case 'edit':
      return 'btn-outline-primary';
    case 'delete':
      return 'btn-outline-danger';
    case 'view':
      return 'btn-outline-info';
    case 'approve':
      return 'btn-outline-success';
    case 'reject':
      return 'btn-outline-warning';
    default:
      return 'btn-outline-secondary';
  }
};

const handleAction = async (action: ActionButton): Promise<void> => {
  // Confirmation si requise
  if (action.confirm) {
    const confirmed = window.confirm(`Êtes-vous sûr de vouloir ${action.title.toLowerCase()} ?`);
    if (!confirmed) return;
  }
  
  emit('action', action.type, props.row, action);
};
</script>
```

## 5. Utilisation dans une Page

### 5.1 InventoryPage.vue

```vue
<!-- pages/InventoryPage.vue -->
<template>
  <div class="inventory-page">
    <div class="container-fluid">
      <div class="row">
        <div class="col-12">
          <DataTable
            ref="dataTableRef"
            endpoint="/api/inventory/datatable/"
            :columns="columns"
            title="Gestion des Inventaires"
            title-icon="fa fa-boxes"
            :config="tableConfig"
            :initial-filters="initialFilters"
            @row-action="handleRowAction"
            @data-loaded="onDataLoaded"
            @error="onError"
          >
            <template #actions>
              <button @click="exportData('csv')" class="btn btn-success btn-sm">
                <i class="fa fa-download"></i> Export CSV
              </button>
              <button @click="refreshTable" class="btn btn-primary btn-sm">
                <i class="fa fa-refresh"></i> Actualiser
              </button>
              <router-link to="/inventory/create" class="btn btn-primary btn-sm">
                <i class="fa fa-plus"></i> Nouvel inventaire
              </router-link>
            </template>
          </DataTable>
        </div>
      </div>
    </div>
    
    <!-- Modal de confirmation -->
    <ConfirmModal
      v-if="showConfirmModal"
      :title="confirmModal.title"
      :message="confirmModal.message"
      @confirm="confirmAction"
      @cancel="cancelAction"
    />
    
    <!-- Notifications -->
    <NotificationContainer />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useNotifications } from '@/composables/useNotifications';
import { useApi } from '@/composables/useApi';
import DataTable from '@/components/DataTable.vue';
import DataTableActions from '@/components/DataTableActions.vue';
import ConfirmModal from '@/components/ConfirmModal.vue';
import NotificationContainer from '@/components/NotificationContainer.vue';
import type { 
  DataTableColumn, 
  DataTableConfig, 
  DataTableFilters,
  InventoryItem,
  ActionButton
} from '@/types/datatable';

// Composables
const router = useRouter();
const { showNotification } = useNotifications();
const { delete: deleteItem } = useApi();

// Refs
const dataTableRef = ref<InstanceType<typeof DataTable>>();

// État
const showConfirmModal = ref(false);
const confirmModal = reactive({
  title: '',
  message: '',
  action: null as (() => void) | null
});

// Configuration du tableau
const tableConfig: DataTableConfig = {
  pageLength: 25,
  autoRefresh: 30, // Actualisation toutes les 30 secondes
  responsive: true,
  language: {
    url: '/static/datatables/fr.json'
  }
};

// Filtres initiaux
const initialFilters: DataTableFilters = {
  status: 'active'
};

// Configuration des colonnes
const columns: DataTableColumn[] = [
  {
    data: 'id',
    name: 'id',
    title: 'ID',
    width: '60px',
    searchable: false,
    orderable: true
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
    render: (data: string, type: string, row: InventoryItem) => {
      const statusClasses: Record<string, string> = {
        'active': 'badge-success',
        'inactive': 'badge-danger',
        'pending': 'badge-warning'
      };
      const cssClass = statusClasses[row.status] || 'badge-secondary';
      return `<span class="badge ${cssClass}">${data}</span>`;
    }
  },
  {
    data: 'quantity',
    name: 'quantity',
    title: 'Quantité',
    searchable: false,
    orderable: true,
    render: (data: number) => {
      return new Intl.NumberFormat('fr-FR').format(data);
    }
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
    component: DataTableActions
  }
];

// Méthodes
const handleRowAction = async (action: string, row: InventoryItem, actionData?: ActionButton): Promise<void> => {
  switch (action) {
    case 'view':
      router.push(`/inventory/${row.id}`);
      break;
      
    case 'edit':
      router.push(`/inventory/${row.id}/edit`);
      break;
      
    case 'delete':
      confirmModal.title = 'Confirmer la suppression';
      confirmModal.message = `Êtes-vous sûr de vouloir supprimer l'inventaire "${row.label}" ?`;
      confirmModal.action = () => deleteInventory(row.id);
      showConfirmModal.value = true;
      break;
      
    default:
      console.warn('Action non reconnue:', action);
  }
};

const deleteInventory = async (id: number): Promise<void> => {
  try {
    await deleteItem(`/api/inventory/${id}/`);
    showNotification('Inventaire supprimé avec succès', 'success');
    refreshTable();
  } catch (error) {
    console.error('Erreur lors de la suppression:', error);
    showNotification('Erreur lors de la suppression', 'error');
  }
};

const refreshTable = (): void => {
  dataTableRef.value?.refresh();
};

const exportData = (format: 'csv' | 'excel' | 'pdf'): void => {
  dataTableRef.value?.exportData(format);
};

const confirmAction = (): void => {
  if (confirmModal.action) {
    confirmModal.action();
  }
  showConfirmModal.value = false;
  confirmModal.action = null;
};

const cancelAction = (): void => {
  showConfirmModal.value = false;
  confirmModal.action = null;
};

const onDataLoaded = (data: InventoryItem[]): void => {
  console.log('Données chargées:', data.length, 'éléments');
};

const onError = (error: string): void => {
  showNotification(error, 'error');
};

// Lifecycle
onMounted(() => {
  console.log('Page inventaire montée');
});
</script>

<style scoped>
.inventory-page {
  padding: 1rem;
}

@media (max-width: 768px) {
  .inventory-page {
    padding: 0.5rem;
  }
}
</style>
```

## 6. Configuration et Build

### 6.1 Package.json

```json
{
  "name": "vue-datatable-package",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "type-check": "vue-tsc --noEmit",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix --ignore-path .gitignore",
    "format": "prettier --write src/"
  },
  "dependencies": {
    "vue": "^3.3.4",
    "vue-router": "^4.2.4",
    "@vueuse/core": "^10.4.1"
  },
  "devDependencies": {
    "@types/node": "^20.5.9",
    "@typescript-eslint/eslint-plugin": "^6.7.0",
    "@typescript-eslint/parser": "^6.7.0",
    "@vitejs/plugin-vue": "^4.3.4",
    "@vue/eslint-config-prettier": "^8.0.0",
    "@vue/eslint-config-typescript": "^11.0.3",
    "@vue/tsconfig": "^0.4.0",
    "eslint": "^8.49.0",
    "eslint-plugin-vue": "^9.17.0",
    "prettier": "^3.0.3",
    "typescript": "~5.2.0",
    "vite": "^4.4.9",
    "vue-tsc": "^1.8.8"
  }
}
```

### 6.2 Vite.config.ts

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'VueDataTable',
      fileName: 'vue-datatable'
    },
    rollupOptions: {
      external: ['vue', 'vue-router'],
      output: {
        globals: {
          vue: 'Vue',
          'vue-router': 'VueRouter'
        }
      }
    }
  }
});
```

### 6.3 Index d'export

```typescript
// src/index.ts
export { default as DataTable } from './components/DataTable.vue';
export { default as DataTableFilters } from './components/DataTableFilters.vue';
export { default as DataTablePagination } from './components/DataTablePagination.vue';
export { default as DataTableActions } from './components/DataTableActions.vue';

export { useDataTable } from './composables/useDataTable';
export { useApi } from './composables/useApi';

export type * from './types/datatable';
export type * from './types/composables';
```

Cette documentation vous donne une base complète pour intégrer votre package DataTable backend Django avec Vue.js 3 + TypeScript. L'architecture est moderne, type-safe et hautement réutilisable ! 🚀

