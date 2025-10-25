# Exemples Complets - DataTable API

Ce document présente des exemples complets et concrets d'utilisation de l'API DataTable.

## 📋 Scénarios d'utilisation

### Scénario 1 : Affichage simple d'une liste d'items

#### Requête DataTable
```
GET /api/items/?start=0&length=25&draw=1
```

#### Réponse
```json
{
  "draw": 1,
  "recordsTotal": 1500,
  "recordsFiltered": 1500,
  "data": [
    {
      "id": 1,
      "reference_auto": "ITEM-000001",
      "statut": "affecter",
      "article_full_name": "Laptop Dell Latitude - ARTL-001507",
      "affectation_personne_full_name": "ASSOULI khadija",
      "emplacement_nom": "Bureau 101",
      "departement_nom": "Informatique",
      "created_at": "2025-01-11T10:30:00Z",
      "date_affectation": "2025-01-10"
    },
    {
      "id": 2,
      "reference_auto": "ITEM-000002",
      "statut": "non affecter",
      "article_full_name": "Imprimante HP LaserJet - ARTL-000234",
      "affectation_personne_full_name": null,
      "emplacement_nom": "Stock Central",
      "departement_nom": "Administration",
      "created_at": "2025-01-10T15:20:00Z",
      "date_affectation": null
    }
    // ... 23 autres items
  ]
}
```

---

### Scénario 2 : Recherche d'items contenant "laptop"

#### Requête DataTable
```
GET /api/items/?start=0&length=25&search[value]=laptop&draw=2
```

#### Requête REST API équivalente
```
GET /api/items/?page=1&page_size=25&search=laptop
```

#### Réponse
```json
{
  "draw": 2,
  "recordsTotal": 1500,
  "recordsFiltered": 45,
  "data": [
    {
      "id": 1,
      "reference_auto": "ITEM-000001",
      "statut": "affecter",
      "article_full_name": "Laptop Dell Latitude - ARTL-001507",
      "affectation_personne_full_name": "ASSOULI khadija",
      "emplacement_nom": "Bureau 101",
      "departement_nom": "Informatique",
      "created_at": "2025-01-11T10:30:00Z"
    },
    {
      "id": 15,
      "reference_auto": "ITEM-000015",
      "statut": "affecter",
      "article_full_name": "Laptop HP EliteBook - ARTL-002341",
      "affectation_personne_full_name": "BENALI Mohamed",
      "emplacement_nom": "Bureau 205",
      "departement_nom": "Comptabilité",
      "created_at": "2025-01-09T14:15:00Z"
    }
    // ... 23 autres laptops
  ]
}
```

---

### Scénario 3 : Tri par date de création (plus récent en premier)

#### Requête DataTable
```
GET /api/items/?start=0&length=25&order[0][column]=7&order[0][dir]=desc&columns[7][data]=created_at&draw=3
```

#### Requête REST API équivalente
```
GET /api/items/?page=1&page_size=25&ordering=-created_at
```

#### Réponse
```json
{
  "draw": 3,
  "recordsTotal": 1500,
  "recordsFiltered": 1500,
  "data": [
    {
      "id": 1500,
      "reference_auto": "ITEM-001500",
      "created_at": "2025-01-11T16:45:00Z"
      // ... autres champs
    },
    {
      "id": 1499,
      "reference_auto": "ITEM-001499",
      "created_at": "2025-01-11T15:30:00Z"
      // ... autres champs
    }
    // ... les 23 plus récents
  ]
}
```

---

### Scénario 4 : Filtre sur statut "affecter"

#### Requête DataTable
```
GET /api/items/?start=0&length=25&statut_exact=affecter&draw=4
```

#### Requête REST API équivalente
```
GET /api/items/?page=1&page_size=25&statut_exact=affecter
```

#### Réponse
```json
{
  "draw": 4,
  "recordsTotal": 1500,
  "recordsFiltered": 890,
  "data": [
    // ... uniquement les items avec statut="affecter"
  ]
}
```

---

### Scénario 5 : Filtre sur nom complet de personne (colonne composée)

#### Requête DataTable
```
GET /api/items/?start=0&length=25&affectation_personne_full_name_exact=ASSOULI+khadija&draw=5
```

#### Requête REST API équivalente
```
GET /api/items/?page=1&page_size=25&affectation_personne_full_name_exact=ASSOULI khadija
```

#### Réponse
```json
{
  "draw": 5,
  "recordsTotal": 1500,
  "recordsFiltered": 12,
  "data": [
    {
      "id": 1,
      "reference_auto": "ITEM-000001",
      "statut": "affecter",
      "affectation_personne_full_name": "ASSOULI khadija",
      "article_full_name": "Laptop Dell Latitude - ARTL-001507"
      // ... autres champs
    },
    {
      "id": 45,
      "reference_auto": "ITEM-000045",
      "statut": "affecter",
      "affectation_personne_full_name": "ASSOULI khadija",
      "article_full_name": "Souris Logitech - ARTL-003456"
      // ... autres champs
    }
    // ... 10 autres items affectés à ASSOULI khadija
  ]
}
```

---

### Scénario 6 : Recherche + Filtre + Tri combinés

#### Requête DataTable
```
GET /api/items/?start=0&length=10&search[value]=laptop&statut_exact=affecter&order[0][column]=2&order[0][dir]=asc&columns[2][data]=article__designation&draw=6
```

#### Requête REST API équivalente
```
GET /api/items/?page=1&page_size=10&search=laptop&statut_exact=affecter&ordering=article__designation
```

#### Réponse
```json
{
  "draw": 6,
  "recordsTotal": 1500,
  "recordsFiltered": 28,
  "data": [
    {
      "id": 230,
      "reference_auto": "ITEM-000230",
      "statut": "affecter",
      "article_full_name": "Laptop Acer Aspire - ARTL-004567",
      "affectation_personne_full_name": "BENALI Mohamed"
    },
    {
      "id": 1,
      "reference_auto": "ITEM-000001",
      "statut": "affecter",
      "article_full_name": "Laptop Dell Latitude - ARTL-001507",
      "affectation_personne_full_name": "ASSOULI khadija"
    },
    {
      "id": 156,
      "reference_auto": "ITEM-000156",
      "statut": "affecter",
      "article_full_name": "Laptop HP EliteBook - ARTL-002341",
      "affectation_personne_full_name": "CHAKIR Fatima"
    }
    // ... 7 autres laptops affectés, triés par désignation
  ]
}
```

---

### Scénario 7 : Filtre sur intervalle de prix

#### Requête
```
GET /api/items/?start=0&length=25&article__prix_achat_range=5000,10000&draw=7
```

ou en REST API :
```
GET /api/items/?page=1&page_size=25&article__prix_achat_range=5000,10000
```

#### Réponse
```json
{
  "draw": 7,
  "recordsTotal": 1500,
  "recordsFiltered": 234,
  "data": [
    // ... items dont le prix d'achat est entre 5000 et 10000 DH
  ]
}
```

---

### Scénario 8 : Filtre sur items sans tag (NULL)

#### Requête
```
GET /api/items/?start=0&length=25&tag_isnull=true&draw=8
```

ou en REST API :
```
GET /api/items/?page=1&page_size=25&tag_isnull=true
```

#### Réponse
```json
{
  "draw": 8,
  "recordsTotal": 1500,
  "recordsFiltered": 345,
  "data": [
    {
      "id": 567,
      "reference_auto": "ITEM-000567",
      "tag": null,
      "statut": "non affecter"
      // ... items sans tag
    }
  ]
}
```

---

### Scénario 9 : Export Excel avec filtres

#### Requête
```
GET /api/items/?export=excel&statut_exact=affecter&search[value]=laptop
```

ou en REST API :
```
GET /api/items/?export=excel&statut_exact=affecter&search=laptop
```

#### Réponse
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="items_export_2025-01-11_16-30-45.xlsx"

[Fichier Excel binaire contenant tous les laptops affectés]
```

Le fichier Excel contiendra :
- Toutes les colonnes configurées
- Tous les items correspondant aux filtres (pas de pagination)
- En-têtes de colonnes
- Formatage basique

---

### Scénario 10 : Pagination avancée (page 3)

#### Requête DataTable
```
GET /api/items/?start=50&length=25&draw=10
```

#### Requête REST API équivalente
```
GET /api/items/?page=3&page_size=25
```

#### Réponse
```json
{
  "draw": 10,
  "recordsTotal": 1500,
  "recordsFiltered": 1500,
  "data": [
    {
      "id": 51,
      "reference_auto": "ITEM-000051"
      // ... items 51 à 75
    }
  ]
}
```

---

## 🔧 Configuration Frontend

### Exemple jQuery DataTable complet

```javascript
$(document).ready(function() {
    var table = $('#itemsTable').DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: '/api/items/',
            type: 'GET',
            data: function(d) {
                // Ajouter des filtres personnalisés
                d.statut_exact = $('#filter_statut').val();
                d.departement_id = $('#filter_dept').val();
                
                // Filtre de date
                if ($('#filter_date_from').val()) {
                    d.created_at_gte = $('#filter_date_from').val();
                }
                if ($('#filter_date_to').val()) {
                    d.created_at_lte = $('#filter_date_to').val();
                }
            }
        },
        columns: [
            { 
                data: 'reference_auto',
                title: 'Référence'
            },
            { 
                data: 'article_full_name',
                title: 'Article'
            },
            { 
                data: 'affectation_personne_full_name',
                title: 'Affecté à',
                defaultContent: '<em>Non affecté</em>'
            },
            { 
                data: 'emplacement_nom',
                title: 'Emplacement'
            },
            { 
                data: 'departement_nom',
                title: 'Département'
            },
            { 
                data: 'statut',
                title: 'Statut',
                render: function(data) {
                    if (data === 'affecter') {
                        return '<span class="badge badge-success">Affecté</span>';
                    }
                    return '<span class="badge badge-secondary">Non affecté</span>';
                }
            },
            { 
                data: 'created_at',
                title: 'Date création',
                render: function(data) {
                    return new Date(data).toLocaleDateString('fr-FR');
                }
            }
        ],
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        order: [[6, 'desc']], // Tri par date de création descendant
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/fr-FR.json'
        }
    });
    
    // Bouton Export Excel
    $('#btn_export_excel').on('click', function() {
        var url = '/api/items/?export=excel';
        
        // Ajouter les filtres actifs
        var filters = table.ajax.params();
        delete filters.draw;
        delete filters.start;
        delete filters.length;
        
        url += '&' + $.param(filters);
        window.location.href = url;
    });
    
    // Filtres personnalisés
    $('#filter_statut, #filter_dept').on('change', function() {
        table.ajax.reload();
    });
});
```

### HTML correspondant

```html
<div class="card">
    <div class="card-header">
        <h3>Liste des Items</h3>
        <div class="row mt-3">
            <div class="col-md-3">
                <label>Statut</label>
                <select id="filter_statut" class="form-control">
                    <option value="">Tous</option>
                    <option value="affecter">Affecté</option>
                    <option value="non affecter">Non affecté</option>
                </select>
            </div>
            <div class="col-md-3">
                <label>Département</label>
                <select id="filter_dept" class="form-control">
                    <option value="">Tous</option>
                    <option value="1">Informatique</option>
                    <option value="2">Comptabilité</option>
                    <!-- ... -->
                </select>
            </div>
            <div class="col-md-3">
                <label>Date de</label>
                <input type="date" id="filter_date_from" class="form-control">
            </div>
            <div class="col-md-3">
                <label>Date à</label>
                <input type="date" id="filter_date_to" class="form-control">
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-12">
                <button id="btn_export_excel" class="btn btn-success">
                    <i class="fa fa-file-excel"></i> Export Excel
                </button>
            </div>
        </div>
    </div>
    <div class="card-body">
        <table id="itemsTable" class="table table-striped table-bordered">
            <!-- Les colonnes sont définies dans DataTable -->
        </table>
    </div>
</div>
```

---

## 🚀 Exemple Vue.js 3 + Composition API

```vue
<template>
  <div class="items-list">
    <div class="filters">
      <input 
        v-model="filters.search" 
        @input="debouncedSearch"
        placeholder="Rechercher..."
        class="form-control"
      />
      
      <select v-model="filters.statut" @change="loadItems" class="form-control">
        <option value="">Tous les statuts</option>
        <option value="affecter">Affecté</option>
        <option value="non affecter">Non affecté</option>
      </select>
      
      <button @click="exportExcel" class="btn btn-success">
        Export Excel
      </button>
    </div>
    
    <table class="table">
      <thead>
        <tr>
          <th @click="sort('reference_auto')">Référence</th>
          <th @click="sort('article__designation')">Article</th>
          <th @click="sort('affectation_personne__nom')">Affecté à</th>
          <th @click="sort('statut')">Statut</th>
          <th @click="sort('created_at')">Date</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.reference_auto }}</td>
          <td>{{ item.article_full_name }}</td>
          <td>{{ item.affectation_personne_full_name || '-' }}</td>
          <td>
            <span :class="statusClass(item.statut)">
              {{ item.statut }}
            </span>
          </td>
          <td>{{ formatDate(item.created_at) }}</td>
        </tr>
      </tbody>
    </table>
    
    <div class="pagination">
      <button @click="prevPage" :disabled="page === 1">Précédent</button>
      <span>Page {{ page }} / {{ totalPages }}</span>
      <button @click="nextPage" :disabled="page >= totalPages">Suivant</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { debounce } from 'lodash'

const items = ref([])
const page = ref(1)
const pageSize = ref(25)
const totalRecords = ref(0)
const filters = reactive({
  search: '',
  statut: '',
  ordering: '-created_at'
})

const totalPages = computed(() => Math.ceil(totalRecords.value / pageSize.value))

async function loadItems() {
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      ...filters
    }
    
    // Supprimer les filtres vides
    Object.keys(params).forEach(key => {
      if (params[key] === '') delete params[key]
    })
    
    const response = await axios.get('/api/items/', { params })
    
    items.value = response.data.results
    totalRecords.value = response.data.count
  } catch (error) {
    console.error('Erreur chargement items:', error)
  }
}

const debouncedSearch = debounce(() => {
  page.value = 1
  loadItems()
}, 500)

function sort(field) {
  if (filters.ordering === field) {
    filters.ordering = '-' + field
  } else if (filters.ordering === '-' + field) {
    filters.ordering = field
  } else {
    filters.ordering = field
  }
  loadItems()
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    loadItems()
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    loadItems()
  }
}

async function exportExcel() {
  const params = { ...filters, export: 'excel' }
  delete params.ordering
  
  const queryString = new URLSearchParams(params).toString()
  window.location.href = `/api/items/?${queryString}`
}

function statusClass(statut) {
  return statut === 'affecter' ? 'badge badge-success' : 'badge badge-secondary'
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('fr-FR')
}

onMounted(() => {
  loadItems()
})
</script>
```

---

## 📊 Résumé des opérateurs disponibles

| Opérateur | Utilisation | Exemple |
|-----------|-------------|---------|
| `exact` | Égalité exacte | `statut_exact=affecter` |
| `icontains` | Contient (insensible) | `nom_icontains=bureau` |
| `startswith` | Commence par | `code_startswith=ARTL` |
| `endswith` | Termine par | `ref_endswith=001` |
| `gt` | Supérieur à | `prix_gt=1000` |
| `gte` | Supérieur ou égal | `prix_gte=1000` |
| `lt` | Inférieur à | `prix_lt=5000` |
| `lte` | Inférieur ou égal | `prix_lte=5000` |
| `in` | Dans liste | `statut_in=affecter,archive` |
| `range` | Intervalle | `prix_range=1000,5000` |
| `isnull` | Est null | `tag_isnull=true` |
| `date` | Date exacte | `created_at_date=2025-01-11` |
| `year` | Année | `created_at_year=2025` |
| `month` | Mois | `created_at_month=1` |
| `day` | Jour | `created_at_day=15` |

---

**Version :** 1.0  
**Date :** 2025-01-11

