# Exceptions pour l'application mobile

from .auth_exceptions import (
    AuthException,
    UserNotFoundException,
    InvalidCredentialsException,
    TokenInvalidException,
    UserInactiveException,
)

from .sync_exceptions import (
    SyncException,
    SyncDataException,
    UploadDataException,
    JobNotFoundException,
    AssignmentNotFoundException,
    CountingNotFoundException,
)

from .inventory_exceptions import (
    InventoryException,
    InventoryNotFoundException,
    AccountNotFoundException,
    DatabaseConnectionException,
    DataValidationException,
)

from .user_exceptions import (
    UserException,
    ProductNotFoundException,
    LocationNotFoundException,
    StockNotFoundException,
)

from .assignment_exceptions import (
    AssignmentNotFoundException,
    UserNotAssignedException,
    InvalidStatusTransitionException,
    JobNotFoundException,
    AssignmentValidationException,
)

from .counting_detail_exceptions import (
    CountingDetailValidationError,
    ProductPropertyValidationError,
    CountingAssignmentValidationError,
    JobDetailValidationError,
    NumeroSerieValidationError,
    CountingModeValidationError,
    CountingDetailBatchError,
    CountingDetailNotFoundError,
    CountingDetailUpdateError,
)

__all__ = [
    # Auth exceptions
    'AuthException',
    'UserNotFoundException',
    'InvalidCredentialsException',
    'TokenInvalidException',
    'UserInactiveException',
    
    # Sync exceptions
    'SyncException',
    'SyncDataException',
    'UploadDataException',
    'JobNotFoundException',
    'AssignmentNotFoundException',
    'CountingNotFoundException',
    
    # Inventory exceptions
    'InventoryException',
    'InventoryNotFoundException',
    'AccountNotFoundException',
    'DatabaseConnectionException',
    'DataValidationException',
    
    # User exceptions
    'UserException',
    'ProductNotFoundException',
    'LocationNotFoundException',
    'StockNotFoundException',
    
    # Assignment exceptions
    'AssignmentNotFoundException',
    'UserNotAssignedException',
    'InvalidStatusTransitionException',
    'JobNotFoundException',
    'AssignmentValidationException',
    
    # Counting detail exceptions
    'CountingDetailValidationError',
    'ProductPropertyValidationError',
    'CountingAssignmentValidationError',
    'JobDetailValidationError',
    'NumeroSerieValidationError',
    'CountingModeValidationError',
    'CountingDetailBatchError',
    'CountingDetailNotFoundError',
    'CountingDetailUpdateError',
] 