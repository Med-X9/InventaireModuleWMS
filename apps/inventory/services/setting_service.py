"""
Service pour la gestion des Settings (lancement de warehouse).
"""
from typing import Dict, Any
from django.db import transaction
from django.utils import timezone
from ..repositories.setting_repository import SettingRepository
from ..repositories.inventory_repository import InventoryRepository
from ..repositories.job_repository import JobRepository
from ..models import Setting, Inventory
from ..exceptions.inventory_exceptions import (
    InventoryValidationError,
    InventoryNotFoundError,
    InventoryStatusError
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
    ):
        """
        Initialise le service de gestion des Settings.

        Args:
            setting_repository: Repository pour l'accès aux Settings.
            inventory_repository: Repository pour l'accès aux Inventories.
            job_repository: Repository pour l'accès aux Jobs.
        """
        self.setting_repository = setting_repository or SettingRepository()
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.job_repository = job_repository or JobRepository()
        self.validation_use_case = WarehouseLaunchValidationUseCase()
    
    @transaction.atomic
    def launch_warehouse(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        """
        Lance un warehouse (Setting) en changeant son statut de 'EN ATTENTE' à 'LANCEE'.
        
        Conditions (validées par warehouse):
        - L'inventaire doit être en statut 'EN PREPARATION'
        - Aucun autre inventaire ne doit être en statut 'EN REALISATION' pour le même compte
        - Validation de l'image de stock pour le warehouse
        - Pour GENERAL: tous les emplacements du warehouse doivent être affectés, tous les jobs du warehouse doivent être PRET
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
        inventory = setting.inventory
        
        # Vérifier que l'inventaire est en statut 'EN PREPARATION'
        if inventory.status != 'EN PREPARATION':
            raise InventoryValidationError(
                f"L'inventaire doit être en statut 'EN PREPARATION' pour lancer un warehouse. "
                f"Statut actuel: {inventory.status}"
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
    def close_warehouse(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        """
        Marque un warehouse (Setting) comme clôturé pour un inventaire donné.

        Conditions métier :
        - Le Setting doit être en statut 'LANCEE'.
        - L'inventaire lié doit être en statut 'EN REALISATION'.
        - Il doit exister au moins un Job pour cet inventaire et ce warehouse.
        - Tous les Jobs de cet inventaire et de ce warehouse doivent être au statut 'TERMINE'.

        Args:
            inventory_id: ID de l'inventaire.
            warehouse_id: ID du warehouse.

        Returns:
            Dict[str, Any]: Résultat de l'opération contenant notamment :
                - success: bool indiquant si la clôture est effectuée.
                - message: description de l'état.
                - jobs_not_completed: liste des jobs non terminés le cas échéant.
                - total_jobs: nombre total de jobs du couple inventaire/warehouse.
                - completed_jobs: nombre de jobs terminés.

        Raises:
            InventoryNotFoundError: Si le Setting n'existe pas.
            InventoryStatusError: Si le Setting n'est pas en statut 'LANCEE'.
            InventoryValidationError: Si les conditions de clôture ne sont pas remplies.
        """
        # Récupérer le Setting par inventory_id et warehouse_id
        setting = self.setting_repository.get_by_warehouse_and_inventory(warehouse_id, inventory_id)

        # Vérifier que le Setting est en statut 'LANCEE'
        if setting.status != 'LANCEE':
            raise InventoryStatusError(
                "Le warehouse ne peut être clôturé que s'il est en statut 'LANCEE'. "
                f"Statut actuel: {setting.status}"
            )

        # Vérifier le statut de l'inventaire
        inventory = setting.inventory
        if inventory.status != 'EN REALISATION':
            raise InventoryValidationError(
                "Seuls les inventaires en statut 'EN REALISATION' peuvent avoir des warehouses clôturés. "
                f"Statut actuel de l'inventaire: {inventory.status}"
            )

        # Récupérer tous les jobs pour cet inventaire et ce warehouse
        jobs = self.job_repository.get_jobs_by_inventory_and_warehouse(inventory_id, warehouse_id)

        # Vérifier qu'il y a au moins un job
        if not jobs:
            raise InventoryValidationError(
                "Aucun job trouvé pour cet inventaire et ce warehouse. Impossible de clôturer le warehouse."
            )

        # Vérifier que tous les jobs sont terminés
        jobs_not_completed = [job for job in jobs if job.status != 'TERMINE']

        if jobs_not_completed:
            jobs_not_completed_list = [
                {
                    'id': job.id,
                    'reference': job.reference,
                    'status': job.status,
                }
                for job in jobs_not_completed
            ]

            return {
                'success': False,
                'message': (
                    "Impossible de clôturer le warehouse. "
                    f"{len(jobs_not_completed)} job(s) non terminé(s) pour cet inventaire et warehouse."
                ),
                'jobs_not_completed': jobs_not_completed_list,
                'total_jobs': len(jobs),
                'completed_jobs': len([job for job in jobs if job.status == 'TERMINE']),
                'setting_id': setting.id,
                'setting_reference': setting.reference,
                'warehouse_id': setting.warehouse.id,
                'warehouse_name': setting.warehouse.warehouse_name,
                'inventory_id': inventory.id,
                'inventory_reference': inventory.reference,
                'status': setting.status,
            }

        # Tous les jobs sont terminés : clôturer le Setting
        setting.status = 'CLOTURE'
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
            'success': True,
            'message': "Le warehouse a été clôturé avec succès.",
            'jobs_not_completed': [],
            'total_jobs': len(jobs),
            'completed_jobs': len(jobs),
            'setting_id': setting.id,
            'setting_reference': setting.reference,
            'warehouse_id': setting.warehouse.id,
            'warehouse_name': setting.warehouse.warehouse_name,
            'inventory_id': inventory.id,
            'inventory_reference': inventory.reference,
            'status': setting.status,
            'status_date_cloture': setting.status_date_cloture.isoformat() if setting.status_date_cloture else None,
        }