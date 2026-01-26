"""
Use cases pour l'application mobile.

Les use cases encapsulent la logique métier selon les principes SOLID, KISS et DRY.
Chaque use case a une responsabilité unique et peut être testé indépendamment.
"""

from .counting_detail_batch_creation import CountingDetailBatchCreationUseCase
from .counting_detail_batch_validation import CountingDetailBatchValidationUseCase
from .ecart_comptage_automatic_processing import EcartComptageAutomaticProcessingUseCase

__all__ = [
    'CountingDetailBatchCreationUseCase',
    'CountingDetailBatchValidationUseCase',
    'EcartComptageAutomaticProcessingUseCase',
]

