# Exceptions pour l'application inventory

# Import des exceptions d'assignment
from .assignment_exceptions import (
    AssignmentError,
    AssignmentNotFoundError,
    AssignmentValidationError,
    AssignmentBusinessRuleError,
    AssignmentSessionError
)

# Import des exceptions de stock
from .stock_exceptions import (
    StockValidationError,
    StockNotFoundError,
    StockImportError,
    StockDuplicateError
)

# Import des exceptions d'inventaire
from .inventory_exceptions import (
    InventoryError,
    InventoryValidationError,
    InventoryNotFoundError,
    InventoryCreationError,
    InventoryStatusError,
    InventoryDateError,
    CountingError,
    CountingValidationError
)

# Import des exceptions de job
from .job_exceptions import (
    JobCreationError,
    JobNotFoundError,
    JobStatusError
)

# Import des exceptions de planning
from .planning_exceptions import (
    PlanningCreationError,
    PlanningNotFoundError,
    PlanningDateError
)

# Import des exceptions de PDA
from .pda_exceptions import (
    PdaCreationError,
    PdaNotFoundError,
    PdaLabelError
)

# Import des exceptions de resource assignment
from .resource_assignment_exceptions import (
    ResourceAssignmentValidationError
)

# Import des exceptions de counting detail (nouvelles)
from .counting_detail_exceptions import (
    CountingDetailValidationError,
    ProductPropertyValidationError,
    CountingAssignmentValidationError,
    JobDetailValidationError,
    NumeroSerieValidationError,
    CountingModeValidationError
)

# Import des exceptions d'entrepôt
from .warehouse_exceptions import (
    WarehouseAccountValidationError,
    WarehouseAccountNotFoundError,
)

# Import des exceptions de PDF
from .pdf_exceptions import (
    PDFGenerationError,
    PDFValidationError,
    PDFNotFoundError,
    PDFEmptyContentError,
    PDFInvalidContentError,
    PDFRepositoryError,
    PDFServiceError,
)

# Liste des exceptions disponibles
__all__ = [
    # Assignment exceptions
    'AssignmentError',
    'AssignmentNotFoundError',
    'AssignmentValidationError',
    'AssignmentBusinessRuleError',
    'AssignmentSessionError',
    
    # Stock exceptions
    'StockValidationError',
    'StockNotFoundError',
    'StockImportError',
    'StockDuplicateError',
    
    # Inventory exceptions
    'InventoryError',
    'InventoryValidationError',
    'InventoryNotFoundError',
    'InventoryCreationError',
    'InventoryStatusError',
    'InventoryDateError',
    'CountingError',
    'CountingValidationError',
    
    # Job exceptions
    'JobCreationError',
    'JobNotFoundError',
    'JobStatusError',
    
    # Planning exceptions
    'PlanningCreationError',
    'PlanningNotFoundError',
    'PlanningDateError',
    
    # PDA exceptions
    'PdaCreationError',
    'PdaNotFoundError',
    'PdaLabelError',
    
    # Resource assignment exceptions
    'ResourceAssignmentValidationError',
    
    # CountingDetail exceptions (nouvelles)
    'CountingDetailValidationError',
    'ProductPropertyValidationError',
    'CountingAssignmentValidationError',
    'JobDetailValidationError',
    'NumeroSerieValidationError',
    'CountingModeValidationError',

    # Warehouse exceptions
    'WarehouseAccountValidationError',
    'WarehouseAccountNotFoundError',
    
    # PDF exceptions
    'PDFGenerationError',
    'PDFValidationError',
    'PDFNotFoundError',
    'PDFEmptyContentError',
    'PDFInvalidContentError',
    'PDFRepositoryError',
    'PDFServiceError',
]
