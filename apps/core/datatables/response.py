"""
Modèle de réponse compatible AG-Grid.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ResponseModel:
    """
    Modèle de réponse compatible AG-Grid.
    
    Format AG-Grid pour getRows():
    {
        "rowData": [...],
        "rowCount": 1000
    }
    """
    row_data: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    success: bool = True
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire compatible AG-Grid"""
        result = {
            "rowData": self.row_data,
            "rowCount": self.row_count,
            "success": self.success
        }
        
        if self.message:
            result["message"] = self.message
        
        return result
    
    @classmethod
    def from_data(
        cls,
        data: List[Dict[str, Any]],
        total_count: int,
        success: bool = True,
        message: Optional[str] = None
    ) -> 'ResponseModel':
        """Crée depuis des données"""
        return cls(
            row_data=data,
            row_count=total_count,
            success=success,
            message=message
        )

