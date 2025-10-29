# Guide des Paramètres API DataTable vs REST API

Ce guide présente la correspondance entre les paramètres DataTables (frontend) et les paramètres REST API (backend).

## 📋 Table de correspondance complète

| Fonctionnalité | Paramètre DataTable | Paramètre REST API | Exemple DataTable | Exemple REST API | Description |
|----------------|---------------------|-------------------|-------------------|------------------|-------------|
| **Pagination** |
| Page | `start=0` | `page=1` | `start=0` | `page=1` | Début de la page (DataTable utilise l'offset, API utilise le numéro de page) |
| Taille de page | `length=25` | `page_size=25` | `length=25` | `page_size=25` | Nombre d'éléments par page |
| **Tri** |
| Tri simple | `order[0][column]=2&order[0][dir]=asc` | `ordering=field` | `order[0][column]=2&order[0][dir]=asc` | `ordering=nom` | Tri par colonne (DataTable utilise l'index, API utilise le nom du champ) |
| Tri descendant | `order[0][column]=2&order[0][dir]=desc` | `ordering=-field` | `order[0][column]=2&order[0][dir]=desc` | `ordering=-nom` | Tri descendant (préfixe `-` pour l'API) |
| Tri multiple | `order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc` | `ordering=field1,-field2` | `order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc` | `ordering=nom,-date` | Tri sur plusieurs colonnes |
| **Recherche** |
| Recherche globale | `search[value]=texte` | `search=texte` | `search[value]=laptop` | `search=laptop` | Recherche dans toutes les colonnes configurées |
| Recherche par colonne | `columns[2][search][value]=texte` | `field_icontains=texte` | `columns[2][search][value]=Dell` | `marque_icontains=Dell` | Recherche dans une colonne spécifique |
| **Filtres dynamiques** |
| Égalité exacte | `field_exact=value` | `field_exact=value` | `statut_exact=affecter` | `statut_exact=affecter` | Filtre exact |
| Contient (insensible) | `field_icontains=value` | `field_icontains=value` | `nom_icontains=bureau` | `nom_icontains=bureau` | Contient le texte (insensible à la casse) |
| Commence par | `field_startswith=value` | `field_startswith=value` | `code_startswith=ARTL` | `code_startswith=ARTL` | Commence par |
| Termine par | `field_endswith=value` | `field_endswith=value` | `reference_endswith=001` | `reference_endswith=001` | Termine par |
| Supérieur à | `field_gt=value` | `field_gt=value` | `prix_gt=1000` | `prix_gt=1000` | Supérieur à |
| Supérieur ou égal | `field_gte=value` | `field_gte=value` | `prix_gte=1000` | `prix_gte=1000` | Supérieur ou égal à |
| Inférieur à | `field_lt=value` | `field_lt=value` | `prix_lt=5000` | `prix_lt=5000` | Inférieur à |
| Inférieur ou égal | `field_lte=value` | `field_lte=value` | `prix_lte=5000` | `prix_lte=5000` | Inférieur ou égal à |
| Dans une liste | `field_in=val1,val2,val3` | `field_in=val1,val2,val3` | `statut_in=affecter,non affecter` | `statut_in=affecter,non affecter` | Valeur dans la liste |
| Range | `field_range=min,max` | `field_range=min,max` | `prix_range=1000,5000` | `prix_range=1000,5000` | Entre deux valeurs |
| Date | `field_date=2025-01-11` | `field_date=2025-01-11` | `created_at_date=2025-01-11` | `created_at_date=2025-01-11` | Date exacte |
| Année | `field_year=2025` | `field_year=2025` | `created_at_year=2025` | `created_at_year=2025` | Année |
| Mois | `field_month=1` | `field_month=1` | `created_at_month=1` | `created_at_month=1` | Mois (1-12) |
| Null/Non-null | `field_isnull=true` ou `false` | `field_isnull=true` ou `false` | `tag_isnull=true` | `tag_isnull=true` | Champ null ou non-null |
| **Colonnes composées** |
| Filtre composé exact | `composite_field_exact=value` | `composite_field_exact=value` | `affectation_personne_full_name_exact=ASSOULI khadija` | `affectation_personne_full_name_exact=ASSOULI khadija` | Filtre exact sur colonne composée (concat) |
| Filtre composé contient | `composite_field_icontains=value` | `composite_field_icontains=value` | `affectation_personne_full_name_icontains=ASSOULI` | `affectation_personne_full_name_icontains=ASSOULI` | Contient dans colonne composée |
| **Export** |
| Export format | `export=excel` ou `csv` | `export=excel` ou `csv` | `export=excel` | `export=excel` | Format d'export (Excel ou CSV) |
| **Informations DataTable** |
| Draw counter | `draw=1` | - | `draw=1` | - | Compteur de requête DataTable (pour synchronisation) |

## 🔍 Exemples d'URLs complètes

### Exemple 1 : Liste simple avec pagination
```
DataTable:
/api/items/?start=0&length=25&draw=1

REST API:
/api/items/?page=1&page_size=25
```

### Exemple 2 : Recherche globale
```
DataTable:
/api/items/?start=0&length=25&search[value]=laptop&draw=1

REST API:
/api/items/?page=1&page_size=25&search=laptop
```

### Exemple 3 : Tri par nom ascendant
```
DataTable:
/api/items/?start=0&length=25&order[0][column]=2&order[0][dir]=asc&columns[2][data]=nom&draw=1

REST API:
/api/items/?page=1&page_size=25&ordering=nom
```

### Exemple 4 : Tri descendant par date
```
DataTable:
/api/items/?start=0&length=25&order[0][column]=5&order[0][dir]=desc&columns[5][data]=created_at&draw=1

REST API:
/api/items/?page=1&page_size=25&ordering=-created_at
```

### Exemple 5 : Filtre exact sur statut
```
DataTable:
/api/items/?start=0&length=25&statut_exact=affecter&draw=1

REST API:
/api/items/?page=1&page_size=25&statut_exact=affecter
```

### Exemple 6 : Filtre avec recherche contenant
```
DataTable:
/api/items/?start=0&length=25&marque_icontains=Dell&draw=1

REST API:
/api/items/?page=1&page_size=25&marque_icontains=Dell
```

### Exemple 7 : Filtre sur range de prix
```
DataTable:
/api/items/?start=0&length=25&prix_range=1000,5000&draw=1

REST API:
/api/items/?page=1&page_size=25&prix_range=1000,5000
```

### Exemple 8 : Recherche + Tri + Filtre combinés
```
DataTable:
/api/items/?start=0&length=25&search[value]=laptop&order[0][column]=2&order[0][dir]=asc&columns[2][data]=nom&statut_exact=affecter&draw=1

REST API:
/api/items/?page=1&page_size=25&search=laptop&ordering=nom&statut_exact=affecter
```

### Exemple 9 : Filtre sur colonne composée (nom complet)
```
DataTable:
/api/items/?start=0&length=25&affectation_personne_full_name_exact=ASSOULI khadija&draw=1

REST API:
/api/items/?page=1&page_size=25&affectation_personne_full_name_exact=ASSOULI khadija
```

### Exemple 10 : Export en Excel
```
DataTable:
/api/items/?export=excel&search[value]=laptop&statut_exact=affecter

REST API:
/api/items/?export=excel&search=laptop&statut_exact=affecter
```

## 📊 Format de réponse

### Réponse DataTable (JSON)
```json
{
  "draw": 1,
  "recordsTotal": 1500,
  "recordsFiltered": 45,
  "data": [
    {
      "id": 1,
      "reference_auto": "ITEM-000001",
      "statut": "affecter",
      "article_full_name": "Laptop Dell - ARTL-001507",
      "affectation_personne_full_name": "ASSOULI khadija",
      "emplacement_nom": "Bureau 101",
      "departement_nom": "IT",
      "created_at": "2025-01-11T10:30:00Z"
    },
    // ... autres items
  ]
}
```

### Réponse REST API (JSON)
```json
{
  "count": 1500,
  "next": "http://api.example.com/items/?page=2&page_size=25",
  "previous": null,
  "results": [
    {
      "id": 1,
      "reference_auto": "ITEM-000001",
      "statut": "affecter",
      "article_full_name": "Laptop Dell - ARTL-001507",
      "affectation_personne_full_name": "ASSOULI khadija",
      "emplacement_nom": "Bureau 101",
      "departement_nom": "IT",
      "created_at": "2025-01-11T10:30:00Z"
    },
    // ... autres items
  ]
}
```

## 🔧 Configuration Backend

### Colonnes searchables (recherche globale)
```python
search_fields = [
    'reference_auto',
    'article__designation',
    'article__code_article',
    'affectation_personne__nom',
    'affectation_personne__prenom',
    'emplacement__nom',
    'departement__nom',
]
```

### Colonnes triables
```python
ordering_fields = [
    'reference_auto',
    'statut',
    'article__designation',
    'affectation_personne__nom',
    'emplacement__nom',
    'departement__nom',
    'created_at',
    'date_affectation',
]
```

### Colonnes composées (concatenation)
```python
composite_columns = {
    'affectation_personne_full_name': {
        'type': 'concat',
        'fields': ['affectation_personne__nom', 'affectation_personne__prenom'],
        'separator': ' '
    },
    'article_full_name': {
        'type': 'concat',
        'fields': ['article__designation', 'article__code_article'],
        'separator': ' - '
    }
}
```

### Mapping de filtres (aliases)
```python
filter_aliases = {
    'article_designation': 'article__designation',
    'article_code': 'article__code_article',
    'marque': 'article__marque__nom',
    'zone': 'emplacement__zone__nom',
    'location': 'emplacement__zone__location__nom',
}
```

## 🎯 Bonnes pratiques

### 1. Pagination
- Utilisez toujours la pagination pour améliorer les performances
- Taille de page recommandée : 10-50 éléments
- Maximum : 100 éléments par page

### 2. Recherche
- La recherche globale (`search`) cherche dans tous les champs définis dans `search_fields`
- Pour des recherches précises, utilisez des filtres spécifiques (`field_icontains`, `field_exact`)

### 3. Tri
- Tri par défaut : `-created_at` (plus récent en premier)
- Pour tri ascendant : `ordering=field`
- Pour tri descendant : `ordering=-field`
- Tri multiple : `ordering=field1,-field2,field3`

### 4. Filtres
- Utilisez `_exact` pour des correspondances exactes
- Utilisez `_icontains` pour des recherches partielles (insensible à la casse)
- Utilisez `_in` pour filtrer sur plusieurs valeurs
- Utilisez `_range` pour des intervalles

### 5. Performance
- Limitez le nombre de colonnes retournées si possible
- Utilisez `select_related` et `prefetch_related` côté backend
- Évitez les recherches trop larges sans filtres

### 6. Export
- Les exports respectent tous les filtres actifs
- Format Excel : meilleur pour l'analyse
- Format CSV : plus léger, meilleur pour l'import

## 📝 Notes importantes

1. **draw** : Paramètre DataTable uniquement, utilisé pour synchroniser les requêtes asynchrones
2. **start vs page** : DataTable utilise l'offset (start=0, 25, 50...), REST API utilise le numéro de page (page=1, 2, 3...)
3. **Conversion automatique** : Le backend convertit automatiquement les paramètres DataTable en paramètres REST API
4. **Colonnes composées** : Gérées nativement par le backend via `composite_columns`
5. **Opérateurs** : Le backend convertit automatiquement `equals` en `exact` pour compatibilité

## 🔄 Conversion Start/Page

### Formule de conversion
```
page = (start / length) + 1
start = (page - 1) * length
```

### Exemples
| DataTable (start, length) | REST API (page, page_size) |
|---------------------------|---------------------------|
| start=0, length=25 | page=1, page_size=25 |
| start=25, length=25 | page=2, page_size=25 |
| start=50, length=25 | page=3, page_size=25 |
| start=0, length=10 | page=1, page_size=10 |
| start=100, length=50 | page=3, page_size=50 |

## 🚀 Exemples d'intégration Frontend

### jQuery DataTable
```javascript
$('#myTable').DataTable({
    processing: true,
    serverSide: true,
    ajax: {
        url: '/api/items/',
        type: 'GET',
        data: function(d) {
            // Ajouter des filtres personnalisés
            d.statut_exact = $('#filter_statut').val();
            d.departement_id = $('#filter_dept').val();
        }
    },
    columns: [
        { data: 'reference_auto' },
        { data: 'article_full_name' },
        { data: 'affectation_personne_full_name' },
        { data: 'emplacement_nom' },
        { data: 'statut' },
        { data: 'created_at' }
    ]
});
```

### Axios (Vue.js, React)
```javascript
async function fetchItems(page = 1, pageSize = 25, filters = {}) {
    const params = {
        page: page,
        page_size: pageSize,
        ...filters
    };
    
    const response = await axios.get('/api/items/', { params });
    return response.data;
}

// Utilisation
const items = await fetchItems(1, 25, {
    search: 'laptop',
    ordering: '-created_at',
    statut_exact: 'affecter'
});
```

### Fetch API (Vanilla JS)
```javascript
async function fetchItems(filters = {}) {
    const params = new URLSearchParams({
        page: 1,
        page_size: 25,
        ...filters
    });
    
    const response = await fetch(`/api/items/?${params}`);
    const data = await response.json();
    return data;
}
```

---

**Version :** 1.0  
**Date :** 2025-01-11  
**Auteur :** Solution AMS Backend Team

