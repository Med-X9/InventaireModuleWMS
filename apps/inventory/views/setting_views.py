"""
Vues pour la gestion des Settings (lancement de warehouse).
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..services.setting_service import SettingService
from ..exceptions.inventory_exceptions import (
    InventoryValidationError,
    InventoryNotFoundError,
    InventoryStatusError,
)
from ..utils.response_utils import success_response, error_response

logger = logging.getLogger(__name__)


class SettingLaunchView(APIView):
    """
    Vue pour lancer un warehouse (Setting).
    
    Conditions:
    - Aucun inventaire ne doit être en statut 'EN REALISATION'
    - Si au moins un warehouse est lancé, l'inventaire lié passe en 'EN REALISATION'
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

    Conditions :
    - Le Setting doit être en statut 'LANCEE'.
    - L'inventaire doit être en statut 'EN REALISATION'.
    - Tous les jobs de cet inventaire et de ce warehouse doivent être au statut 'TERMINE'.
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, setting_service: SettingService = None, **kwargs):
        super().__init__(**kwargs)
        self.setting_service = setting_service or SettingService()

    def post(self, request, inventory_id: int, warehouse_id: int):
        """
        Clôture un warehouse (Setting) pour un inventaire donné en vérifiant
        que tous les jobs sont terminés.

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

            # Clôture impossible car des jobs ne sont pas terminés
            errors = [
                f"Job {job.get('reference', job.get('id', 'inconnu'))} non terminé (statut: {job.get('status')})"
                for job in result.get('jobs_not_completed', [])
            ]

            return error_response(
                message=result.get(
                    'message',
                    "Impossible de clôturer le warehouse : des jobs ne sont pas terminés."
                ),
                errors=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                **result,
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

