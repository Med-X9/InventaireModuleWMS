"""
Vues pour la gestion des Settings (lancement de warehouse).
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..services.setting_service import SettingService
from ..serializers.setting_serializer import MultiWarehouseLaunchSerializer
from ..exceptions.inventory_exceptions import (
    InventoryValidationError,
    InventoryNotFoundError,
    InventoryStatusError,
)
from ..utils.response_utils import (
    success_response,
    error_response,
    validation_error_response,
)

logger = logging.getLogger(__name__)


class SettingMultiLaunchView(APIView):
    """
    Lance une sélection de magasins pour un inventaire.

    POST /web/api/inventory/{inventory_id}/warehouses/launch/
    Body: { "warehouse_ids": [5, 6, 7] }

    Règles (par type) via WarehouseLaunchValidationUseCase :
    - GENERAL / MAGASIN : tous emplacements affectés + tous jobs PRET
    - TOURNANT : ≥1 job PRET + ≥1 emplacement affecté
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, setting_service: SettingService = None, **kwargs):
        super().__init__(**kwargs)
        self.setting_service = setting_service or SettingService()

    def post(self, request, inventory_id: int):
        serializer = MultiWarehouseLaunchSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            result = self.setting_service.launch_warehouses(
                inventory_id,
                serializer.validated_data["warehouse_ids"],
            )

            if result["launched_count"] == 0:
                return error_response(
                    "Aucun magasin n'a pu être lancé",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=result,
                )

            message = (
                "Tous les magasins sélectionnés ont été lancés"
                if result["success"]
                else (
                    f"{result['launched_count']}/{result['requested_count']} "
                    "magasin(s) lancé(s) (succès partiel)"
                )
            )
            return success_response(
                data=result,
                message=message,
                status_code=status.HTTP_200_OK,
            )

        except InventoryValidationError as e:
            logger.warning("Validation multi-lancement: %s", e)
            return error_response(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        except InventoryNotFoundError as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Erreur multi-lancement magasins: %s", e, exc_info=True)
            return error_response(
                "Une erreur est survenue lors du lancement multi-magasins",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SettingLaunchView(APIView):
    """
    Vue pour lancer un warehouse (Setting).
    
    Conditions:
    - Inventaire EN PREPARATION ou EN REALISATION
    - Setting EN ATTENTE → LANCEE
    - GENERAL / MAGASIN : couverture complète (jobs PRET)
    - TOURNANT : au moins un job PRET
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, setting_service: SettingService = None, **kwargs):
        super().__init__(**kwargs)
        self.setting_service = setting_service or SettingService()
    
    def post(self, request, inventory_id: int, warehouse_id: int):
        """
        Lance un warehouse (Setting).
        
        URL Parameters:
        - inventory_id: L'ID de l'inventaire
        - warehouse_id: L'ID du warehouse
        
        Returns:
            Response: Réponse avec les informations du Setting lancé
        """
        try:
            # Lancer le warehouse via le service
            result = self.setting_service.launch_warehouse(inventory_id, warehouse_id)
            
            # Préparer la réponse avec les informations de validation
            extra_data = {}
            if result and 'infos' in result:
                extra_data['infos'] = result.pop('infos')
            
            return success_response(
                data=result,
                message="Warehouse lancé avec succès",
                status_code=status.HTTP_200_OK,
                **extra_data
            )
            
        except InventoryStatusError as e:
            logger.warning(f"Erreur de statut lors du lancement du warehouse: {str(e)}")
            return error_response(
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors du lancement du warehouse: {str(e)}")
            return error_response(
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Setting non trouvé: {str(e)}")
            return error_response(
                str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors du lancement du warehouse: {str(e)}", exc_info=True)
            return error_response(
                "Une erreur est survenue lors du lancement du warehouse",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SettingCancelLaunchView(APIView):
    """
    Vue pour annuler le lancement d'un warehouse (Setting).
    
    Conditions:
    - Le Setting doit être en statut 'LANCEE'
    - Si c'est le dernier warehouse lancé, l'inventaire repasse en 'EN PREPARATION'
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, setting_service: SettingService = None, **kwargs):
        super().__init__(**kwargs)
        self.setting_service = setting_service or SettingService()
    
    def post(self, request, inventory_id: int, warehouse_id: int):
        """
        Annule le lancement d'un warehouse (Setting).
        
        URL Parameters:
        - inventory_id: L'ID de l'inventaire
        - warehouse_id: L'ID du warehouse
        
        Returns:
            Response: Réponse avec les informations du Setting annulé
        """
        try:
            # Annuler le lancement du warehouse via le service
            result = self.setting_service.cancel_warehouse_launch(inventory_id, warehouse_id)
            
            return success_response(
                data=result,
                message="Lancement du warehouse annulé avec succès",
                status_code=status.HTTP_200_OK
            )
            
        except InventoryStatusError as e:
            logger.warning(f"Erreur de statut lors de l'annulation du warehouse: {str(e)}")
            return error_response(
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Setting non trouvé: {str(e)}")
            return error_response(
                str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'annulation du warehouse: {str(e)}", exc_info=True)
            return error_response(
                "Une erreur est survenue lors de l'annulation du warehouse",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SettingCloseView(APIView):
    """
    Vue pour clôturer un warehouse (Setting) pour un inventaire donné.

    MAGASIN : statut ANALYSER → CLOTURE.
    GENERAL / TOURNANT : statut LANCEE + tous jobs TERMINE → CLOTURE.
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, setting_service: SettingService = None, **kwargs):
        super().__init__(**kwargs)
        self.setting_service = setting_service or SettingService()

    def post(self, request, inventory_id: int, warehouse_id: int):
        """
        Clôture un warehouse (Setting) pour un inventaire donné.

        URL Parameters:
        - inventory_id: ID de l'inventaire.
        - warehouse_id: ID du warehouse.
        """
        try:
            result = self.setting_service.close_warehouse(inventory_id, warehouse_id)

            if result.get('success'):
                # Clôture réussie
                return success_response(
                    data=result,
                    message=result.get('message', "Le warehouse a été clôturé avec succès."),
                    status_code=status.HTTP_200_OK,
                )

            # Clôture impossible : jobs non terminés et/ou écarts stock non validés
            errors = [
                f"Job {job.get('reference', job.get('id', 'inconnu'))} non terminé (statut: {job.get('status')})"
                for job in result.get('jobs_not_completed', [])
            ]
            for row in result.get('ecarts_non_valides', []):
                errors.append(
                    f"Écart stock id={row.get('id')} article={row.get('article_cle')} non validé"
                )

            return error_response(
                message=result.get(
                    'message',
                    "Impossible de clôturer le warehouse.",
                ),
                errors=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                **{k: v for k, v in result.items() if k != 'message'},
            )

        except InventoryStatusError as exc:
            logger.warning("Erreur de statut lors de la clôture du warehouse: %s", str(exc))
            return error_response(
                str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except InventoryValidationError as exc:
            logger.warning("Erreur de validation lors de la clôture du warehouse: %s", str(exc))
            return error_response(
                str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except InventoryNotFoundError as exc:
            logger.warning("Setting non trouvé lors de la clôture du warehouse: %s", str(exc))
            return error_response(
                str(exc),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:  # pragma: no cover - sécurité
            logger.error(
                "Erreur inattendue lors de la clôture du warehouse: %s",
                str(exc),
                exc_info=True,
            )
            return error_response(
                "Une erreur est survenue lors de la clôture du warehouse",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SettingTermineView(APIView):
    """
    Passe un magasin MAGASIN de LANCEE à TERMINEE (tous jobs TERMINE).

    POST /web/api/inventory/{inventory_id}/warehouse/{warehouse_id}/termine/
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, setting_service: SettingService = None, **kwargs):
        super().__init__(**kwargs)
        self.setting_service = setting_service or SettingService()

    def post(self, request, inventory_id: int, warehouse_id: int):
        try:
            result = self.setting_service.complete_warehouse(inventory_id, warehouse_id)

            if result.get("success"):
                return success_response(
                    data=result,
                    message=result.get(
                        "message", "Le warehouse a été marqué TERMINEE."
                    ),
                    status_code=status.HTTP_200_OK,
                )

            errors = [
                (
                    f"Job {job.get('reference', job.get('id', 'inconnu'))} "
                    f"non terminé (statut: {job.get('status')})"
                )
                for job in result.get("jobs_not_completed", [])
            ]
            return error_response(
                message=result.get(
                    "message",
                    "Impossible de terminer le warehouse : des jobs ne sont pas terminés.",
                ),
                errors=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                **{k: v for k, v in result.items() if k not in ("message",)},
            )
        except InventoryStatusError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except InventoryValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except InventoryNotFoundError as exc:
            return error_response(str(exc), status_code=status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error("Erreur TERMINEE warehouse: %s", exc, exc_info=True)
            return error_response(
                "Une erreur est survenue lors de la terminaison du warehouse",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SettingMultiTermineView(APIView):
    """
    Termine une sélection de magasins MAGASIN.

    POST /web/api/inventory/{inventory_id}/warehouses/termine/
    Body: { "warehouse_ids": [5, 6, 7] }
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, setting_service: SettingService = None, **kwargs):
        super().__init__(**kwargs)
        self.setting_service = setting_service or SettingService()

    def post(self, request, inventory_id: int):
        serializer = MultiWarehouseLaunchSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            result = self.setting_service.complete_warehouses(
                inventory_id,
                serializer.validated_data["warehouse_ids"],
            )

            if result["completed_count"] == 0:
                return error_response(
                    "Aucun magasin n'a pu être terminé",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data=result,
                )

            message = (
                "Tous les magasins sélectionnés ont été terminés"
                if result["success"]
                else (
                    f"{result['completed_count']}/{result['requested_count']} "
                    "magasin(s) terminé(s) (succès partiel)"
                )
            )
            return success_response(
                data=result,
                message=message,
                status_code=status.HTTP_200_OK,
            )
        except InventoryValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except InventoryNotFoundError as exc:
            return error_response(str(exc), status_code=status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error("Erreur multi-TERMINEE: %s", exc, exc_info=True)
            return error_response(
                "Une erreur est survenue lors de la terminaison multi-magasins",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SettingAnalyserView(APIView):
    """
    Sync écarts stock théorique + passe le Setting à ANALYSER.

    POST /web/api/inventory/{inventory_id}/warehouse/{warehouse_id}/analyser/
    Prérequis : statut TERMINEE (MAGASIN).
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, setting_service: SettingService = None, **kwargs):
        super().__init__(**kwargs)
        self.setting_service = setting_service or SettingService()

    def post(self, request, inventory_id: int, warehouse_id: int):
        try:
            result = self.setting_service.analyse_warehouse(inventory_id, warehouse_id)
            return success_response(
                data=result,
                message=result.get(
                    "message", "Analyse terminée, statut ANALYSER."
                ),
                status_code=status.HTTP_200_OK,
            )
        except InventoryStatusError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except InventoryValidationError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        except InventoryNotFoundError as exc:
            return error_response(str(exc), status_code=status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error("Erreur ANALYSER warehouse: %s", exc, exc_info=True)
            return error_response(
                "Une erreur est survenue lors de l'analyse du warehouse",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

