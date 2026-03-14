"""
Service pour la gestion des entrepôts liés aux comptes.
"""
from typing import List, Optional
import logging

from apps.masterdata.models import Account, Warehouse

from ..repositories.warehouse_repository import WarehouseRepository
from ..exceptions import (
    WarehouseAccountValidationError,
    WarehouseAccountNotFoundError,
)

logger = logging.getLogger(__name__)


class WarehouseService:
    """Service gérant la récupération des entrepôts."""

    def __init__(self, warehouse_repository: Optional[WarehouseRepository] = None) -> None:
        """
        Initialise le service avec son repository.

        Args:
            warehouse_repository: Repository pour accéder aux entrepôts.
        """
        self.repository = warehouse_repository or WarehouseRepository()

    def get_warehouses_by_account(self, account_id: int) -> List[Warehouse]:
        """
        Récupère la liste des entrepôts associés à un compte donné.

        Args:
            account_id: Identifiant du compte.

        Returns:
            Liste d'entrepôts liés au compte.

        Raises:
            WarehouseAccountValidationError: Si l'identifiant du compte est invalide.
            WarehouseAccountNotFoundError: Si aucun entrepôt n'est trouvé pour le compte.
        """
        if account_id is None:
            logger.error("Identifiant de compte manquant pour la récupération des entrepôts.")
            raise WarehouseAccountValidationError("L'identifiant du compte est obligatoire.")

        if not Account.objects.filter(id=account_id).exists():
            logger.warning("Compte introuvable pour l'identifiant %s.", account_id)
            raise WarehouseAccountNotFoundError("Le compte demandé n'existe pas.")

        warehouses = self.repository.get_by_account_id(account_id)

        if not warehouses:
            logger.info("Aucun entrepôt associé au compte %s.", account_id)
            raise WarehouseAccountNotFoundError("Aucun entrepôt associé à ce compte.")

        logger.debug(
            "Récupération de %d entrepôts pour le compte %s.",
            len(warehouses),
            account_id,
        )
        return warehouses

