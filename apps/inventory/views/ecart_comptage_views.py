from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.ecart_comptage_serializer import EcartComptageSerializer
from ..services.ecart_comptage_service import EcartComptageService
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from apps.inventory.exceptions.warehouse_exceptions import WarehouseNotFoundError


class EcartComptageUpdateFinalResultView(APIView):
    """
    API pour modifier le résultat final d'un EcartComptage.

    Contraintes métier :
    - Il doit y avoir au moins deux comptages (séquences) enregistrés
      pour l'écart cible.

    Corps attendu (JSON) :
    {
        "final_result": 120,
        "justification": "Ajustement manuel après contrôle",
        "resolved": true
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = EcartComptageService()

    def patch(self, request, ecart_id: int):
        serializer = EcartComptageSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Erreur de validation",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        final_result = serializer.validated_data.get("final_result")
        if final_result is None:
            return Response(
                {
                    "success": False,
                    "message": "Le champ 'final_result' est obligatoire.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        justification = serializer.validated_data.get("justification")
        resolved = serializer.validated_data.get("resolved")

        try:
            ecart = self.service.update_final_result(
                ecart_id=ecart_id,
                final_result=final_result,
                justification=justification,
                resolved=resolved,
            )
        except InventoryNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except InventoryValidationError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Résultat final mis à jour avec succès.",
                "data": EcartComptageSerializer(ecart).data,
            },
            status=status.HTTP_200_OK,
        )


class EcartComptageResolveView(APIView):
    """
    API pour marquer un EcartComptage comme résolu (resolved = true).

    Contraintes métier selon le type d'inventaire :
    - GENERAL : au moins 2 séquences de comptage
    - MAGASIN / TOURNANT : au moins 1 séquence
    - Le champ final_result doit être renseigné (non nul)

    Corps attendu (JSON) :
    {
        "justification": "Résolution manuelle après contrôle"  // optionnel
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = EcartComptageService()

    def patch(self, request, ecart_id: int):
        # On ne valide que la justification éventuellement fournie
        serializer = EcartComptageSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Erreur de validation",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        justification = serializer.validated_data.get("justification")

        try:
            ecart = self.service.resolve_ecart(
                ecart_id=ecart_id,
                justification=justification,
            )
        except InventoryNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except InventoryValidationError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Écart de comptage résolu avec succès.",
                "data": EcartComptageSerializer(ecart).data,
            },
            status=status.HTTP_200_OK,
        )


class EcartComptageBulkResolveView(APIView):
    """
    Résolution en masse des EcartComptage pour un inventaire / magasin.

    Contraintes métier :
    - Scope limité au magasin (warehouse_id), pas tout l'inventaire
    - Seuls les écarts avec final_result non nul sont résolus
    - Nombre minimal de comptages selon le type d'inventaire :
      - GENERAL : ≥ 2 séquences
      - MAGASIN / TOURNANT : ≥ 1 séquence
    - Clôture ensuite les jobs du magasin éligibles (emplacements TERMINE,
      plus d'écart non résolu)

    Méthode HTTP : PATCH
    URL : /web/api/ecarts-comptage/bulk-resolve/<inventory_id>/warehouse/<warehouse_id>/

    Corps attendu (JSON) : Aucun corps requis
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = EcartComptageService()

    def patch(self, request, inventory_id: int, warehouse_id: int):
        try:
            result = self.service.bulk_resolve_ecarts_and_close_jobs_by_inventory(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
            )
        except InventoryNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except WarehouseNotFoundError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except InventoryValidationError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolved_count = result.get("resolved_count", 0)
        closed_jobs_count = result.get("closed_jobs_count", 0)

        return Response(
            {
                "success": True,
                "message": (
                    f"{resolved_count} écarts de comptage ont été marqués "
                    f"comme résolus pour le magasin {warehouse_id}."
                ),
                "data": {
                    "inventory_id": inventory_id,
                    "warehouse_id": warehouse_id,
                    "inventory_type": result.get("inventory_type"),
                    "min_sequences_required": result.get("min_sequences_required"),
                    "resolved_count": resolved_count,
                    "closed_jobs_count": closed_jobs_count,
                },
            },
            status=status.HTTP_200_OK,
        )


