# API de Création de Jobs d'Inventaire

## Description

Cette API permet de créer des jobs d'inventaire pour un entrepôt spécifique dans le cadre d'un inventaire donné. Un job est créé avec les emplacements spécifiés et est automatiquement assigné aux comptages selon la configuration de l'inventaire.

**Note importante** : La création des JobDetails et Assignments dépend du mode de comptage du 1er comptage :

### Cas 1 : 1er comptage = "image de stock"
- Les emplacements sont créés **uniquement** pour le 2ème comptage
- Une seule affectation (Assignment) est créée pour le 2ème comptage
- Le 1er comptage (image de stock) n'a pas d'affectation

### Cas 2 : 1er comptage différent de "image de stock"
- Les emplacements sont **dupliqués** pour les deux comptages
- Deux affectations (Assignments) sont créées (une pour chaque comptage)
- Chaque emplacement apparaît deux fois dans les JobDetails (une fois par comptage)

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
3. **Création des Assignments** : Des assignments sont créés selon la configuration des comptages

### Configuration des assignments selon le mode de comptage

#### Cas 1 : 1er comptage = "image de stock"

```
1er comptage : "image de stock" → Aucune affectation créée
2ème comptage : "en vrac" ou "par article" → Affectation créée avec statut "EN ATTENTE"
```

**Résultat :** 1 seul assignment créé pour le 2ème comptage

#### Cas 2 : 1er comptage ≠ "image de stock"

```
1er comptage : "en vrac" ou "par article" → Affectation créée avec statut "EN ATTENTE"
2ème comptage : "en vrac" ou "par article" → Affectation créée avec statut "EN ATTENTE"
```

**Résultat :** 2 assignments créés pour les deux comptages

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

#### Assignment (selon la configuration)

**Cas image de stock :**
- **Référence** : Générée automatiquement avec le préfixe "ASS"
- **Job** : Le job créé
- **Counting** : Le 2ème comptage uniquement
- **Statut** : "EN ATTENTE"
- **Session** : Null (à affecter ultérieurement)

**Cas normal :**
- **Référence** : Générée automatiquement avec le préfixe "ASS"
- **Job** : Le job créé
- **Counting** : Les deux premiers comptages
- **Statut** : "EN ATTENTE"
- **Session** : Null (à affecter ultérieurement)

## Exemples d'utilisation

### Exemple 1 : Configuration avec image de stock

```bash
curl -X POST \
  http://localhost:8000/api/inventory/planning/1/warehouse/1/jobs/create/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{
    "emplacements": [1, 2, 3, 4, 5]
}'
```

**Configuration de l'inventaire :**
- 1er comptage : "image de stock"
- 2ème comptage : "en vrac"

**Résultat :**
- 1 job créé avec 5 JobDetails
- 1 assignment créé pour le 2ème comptage uniquement

### Exemple 2 : Configuration normale

```bash
curl -X POST \
  http://localhost:8000/api/inventory/planning/2/warehouse/1/jobs/create/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{
    "emplacements": [1, 2, 3, 4, 5]
}'
```

**Configuration de l'inventaire :**
- 1er comptage : "en vrac"
- 2ème comptage : "par article"

**Résultat :**
- 1 job créé avec 5 JobDetails
- 2 assignments créés pour les deux comptages

## Workflow complet

### 1. Création des jobs
```
POST /api/inventory/planning/{inventory_id}/warehouse/{warehouse_id}/jobs/create/
→ Jobs créés avec assignments selon la configuration
```

### 2. Affectation de sessions (optionnel)
```
POST /api/inventory/{inventory_id}/assign-jobs/
→ Sessions affectées aux assignments existants
```

### 3. Validation des jobs
```
POST /api/inventory/jobs/validate/
→ Jobs validés pour passer au statut "VALIDE"
```

### 4. Mise en prêt
```
POST /api/inventory/jobs/ready/
→ Jobs mis en PRET selon les règles métier
```

## Intégration avec les autres APIs

### API d'affectation de sessions
- Seuls les assignments existants peuvent recevoir des sessions
- Dans le cas "image de stock", seul le 2ème comptage peut recevoir une session
- Dans le cas normal, les deux comptages peuvent recevoir des sessions

### API de mise en prêt
- Les jobs peuvent être mis en PRET même avec un seul assignment affecté (cas image de stock)
- Les jobs normaux nécessitent que les deux assignments soient affectés

## Cas d'usage courants

### Inventaire avec image de stock
1. Créer l'inventaire avec 1er comptage = "image de stock"
2. Créer les jobs → 1 assignment par job (2ème comptage)
3. Affecter une session au 2ème comptage
4. Mettre les jobs en PRET

### Inventaire normal
1. Créer l'inventaire avec comptages normaux
2. Créer les jobs → 2 assignments par job
3. Affecter des sessions aux deux comptages
4. Mettre les jobs en PRET

## Dépannage

### Erreurs courantes

**"Il faut au moins deux comptages pour l'inventaire"**
- Vérifiez que l'inventaire a bien 2 comptages configurés
- Les comptages doivent être dans l'ordre 1 et 2

**"L'emplacement n'appartient pas au warehouse"**
- Vérifiez que l'emplacement appartient bien au warehouse via la hiérarchie : emplacement → sous-zone → zone → warehouse

**"L'emplacement est déjà affecté"**
- Vérifiez qu'aucun autre job n'utilise déjà cet emplacement pour cet inventaire
- Supprimez l'affectation existante si nécessaire

### Validation des données

Avant de créer les jobs, vérifiez :
1. L'existence de l'inventaire et du warehouse
2. La configuration des comptages (au moins 2)
3. L'existence et l'appartenance des emplacements
4. L'absence de conflits d'affectation

## Performance et limitations

### Limitations
- Pas de limite sur le nombre d'emplacements par job
- Pas de limite sur le nombre de jobs par inventaire/warehouse
- Les emplacements doivent appartenir au même warehouse

### Performance
- Création en transaction atomique
- Vérifications optimisées avec requêtes groupées
- Génération automatique des références

## Évolutions futures

### Fonctionnalités prévues
- Support pour plus de 2 comptages
- Validation automatique des jobs selon des règles métier
- Intégration avec des workflows d'approbation

### Améliorations possibles
- Validation en temps réel des emplacements
- Prévisualisation des jobs avant création
- Historique des modifications de jobs 