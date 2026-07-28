"""
Interface provider stock théorique (Excel V1 / WMS phase 2).
"""
from abc import ABC, abstractmethod
from typing import Dict


class ITheoreticalStockProvider(ABC):
    """
    Fournit les quantités théoriques agrégées par product_id
    pour un inventaire + magasin.
    """

    @abstractmethod
    def get_quantities_by_product(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> Dict[int, int]:
        """
        Returns:
            Dict[product_id, quantité théorique agrégée]
        """
        raise NotImplementedError
