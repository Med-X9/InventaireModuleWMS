from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.ecart_comptage_serializer import EcartComptageSerializer
from ..services.ecart_comptage_service import EcartComptageService
from ..exceptions import InventoryValidationError, InventoryNotFoundError


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

    Contraintes métier :
    - Il doit y avoir au moins deux comptages (séquences) enregistrés.
    - Le champ final_result doit être renseigné (non nul).

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


