"""
Service pour la gestion des Settings (lancement de warehouse).
"""
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from apps.inventory.constants import InventoryType, SettingStatus
from apps.inventory.services.ecart_stock_theorique_service import (
    EcartStockTheoriqueService,
)

from ..repositories.setting_repository import SettingRepository
from ..repositories.inventory_repository import InventoryRepository
from ..repositories.job_repository import JobRepository
from ..exceptions.inventory_exceptions import (
    InventoryValidationError,
    InventoryNotFoundError,
    InventoryStatusError,
)
from ..usecases.warehouse_launch_validation import WarehouseLaunchValidationUseCase
import logging

logger = logging.getLogger(__name__)


class SettingService:
    """
    Service pour la gestion des Settings.
    """

    def __init__(
        self,
        setting_repository: SettingRepository = None,
        inventory_repository: InventoryRepository = None,
        job_repository: JobRepository = None,
        ecart_stock_service: Optional[EcartStockTheoriqueService] = None,
    ):
        """
        Initialise le service de gestion des Settings.

        Args:
            setting_repository: Repository pour l'accès aux Settings.
            inventory_repository: Repository pour l'accès aux Inventories.
            job_repository: Repository pour l'accès aux Jobs.
            ecart_stock_service: Service sync écarts stock théorique.
        """
        self.setting_repository = setting_repository or SettingRepository()
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.job_repository = job_repository or JobRepository()
        self.ecart_stock_service = ecart_stock_service or EcartStockTheoriqueService()
        self.validation_use_case = WarehouseLaunchValidationUseCase()

    def get_setting_status(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> Dict[str, Any]:
        """
        Retourne le statut Setting pour un inventaire et un magasin.

        Args:
            inventory_id: ID inventaire
            warehouse_id: ID warehouse / magasin

        Returns:
            Dict sérialisable avec status et métadonnées

        Raises:
            InventoryNotFoundError: Si le Setting n'existe pas
        """
        setting = self.setting_repository.get_by_warehouse_and_inventory(
            warehouse_id=warehouse_id,
            inventory_id=inventory_id,
        )
        inventory = setting.inventory
        warehouse = setting.warehouse
        return {
            "setting_id": setting.id,
            "reference": setting.reference,
            "status": setting.status,
            "inventory_id": inventory.id,
            "inventory_reference": getattr(inventory, "reference", None),
            "inventory_label": getattr(inventory, "label", None),
            "inventory_type": getattr(inventory, "inventory_type", None),
            "warehouse_id": warehouse.id,
            "warehouse_name": getattr(warehouse, "warehouse_name", None),
            "warehouse_reference": getattr(warehouse, "reference", None),
            "warehouse_date": setting.warehouse_date,
            "status_date_lancement": setting.status_date_lancement,
            "status_date_termine": setting.status_date_termine,
            "status_date_analyse": setting.status_date_analyse,
            "status_date_cloture": setting.status_date_cloture,
        }

    @staticmethod
    def _jobs_not_completed_payload(jobs) -> List[Dict[str, Any]]:
        return [
            {
                "id": job.id,
                "reference": job.reference,
                "status": job.status,
            }
            for job in jobs
            if job.status != "TERMINE"
        ]
    
    @transaction.atomic
    def launch_warehouse(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        """
        Lance un warehouse (Setting) en changeant son statut de 'EN ATTENTE' à 'LANCEE'.
        
        Conditions (validées par warehouse):
        - L'inventaire doit être en statut 'EN PREPARATION'
        - Aucun autre inventaire ne doit être en statut 'EN REALISATION' pour le même compte
        - Validation de l'image de stock pour le warehouse
        - Pour GENERAL / MAGASIN: tous les emplacements du warehouse doivent être affectés, tous les jobs du warehouse doivent être PRET
        - Pour TOURNANT: au moins un job du warehouse doit être PRET, au moins un emplacement du warehouse doit être affecté
        - Si au moins un warehouse est lancé, l'inventaire lié passe en 'EN REALISATION'
        
        Args:
            inventory_id: L'ID de l'inventaire
            warehouse_id: L'ID du warehouse
            
        Returns:
            Dict[str, Any]: Résultat du lancement avec les informations mises à jour
            
        Raises:
            InventoryNotFoundError: Si le Setting n'existe pas
            InventoryValidationError: Si les conditions ne sont pas remplies
            InventoryStatusError: Si le Setting n'est pas en statut 'EN ATTENTE'
        """
        # Récupérer le Setting par inventory_id et warehouse_id
        setting = self.setting_repository.get_by_warehouse_and_inventory(warehouse_id, inventory_id)
        
        # Vérifier que le Setting est en statut 'EN ATTENTE'
        if setting.status != 'EN ATTENTE':
            raise InventoryStatusError(
                f"Le warehouse ne peut être lancé que s'il est en statut 'EN ATTENTE'. "
                f"Statut actuel: {setting.status}"
            )
        
        # Récupérer l'inventaire pour vérifier son statut
        from apps.inventory.constants import InventoryStatus

        inventory = setting.inventory

        # Multi-magasin : le 1er lancement passe l'inventaire en EN REALISATION ;
        # les magasins suivants doivent pouvoir être lancés ensuite.
        if inventory.status not in (
            InventoryStatus.EN_PREPARATION,
            InventoryStatus.EN_REALISATION,
        ):
            raise InventoryValidationError(
                "L'inventaire doit être en statut 'EN PREPARATION' ou 'EN REALISATION' "
                f"pour lancer un warehouse. Statut actuel: {inventory.status}"
            )
        
        # Validation métier complète pour le warehouse
        validation_result = self.validation_use_case.validate(inventory_id, warehouse_id)
        
        # Mettre à jour le statut du Setting à 'LANCEE'
        setting.status = 'LANCEE'
        setting.status_date_lancement = timezone.now()
        setting.save()
        
        # Vérifier si au moins un warehouse est lancé pour cet inventaire
        settings_lances = self.setting_repository.get_lancees_by_inventory(inventory.id)
        
        # Si au moins un warehouse est lancé, mettre l'inventaire en 'EN REALISATION'
        if settings_lances.exists():
            # Vérifier que l'inventaire n'est pas déjà en réalisation
            if inventory.status != 'EN REALISATION':
                inventory.status = 'EN REALISATION'
                inventory.en_realisation_status_date = timezone.now()
                inventory.save()
                
                logger.info(
                    f"Inventaire {inventory.id} ({inventory.reference}) "
                    f"passé en statut 'EN REALISATION' après le lancement du warehouse {setting.id}"
                )
        
        logger.info(
            f"Warehouse {setting.id} ({setting.warehouse.warehouse_name}) "
            f"lancé avec succès pour l'inventaire {inventory.id}"
        )
        
        # Préparer la réponse avec les informations de validation
        result = {
            'setting_id': setting.id,
            'setting_reference': setting.reference,
            'warehouse_id': setting.warehouse.id,
            'warehouse_name': setting.warehouse.warehouse_name,
            'inventory_id': inventory.id,
            'inventory_reference': inventory.reference,
            'inventory_status': inventory.status,
            'status': 'LANCEE',
            'status_date_lancement': setting.status_date_lancement.isoformat() if setting.status_date_lancement else None
        }
        
        # Ajouter les messages d'information de validation si présents
        if validation_result and 'infos' in validation_result:
            result['infos'] = validation_result['infos']
        
        return result

    def launch_warehouses(
        self, inventory_id: int, warehouse_ids: list[int]
    ) -> Dict[str, Any]:
        """
        Lance une sélection de magasins/warehouses pour un inventaire.

        Réutilise launch_warehouse (mêmes règles GENERAL / MAGASIN / TOURNANT).
        Succès partiel autorisé.

        Args:
            inventory_id: ID inventaire
            warehouse_ids: IDs magasins sélectionnés

        Returns:
            Dict launched / failed / compteurs
        """
        if not warehouse_ids:
            raise InventoryValidationError(
                "La liste warehouse_ids est obligatoire et ne peut pas être vide."
            )

        seen = set()
        unique_ids: list[int] = []
        for wid in warehouse_ids:
            if wid not in seen:
                seen.add(wid)
                unique_ids.append(wid)

        launched = []
        failed = []

        for warehouse_id in unique_ids:
            try:
                result = self.launch_warehouse(inventory_id, warehouse_id)
                launched.append(result)
            except (
                InventoryNotFoundError,
                InventoryValidationError,
                InventoryStatusError,
            ) as exc:
                failed.append(
                    {
                        "warehouse_id": warehouse_id,
                        "error": str(exc),
                    }
                )
                logger.warning(
                    "Échec lancement magasin inventory=%s warehouse=%s: %s",
                    inventory_id,
                    warehouse_id,
                    exc,
                )

        inventory = self.inventory_repository.get_by_id(inventory_id)
        return {
            "inventory_id": inventory_id,
            "inventory_reference": inventory.reference if inventory else None,
            "inventory_status": inventory.status if inventory else None,
            "inventory_type": inventory.inventory_type if inventory else None,
            "requested_count": len(unique_ids),
            "launched_count": len(launched),
            "failed_count": len(failed),
            "launched": launched,
            "failed": failed,
            "success": len(failed) == 0 and len(launched) > 0,
        }
    
    @transaction.atomic
    def cancel_warehouse_launch(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        """
        Annule le lancement d'un warehouse (Setting) en changeant son statut de 'LANCEE' à 'EN ATTENTE'.
        
        Conditions:
        - Le Setting doit être en statut 'LANCEE'
        - Si c'est le dernier warehouse lancé, l'inventaire repasse en 'EN PREPARATION'
        
        Args:
            inventory_id: L'ID de l'inventaire
            warehouse_id: L'ID du warehouse
            
        Returns:
            Dict[str, Any]: Résultat de l'annulation avec les informations mises à jour
            
        Raises:
            InventoryNotFoundError: Si le Setting n'existe pas
            InventoryStatusError: Si le Setting n'est pas en statut 'LANCEE'
        """
        # Récupérer le Setting par inventory_id et warehouse_id
        setting = self.setting_repository.get_by_warehouse_and_inventory(warehouse_id, inventory_id)
        
        # Vérifier que le Setting est en statut 'LANCEE'
        if setting.status != 'LANCEE':
            raise InventoryStatusError(
                f"Le warehouse ne peut être annulé que s'il est en statut 'LANCEE'. "
                f"Statut actuel: {setting.status}"
            )
        
        # Récupérer l'inventaire
        inventory = setting.inventory
        
        # Mettre à jour le statut du Setting à 'EN ATTENTE'
        setting.status = 'EN ATTENTE'
        setting.status_date_lancement = None  # Réinitialiser la date de lancement
        setting.save()
        
        # Vérifier s'il reste des warehouses lancés pour cet inventaire
        settings_lances = self.setting_repository.get_lancees_by_inventory(inventory.id)
        
        # Si aucun warehouse n'est lancé, remettre l'inventaire en 'EN PREPARATION'
        if not settings_lances.exists():
            if inventory.status == 'EN REALISATION':
                inventory.status = 'EN PREPARATION'
                inventory.en_realisation_status_date = None  # Réinitialiser la date de réalisation
                inventory.save()
                
                logger.info(
                    f"Inventaire {inventory.id} ({inventory.reference}) "
                    f"repassé en statut 'EN PREPARATION' après l'annulation du dernier warehouse {setting.id}"
                )
        
        logger.info(
            f"Lancement du warehouse {setting.id} ({setting.warehouse.warehouse_name}) "
            f"annulé avec succès pour l'inventaire {inventory.id}"
        )
        
        return {
            'setting_id': setting.id,
            'setting_reference': setting.reference,
            'warehouse_id': setting.warehouse.id,
            'warehouse_name': setting.warehouse.warehouse_name,
            'inventory_id': inventory.id,
            'inventory_reference': inventory.reference,
            'inventory_status': inventory.status,
            'status': 'EN ATTENTE',
            'status_date_lancement': None
        }

    @transaction.atomic
    def complete_warehouse(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        """
        Passe un magasin MAGASIN de LANCEE à TERMINEE si tous les jobs sont TERMINE.

        Returns:
            Dict avec success, jobs_not_completed éventuels, status.
        """
        setting = self.setting_repository.get_by_warehouse_and_inventory(
            warehouse_id, inventory_id
        )
        inventory = setting.inventory

        if inventory.inventory_type != InventoryType.MAGASIN:
            raise InventoryValidationError(
                "La terminaison magasin (TERMINEE) est réservée aux inventaires type MAGASIN."
            )

        if setting.status != SettingStatus.LANCEE:
            raise InventoryStatusError(
                "Le warehouse ne peut être terminé que s'il est en statut 'LANCEE'. "
                f"Statut actuel: {setting.status}"
            )

        if inventory.status != "EN REALISATION":
            raise InventoryValidationError(
                "Seuls les inventaires en statut 'EN REALISATION' peuvent être terminés. "
                f"Statut actuel de l'inventaire: {inventory.status}"
            )

        jobs = self.job_repository.get_jobs_by_inventory_and_warehouse(
            inventory_id, warehouse_id
        )
        if not jobs:
            raise InventoryValidationError(
                "Aucun job trouvé pour cet inventaire et ce warehouse. "
                "Impossible de terminer le warehouse."
            )

        jobs_not_completed = self._jobs_not_completed_payload(jobs)
        if jobs_not_completed:
            return {
                "success": False,
                "message": (
                    "Impossible de terminer le warehouse. "
                    f"{len(jobs_not_completed)} job(s) non terminé(s) "
                    "pour cet inventaire et warehouse."
                ),
                "jobs_not_completed": jobs_not_completed,
                "total_jobs": len(jobs),
                "completed_jobs": len(jobs) - len(jobs_not_completed),
                "setting_id": setting.id,
                "setting_reference": setting.reference,
                "warehouse_id": setting.warehouse.id,
                "warehouse_name": setting.warehouse.warehouse_name,
                "inventory_id": inventory.id,
                "inventory_reference": inventory.reference,
                "status": setting.status,
            }

        setting.status = SettingStatus.TERMINEE
        setting.status_date_termine = timezone.now()
        setting.save()

        logger.info(
            "Warehouse %s (%s) TERMINEE pour inventaire %s (%s). Jobs: %s",
            setting.id,
            setting.warehouse.warehouse_name,
            inventory.id,
            inventory.reference,
            len(jobs),
        )

        return {
            "success": True,
            "message": "Le warehouse a été marqué TERMINEE avec succès.",
            "jobs_not_completed": [],
            "total_jobs": len(jobs),
            "completed_jobs": len(jobs),
            "setting_id": setting.id,
            "setting_reference": setting.reference,
            "warehouse_id": setting.warehouse.id,
            "warehouse_name": setting.warehouse.warehouse_name,
            "inventory_id": inventory.id,
            "inventory_reference": inventory.reference,
            "status": setting.status,
            "status_date_termine": (
                setting.status_date_termine.isoformat()
                if setting.status_date_termine
                else None
            ),
        }

    def complete_warehouses(
        self, inventory_id: int, warehouse_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Termine une sélection de magasins (succès partiel autorisé).
        """
        if not warehouse_ids:
            raise InventoryValidationError(
                "La liste warehouse_ids est obligatoire et ne peut pas être vide."
            )

        seen = set()
        unique_ids: List[int] = []
        for wid in warehouse_ids:
            if wid not in seen:
                seen.add(wid)
                unique_ids.append(wid)

        completed = []
        failed = []

        for warehouse_id in unique_ids:
            try:
                result = self.complete_warehouse(inventory_id, warehouse_id)
                if result.get("success"):
                    completed.append(result)
                else:
                    failed.append(
                        {
                            "warehouse_id": warehouse_id,
                            "error": result.get("message"),
                            "jobs_not_completed": result.get("jobs_not_completed", []),
                        }
                    )
            except (
                InventoryNotFoundError,
                InventoryValidationError,
                InventoryStatusError,
            ) as exc:
                failed.append({"warehouse_id": warehouse_id, "error": str(exc)})
                logger.warning(
                    "Échec TERMINEE inventory=%s warehouse=%s: %s",
                    inventory_id,
                    warehouse_id,
                    exc,
                )

        inventory = self.inventory_repository.get_by_id(inventory_id)
        return {
            "inventory_id": inventory_id,
            "inventory_reference": inventory.reference if inventory else None,
            "inventory_status": inventory.status if inventory else None,
            "inventory_type": inventory.inventory_type if inventory else None,
            "requested_count": len(unique_ids),
            "completed_count": len(completed),
            "failed_count": len(failed),
            "completed": completed,
            "failed": failed,
            "success": len(failed) == 0 and len(completed) > 0,
        }

    @transaction.atomic
    def analyse_warehouse(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        """
        Sync écarts stock théorique → table, puis passe le Setting à ANALYSER.

        Prérequis MAGASIN : statut TERMINEE.
        """
        setting = self.setting_repository.get_by_warehouse_and_inventory(
            warehouse_id, inventory_id
        )
        inventory = setting.inventory

        if inventory.inventory_type != InventoryType.MAGASIN:
            raise InventoryValidationError(
                "L'analyse magasin est réservée aux inventaires type MAGASIN."
            )

        if setting.status != SettingStatus.TERMINEE:
            raise InventoryStatusError(
                "Le warehouse ne peut être analysé que s'il est en statut 'TERMINEE'. "
                f"Statut actuel: {setting.status}"
            )

        sync_result = self.ecart_stock_service.sync_from_compute(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
            only_nonzero=False,
        )

        setting.status = SettingStatus.ANALYSER
        setting.status_date_analyse = timezone.now()
        setting.save()

        logger.info(
            "Warehouse %s (%s) ANALYSER pour inventaire %s — sync created=%s updated=%s",
            setting.id,
            setting.warehouse.warehouse_name,
            inventory.id,
            sync_result.get("created"),
            sync_result.get("updated"),
        )

        return {
            "success": True,
            "message": "Analyse terminée : écarts synchronisés, statut ANALYSER.",
            "setting_id": setting.id,
            "setting_reference": setting.reference,
            "warehouse_id": setting.warehouse.id,
            "warehouse_name": setting.warehouse.warehouse_name,
            "inventory_id": inventory.id,
            "inventory_reference": inventory.reference,
            "status": setting.status,
            "status_date_analyse": (
                setting.status_date_analyse.isoformat()
                if setting.status_date_analyse
                else None
            ),
            "sync": sync_result,
        }

    @transaction.atomic
    def close_warehouse(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        """
        Clôture un warehouse (Setting).

        MAGASIN : depuis ANALYSER uniquement (jobs déjà vérifiés à TERMINEE).
        Autres types : depuis LANCEE si tous les jobs sont TERMINE (comportement historique).
        """
        setting = self.setting_repository.get_by_warehouse_and_inventory(
            warehouse_id, inventory_id
        )
        inventory = setting.inventory

        if inventory.status != "EN REALISATION":
            raise InventoryValidationError(
                "Seuls les inventaires en statut 'EN REALISATION' peuvent avoir "
                "des warehouses clôturés. "
                f"Statut actuel de l'inventaire: {inventory.status}"
            )

        if inventory.inventory_type == InventoryType.MAGASIN:
            if setting.status != SettingStatus.ANALYSER:
                raise InventoryStatusError(
                    "Le warehouse MAGASIN ne peut être clôturé que s'il est en "
                    "statut 'ANALYSER'. "
                    f"Statut actuel: {setting.status}"
                )

            # Toutes les lignes EcartStockTheorique du magasin doivent être validées
            non_valides_qs = self.ecart_stock_service.repository.get_non_valides(
                inventory_id, warehouse_id
            )
            non_valides_count = non_valides_qs.count()
            if non_valides_count > 0:
                sample = [
                    {
                        "id": row.id,
                        "article_cle": row.article_cle,
                        "resultat_final": row.resultat_final,
                        "valide": row.valide,
                    }
                    for row in non_valides_qs[:50]
                ]
                return {
                    "success": False,
                    "message": (
                        "Impossible de clôturer le magasin. "
                        f"{non_valides_count} ligne(s) d'écart stock non validée(s)."
                    ),
                    "ecarts_non_valides": sample,
                    "ecarts_non_valides_count": non_valides_count,
                    "jobs_not_completed": [],
                    "setting_id": setting.id,
                    "setting_reference": setting.reference,
                    "warehouse_id": setting.warehouse.id,
                    "warehouse_name": setting.warehouse.warehouse_name,
                    "inventory_id": inventory.id,
                    "inventory_reference": inventory.reference,
                    "status": setting.status,
                }

            setting.status = SettingStatus.CLOTURE
            setting.status_date_cloture = timezone.now()
            setting.save()

            logger.info(
                "Warehouse MAGASIN %s (%s) clôturé pour inventaire %s (%s)",
                setting.id,
                setting.warehouse.warehouse_name,
                inventory.id,
                inventory.reference,
            )
            return {
                "success": True,
                "message": "Le warehouse a été clôturé avec succès.",
                "jobs_not_completed": [],
                "ecarts_non_valides": [],
                "ecarts_non_valides_count": 0,
                "total_jobs": None,
                "completed_jobs": None,
                "setting_id": setting.id,
                "setting_reference": setting.reference,
                "warehouse_id": setting.warehouse.id,
                "warehouse_name": setting.warehouse.warehouse_name,
                "inventory_id": inventory.id,
                "inventory_reference": inventory.reference,
                "status": setting.status,
                "status_date_cloture": (
                    setting.status_date_cloture.isoformat()
                    if setting.status_date_cloture
                    else None
                ),
            }

        # GENERAL / TOURNANT : LANCEE + tous jobs TERMINE
        if setting.status != SettingStatus.LANCEE:
            raise InventoryStatusError(
                "Le warehouse ne peut être clôturé que s'il est en statut 'LANCEE'. "
                f"Statut actuel: {setting.status}"
            )

        jobs = self.job_repository.get_jobs_by_inventory_and_warehouse(
            inventory_id, warehouse_id
        )
        if not jobs:
            raise InventoryValidationError(
                "Aucun job trouvé pour cet inventaire et ce warehouse. "
                "Impossible de clôturer le warehouse."
            )

        jobs_not_completed = self._jobs_not_completed_payload(jobs)
        if jobs_not_completed:
            return {
                "success": False,
                "message": (
                    "Impossible de clôturer le warehouse. "
                    f"{len(jobs_not_completed)} job(s) non terminé(s) "
                    "pour cet inventaire et warehouse."
                ),
                "jobs_not_completed": jobs_not_completed,
                "total_jobs": len(jobs),
                "completed_jobs": len(jobs) - len(jobs_not_completed),
                "setting_id": setting.id,
                "setting_reference": setting.reference,
                "warehouse_id": setting.warehouse.id,
                "warehouse_name": setting.warehouse.warehouse_name,
                "inventory_id": inventory.id,
                "inventory_reference": inventory.reference,
                "status": setting.status,
            }

        setting.status = SettingStatus.CLOTURE
        setting.status_date_cloture = timezone.now()
        setting.save()

        logger.info(
            "Warehouse %s (%s) clôturé pour l'inventaire %s (%s). Jobs terminés: %s",
            setting.id,
            setting.warehouse.warehouse_name,
            inventory.id,
            inventory.reference,
            len(jobs),
        )

        return {
            "success": True,
            "message": "Le warehouse a été clôturé avec succès.",
            "jobs_not_completed": [],
            "total_jobs": len(jobs),
            "completed_jobs": len(jobs),
            "setting_id": setting.id,
            "setting_reference": setting.reference,
            "warehouse_id": setting.warehouse.id,
            "warehouse_name": setting.warehouse.warehouse_name,
            "inventory_id": inventory.id,
            "inventory_reference": inventory.reference,
            "status": setting.status,
            "status_date_cloture": (
                setting.status_date_cloture.isoformat()
                if setting.status_date_cloture
                else None
            ),
        }