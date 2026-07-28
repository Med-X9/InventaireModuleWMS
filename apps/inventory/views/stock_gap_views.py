"""
Vue API DataTable — écarts stock depuis la table EcartStockTheorique.
"""
import logging
from typing import Any, Dict, Optional

from rest_framework import status
from rest_framework.response import Response

from apps.core.datatables.mixins import ServerSideDataTableView
from apps.inventory.exceptions import InventoryNotFoundError
from apps.inventory.serializers.stock_gap_serializer import StockGapLineSerializer
from apps.inventory.services.stock_gap_service import StockGapService

logger = logging.getLogger(__name__)


class StockGapListView(ServerSideDataTableView):
    """
    Liste les écarts stock depuis EcartStockTheorique (après ANALYSER).

    GET|POST /inventory/<inventory_id>/warehouses/<warehouse_id>/stock-gaps/

    Lit la table (pas de recalcul). Inclut resultat_final et valide.
    Pas de mode de regroupement dans la réponse.
    """

    serializer_class = StockGapLineSerializer
    default_page_size = 20
    max_page_size = 500
    export_filename = "ecarts_stock_theorique"

    search_fields = [
        "cle",
        "designation",
    ]

    column_field_mapping = {
        "ecart_id": "ecart_id",
        "cle": "cle",
        "designation": "designation",
        "qte_theorique": "qte_theorique",
        "qte_inventoriee": "qte_inventoriee",
        "ecart": "ecart",
        "resultat_final": "resultat_final",
        "valide": "valide",
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = StockGapService()
        self._gap_meta: Optional[Dict[str, Any]] = None

    def get_data_source(self):
        """Lit les lignes persistées puis expose une ListDataSource."""
        from apps.core.datatables.datasource import DataSourceFactory

        inventory_id = self.kwargs.get("inventory_id")
        warehouse_id = self.kwargs.get("warehouse_id")
        if not inventory_id or not warehouse_id:
            raise InventoryNotFoundError(
                "inventory_id et warehouse_id sont requis."
            )

        only_nonzero_raw = self.request.query_params.get("only_nonzero", "true")
        only_nonzero = str(only_nonzero_raw).lower() not in ("0", "false", "no")

        result = self.service.list_persisted_stock_gaps(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
            only_nonzero=only_nonzero,
        )
        self._gap_meta = {
            "inventory_id": result["inventory_id"],
            "warehouse_id": result["warehouse_id"],
            "source": result.get("source", "ecart_stock_theorique"),
            "totaux": result["totaux"],
        }
        return DataSourceFactory.create(result["lignes"])

    def process_request(self, request, *args, **kwargs):
        """QueryModel + métadonnées (source, totaux)."""
        try:
            response = super().process_request(request, *args, **kwargs)
        except InventoryNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "errors": [str(exc)],
                    "rows": [],
                    "total": 0,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            self._gap_meta
            and hasattr(response, "data")
            and isinstance(response.data, dict)
            and response.status_code == status.HTTP_200_OK
        ):
            response.data.update(self._gap_meta)

        if (
            response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            and isinstance(response.data, dict)
        ):
            message = str(response.data.get("message", ""))
            if "introuvable" in message.lower() or "not found" in message.lower():
                response.status_code = status.HTTP_404_NOT_FOUND
                response.data["success"] = False
                if "errors" not in response.data:
                    response.data["errors"] = [message]

        return response
