"""
Use case pour la generation du PDF d'un job/assignment/equipe
"""
from typing import Dict, Any, Optional
from io import BytesIO
from ..services.pdf_service import PDFService
import logging

logger = logging.getLogger(__name__)


class JobAssignmentPdfUseCase:
    """Use case pour la generation du PDF d'un job/assignment/equipe"""
    
    def __init__(self):
        self.pdf_service = PDFService()
    
    def execute(
        self, 
        job_id: int, 
        assignment_id: int, 
        equipe_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute la generation du PDF d'un job/assignment/equipe
        
        Args:
            job_id: ID du job
            assignment_id: ID de l'assignment
            equipe_id: ID de l'equipe (optionnel)
            
        Returns:
            Dict contenant le PDF et les metadonnees
            
        Raises:
            Exception: Si une erreur survient
        """
        try:
            logger.info(
                f"Generation du PDF pour le job {job_id}, "
                f"assignment {assignment_id}, equipe {equipe_id}"
            )
            
            # Generer le PDF
            pdf_buffer = self.pdf_service.generate_job_assignment_pdf(
                job_id, 
                assignment_id, 
                equipe_id
            )
            
            # Retourner le resultat
            return {
                'success': True,
                'pdf_buffer': pdf_buffer,
                'job_id': job_id,
                'assignment_id': assignment_id,
                'equipe_id': equipe_id
            }
            
        except ValueError as e:
            logger.error(f"Erreur de validation lors de la generation du PDF: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la generation du PDF: {str(e)}")
            raise

