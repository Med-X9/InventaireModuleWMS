# Type de retour - Export Excel/CSV

## 📥 Endpoint d'export

```
GET /api/items/?export=excel&search[value]=laptop&statut_exact=affecter
```

## 🎯 Type de retour

### Pour Excel (`export=excel`)

**Type HTTP :** `HttpResponse` avec fichier binaire Excel

**Content-Type :**
```
application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

**Content-Disposition :**
```
attachment; filename="items_export_2025-01-11_16-30-45.xlsx"
```

**Corps de la réponse :**
- Fichier Excel binaire (.xlsx) généré par `openpyxl`
- Format Office Open XML
- Prêt à télécharger

### Pour CSV (`export=csv`)

**Type HTTP :** `HttpResponse` avec fichier texte CSV

**Content-Type :**
```
text/csv; charset=utf-8
```

**Content-Disposition :**
```
attachment; filename="items_export_2025-01-11_16-30-45.csv"
```

**Corps de la réponse :**
- Fichier texte CSV
- Encodage UTF-8 avec BOM (pour Excel)
- Délimiteur : virgule (,)

## 📊 Structure du fichier Excel

### En-têtes (ligne 1)
```
| id | reference_auto | statut | article_full_name | affectation_personne_full_name | emplacement_nom | departement_nom | created_at | date_affectation |
```

**Style des en-têtes :**
- Police : Gras, Blanc
- Fond : Bleu (#4472C4)
- Alignement : Centré

### Données (lignes 2+)
```
| 1 | ITEM-000001 | affecter | Laptop Dell Latitude - ARTL-001507 | ASSOULI khadija | Bureau 101 | Informatique | 2025-01-11 10:30:00 | 2025-01-10 |
| 45 | ITEM-000045 | affecter | Laptop HP EliteBook - ARTL-002341 | BENALI Mohamed | Bureau 205 | Comptabilité | 2025-01-09 14:15:00 | 2025-01-08 |
...
```

**Formatage des données :**
- Dates : `YYYY-MM-DD HH:MM:SS` ou `YYYY-MM-DD`
- Booléens : `Oui` / `Non`
- Null : cellule vide
- Nombres décimaux : format float
- Largeur des colonnes : auto-ajustée (max 50 caractères)

## 📊 Structure du fichier CSV

### Format
```csv
id,reference_auto,statut,article_full_name,affectation_personne_full_name,emplacement_nom,departement_nom,created_at,date_affectation
1,ITEM-000001,affecter,"Laptop Dell Latitude - ARTL-001507","ASSOULI khadija",Bureau 101,Informatique,2025-01-11 10:30:00,2025-01-10
45,ITEM-000045,affecter,"Laptop HP EliteBook - ARTL-002341","BENALI Mohamed",Bureau 205,Comptabilité,2025-01-09 14:15:00,2025-01-08
```

**Caractéristiques :**
- Délimiteur : virgule (`,`)
- Guillemets : automatiques pour les valeurs contenant des virgules
- Encodage : UTF-8 avec BOM (compatible Excel Windows)
- Fin de ligne : CRLF (`\r\n`)

## 🔍 Exemple de réponse HTTP complète

### Excel
```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="items_export_2025-01-11_16-30-45.xlsx"
Content-Length: 52341
Date: Sat, 11 Jan 2025 16:30:45 GMT

[Binary Excel file content - .xlsx format]
```

### CSV
```http
HTTP/1.1 200 OK
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="items_export_2025-01-11_16-30-45.csv"
Content-Length: 12543
Date: Sat, 11 Jan 2025 16:30:45 GMT

id,reference_auto,statut,article_full_name...
1,ITEM-000001,affecter,"Laptop Dell..."...
45,ITEM-000045,affecter,"Laptop HP..."...
```

## 💻 Code Backend (Python)

### Export Excel
```python
# Dans datatables/exporters.py, classe ExcelExporter

def export(self, queryset, serializer_class=None, filename='export'):
    # Créer le workbook Excel
    wb = Workbook()
    ws = wb.active
    ws.title = 'Data'
    
    # Sérialiser les données
    serializer = serializer_class(queryset, many=True)
    data = serializer.data  # Liste de dictionnaires
    
    # Écrire les en-têtes
    headers = list(data[0].keys())
    ws.append(headers)
    
    # Appliquer le style aux en-têtes
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    
    # Écrire les données
    for row_data in data:
        row = [format_value(row_data.get(h)) for h in headers]
        ws.append(row)
    
    # Créer la réponse HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    
    # Sauvegarder le workbook dans la réponse
    wb.save(response)
    
    return response  # HttpResponse avec fichier Excel binaire
```

### Export CSV
```python
# Dans datatables/exporters.py, classe CSVExporter

def export(self, queryset, serializer_class=None, filename='export'):
    # Sérialiser les données
    serializer = serializer_class(queryset, many=True)
    data = serializer.data  # Liste de dictionnaires
    
    # Créer la réponse HTTP
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    # Créer le writer CSV
    headers = list(data[0].keys())
    writer = csv.DictWriter(response, fieldnames=headers, delimiter=',')
    
    # Écrire les en-têtes et données
    writer.writeheader()
    for row_data in data:
        writer.writerow(row_data)
    
    return response  # HttpResponse avec fichier CSV texte
```

## 🌐 Gestion Frontend

### JavaScript (téléchargement automatique)
```javascript
// Le navigateur télécharge automatiquement le fichier
window.location.href = '/api/items/?export=excel&statut_exact=affecter';
```

### Axios (avec gestion manuelle)
```javascript
// Pour gérer manuellement le téléchargement
axios.get('/api/items/', {
    params: {
        export: 'excel',
        statut_exact: 'affecter'
    },
    responseType: 'blob'  // Important pour les fichiers binaires
})
.then(response => {
    // Créer un lien de téléchargement
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    
    // Extraire le nom du fichier depuis Content-Disposition
    const contentDisposition = response.headers['content-disposition'];
    const filename = contentDisposition.split('filename=')[1].replace(/"/g, '');
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    // Libérer l'URL
    window.URL.revokeObjectURL(url);
})
.catch(error => {
    console.error('Erreur export:', error);
});
```

### Fetch API
```javascript
fetch('/api/items/?export=excel&statut_exact=affecter')
    .then(response => response.blob())
    .then(blob => {
        // Créer une URL pour le blob
        const url = window.URL.createObjectURL(blob);
        
        // Créer un lien et déclencher le téléchargement
        const a = document.createElement('a');
        a.href = url;
        a.download = 'items_export.xlsx';
        document.body.appendChild(a);
        a.click();
        a.remove();
        
        // Libérer l'URL
        window.URL.revokeObjectURL(url);
    });
```

### jQuery (simple)
```javascript
// Téléchargement automatique
$('#btn_export').on('click', function() {
    const filters = table.ajax.params();
    const url = '/api/items/?export=excel&' + $.param(filters);
    window.location.href = url;
});
```

## 📝 Différences avec endpoint normal

### Endpoint normal (sans export)
```
GET /api/items/?page=1&page_size=25&statut_exact=affecter
```

**Retour :** JSON
```json
{
  "count": 890,
  "next": "http://api.../items/?page=2&page_size=25&statut_exact=affecter",
  "previous": null,
  "results": [
    {
      "id": 1,
      "reference_auto": "ITEM-000001",
      "statut": "affecter",
      ...
    }
  ]
}
```

**Content-Type :** `application/json`

### Endpoint avec export
```
GET /api/items/?export=excel&statut_exact=affecter
```

**Retour :** Fichier Excel binaire (ou CSV texte)

**Content-Type :** 
- Excel : `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- CSV : `text/csv; charset=utf-8`

**Différences clés :**
1. ✅ Pas de pagination (tous les résultats)
2. ✅ Fichier téléchargeable (Content-Disposition: attachment)
3. ✅ Format binaire (Excel) ou texte (CSV)
4. ✅ Les filtres sont respectés
5. ✅ La recherche est respectée
6. ✅ Le tri est respecté

## ⚠️ Points importants

### 1. Pas de pagination pour l'export
```python
# L'export ignore la pagination et retourne TOUTES les données filtrées
queryset = self.get_datatable_queryset()  # Tous les résultats
# Pas de queryset[start:end]
```

### 2. Limites de performance
- **Recommandé :** < 10 000 lignes
- **Maximum :** Dépend de la mémoire serveur
- Pour de très gros exports, considérez :
  - Export asynchrone (Celery)
  - Export par lots
  - Compression

### 3. Format MIME types
```python
# Excel
'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # .xlsx
'application/vnd.ms-excel'  # .xls (ancien format)

# CSV
'text/csv'
'text/plain'  # Alternative

# Autres (non implémentés)
'application/pdf'  # PDF
'application/json'  # JSON
```

### 4. Nom de fichier
```python
# Format du nom
f"{export_filename}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.{extension}"

# Exemples
"items_export_2025-01-11_16-30-45.xlsx"
"items_export_2025-01-11_16-30-45.csv"
```

## 🔧 Configuration dans la vue

```python
class ItemListAPIView(ServerSideDataTableView):
    model = item
    serializer_class = ItemSerializer
    
    # Configuration export
    enable_export = True  # Activer l'export
    export_formats = ['excel', 'csv']  # Formats disponibles
    export_filename = 'items_export'  # Nom de base du fichier
```

## 📊 Résumé

| Aspect | Excel | CSV |
|--------|-------|-----|
| **Type de retour** | `HttpResponse` (binaire) | `HttpResponse` (texte) |
| **Content-Type** | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `text/csv; charset=utf-8` |
| **Extension** | `.xlsx` | `.csv` |
| **Format** | Office Open XML | Texte délimité |
| **Taille** | Plus grand (~50KB pour 100 lignes) | Plus petit (~12KB pour 100 lignes) |
| **Formatage** | Oui (styles, couleurs, largeurs) | Non (texte brut) |
| **Compatible Excel** | ✅ Natif | ✅ Avec BOM UTF-8 |
| **Éditable** | ✅ Excel, LibreOffice | ✅ Éditeur texte, Excel |
| **Formules** | ❌ Non | ❌ Non |
| **Bibliothèque** | openpyxl | csv (Python standard) |

---

**Version :** 1.0  
**Date :** 2025-01-11  
**Documentation complète :** Voir `datatables/exporters.py`

