# Structure des Vues - App Mobile

## 🏗️ **Organisation des vues par catégorie**

Les vues de l'app mobile sont maintenant organisées dans une structure claire et modulaire pour une meilleure maintenabilité.

## 📁 **Structure des dossiers**

```
apps/mobile/views/
├── __init__.py                    # Import centralisé de toutes les vues
├── auth/                          # Vues d'authentification
│   ├── __init__.py
│   ├── login_view.py             # LoginView
│   ├── logout_view.py            # LogoutView
│   └── refresh_view.py           # RefreshTokenView
├── sync/                          # Vues de synchronisation
│   ├── __init__.py
│   ├── sync_data_view.py         # SyncDataView
│   └── upload_data_view.py       # UploadDataView
├── inventory/                     # Vues d'inventaire
│   ├── __init__.py
│   └── inventory_users_view.py   # InventoryUsersView
├── user/                          # Vues utilisateur
│   ├── __init__.py
│   ├── user_products_view.py     # UserProductsView
│   ├── user_locations_view.py    # UserLocationsView
│   └── user_stocks_view.py       # UserStocksView
└── assignment/                    # Vues d'assignment
    ├── __init__.py
    └── status_view.py            # AssignmentStatusView
```

## 🔐 **Vues d'authentification (`auth/`)**

- **`LoginView`** : Connexion utilisateur
- **`LogoutView`** : Déconnexion utilisateur
- **`RefreshTokenView`** : Renouvellement de token

## 🔄 **Vues de synchronisation (`sync/`)**

- **`SyncDataView`** : Synchronisation des données
- **`UploadDataView`** : Upload des données

## 📦 **Vues d'inventaire (`inventory/`)**

- **`InventoryUsersView`** : Utilisateurs d'un inventaire

## 👤 **Vues utilisateur (`user/`)**

- **`UserProductsView`** : Produits d'un utilisateur
- **`UserLocationsView`** : Locations d'un utilisateur
- **`UserStocksView`** : Stocks d'un utilisateur

## 📋 **Vues d'assignment (`assignment/`)**

- **`AssignmentStatusView`** : Mise à jour des statuts d'assignment et job

## ✨ **Avantages de cette structure**

### 1. **Organisation claire**
- Chaque type de vue a son propre dossier
- Séparation logique des responsabilités
- Facile de trouver une vue spécifique

### 2. **Maintenabilité**
- Code plus facile à maintenir
- Modifications isolées par catégorie
- Réduction des conflits de merge

### 3. **Évolutivité**
- Ajout facile de nouvelles vues
- Structure extensible
- Import centralisé dans `__init__.py`

### 4. **Lisibilité**
- Structure intuitive
- Nommage cohérent des fichiers
- Documentation claire

## 🔧 **Ajout d'une nouvelle vue**

Pour ajouter une nouvelle vue :

1. **Créer le fichier** dans le dossier approprié
2. **Ajouter l'import** dans le `__init__.py` du dossier
3. **Ajouter dans le `__init__.py` principal** des vues
4. **Mettre à jour `__all__`** si nécessaire

## 📝 **Exemple d'ajout**

```python
# 1. Créer apps/mobile/views/user/new_feature_view.py
class NewFeatureView(APIView):
    # ... code de la vue

# 2. Ajouter dans apps/mobile/views/user/__init__.py
from .new_feature_view import NewFeatureView

__all__ = [
    # ... autres vues
    'NewFeatureView'
]

# 3. Ajouter dans apps/mobile/views/__init__.py
from .user import NewFeatureView

__all__ = [
    # ... autres vues
    'NewFeatureView'
]
```

## 🎯 **Utilisation**

Les vues sont automatiquement disponibles via l'import principal :

```python
from apps.mobile.views import (
    LoginView,
    AssignmentStatusView,
    UserProductsView
)
```

Cette structure garantit une organisation claire et une maintenance facile du code de l'app mobile.
