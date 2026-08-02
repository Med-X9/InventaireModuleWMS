"""
Vues d'export analyse écarts (Excel) et PDF recomptage des lignes avec écart.
"""
import logging

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.inventory.exceptions.inventory_exceptions import InventoryNotFoundError
from apps.inventory.exceptions.warehouse_exceptions import WarehouseNotFoundError
from apps.inventory.services.ecart_analyse_export_service import (
    EcartAnalyseExportService,
)

logger = logging.getLogger(__name__)


class EcartAnalyseExcelExportView(APIView):
    """
    Export Excel des données d'analyse (EcartStockTheorique).

    GET /web/api/inventory/{inventory_id}/warehouse/{warehouse_id}/analyse/export/excel/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, inventory_id: int, warehouse_id: int):
        try:
            service = EcartAnalyseExportService()
            buffer = service.generate_analyse_excel(inventory_id, warehouse_id)
            filename = f"analyse_ecarts_inv{inventory_id}_wh{warehouse_id}.xlsx"
            response = HttpResponse(
                buffer.getvalue(),
                content_type=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except InventoryNotFoundError as exc:
            return HttpResponse(str(exc), status=404, content_type="text/plain")
        except WarehouseNotFoundError as exc:
            return HttpResponse(str(exc), status=404, content_type="text/plain")
        except ValueError as exc:
            return HttpResponse(str(exc), status=400, content_type="text/plain")
        except Exception as exc:
            logger.error(
                "Export Excel analyse échoué inv=%s wh=%s: %s",
                inventory_id,
                warehouse_id,
                exc,
                exc_info=True,
            )
            return HttpResponse(
                f"Erreur lors de l'export Excel: {exc}",
                status=500,
                content_type="text/plain",
            )


class EcartAnalysePdfExportView(APIView):
    """
    Export PDF des lignes avec écart (théorique vs physique).

    Tableau : N° | Job | Emplacement | Désignation | Barcode | |Écart| |
    Positif/Négatif | 3e | 4e | 5e comptage
    Tri décroissant sur |écart|.
    Job et emplacements issus de CountingDetail (pas Stock).
    Header : nom du magasin

    GET /web/api/inventory/{inventory_id}/warehouse/{warehouse_id}/analyse/export/pdf/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, inventory_id: int, warehouse_id: int):
        try:
            service = EcartAnalyseExportService()
            buffer = service.generate_ecart_pdf(inventory_id, warehouse_id)
            filename = f"recomptage_ecarts_inv{inventory_id}_wh{warehouse_id}.pdf"
            response = HttpResponse(
                buffer.getvalue(),
                content_type="application/pdf",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except InventoryNotFoundError as exc:
            return HttpResponse(str(exc), status=404, content_type="text/plain")
        except WarehouseNotFoundError as exc:
            return HttpResponse(str(exc), status=404, content_type="text/plain")
        except ValueError as exc:
            return HttpResponse(str(exc), status=400, content_type="text/plain")
        except Exception as exc:
            logger.error(
                "Export PDF écarts échoué inv=%s wh=%s: %s",
                inventory_id,
                warehouse_id,
                exc,
                exc_info=True,
            )
            return HttpResponse(
                f"Erreur lors de l'export PDF: {exc}",
                status=500,
                content_type="text/plain",
            )
