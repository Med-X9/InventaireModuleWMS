"""
Vue pour l'export Excel consolidé par article
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from ..services.excel_export_service import ExcelExportService
from ..utils.response_utils import error_response
import logging

logger = logging.getLogger(__name__)


class ConsolidatedArticleExcelExportView(APIView):
    """
    Vue pour exporter un fichier Excel consolidé par article.
    
    Pour chaque article, le fichier contient :
    - Les informations de l'article (référence, code, description, etc.)
    - La quantité consolidée (somme de toutes les quantités dans tous les emplacements)
    - Une colonne par emplacement avec la quantité dans cet emplacement
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = ExcelExportService()
    
    def get(self, request, inventory_id: int, *args, **kwargs):
        """
        Exporte un fichier Excel consolidé par article pour un inventaire.
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Fichier Excel avec les données consolidées par article
        """
        try:
            # Générer le fichier Excel
            excel_buffer = self.service.generate_consolidated_excel(inventory_id)
            
            # Récupérer les informations de l'inventaire pour le nom du fichier
            try:
                from ..models import Inventory
                inventory = Inventory.objects.get(id=inventory_id)
                inventory_ref = inventory.reference.replace(' ', '_')
            except Inventory.DoesNotExist:
                inventory_ref = f"inventaire_{inventory_id}"
            
            # Définir le nom du fichier
            filename = f"articles_consolides_{inventory_ref}.xlsx"
            
            # Créer la réponse HTTP avec le fichier Excel
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except ValueError as error:
            logger.warning(
                "Erreur de validation lors de l'export Excel (id=%s): %s",
                inventory_id,
                error,
            )
            return error_response(
                message=str(error),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except ImportError as error:
            logger.error(
                "Dépendance manquante pour l'export Excel (id=%s): %s",
                inventory_id,
                error,
            )
            return error_response(
                message=f"Configuration manquante pour l'export Excel: {str(error)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as error:
            logger.error(
                "Erreur inattendue lors de l'export Excel (id=%s): %s",
                inventory_id,
                error,
                exc_info=True,
            )
            return error_response(
                message=f"Une erreur inattendue est survenue lors de l'export Excel: {str(error)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

