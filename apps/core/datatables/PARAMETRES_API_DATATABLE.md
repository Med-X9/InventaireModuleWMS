# Paramètres API DataTable - Référence Rapide

## 📊 Tableau de correspondance complet

| Fonctionnalité | Paramètre DataTable | Paramètre REST API | Exemple DT | Exemple API |
|----------------|---------------------|-------------------|------------|-------------|
| **PAGINATION** |
| Page (offset) | `start=0` | `page=1` | `start=0` | `page=1` |
| Page suivante | `start=25` | `page=2` | `start=25` | `page=2` |
| Taille de page | `length=25` | `page_size=25` | `length=25` | `page_size=25` |
| **TRI** |
| Tri ascendant | `order[0][column]=2&order[0][dir]=asc` | `ordering=nom` | `order[0][column]=2&order[0][dir]=asc` | `ordering=nom` |
| Tri descendant | `order[0][column]=2&order[0][dir]=desc` | `ordering=-nom` | `order[0][column]=2&order[0][dir]=desc` | `ordering=-nom` |
| Tri multiple | `order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc` | `ordering=nom,-date` | Multiple colonnes | `ordering=nom,-date` |
| **RECHERCHE** |
| Recherche globale | `search[value]=texte` | `search=texte` | `search[value]=laptop` | `search=laptop` |
| Recherche par colonne | `columns[2][search][value]=texte` | `field_icontains=texte` | Colonne spécifique | `nom_icontains=texte` |
| **FILTRES DE BASE** |
| Égalité exacte | `field_exact=value` | `field_exact=value` | `statut_exact=affecter` | `statut_exact=affecter` |
| Contient (case-insensitive) | `field_icontains=value` | `field_icontains=value` | `nom_icontains=bureau` | `nom_icontains=bureau` |
| Commence par | `field_startswith=value` | `field_startswith=value` | `code_startswith=ARTL` | `code_startswith=ARTL` |
| Termine par | `field_endswith=value` | `field_endswith=value` | `ref_endswith=001` | `ref_endswith=001` |
| **FILTRES NUMÉRIQUES** |
| Supérieur à | `field_gt=value` | `field_gt=value` | `prix_gt=1000` | `prix_gt=1000` |
| Supérieur ou égal | `field_gte=value` | `field_gte=value` | `prix_gte=1000` | `prix_gte=1000` |
| Inférieur à | `field_lt=value` | `field_lt=value` | `prix_lt=5000` | `prix_lt=5000` |
| Inférieur ou égal | `field_lte=value` | `field_lte=value` | `prix_lte=5000` | `prix_lte=5000` |
| Dans une liste | `field_in=val1,val2` | `field_in=val1,val2` | `statut_in=affecter,archive` | `statut_in=affecter,archive` |
| Intervalle (range) | `field_range=min,max` | `field_range=min,max` | `prix_range=1000,5000` | `prix_range=1000,5000` |
| **FILTRES DE DATES** |
| Date exacte | `field_date=2025-01-11` | `field_date=2025-01-11` | `created_at_date=2025-01-11` | `created_at_date=2025-01-11` |
| Année | `field_year=2025` | `field_year=2025` | `created_at_year=2025` | `created_at_year=2025` |
| Mois | `field_month=1` | `field_month=1` | `created_at_month=1` | `created_at_month=1` |
| Jour | `field_day=15` | `field_day=15` | `created_at_day=15` | `created_at_day=15` |
| **FILTRES BOOLÉENS** |
| Est null | `field_isnull=true` | `field_isnull=true` | `tag_isnull=true` | `tag_isnull=true` |
| N'est pas null | `field_isnull=false` | `field_isnull=false` | `tag_isnull=false` | `tag_isnull=false` |
| **COLONNES COMPOSÉES** |
| Exact (concat) | `composite_exact=value` | `composite_exact=value` | `full_name_exact=ASSOULI khadija` | `full_name_exact=ASSOULI khadija` |
| Contient (concat) | `composite_icontains=value` | `composite_icontains=value` | `full_name_icontains=ASSOULI` | `full_name_icontains=ASSOULI` |
| **EXPORT** |
| Export Excel | `export=excel` | `export=excel` | `export=excel` | `export=excel` |
| Export CSV | `export=csv` | `export=csv` | `export=csv` | `export=csv` |
| **AUTRES** |
| Draw counter | `draw=1` | - | `draw=1` | (ignoré par API) |

## 🔄 Conversion Start ↔ Page

```
page = (start ÷ length) + 1
start = (page - 1) × length
```

| start | length | page | page_size |
|-------|--------|------|-----------|
| 0 | 25 | 1 | 25 |
| 25 | 25 | 2 | 25 |
| 50 | 25 | 3 | 25 |
| 0 | 10 | 1 | 10 |
| 100 | 50 | 3 | 50 |

## 📡 Format de réponse

### DataTable
```json
{
  "draw": 1,
  "recordsTotal": 1500,
  "recordsFiltered": 45,
  "data": [...]
}
```

### REST API
```json
{
  "count": 1500,
  "next": "...",
  "previous": null,
  "results": [...]
}
```

## 🎯 Exemples d'URLs complètes

### Exemple 1 : Liste simple
```
DT:  /api/items/?start=0&length=25&draw=1
API: /api/items/?page=1&page_size=25
```

### Exemple 2 : Recherche + Tri
```
DT:  /api/items/?start=0&length=25&search[value]=laptop&order[0][column]=2&order[0][dir]=asc&draw=1
API: /api/items/?page=1&page_size=25&search=laptop&ordering=nom
```

### Exemple 3 : Filtres multiples
```
DT:  /api/items/?start=0&length=25&statut_exact=affecter&prix_range=1000,5000&draw=1
API: /api/items/?page=1&page_size=25&statut_exact=affecter&prix_range=1000,5000
```

### Exemple 4 : Colonne composée
```
DT:  /api/items/?start=0&length=25&affectation_personne_full_name_exact=ASSOULI+khadija&draw=1
API: /api/items/?page=1&page_size=25&affectation_personne_full_name_exact=ASSOULI khadija
```

### Exemple 5 : Export avec filtres
```
DT:  /api/items/?export=excel&statut_exact=affecter&search[value]=laptop
API: /api/items/?export=excel&statut_exact=affecter&search=laptop
```

## 💡 Notes importantes

1. **start vs page** : DataTable utilise l'offset (0, 25, 50...), API utilise le numéro de page (1, 2, 3...)
2. **draw** : Paramètre DataTable uniquement, ignoré par l'API REST
3. **Espaces dans URLs** : Remplacés par `+` ou `%20` selon l'encodage
4. **Conversion automatique** : Le backend `ServerSideDataTableView` gère automatiquement la conversion
5. **Filtres composés** : Les colonnes composées (concat) sont gérées nativement via `composite_columns`
6. **Export** : L'export respecte tous les filtres, recherches et tris actifs

## 🔗 Voir aussi

- `API_PARAMETERS_GUIDE.md` - Guide détaillé avec exemples de code
- `FRONTEND_BACKEND_CONTRACT.md` - Contrat d'interface frontend/backend
- `README.md` - Documentation générale du package DataTable

---

**Version :** 1.0  
**Date :** 2025-01-11

