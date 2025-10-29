# API de Génération de PDF des Jobs d'Inventaire

## Vue d'ensemble

Cette API permet de générer un PDF contenant tous les jobs d'un inventaire, organisés par comptage avec leurs modes et ordres respectifs.

## Endpoint

```
POST /web/api/inventory/{inventory_id}/jobs/pdf/
```

## Structure du Projet

L'API respecte l'architecture du projet avec la séparation des responsabilités :

- **Interface** (`apps/inventory/interfaces/pdf_interface.py`) : Définition des contrats
- **Repository** (`apps/inventory/repositories/pdf_repository.py`) : Accès aux données
- **Service** (`apps/inventory/services/pdf_service.py`) : Logique métier de génération PDF
- **UseCase** (`apps/inventory/usecases/inventory_jobs_pdf.py`) : Orchestration
- **View** (`apps/inventory/views/pdf_views.py`) : Point d'entrée API

## Requête

### URL Parameters

- `inventory_id` (requis) : ID de l'inventaire

**Pas de body requis** - L'API génère le PDF pour tous les comptages de l'inventaire.

### Exemple avec cURL

```bash
# Génération du PDF pour tous les comptages
curl -X POST http://localhost:8000/web/api/inventory/1/jobs/pdf/ \
  --output jobs_inventaire.pdf
```

## Réponse

### Succès (200 OK)

Retourne un fichier PDF avec les en-têtes appropriés :

- **Content-Type**: `application/pdf`
- **Content-Disposition**: `attachment; filename="inventaire_{inventory_id}.pdf"`

### Erreurs

#### 400 Bad Request - Inventaire non trouvé

```json
{
    "success": false,
    "message": "Inventaire avec l'ID 999 non trouvé"
}
```

#### 500 Internal Server Error

```json
{
    "success": false,
    "message": "Erreur interne : [détails]"
}
```

## Structure du PDF

### 1. En-tête Principal

- **Titre**: "Jobs d'Inventaire"
- **Libellé**: Nom de l'inventaire
- **Référence**: Référence de l'inventaire
- **Date de génération**: Date et heure

### 2. Sections par Comptage

Pour chaque comptage de l'inventaire :

#### En-tête du Comptage
- **Titre**: "Comptage {ordre}: {MODE}"
  - Exemple: "Comptage 1: EN VRAC"
  - Exemple: "Comptage 2: PAR ARTICLE"

#### Jobs par Utilisateur

Les jobs sont groupés par utilisateur affecté :

- **Affecté à**: {nom_utilisateur}
- **Non affecté**: Si aucun utilisateur n'est assigné

### 3. Tableaux des Jobs

Chaque job affiche un tableau avec des colonnes variables selon le mode de comptage.

#### Mode "EN VRAC" ou "IMAGE DE STOCK"

| Emplacement | Quantité |
|-------------|----------|
| J-06-01-04  | 150      |
| H-01-01-02  | 75       |

#### Mode "PAR ARTICLE"

| Emplacement | Article      | Quantité | DLC    | N° Lot | Variante |
|-------------|--------------|----------|--------|--------|----------|
| J-06-01-04  | Produit A    | 100      | Oui    | Oui    | Oui      |
|             | Produit B    | 50       | Non    | Non    | Non      |
| H-01-01-02  | Produit C    | 75       | Oui    | Oui    | Non      |

**Note**: Si l'inventaire a des stocks importés, chaque emplacement affiche tous ses articles avec leurs quantités.

## Logique de Génération

### Récupération des Données

1. Vérifie que l'inventaire existe
2. Récupère tous les comptages de l'inventaire (ordonnés par `order`)
3. Pour chaque comptage, récupère tous les jobs associés
4. Pour chaque job, récupère les JobDetails correspondants au comptage
5. Groupe les jobs par utilisateur via les Assignments

### Adaptation selon le Mode

Le service vérifie le paramétrage du comptage pour déterminer les colonnes :

- `counting.dlc == True` → Colonne DLC affichée
- `counting.n_lot == True` → Colonne N° Lot affichée
- `counting.is_variant == True` → Colonne Variante affichée

### Pagination

- 20 lignes par page (limitation de ReportLab)
- Saut de page entre les comptages
- Page de garde avec les informations générales

## Exemple d'Utilisation

### Python

```python
import requests

url = "http://localhost:8000/web/api/inventory/1/jobs/pdf/"
response = requests.post(url)

if response.status_code == 200:
    with open("jobs.pdf", "wb") as f:
        f.write(response.content)
    print("PDF généré avec succès!")
else:
    print(f"Erreur: {response.text}")
```

### JavaScript (Frontend)

```javascript
fetch('http://localhost:8000/web/api/inventory/1/jobs/pdf/', {
    method: 'POST'
})
.then(response => response.blob())
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'jobs_inventaire.pdf';
    a.click();
});
```

### Exemple React

```jsx
const generatePdf = (inventoryId) => {
  fetch(`http://localhost:8000/web/api/inventory/${inventoryId}/jobs/pdf/`, {
    method: 'POST'
  })
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `inventaire_${inventoryId}.pdf`;
    document.body.appendChild(a);
    a.click();
水体
```

## Dépendances

- **reportlab** (>= 4.2.5) : Génération de PDF
- **Django** : Framework web
- **djangorestframework** : API REST

## Installation

```bash
pip install reportlab
```

## Tests

Un script de test est disponible : `test_pdf_api.py`

```bash
python test_pdf_api.py
```

## Notes Techniques

- Le PDF utilise le format A4 avec des marges de 1.5 cm
- Les colonnes s'adaptent automatiquement selon le mode de comptage
- Les stocks sont récupérés depuis le modèle `Stock` de masterdata
- Les assignments utilisent les sessions utilisateurs (`UserApp` de type 'Mobile')
- **Tous les comptages** de l'inventaire sont inclus dans le PDF