# Architecture de l'API d'Affectation des Jobs

## Vue d'ensemble

L'API d'affectation des jobs de comptage suit une architecture en couches avec séparation des responsabilités.

## Structure des Fichiers

```
apps/inventory/
├── interfaces/assignment_interface.py
├── repositories/assignment_repository.py
├── services/assignment_service.py
├── usecases/job_assignment.py
├── serializers/assignment_serializer.py
├── views/assignment_views.py
├── exceptions/assignment_exceptions.py
└── tests/test_assignment_api.py
```

## Architecture en Couches

### 1. Interface Layer
- Définit les contrats pour les services et repositories
- Permet l'injection de dépendances

### 2. Repository Layer
- Gère l'accès aux données (Job, Counting, Assigment)
- Isolation de la couche données

### 3. Service Layer
- Contient la logique métier
- Validation des données et règles métier

### 4. Use Case Layer
- Orchestration des services
- Gestion des cas d'usage spécifiques

### 5. API Layer
- Endpoints REST
- Sérialisation des données

## Règles Métier

- **Image Stock** : Pas d'affectation de session
- **En Vrac/Par Article** : Affectation de session autorisée
- Tous les jobs doivent appartenir au même inventaire
- Un job ne peut avoir qu'une seule affectation

## Flux de Données

### 1. Requête d'Affectation

```
Client → API View → Serializer → Use Case → Service → Repository → Database
```

### 2. Réponse d'Affectation

```
Database → Repository → Service → Use Case → Serializer → API View → Client
```

## Règles Métier Implémentées

### 1. Validation des Modes de Comptage

- **Image Stock** : Pas d'affectation de session (automatique)
- **En Vrac** : Affectation de session autorisée
- **Par Article** : Affectation de session autorisée

### 2. Validation des Ordres de Comptage

- Seuls les ordres 1, 2, 3 sont autorisés
- Validation de l'existence du comptage

### 3. Validation des Jobs

- Tous les jobs doivent appartenir au même inventaire
- Un job ne peut avoir qu'une seule affectation
- Validation de l'existence des jobs

### 4. Validation des Sessions

- La session doit être un opérateur valide
- Vérification du rôle "Operateur"

## Gestion des Erreurs

### 1. Hiérarchie des Exceptions

```
AssignmentError (base)
├── AssignmentValidationError
├── AssignmentBusinessRuleError
├── AssignmentSessionError
└── AssignmentNotFoundError
```

### 2. Mapping des Erreurs HTTP

- `400 Bad Request` : Erreurs de validation ou règles métier
- `404 Not Found` : Ressources non trouvées
- `500 Internal Server Error` : Erreurs système

## Tests

### 1. Tests Unitaires

**Fichier :** `tests/test_assignment_api.py`

Tests couvrant :
- Affectation réussie
- Validation des règles métier
- Gestion des erreurs
- Cas limites

### 2. Types de Tests

- Tests d'intégration API
- Tests de validation des données
- Tests des règles métier
- Tests de gestion d'erreurs

## Configuration et Déploiement

### 1. URLs

```python
# apps/inventory/urls.py
path('assign-jobs/', assign_jobs_to_counting, name='assign-jobs-to-counting'),
path('assignment-rules/', get_assignment_rules, name='assignment-rules'),
```

### 2. Permissions

- Authentification requise (`IsAuthenticated`)
- Validation des rôles dans le service

### 3. Transactions

- Utilisation de `@transaction.atomic` pour garantir la cohérence
- Rollback automatique en cas d'erreur

## Extensibilité

### 1. Ajout de Nouveaux Modes de Comptage

1. Ajouter le mode dans `AssignmentService.can_assign_session_to_counting()`
2. Mettre à jour les tests
3. Documenter les nouvelles règles

### 2. Ajout de Nouvelles Validations

1. Créer une nouvelle exception si nécessaire
2. Ajouter la validation dans le service
3. Mettre à jour les tests

### 3. Ajout de Nouveaux Endpoints

1. Créer la vue dans `assignment_views.py`
2. Ajouter l'URL dans `urls.py`
3. Créer les tests correspondants

## Bonnes Pratiques

### 1. Séparation des Responsabilités

- Chaque couche a une responsabilité claire
- Pas de logique métier dans les vues
- Pas d'accès direct aux modèles dans les services

### 2. Injection de Dépendances

- Utilisation d'interfaces pour les dépendances
- Facilite les tests et la maintenance

### 3. Gestion des Erreurs

- Exceptions spécifiques pour chaque type d'erreur
- Messages d'erreur clairs et informatifs
- Logging approprié

### 4. Tests

- Couverture de code élevée
- Tests unitaires et d'intégration
- Tests des cas d'erreur

## Monitoring et Logging

### 1. Logs Recommandés

- Création d'affectations
- Erreurs de validation
- Violations des règles métier
- Performances des requêtes

### 2. Métriques à Surveiller

- Nombre d'affectations par jour
- Taux d'erreur par type
- Temps de réponse des endpoints
- Utilisation des ressources 