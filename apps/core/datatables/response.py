"""
Modèle de réponse pour le nouveau format QueryModel.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ResponseModel:
    """
    Modèle de réponse pour le nouveau format QueryModel.
    
    Format de réponse:
    {
        "rows": [...],
        "page": 2,
        "pageSize": 10,
        "total": 28,
        "totalPages": 3
    }
    """
    row_data: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    page: int = 1
    page_size: int = 10
    
    def to_dict(self, include_block_indices: bool = False) -> Dict[str, Any]:
        """
        Convertit en dictionnaire pour le format QueryModel.

        Args:
            include_block_indices: Si True, ajoute startRow et endRow (indices 0-based
                du bloc renvoyé). Optionnel, utile pour le virtual scrolling.
        """
        result = {
            "rows": self.row_data,
            "total": self.row_count,
            "page": self.page,
            "pageSize": self.page_size,
        }
        
        if self.page_size > 0:
            result["totalPages"] = (self.row_count + self.page_size - 1) // self.page_size
        else:
            result["totalPages"] = 0
        
        if include_block_indices:
            start_row = (self.page - 1) * self.page_size
            result["startRow"] = start_row
            result["endRow"] = start_row + len(self.row_data)
        
        return result
    
    @classmethod
    def from_data(
        cls,
        data: List[Dict[str, Any]],
        total_count: int,
        page: int = 1,
        page_size: int = 10
    ) -> 'ResponseModel':
        """Crée depuis des données"""
        return cls(
            row_data=data,
            row_count=total_count,
            page=page,
            page_size=page_size
        )

