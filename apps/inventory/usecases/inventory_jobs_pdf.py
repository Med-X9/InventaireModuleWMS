"""
Use case pour la generation du PDF des jobs d'inventaire
"""
from typing import Dict, Any, Optional
from io import BytesIO
from ..interfaces.pdf_interface import PDFUseCaseInterface
from ..services.pdf_service import PDFService
import logging

logger = logging.getLogger(__name__)


class InventoryJobsPdfUseCase(PDFUseCaseInterface):
    """Use case pour la generation du PDF des jobs d'inventaire"""
    
    def __init__(self):
        self.pdf_service = PDFService()
    
    def execute(self, inventory_id: int, counting_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute la generation du PDF des jobs d'inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            counting_id: ID du comptage (optionnel)
            
        Returns:
            Dict contenant le PDF et les metadonnees
            
        Raises:
            Exception: Si une erreur survient
        """
        try:
            logger.info(f"Generation du PDF pour l'inventaire {inventory_id}, comptage {counting_id}")
            
            # Generer le PDF
            pdf_buffer = self.pdf_service.generate_inventory_jobs_pdf(inventory_id, counting_id)
            
            # Retourner le resultat
            return {
                'success': True,
                'pdf_buffer': pdf_buffer,
                'inventory_id': inventory_id,
                'counting_id': counting_id
            }
            
        except ValueError as e:
            logger.error(f"Erreur de validation lors de la generation du PDF: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la generation du PDF: {str(e)}")
            raise

