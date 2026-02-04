# Import des vues organisées par catégorie

# Vues d'authentification
from .auth import (
    LoginView,
    JWTLoginView,
    LogoutView,
    RefreshTokenView
)

# Vues de synchronisation
from .sync import (
    SyncDataView,
    UploadDataView
)

# Vues d'inventaire
from .inventory import (
    InventoryUsersView
)

# Vues utilisateur
from .user import (
    UserProductsView,
    AllProductsView,
    UserProductsExportView,
    UserLocationsView,
    UserStocksView
)

# Vues d'assignment
from .assignment import (
    AssignmentStatusView,
    CloseJobView,
    BlockAssignmentView,
    UnblockAssignmentView
)

# Vues de comptage
from .counting import (
    CountingDetailView
)

# Vues de personnes
from .person import (
    PersonListView,
)

__all__ = [
    # Auth views
    'LoginView',
    'JWTLoginView',
    'LogoutView',
    'RefreshTokenView',

    # Sync views
    'SyncDataView',
    'UploadDataView',

    # Inventory views
    'InventoryUsersView',

    # User views
    'UserProductsView',
    'AllProductsView',
    'UserProductsExportView',
    'UserLocationsView',
    'UserStocksView',

    # Assignment views
    'AssignmentStatusView',
    'CloseJobView',
    'BlockAssignmentView',
    'UnblockAssignmentView',

    # Counting views
    'CountingDetailView',

    # Person views
    'PersonListView',
]
