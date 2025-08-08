# Séparation des Services et Repositories du Core

## Vue d'ensemble

Les services et repositories de l'application mobile ont été séparés dans une structure `core` partagée pour améliorer la modularité et la réutilisabilité du code.

## Structure

```
core/
├── __init__.py                 # Package principal du core
├── services/
│   ├── __init__.py            # Services exposés
│   ├── mobile_auth_service.py # Service d'authentification mobile
│   └── mobile_sync_service.py # Service de synchronisation mobile
├── repositories/
│   ├── __init__.py            # Repositories exposés
│   └── mobile_sync_repository.py # Repository de synchronisation mobile
└── exceptions/
    ├── __init__.py            # Exceptions exposées
    └── mobile_exceptions.py   # Exceptions pour la synchronisation mobile
```

## Services

### MobileAuthService
- **Localisation**: `core/services/mobile_auth_service.py`
- **Fonctionnalités**:
  - Authentification des utilisateurs
  - Génération de tokens JWT
  - Gestion des sessions
  - Refresh de tokens

### MobileSyncService
- **Localisation**: `core/services/mobile_sync_service.py`
- **Fonctionnalités**:
  - Synchronisation des données mobiles
  - Récupération des inventaires, jobs, assignations
  - Gestion des produits, locations, stocks par utilisateur
  - Upload des données de synchronisation

## Repositories

### MobileSyncRepository
- **Localisation**: `core/repositories/mobile_sync_repository.py`
- **Fonctionnalités**:
  - Accès aux données de synchronisation
  - Requêtes complexes pour les relations entre modèles
  - Formatage des données pour l'API
  - Gestion des relations complexes (Stock -> Location -> SousZone -> Zone -> Warehouse -> Setting -> Account)

## Exceptions

### Exceptions de Base
- **MobileSyncException**: Exception de base pour la synchronisation mobile

### Exceptions Spécifiques
- **InventoryNotFoundException**: Inventaire non trouvé
- **UserNotFoundException**: Utilisateur non trouvé
- **WarehouseNotFoundException**: Entrepôt non trouvé
- **AccountNotFoundException**: Compte non trouvé
- **ProductNotFoundException**: Produit non trouvé
- **LocationNotFoundException**: Location non trouvée
- **StockNotFoundException**: Stock non trouvé
- **DatabaseConnectionException**: Erreur de connexion à la base de données
- **DataValidationException**: Erreur de validation des données

## Utilisation

### Import des Services
```python
from core.services.mobile_auth_service import MobileAuthService
from core.services.mobile_sync_service import MobileSyncService
```

### Import des Repositories
```python
from core.repositories.mobile_sync_repository import MobileSyncRepository
```

### Import des Exceptions
```python
from core.exceptions.mobile_exceptions import (
    MobileSyncException,
    UserNotFoundException,
    StockNotFoundException
)
```

### Utilisation dans les Vues
```python
from core.services.mobile_sync_service import MobileSyncService
from core.exceptions.mobile_exceptions import UserNotFoundException

class UserStocksView(APIView):
    def get(self, request, user_id):
        try:
            sync_service = MobileSyncService()
            response_data = sync_service.get_user_stocks(user_id)
            return Response(response_data, status=status.HTTP_200_OK)
        except UserNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'USER_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
```

## Avantages de la Séparation

### 1. Modularité
- Services et repositories séparés de l'application mobile
- Réutilisables par d'autres applications Django
- Structure claire et organisée

### 2. Testabilité
- Services et repositories peuvent être testés indépendamment
- Mocking plus facile pour les tests unitaires
- Isolation des responsabilités

### 3. Maintenabilité
- Code centralisé dans le core
- Modifications appliquées à toutes les applications utilisant le core
- Réduction de la duplication de code

### 4. Extensibilité
- Facile d'ajouter de nouveaux services au core
- Structure prête pour d'autres types de services (web, API, etc.)
- Architecture scalable

## Migration

### Ancienne Structure
```
apps/mobile/
├── services/
│   ├── mobile_auth_service.py
│   └── mobile_sync_service.py
├── repositories/
│   └── mobile_sync_repository.py
└── exceptions.py
```

### Nouvelle Structure
```
core/
├── services/
│   ├── mobile_auth_service.py
│   └── mobile_sync_service.py
├── repositories/
│   └── mobile_sync_repository.py
└── exceptions/
    └── mobile_exceptions.py

apps/mobile/
└── views.py  # Utilise les services du core
```

## Tests

Pour vérifier que la séparation fonctionne correctement :

```bash
python test_core_separation.py
```

Ce script teste :
- Les imports du core
- L'instanciation des services
- L'instanciation des repositories
- La gestion des exceptions
- Le fonctionnement des vues mobile

## API Endpoints Disponibles

### Authentification
- `POST /api/mobile/auth/login/` - Connexion
- `POST /api/mobile/auth/logout/` - Déconnexion
- `POST /api/mobile/auth/refresh/` - Refresh token

### Synchronisation
- `GET /api/mobile/sync/data/` - Synchronisation générale
- `GET /api/mobile/sync/data/user/{user_id}/` - Synchronisation par utilisateur
- `POST /api/mobile/sync/upload/` - Upload des données

### Données par Utilisateur
- `GET /api/mobile/user/{user_id}/products/` - Produits de l'utilisateur
- `GET /api/mobile/user/{user_id}/locations/` - Locations de l'utilisateur
- `GET /api/mobile/user/{user_id}/stocks/` - Stocks de l'utilisateur

### Données par Inventaire
- `GET /api/mobile/inventory/{inventory_id}/users/` - Utilisateurs de l'inventaire

## Configuration

Aucune configuration supplémentaire n'est nécessaire. Les imports ont été mis à jour automatiquement dans les vues de l'application mobile.

## Maintenance

### Ajout d'un Nouveau Service
1. Créer le service dans `core/services/`
2. Ajouter l'import dans `core/services/__init__.py`
3. Ajouter dans `core/__init__.py` si nécessaire

### Ajout d'un Nouveau Repository
1. Créer le repository dans `core/repositories/`
2. Ajouter l'import dans `core/repositories/__init__.py`
3. Ajouter dans `core/__init__.py` si nécessaire

### Ajout d'une Nouvelle Exception
1. Créer l'exception dans `core/exceptions/`
2. Ajouter l'import dans `core/exceptions/__init__.py`
3. Ajouter dans `core/__init__.py` si nécessaire 