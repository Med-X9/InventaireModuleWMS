from rest_framework.views import APIView
from django.http import HttpResponse
from ..services.job_export_service import JobExportService
from ..exceptions.job_exceptions import JobCreationError
from ..exceptions.inventory_exceptions import InventoryNotFoundError
from ..exceptions.warehouse_exceptions import WarehouseNotFoundError
import logging

logger = logging.getLogger(__name__)


class JobExportView(APIView):
    """
    Vue pour l'export Excel des jobs prêts
    Exporte par défaut un fichier Excel
    """
    
    def get(self, request, inventory_id, warehouse_id):
        """
        Exporte les jobs prêts en Excel pour un inventaire et un warehouse
        
        URL params:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
        
        Returns:
            Fichier Excel avec les jobs prêts
        """
        try:
            # Appeler le service pour exporter les jobs en Excel
            # La validation de l'inventaire et du warehouse est faite dans le service
            service = JobExportService()
            excel_buffer = service.generate_excel_export(inventory_id, warehouse_id)
            
            # Récupérer les informations pour le nom du fichier
            try:
                from ..models import Inventory
                from apps.masterdata.models import Warehouse
                inventory = Inventory.objects.get(id=inventory_id)
                warehouse = Warehouse.objects.get(id=warehouse_id)
                inventory_ref = inventory.reference.replace(' ', '_')
                warehouse_ref = warehouse.reference.replace(' ', '_')
                filename = f"jobs_prets_{inventory_ref}_{warehouse_ref}.xlsx"
            except Exception:
                filename = f"jobs_prets_{inventory_id}_{warehouse_id}.xlsx"
            
            # Créer la réponse HTTP avec le fichier Excel
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except InventoryNotFoundError as e:
            logger.warning(f"Export Excel échoué - Inventaire non trouvé: {inventory_id}")
            return HttpResponse(
                f"Erreur: {str(e)}",
                status=404,
                content_type='text/plain'
            )
        except WarehouseNotFoundError as e:
            logger.warning(f"Export Excel échoué - Entrepôt non trouvé: {warehouse_id}")
            return HttpResponse(
                f"Erreur: {str(e)}",
                status=404,
                content_type='text/plain'
            )
        except JobCreationError as e:
            logger.error(f"Export Excel échoué - Erreur métier: {str(e)}")
            return HttpResponse(
                f"Erreur: {str(e)}",
                status=400,
                content_type='text/plain'
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'export Excel: {str(e)}", exc_info=True)
            return HttpResponse(
                f"Erreur lors de l'export: {str(e)}",
                status=500,
                content_type='text/plain'
            )

