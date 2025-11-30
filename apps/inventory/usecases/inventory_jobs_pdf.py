"""
Use case pour la generation du PDF des jobs d'inventaire
"""
from typing import Dict, Any, Optional, List
from io import BytesIO
from ..interfaces.pdf_interface import PDFUseCaseInterface
from ..services.pdf_service import PDFService
from ..exceptions.pdf_exceptions import (
    PDFGenerationError,
    PDFValidationError,
    PDFNotFoundError,
    PDFEmptyContentError,
    PDFServiceError,
    PDFRepositoryError
)
import logging

logger = logging.getLogger(__name__)


class InventoryJobsPdfUseCase(PDFUseCaseInterface):
    """Use case pour la generation du PDF des jobs d'inventaire"""
    
    def __init__(self):
        self.pdf_service = PDFService()
    
    def execute(
        self, 
        inventory_id: int, 
        counting_id: Optional[int] = None,
        job_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Execute la generation du PDF des jobs d'inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            counting_id: ID du comptage (optionnel)
            job_ids: Liste des IDs de jobs à exporter (optionnel) - si fourni, 
                     exporte uniquement ces jobs avec assignments PRET ou TRANSFERT
            
        Returns:
            Dict contenant le PDF et les metadonnees
            
        Raises:
            Exception: Si une erreur survient
        """
        try:
            logger.info(f"Generation du PDF pour l'inventaire {inventory_id}, comptage {counting_id}")
            if job_ids:
                logger.info(f"Filtrage par job IDs: {job_ids}")
            
            # Generer le PDF
            pdf_buffer = self.pdf_service.generate_inventory_jobs_pdf(
                inventory_id, 
                counting_id, 
                job_ids=job_ids
            )
            
            # Retourner le resultat
            return {
                'success': True,
                'pdf_buffer': pdf_buffer,
                'inventory_id': inventory_id,
                'counting_id': counting_id,
                'job_ids': job_ids
            }
            
        except (PDFValidationError, PDFNotFoundError, PDFEmptyContentError) as e:
            # Re-propaguer les erreurs de validation et de ressources non trouvées
            logger.error(f"Erreur de validation/ressource lors de la generation du PDF: {str(e)}")
            raise
        except (PDFServiceError, PDFRepositoryError) as e:
            # Re-propaguer les erreurs de service/repository
            logger.error(f"Erreur de service/repository lors de la generation du PDF: {str(e)}")
            raise
        except PDFGenerationError as e:
            # Re-propaguer les autres erreurs de génération PDF
            logger.error(f"Erreur de generation PDF: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la generation du PDF: {str(e)}", exc_info=True)
            raise PDFGenerationError(f"Erreur inattendue lors de la generation du PDF: {str(e)}")

