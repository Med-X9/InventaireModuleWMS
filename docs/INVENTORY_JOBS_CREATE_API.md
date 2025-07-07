# API de Création de Jobs d'Inventaire

## Description

Cette API permet de créer des jobs d'inventaire pour un entrepôt spécifique dans le cadre d'un inventaire donné. Un job est créé avec les emplacements spécifiés et est automatiquement assigné aux deux premiers comptages de l'inventaire.

## Endpoint

```
POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/
```

## Paramètres d'URL

| Paramètre | Type | Description | Requis |
|-----------|------|-------------|--------|
| `inventory_id` | Integer | ID de l'inventaire | Oui |
| `warehouse_id` | Integer | ID de l'entrepôt | Oui |

## Authentification

Cette API nécessite une authentification. Incluez le token d'authentification dans l'en-tête de la requête :

```
Authorization: Token <your_token>
```

## Corps de la requête

### Format JSON

```json
{
    "emplacements": [1, 2, 3, 4, 5]
}
```

### Paramètres du corps

| Paramètre | Type | Description | Requis | Validation |
|-----------|------|-------------|--------|------------|
| `emplacements` | Array[Integer] | Liste des IDs des emplacements à inclure dans le job | Oui | Non vide, tous les emplacements doivent exister et appartenir au warehouse |

## Réponse

### Succès (201 Created)

```json
{
    "success": true,
    "message": "Jobs créés avec succès"
}
```

### Erreur - Validation des données (400 Bad Request)

#### Erreur de validation du serializer

```json
{
    "success": false,
    "message": "Erreur de validation",
    "errors": {
        "emplacements": [
            "Cette liste ne peut pas être vide."
        ]
    }
}
```

#### Erreur métier

```json
{
    "success": false,
    "message": "Inventaire avec l'ID 999 non trouvé"
}
```

```json
{
    "success": false,
    "message": "Warehouse avec l'ID 999 non trouvé"
}
```

```json
{
    "success": false,
    "message": "Il faut au moins deux comptages pour l'inventaire INV001. Comptages trouvés : 1"
}
```

```json
{
    "success": false,
    "message": "Emplacement avec l'ID 999 non trouvé"
}
```

```json
{
    "success": false,
    "message": "L'emplacement LOC001 n'appartient pas au warehouse Entrepôt Central"
}
```

```json
{
    "success": false,
    "message": "L'emplacement LOC001 est déjà affecté au job JOB001"
}
```

### Erreur - Erreur serveur (500 Internal Server Error)

```json
{
    "success": false,
    "message": "Erreur interne : Une erreur inattendue est survenue"
}
```

## Logique métier

### Validations effectuées

1. **Existence de l'inventaire** : Vérification que l'inventaire existe
2. **Existence du warehouse** : Vérification que l'entrepôt existe
3. **Comptages requis** : Vérification qu'il y a au moins 2 comptages pour l'inventaire
4. **Existence des emplacements** : Vérification que tous les emplacements existent
5. **Appartenance au warehouse** : Vérification que tous les emplacements appartiennent au warehouse spécifié
6. **Non-affectation** : Vérification qu'aucun emplacement n'est déjà affecté à un autre job pour cet inventaire

### Processus de création

1. **Création du job** : Un seul job est créé avec une référence générée automatiquement
2. **Création des JobDetails** : Un JobDetail est créé pour chaque emplacement
3. **Création des Assignments** : Des assignments sont créés pour les deux premiers comptages de l'inventaire

### Structure des données créées

#### Job
- **Référence** : Générée automatiquement avec le préfixe "JOB"
- **Statut** : "EN ATTENTE"
- **Warehouse** : L'entrepôt spécifié
- **Inventory** : L'inventaire spécifié

#### JobDetail (pour chaque emplacement)
- **Référence** : Générée automatiquement avec le préfixe "JDT"
- **Location** : L'emplacement spécifié
- **Job** : Le job créé
- **Statut** : "EN ATTENTE"

#### Assignment (pour les 2 premiers comptages)
- **Référence** : Générée automatiquement avec le préfixe "ASG"
- **Job** : Le job créé
- **Counting** : Le comptage de l'inventaire

## Exemples d'utilisation

### Exemple 1 : Création d'un job avec 3 emplacements

**Requête :**
```bash
curl -X POST \
  http://localhost:8000/api/inventory/planning/1/warehouse/2/jobs/create/ \
  -H 'Authorization: Token your_token_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "emplacements": [101, 102, 103]
  }'
```

**Réponse :**
```json
{
    "success": true,
    "message": "Jobs créés avec succès"
}
```

### Exemple 2 : Tentative de création avec un emplacement inexistant

**Requête :**
```bash
curl -X POST \
  http://localhost:8000/api/inventory/planning/1/warehouse/2/jobs/create/ \
  -H 'Authorization: Token your_token_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "emplacements": [101, 999, 103]
  }'
```

**Réponse :**
```json
{
    "success": false,
    "message": "Emplacement avec l'ID 999 non trouvé"
}
```

### Exemple 3 : Tentative de création avec un emplacement déjà affecté

**Requête :**
```bash
curl -X POST \
  http://localhost:8000/api/inventory/planning/1/warehouse/2/jobs/create/ \
  -H 'Authorization: Token your_token_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "emplacements": [101, 102, 103]
  }'
```

**Réponse :**
```json
{
    "success": false,
    "message": "L'emplacement LOC001 est déjà affecté au job JOB001"
}
```

## Codes d'erreur HTTP

| Code | Description |
|------|-------------|
| 201 | Job créé avec succès |
| 400 | Erreur de validation ou erreur métier |
| 401 | Non authentifié |
| 403 | Non autorisé |
| 500 | Erreur interne du serveur |

## Notes importantes

1. **Transaction atomique** : Toute la création se fait dans une transaction atomique. Si une erreur survient, toutes les modifications sont annulées.

2. **Références automatiques** : Les références des jobs, job details et assignments sont générées automatiquement.

3. **Assignments automatiques** : Le job est automatiquement assigné aux deux premiers comptages de l'inventaire.

4. **Statut initial** : Tous les éléments créés ont le statut "EN ATTENTE".

5. **Validation stricte** : Toutes les validations sont effectuées avant la création pour éviter les incohérences.

## Endpoints liés

- `GET /api/inventory/planning/{inventory_id}/warehouses/` - Liste des entrepôts d'un inventaire
- `GET /api/warehouse/{warehouse_id}/pending-jobs/` - Jobs en attente d'un entrepôt
- `GET /api/warehouse/{warehouse_id}/jobs/` - Tous les jobs d'un entrepôt
- `POST /api/jobs/validate/` - Valider des jobs
- `POST /api/jobs/delete/` - Supprimer des jobs 