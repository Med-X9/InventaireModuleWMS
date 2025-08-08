# Séparation Finale du Core - Documentation

## Vue d'ensemble

La séparation finale du core a été implémentée pour organiser les services, repositories et exceptions par domaine fonctionnel plutôt que par application. Cette approche améliore la modularité, la réutilisabilité et la maintenabilité du code.

## Structure Finale

```
core/
├── __init__.py                    # Expose tous les services, repositories et exceptions
├── services/
│   ├── __init__.py               # Expose les services
│   ├── auth_service.py           # Services d'authentification
│   ├── sync_service.py           # Services de synchronisation
│   ├── inventory_service.py      # Services d'inventaire
│   └── user_service.py           # Services utilisateur
├── repositories/
│   ├── __init__.py               # Expose les repositories
│   ├── auth_repository.py        # Repository d'authentification
│   ├── sync_repository.py        # Repository de synchronisation
│   ├── inventory_repository.py   # Repository d'inventaire
│   └── user_repository.py        # Repository utilisateur
└── exceptions/
    ├── __init__.py               # Expose toutes les exceptions
    ├── auth_exceptions.py        # Exceptions d'authentification
    ├── sync_exceptions.py        # Exceptions de synchronisation
    ├── inventory_exceptions.py   # Exceptions d'inventaire
    └── user_exceptions.py        # Exceptions utilisateur
```

## Services

### AuthService (`core/services/auth_service.py`)
Gère l'authentification des utilisateurs mobiles.

**Méthodes principales:**
- `login(username, password)` - Connexion utilisateur
- `logout()` - Déconnexion utilisateur
- `refresh_token(refresh_token)` - Rafraîchissement du token

### SyncService (`core/services/sync_service.py`)
Gère la synchronisation des données mobiles.

**Méthodes principales:**
- `sync_data(user_id, inventory_id=None)` - Récupération des données de synchronisation
- `upload_data(sync_id, countings, assignments)` - Upload des données

### InventoryService (`core/services/inventory_service.py`)
Gère les opérations liées aux inventaires.

**Méthodes principales:**
- `get_inventory_users(inventory_id)` - Récupération des utilisateurs d'un inventaire

### UserService (`core/services/user_service.py`)
Gère les opérations liées aux utilisateurs et leurs données.

**Méthodes principales:**
- `get_user_inventories(user_id)` - Inventaires d'un utilisateur
- `get_user_products(user_id)` - Produits d'un utilisateur
- `get_user_locations(user_id)` - Locations d'un utilisateur
- `get_user_stocks(user_id)` - Stocks d'un utilisateur

## Repositories

### AuthRepository (`core/repositories/auth_repository.py`)
Accès aux données d'authentification.

**Méthodes principales:**
- `get_user_by_username(username)`
- `get_user_by_id(user_id)`
- `is_user_active(user)`
- `update_user_last_login(user)`

### SyncRepository (`core/repositories/sync_repository.py`)
Accès aux données de synchronisation.

**Méthodes principales:**
- `get_inventories_by_status(status)`
- `get_jobs_by_inventory(inventory_id)`
- `get_assignments_by_job(job_id)`
- `get_countings_by_assignment(assignment_id)`

### InventoryRepository (`core/repositories/inventory_repository.py`)
Accès aux données d'inventaire.

**Méthodes principales:**
- `get_users_by_inventory_account(inventory_id)`
- `format_user_data(user)`

### UserRepository (`core/repositories/user_repository.py`)
Accès aux données utilisateur.

**Méthodes principales:**
- `get_inventories_by_user_account(user_id)`
- `get_products_by_user_account(user_id)`
- `get_locations_by_user_account(user_id)`
- `get_stocks_by_user_account(user_id)`

## Exceptions

### AuthExceptions (`core/exceptions/auth_exceptions.py`)
- `AuthException` - Exception de base pour l'authentification
- `UserNotFoundException` - Utilisateur non trouvé
- `InvalidCredentialsException` - Identifiants invalides
- `TokenInvalidException` - Token invalide
- `UserInactiveException` - Utilisateur inactif

### SyncExceptions (`core/exceptions/sync_exceptions.py`)
- `SyncException` - Exception de base pour la synchronisation
- `SyncDataException` - Erreur de synchronisation des données
- `UploadDataException` - Erreur d'upload
- `InventoryNotFoundException` - Inventaire non trouvé
- `JobNotFoundException` - Job non trouvé
- `AssignmentNotFoundException` - Assignment non trouvé
- `CountingNotFoundException` - Counting non trouvé

### InventoryExceptions (`core/exceptions/inventory_exceptions.py`)
- `InventoryException` - Exception de base pour l'inventaire
- `InventoryNotFoundException` - Inventaire non trouvé
- `AccountNotFoundException` - Compte non trouvé
- `DatabaseConnectionException` - Erreur de connexion base de données
- `DataValidationException` - Erreur de validation des données

### UserExceptions (`core/exceptions/user_exceptions.py`)
- `UserException` - Exception de base pour les utilisateurs
- `UserNotFoundException` - Utilisateur non trouvé
- `AccountNotFoundException` - Compte non trouvé
- `ProductNotFoundException` - Produit non trouvé
- `LocationNotFoundException` - Location non trouvée
- `StockNotFoundException` - Stock non trouvé
- `DatabaseConnectionException` - Erreur de connexion base de données
- `DataValidationException` - Erreur de validation des données

## Utilisation dans les Vues

### Exemple d'utilisation dans `apps/mobile/views.py`

```python
from core.services.auth_service import AuthService
from core.services.sync_service import SyncService
from core.services.inventory_service import InventoryService
from core.services.user_service import UserService
from core.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    ProductNotFoundException,
    LocationNotFoundException,
    StockNotFoundException,
    InventoryNotFoundException,
    DatabaseConnectionException,
    DataValidationException,
    SyncDataException,
    UploadDataException
)

class LoginView(APIView):
    def post(self, request):
        auth_service = AuthService()
        response_data, error = auth_service.login(username, password)
        # ...

class SyncDataView(APIView):
    def get(self, request, user_id=None):
        try:
            sync_service = SyncService()
            response_data = sync_service.sync_data(target_user_id, inventory_id)
            # ...
        except (UserNotFoundException, AccountNotFoundException) as e:
            # Gestion des exceptions spécifiques
```

## Avantages de cette Séparation

### 1. **Modularité**
- Chaque service a une responsabilité claire et définie
- Les repositories isolent l'accès aux données
- Les exceptions sont organisées par domaine

### 2. **Réutilisabilité**
- Les services peuvent être utilisés par différentes applications
- Les repositories peuvent être partagés entre services
- Les exceptions sont cohérentes dans toute l'application

### 3. **Testabilité**
- Chaque composant peut être testé indépendamment
- Les mocks sont plus faciles à créer
- Les tests sont plus ciblés et maintenables

### 4. **Maintenabilité**
- Structure claire et organisée
- Séparation des responsabilités
- Code plus lisible et compréhensible

### 5. **Évolutivité**
- Facile d'ajouter de nouveaux services
- Structure extensible pour de nouveaux domaines
- Cohérence dans l'architecture

## Migration depuis l'Ancienne Structure

### Avant
```python
from apps.mobile.services.mobile_auth_service import MobileAuthService
from apps.mobile.services.mobile_sync_service import MobileSyncService
from apps.mobile.exceptions import MobileSyncException

class LoginView(APIView):
    def post(self, request):
        auth_service = MobileAuthService()
        # ...
```

### Après
```python
from core.services.auth_service import AuthService
from core.exceptions.auth_exceptions import UserNotFoundException

class LoginView(APIView):
    def post(self, request):
        auth_service = AuthService()
        # ...
```

## Tests

Un script de test complet est disponible dans `test_core_separation_final.py` pour vérifier:

1. **Imports** - Vérification que tous les modules peuvent être importés
2. **Instanciation** - Test de création des services et repositories
3. **Exceptions** - Test de création et gestion des exceptions
4. **Vues** - Test de création des vues avec les nouveaux services
5. **Structure** - Vérification de la cohérence de la structure

## Bonnes Pratiques

### 1. **Imports**
- Utiliser les imports spécifiques plutôt que les imports génériques
- Importer les exceptions nécessaires explicitement

### 2. **Gestion d'Erreurs**
- Utiliser les exceptions spécifiques au domaine
- Inclure des `error_type` dans les réponses d'API
- Logger les erreurs avec `traceback` pour le débogage

### 3. **Services**
- Un service par domaine fonctionnel
- Méthodes claires et bien nommées
- Gestion d'erreurs appropriée

### 4. **Repositories**
- Accès aux données uniquement
- Pas de logique métier
- Requêtes optimisées

### 5. **Exceptions**
- Hiérarchie claire des exceptions
- Messages d'erreur informatifs
- Codes d'erreur appropriés

## Conclusion

Cette séparation finale du core améliore significativement la structure du projet en:

- Organisant le code par domaine fonctionnel
- Améliorant la modularité et la réutilisabilité
- Facilitant les tests et la maintenance
- Fournissant une architecture claire et extensible

La structure est maintenant prête pour l'évolution future du projet avec une base solide et bien organisée. 