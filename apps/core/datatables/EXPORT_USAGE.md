# Guide d'utilisation de l'export DataTable (Frontend)

## 📥 Vue d'ensemble

Toutes les 12 APIs DataTable supportent maintenant l'export Excel et CSV **activé par défaut**.

L'export respecte automatiquement tous les filtres, recherches et tris appliqués dans le DataTable.

---

## 🚀 Utilisation rapide

### Méthode 1 : URL directe (la plus simple)

```typescript
// Export Excel
window.open('/items/all_items/?export=excel', '_blank');

// Export CSV
window.open('/items/all_items/?export=csv', '_blank');

// Avec filtres
window.open('/items/all_items/?export=excel&statut_exact=affecter&departement_exact=IT', '_blank');
```

### Méthode 2 : Fonction JavaScript

```javascript
function exportData(endpoint, format = 'excel', filters = {}) {
  // Construire les paramètres
  const params = new URLSearchParams();
  params.append('export', format);
  
  // Ajouter les filtres
  Object.entries(filters).forEach(([key, value]) => {
    params.append(key, value);
  });
  
  // Ouvrir dans un nouvel onglet
  const url = `${endpoint}?${params.toString()}`;
  window.open(url, '_blank');
}

// Utilisation
exportData('/items/all_items/', 'excel', {
  statut_exact: 'affecter',
  departement_exact: 'IT'
});
```

### Méthode 3 : Bouton HTML simple

```html
<!-- Export Excel -->
<button onclick="window.open('/items/all_items/?export=excel', '_blank')" 
        class="btn btn-success">
  <i class="fa fa-file-excel"></i> Export Excel
</button>

<!-- Export CSV -->
<button onclick="window.open('/items/all_items/?export=csv', '_blank')" 
        class="btn btn-primary">
  <i class="fa fa-file-csv"></i> Export CSV
</button>
```

---

## 🎯 Intégration Vue 3 + TypeScript

### Composable `useDataTableExport`

```typescript
// composables/useDataTableExport.ts
import { ref } from 'vue';

export interface ExportOptions {
  endpoint: string;
  format: 'excel' | 'csv';
  filters?: Record<string, any>;
  search?: string;
  ordering?: string;
}

export function useDataTableExport() {
  const isExporting = ref(false);
  
  const exportData = (options: ExportOptions): void => {
    isExporting.value = true;
    
    try {
      // Construire l'URL avec tous les paramètres
      const params = new URLSearchParams();
      params.append('export', options.format);
      
      // Ajouter les filtres
      if (options.filters) {
        Object.entries(options.filters).forEach(([key, value]) => {
          if (value !== null && value !== undefined && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      
      // Ajouter la recherche
      if (options.search) {
        params.append('search[value]', options.search);
      }
      
      // Ajouter le tri
      if (options.ordering) {
        params.append('ordering', options.ordering);
      }
      
      // Ouvrir le téléchargement
      const url = `${options.endpoint}?${params.toString()}`;
      window.open(url, '_blank');
      
    } finally {
      // Réinitialiser après un court délai
      setTimeout(() => {
        isExporting.value = false;
      }, 1000);
    }
  };
  
  return {
    isExporting,
    exportData
  };
}
```

### Composant DataTable avec export

```vue
<template>
  <div class="datatable-container">
    <!-- En-tête avec boutons d'export -->
    <div class="datatable-header">
      <h3>{{ title }}</h3>
      
      <div class="export-buttons">
        <button 
          @click="handleExport('excel')"
          :disabled="isExporting"
          class="btn btn-success btn-sm">
          <i class="fa fa-file-excel"></i>
          {{ isExporting ? 'Export en cours...' : 'Export Excel' }}
        </button>
        
        <button 
          @click="handleExport('csv')"
          :disabled="isExporting"
          class="btn btn-primary btn-sm">
          <i class="fa fa-file-csv"></i>
          {{ isExporting ? 'Export en cours...' : 'Export CSV' }}
        </button>
      </div>
    </div>
    
    <!-- DataTable -->
    <DataTable
      :endpoint="endpoint"
      :columns="columns"
      v-model:filters="filters"
      v-model:search="search"
      v-model:ordering="ordering"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useDataTableExport } from '@/composables/useDataTableExport';

interface Props {
  title: string;
  endpoint: string;
  columns: any[];
}

const props = defineProps<Props>();

const { isExporting, exportData } = useDataTableExport();

const filters = ref({});
const search = ref('');
const ordering = ref('-created_at');

const handleExport = (format: 'excel' | 'csv') => {
  exportData({
    endpoint: props.endpoint,
    format,
    filters: filters.value,
    search: search.value,
    ordering: ordering.value
  });
};
</script>

<style scoped>
.datatable-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.export-buttons {
  display: flex;
  gap: 0.5rem;
}

.export-buttons button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
```

### Utilisation du composant

```vue
<template>
  <DataTableWithExport
    title="Liste des Items"
    endpoint="/items/all_items/"
    :columns="itemColumns"
  />
</template>

<script setup lang="ts">
import DataTableWithExport from '@/components/DataTableWithExport.vue';

const itemColumns = [
  { field: 'id', headerName: 'ID', sortable: true },
  { field: 'reference_auto', headerName: 'Référence', sortable: true },
  { field: 'article_designation', headerName: 'Article', sortable: true },
  { field: 'statut', headerName: 'Statut', sortable: true },
];
</script>
```

---

## 🔥 Intégration avec DataTable.js (jQuery)

### HTML + jQuery

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
</head>
<body>
  <div class="container">
    <h2>Liste des Items</h2>
    
    <!-- Boutons d'export -->
    <div class="mb-3">
      <button id="exportExcel" class="btn btn-success">
        <i class="fa fa-file-excel"></i> Export Excel
      </button>
      <button id="exportCsv" class="btn btn-primary">
        <i class="fa fa-file-csv"></i> Export CSV
      </button>
    </div>
    
    <!-- DataTable -->
    <table id="itemsTable" class="display" style="width:100%">
      <thead>
        <tr>
          <th>ID</th>
          <th>Référence</th>
          <th>Article</th>
          <th>Statut</th>
        </tr>
      </thead>
    </table>
  </div>

  <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
  
  <script>
    $(document).ready(function() {
      // Initialiser DataTable
      const table = $('#itemsTable').DataTable({
        processing: true,
        serverSide: true,
        ajax: {
          url: '/items/all_items/',
          type: 'GET',
          data: function(d) {
            // Ajouter des filtres personnalisés si nécessaire
            d.statut_exact = $('#filterStatut').val();
            d.departement_exact = $('#filterDepartement').val();
          }
        },
        columns: [
          { data: 'id' },
          { data: 'reference_auto' },
          { data: 'article_designation' },
          { data: 'statut' }
        ]
      });
      
      // Fonction d'export
      function exportTable(format) {
        // Récupérer les paramètres actuels du DataTable
        const params = table.ajax.params();
        
        // Construire l'URL d'export
        const urlParams = new URLSearchParams();
        urlParams.append('export', format);
        
        // Ajouter les filtres
        Object.entries(params).forEach(([key, value]) => {
          if (key !== 'draw' && key !== 'start' && key !== 'length') {
            urlParams.append(key, value);
          }
        });
        
        // Ouvrir le téléchargement
        window.open('/items/all_items/?' + urlParams.toString(), '_blank');
      }
      
      // Boutons d'export
      $('#exportExcel').on('click', function() {
        exportTable('excel');
      });
      
      $('#exportCsv').on('click', function() {
        exportTable('csv');
      });
    });
  </script>
</body>
</html>
```

---

## 📋 Liste des endpoints avec export

Tous les endpoints suivants supportent `?export=excel` et `?export=csv` :

| Endpoint | Nom du fichier exporté | Description |
|----------|----------------------|-------------|
| `/article/all_articles/` | `articles_<timestamp>` | Liste des articles |
| `/items/all_items/` | `items_<timestamp>` | Liste des items actifs |
| `/items/archive/` | `items_archives_<timestamp>` | Items archivés |
| `/inventaire/all_inventaire/` | `inventaires_emplacement_<timestamp>` | Inventaires par emplacement |
| `/inventaire/all_inventaire_location/` | `inventaires_location_<timestamp>` | Inventaires par location |
| `/inventaire/all_inventaire_zone/` | `inventaires_zone_<timestamp>` | Inventaires par zone |
| `/inventaire/all_inventaire_departement/` | `inventaires_departement_<timestamp>` | Inventaires par département |
| `/inventaire/edit_inventaire/{id}/` | `inventaire_emplacements_detail_<timestamp>` | Détails emplacements |
| `/inventaire/inventaire_detail_emplacement/{id}/` | `inventaire_details_operateurs_<timestamp>` | Détails avec opérateurs |
| `/inventaire/detail-inventaire/{id}/` | `detail_inventaire_<timestamp>` | Détails d'inventaire |
| `/article/all_articles_Consommes/` | `articles_consommes_<timestamp>` | Articles consommés |
| `/transfers/{item_id}/` | `transferts_historique_<timestamp>` | Historique transferts |

---

## 🎨 Exemples d'URLs complètes

### Export simple
```
GET /items/all_items/?export=excel
GET /items/all_items/?export=csv
```

### Export avec filtres
```
GET /items/all_items/?export=excel&statut_exact=affecter
GET /items/all_items/?export=excel&statut_exact=affecter&departement_exact=IT
GET /items/all_items/?export=excel&affectation_personne_full_name_icontains=khadija
```

### Export avec recherche
```
GET /items/all_items/?export=excel&search[value]=Bureau
```

### Export avec tri
```
GET /items/all_items/?export=excel&ordering=-created_at
GET /items/all_items/?export=excel&ordering=article__designation
```

### Export avec tout combiné
```
GET /items/all_items/?export=excel&statut_exact=affecter&search[value]=Dell&ordering=-created_at
```

---

## 🔧 Configuration avancée

### Personnaliser le nom du fichier (Backend)

```python
class ItemListAPIView(ServerSideDataTableView):
    export_filename = 'mes_items'  # Résultat: mes_items_20241010_153045.xlsx
```

### Désactiver l'export pour une API spécifique

```python
class ItemListAPIView(ServerSideDataTableView):
    enable_export = False  # Désactive l'export
```

### Supporter uniquement Excel

```python
class ItemListAPIView(ServerSideDataTableView):
    export_formats = ['excel']  # Uniquement Excel, pas CSV
```

### Ajouter PDF (nécessite extension)

```python
from datatables.exporters import PDFExporter, export_manager

# Enregistrer l'exporter PDF
export_manager.register_exporter('pdf', PDFExporter())

class ItemListAPIView(ServerSideDataTableView):
    export_formats = ['excel', 'csv', 'pdf']
```

---

## 💡 Bonnes pratiques

### 1. Afficher un indicateur de chargement

```typescript
const handleExport = async (format: 'excel' | 'csv') => {
  isExporting.value = true;
  
  // Afficher une notification
  toast.info('Export en cours...');
  
  exportData({ endpoint, format, filters });
  
  // Réinitialiser après un court délai
  setTimeout(() => {
    isExporting.value = false;
    toast.success('Export terminé !');
  }, 2000);
};
```

### 2. Limiter la taille de l'export

```typescript
// Avertir l'utilisateur si trop de données
if (totalRecords > 10000) {
  const confirmed = confirm(
    `Vous allez exporter ${totalRecords} enregistrements. Continuer ?`
  );
  if (!confirmed) return;
}

exportData({ endpoint, format, filters });
```

### 3. Gérer les erreurs

```typescript
const handleExport = async (format: 'excel' | 'csv') => {
  try {
    const params = new URLSearchParams();
    params.append('export', format);
    // ... ajouter filtres
    
    const response = await fetch(`${endpoint}?${params}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Erreur lors de l\'export');
    }
    
    // Télécharger le fichier
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${Date.now()}.${format === 'excel' ? 'xlsx' : 'csv'}`;
    a.click();
    
  } catch (error) {
    console.error('Erreur export:', error);
    toast.error(error.message);
  }
};
```

---

## 🚨 Dépannage

### L'export ne fonctionne pas

1. **Vérifier que openpyxl est installé** (pour Excel)
   ```bash
   pip install openpyxl
   ```

2. **Vérifier que l'export est activé**
   ```python
   enable_export = True  # Dans la vue
   ```

3. **Vérifier les formats supportés**
   ```python
   export_formats = ['excel', 'csv']  # Dans la vue
   ```

### Le fichier est vide

- L'export respecte les filtres appliqués
- Vérifiez que votre queryset retourne des données
- Vérifiez que le serializer fonctionne correctement

### Erreur "Format non supporté"

```json
{
  "error": "Format d'export non supporté: pdf",
  "supported_formats": ["excel", "csv"]
}
```

Solution : Utilisez uniquement les formats configurés dans `export_formats`

---

## 📚 Ressources

- **Documentation backend** : `datatables/exporters.py`
- **Guide DataTable** : `masterdata/DATATABLE_API_GUIDE.md`
- **Contrat Frontend-Backend** : `datatables/FRONTEND_BACKEND_CONTRACT.md`

---

**Dernière mise à jour** : Octobre 2024
**Formats supportés** : Excel (.xlsx), CSV (.csv)
**APIs avec export** : 12/12 ✅

