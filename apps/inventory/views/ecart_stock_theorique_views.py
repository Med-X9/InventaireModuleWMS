"""
Vues API pour EcartStockTheorique.
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.datatables.mixins import ServerSideDataTableView
from apps.inventory.exceptions import InventoryNotFoundError, InventoryValidationError
from apps.inventory.serializers.ecart_stock_theorique_serializer import (
    EcartStockTheoriqueSerializer,
    EcartStockTheoriqueSyncSerializer,
    EcartStockTheoriqueUpdateSerializer,
    EcartStockTheoriqueValiderSelectionSerializer,
)
from apps.inventory.services.ecart_stock_theorique_service import (
    EcartStockTheoriqueService,
)
from apps.inventory.utils.response_utils import error_response, success_response

logger = logging.getLogger(__name__)


class EcartStockTheoriqueSyncView(APIView):
    """
    POST /inventory/{inventory_id}/warehouses/{warehouse_id}/ecarts-stock/sync/

    Synchronise le calcul stock-gaps vers la table persistée.
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = EcartStockTheoriqueService()

    def post(self, request, inventory_id: int, warehouse_id: int):
        serializer = EcartStockTheoriqueSyncSerializer(data=request.data or {})
        if not serializer.is_valid():
            return error_response(
                "Données invalides",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        only_nonzero = serializer.validated_data.get("only_nonzero", False)
        try:
            result = self.service.sync_from_compute(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
                only_nonzero=only_nonzero,
            )
            return success_response(
                data=result,
                message=(
                    f"Sync terminée : {result['created']} créé(s), "
                    f"{result['updated']} mis à jour, "
                    f"{result['skipped_validated']} validé(s) ignoré(s)"
                ),
                status_code=status.HTTP_200_OK,
            )
        except InventoryNotFoundError as exc:
            return error_response(str(exc), status_code=status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error("Erreur sync ecarts-stock: %s", exc, exc_info=True)
            return error_response(
                f"Erreur lors de la synchronisation: {exc}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EcartStockTheoriqueListView(ServerSideDataTableView):
    """
    GET|POST /inventory/{inventory_id}/warehouses/{warehouse_id}/ecarts-stock/

    Liste DataTable des écarts persistés.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EcartStockTheoriqueSerializer
    default_page_size = 20
    max_page_size = 500
    export_filename = "ecarts_stock_theorique"

    search_fields = ["article_cle", "designation", "reference", "mode_groupement"]
    column_field_mapping = {
        "article_cle": "article_cle",
        "designation": "designation",
        "qte_theorique": "qte_theorique",
        "qte_pratique": "qte_pratique",
        "ecart": "ecart",
        "resultat_final": "resultat_final",
        "valide": "valide",
        "mode_groupement": "mode_groupement",
        "reference": "reference",
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = EcartStockTheoriqueService()

    def get_queryset(self):
        inventory_id = self.kwargs.get("inventory_id")
        warehouse_id = self.kwargs.get("warehouse_id")
        return self.service.get_queryset_for_warehouse(inventory_id, warehouse_id)


class EcartStockTheoriqueUpdateView(APIView):
    """
    PATCH /ecarts-stock/{ecart_id}/

    Saisie du résultat final (bloqué si validé).
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = EcartStockTheoriqueService()

    def patch(self, request, ecart_id: int):
        serializer = EcartStockTheoriqueUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Données invalides",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            row = self.service.update_resultat_final(
                ecart_id, serializer.validated_data["resultat_final"]
            )
            return success_response(
                data=EcartStockTheoriqueSerializer(row).data,
                message="Résultat final mis à jour",
            )
        except InventoryNotFoundError as exc:
            return error_response(str(exc), status_code=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error("Erreur update resultat_final: %s", exc, exc_info=True)
            return error_response(
                "Erreur lors de la mise à jour",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EcartStockTheoriqueValiderView(APIView):
    """
    POST /ecarts-stock/{ecart_id}/valider/

    Valide la ligne (verrouille resultat_final).
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = EcartStockTheoriqueService()

    def post(self, request, ecart_id: int):
        try:
            user = request.user if request.user.is_authenticated else None
            row = self.service.valider(ecart_id, user=user)
            return success_response(
                data=EcartStockTheoriqueSerializer(row).data,
                message="Ligne validée avec succès",
            )
        except InventoryNotFoundError as exc:
            return error_response(str(exc), status_code=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error("Erreur validation ecart stock: %s", exc, exc_info=True)
            return error_response(
                "Erreur lors de la validation",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EcartStockTheoriqueValiderSelectionView(APIView):
    """
    POST /ecarts-stock/valider/

    Valide une sélection de lignes (multi).
    Body: { "ecart_ids": [1, 2, 3] }
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = EcartStockTheoriqueService()

    def post(self, request):
        serializer = EcartStockTheoriqueValiderSelectionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Données invalides",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = request.user if request.user.is_authenticated else None
            result = self.service.valider_selection(
                serializer.validated_data["ecart_ids"],
                user=user,
            )
            if result["validated_count"] == 0:
                return error_response(
                    "Aucune ligne n'a pu être validée",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=result,
                )
            message = (
                "Toutes les lignes sélectionnées ont été validées"
                if result["success"]
                else (
                    f"{result['validated_count']}/{result['requested_count']} "
                    "ligne(s) validée(s) (succès partiel)"
                )
            )
            return success_response(
                data=result,
                message=message,
                status_code=status.HTTP_200_OK,
            )
        except InventoryValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error("Erreur validation multi ecarts-stock: %s", exc, exc_info=True)
            return error_response(
                "Erreur lors de la validation multi",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
