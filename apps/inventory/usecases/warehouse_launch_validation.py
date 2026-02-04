"""
Use case pour valider le lancement d'un warehouse (Setting) selon les règles métier.
Adaptation des conditions de lancement d'inventaire au niveau warehouse.
"""
from typing import Dict, Any, List
from apps.inventory.models import Inventory, Job, JobDetail, Counting, Setting
from apps.masterdata.models import Location, RegroupementEmplacement, Stock, Warehouse
from apps.inventory.exceptions import InventoryValidationError, InventoryNotFoundError
from django.db.models import Q
import logging

# Configuration du logger
logger = logging.getLogger(__name__)


class WarehouseLaunchValidationUseCase:
    """
    Usecase pour valider le lancement d'un warehouse selon les règles métier.
    """
    
    def validate(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        """
        Valide le lancement d'un warehouse pour un inventaire donné.
        
        Args:
            inventory_id: L'ID de l'inventaire
            warehouse_id: L'ID du warehouse
            
        Returns:
            Dict[str, Any]: Résultat de la validation avec messages d'info
            
        Raises:
            InventoryNotFoundError: Si l'inventaire ou le warehouse n'existe pas
            InventoryValidationError: Si les conditions ne sont pas remplies
        """
        try:
            inventory = Inventory.objects.get(id=inventory_id, is_deleted=False)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"Inventaire {inventory_id} non trouvé.")
        
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            raise InventoryNotFoundError(f"Warehouse {warehouse_id} non trouvé.")
        
        # Vérifier que le Setting existe
        try:
            setting = Setting.objects.get(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
                is_deleted=False
            )
        except Setting.DoesNotExist:
            raise InventoryNotFoundError(
                f"Le Setting pour l'inventaire {inventory_id} et le warehouse {warehouse_id} n'existe pas."
            )
        
        inventory_type = inventory.inventory_type
        account_ids = list(inventory.awi_links.values_list('account_id', flat=True).distinct())
        if not account_ids:
            raise InventoryValidationError("Aucun compte lié à cet inventaire.")
        account_id = account_ids[0]  # On suppose un seul compte par inventaire
        
        info_messages = []
        errors = []  # Liste pour collecter toutes les erreurs
        
        logger.info(
            f"Validation du warehouse {warehouse_id} pour l'inventaire {inventory_id} "
            f"de type {inventory_type}"
        )
        
        # Vérification qu'il n'y a pas d'autre inventaire en cours pour le même compte
        self._validate_no_running_inventory_for_same_account(inventory, account_id, errors)
        
        # Vérification de l'image de stock pour le warehouse spécifique
        self._validate_stock_image_for_warehouse(inventory, warehouse_id, errors, info_messages)
        
        if inventory_type == 'GENERAL':
            self._validate_general_inventory_for_warehouse(
                inventory, warehouse_id, account_id, errors, info_messages
            )
        elif inventory_type == 'TOURNANT':
            self._validate_tournant_inventory_for_warehouse(
                inventory, warehouse_id, errors, info_messages
            )
        else:
            errors.append(f"Type d'inventaire non supporté: {inventory_type}")
            logger.error(f"Type d'inventaire non supporté: {inventory_type}")
        
        # Si des erreurs ont été collectées, les lever toutes ensemble
        if errors:
            error_message = " | ".join(errors)
            logger.warning(f"Erreurs de validation détectées pour le warehouse {warehouse_id}: {error_message}")
            raise InventoryValidationError(error_message)
        
        logger.info(f"Validation réussie pour le lancement du warehouse {warehouse_id}")
        return {
            "success": True,
            "message": "Validation OK pour le lancement du warehouse.",
            "infos": info_messages
        }
    
    def _validate_no_running_inventory_for_same_account(
        self, inventory: Inventory, account_id: int, errors: List[str]
    ):
        """
        Vérifie qu'il n'y a pas d'autre inventaire en cours pour le même compte.
        """
        # Récupérer tous les inventaires en cours (EN REALISATION) pour le même compte
        running_inventories = Inventory.objects.filter(
            awi_links__account_id=account_id,
            status='EN REALISATION',
            is_deleted=False
        ).exclude(id=inventory.id)  # Exclure l'inventaire actuel
        
        if running_inventories.exists():
            running_inventory = running_inventories.first()
            error_message = (
                f"Impossible de lancer ce warehouse. Un autre inventaire "
                f"({running_inventory.label}) est déjà en cours pour le même compte."
            )
            errors.append(error_message)
            logger.warning(f"Inventaire en cours détecté: {running_inventory.id} ({running_inventory.label}) pour le compte {account_id}")
        else:
            logger.info(f"Aucun inventaire en cours trouvé pour le compte {account_id}")
    
    def _validate_stock_image_for_warehouse(
        self,
        inventory: Inventory,
        warehouse_id: int,
        errors: List[str],
        info_messages: List[str]
    ):
        """
        Vérifie l'image de stock pour le warehouse spécifique.
        """
        # Compter les stocks pour ce warehouse et cet inventaire
        stocks_count = Stock.objects.filter(
            inventory=inventory,
            location__sous_zone__zone__warehouse_id=warehouse_id,
            is_deleted=False
        ).count()
        
        stock_error_message = (
            f"L'image de stock n'a pas été importée pour ce warehouse et cet inventaire."
        )
        stock_info_message = (
            "Pour optimiser le comptage avec quantité et article, veuillez importer l'image de stock."
        )
        
        all_countings = inventory.countings.all().order_by('order')
        
        # Flag pour éviter d'ajouter le message d'info plusieurs fois
        info_message_added = False
        
        for counting in all_countings:
            # Si le comptage est en mode "image de stock", c'est une erreur
            if counting.count_mode == "image de stock":
                if stocks_count == 0:
                    errors.append(stock_error_message)
                    logger.warning(
                        f"Aucun stock trouvé pour le warehouse {warehouse_id} "
                        f"et l'inventaire {inventory.id} (mode image de stock)"
                    )
                else:
                    logger.info(
                        f"Image de stock importée pour le warehouse {warehouse_id}: "
                        f"{stocks_count} stocks trouvés"
                    )
            # Si le comptage a quantity_show=true ou show_product=true, c'est un message d'info
            elif counting.quantity_show or counting.show_product:
                if stocks_count == 0 and not info_message_added:
                    info_messages.append(stock_info_message)
                    info_message_added = True
                    logger.info(
                        f"Message d'info: Image de stock non importée pour le warehouse {warehouse_id} "
                        f"(quantity_show ou show_product activé)"
                    )
                elif stocks_count > 0:
                    logger.info(
                        f"Image de stock importée pour le warehouse {warehouse_id}: "
                        f"{stocks_count} stocks trouvés"
                    )
            else:
                # Pour les autres cas, on ne vérifie pas l'image de stock
                logger.info(
                    f"Pas de vérification d'image de stock pour ce mode de comptage "
                    f"(warehouse {warehouse_id})"
                )
    
    def _validate_general_inventory_for_warehouse(
        self,
        inventory: Inventory,
        warehouse_id: int,
        account_id: int,
        errors: List[str],
        info_messages: List[str]
    ):
        """
        Valide les conditions spécifiques pour un inventaire GENERAL au niveau du warehouse.
        """
        # 1. Tous les emplacements du warehouse et du compte doivent être affectés à des jobs
        regroupement = RegroupementEmplacement.objects.filter(
            account_id=account_id,
            warehouse_id=warehouse_id
        ).first()
        
        if not regroupement:
            errors.append(
                f"Aucun regroupement d'emplacement pour ce compte et ce warehouse."
            )
            logger.warning(
                f"Pas de regroupement d'emplacement pour le compte {account_id} "
                f"et le warehouse {warehouse_id}"
            )
        else:
            # Récupérer les emplacements actifs du regroupement pour ce warehouse
            locations = Location.objects.filter(
                regroupement=regroupement,
                is_active=True,
                sous_zone__zone__warehouse_id=warehouse_id
            )
            location_ids = set(locations.values_list('id', flat=True))
            
            # Récupérer les jobs de ce warehouse pour cet inventaire
            job_ids = Job.objects.filter(
                inventory=inventory,
                warehouse_id=warehouse_id
            ).values_list('id', flat=True)
            
            # Récupérer les emplacements affectés aux jobs de ce warehouse
            job_location_ids = set(
                JobDetail.objects.filter(job_id__in=job_ids)
                .values_list('location_id', flat=True)
            )
            
            missing_locations = location_ids - job_location_ids
            if missing_locations:
                errors.append(
                    f"Tous les emplacements du warehouse ne sont pas affectés à des jobs. "
                    f"({len(missing_locations)} emplacements manquants)"
                )
                logger.warning(
                    f"Emplacements manquants pour le warehouse {warehouse_id}: "
                    f"{len(missing_locations)} emplacements non affectés"
                )
            else:
                logger.info(
                    f"Tous les emplacements du warehouse {warehouse_id} sont affectés aux jobs"
                )
        
        # 2. Tous les jobs du warehouse doivent être PRET
        not_ready_jobs = Job.objects.filter(
            inventory=inventory,
            warehouse_id=warehouse_id
        ).exclude(status='PRET')
        
        if not_ready_jobs.exists():
            errors.append(
                f"Tous les jobs du warehouse ne sont pas au statut PRET. "
                f"({not_ready_jobs.count()} jobs non prêts)"
            )
            logger.warning(
                f"Jobs non prêts pour le warehouse {warehouse_id}: "
                f"{not_ready_jobs.count()} jobs ne sont pas au statut PRET"
            )
        else:
            logger.info(
                f"Tous les jobs du warehouse {warehouse_id} sont au statut PRET"
            )
        
        # Ajout des messages d'information
        info_messages.append(
            "Merci de réceptionner tous les commandes et ranger et clôturer tous les commandes."
        )
    
    def _validate_tournant_inventory_for_warehouse(
        self,
        inventory: Inventory,
        warehouse_id: int,
        errors: List[str],
        info_messages: List[str]
    ):
        """
        Valide les conditions spécifiques pour un inventaire TOURNANT au niveau du warehouse.
        """
        # Au moins un job du warehouse doit être PRET
        ready_jobs_count = Job.objects.filter(
            inventory=inventory,
            warehouse_id=warehouse_id,
            status='PRET'
        ).count()
        
        if ready_jobs_count == 0:
            errors.append(
                f"Au moins un job du warehouse doit être au statut PRET pour lancer le warehouse."
            )
            logger.warning(
                f"Aucun job prêt trouvé pour le warehouse {warehouse_id} "
                f"et l'inventaire tournant {inventory.id}"
            )
        else:
            logger.info(
                f"Jobs prêts trouvés pour le warehouse {warehouse_id}: "
                f"{ready_jobs_count} jobs au statut PRET"
            )
        
        # Au moins un emplacement du warehouse doit être affecté à un job
        job_ids = Job.objects.filter(
            inventory=inventory,
            warehouse_id=warehouse_id
        ).values_list('id', flat=True)
        
        affected_locations_count = JobDetail.objects.filter(
            job_id__in=job_ids
        ).count()
        
        if affected_locations_count == 0:
            errors.append(
                f"Au moins un emplacement du warehouse doit être affecté à un job "
                f"pour lancer le warehouse."
            )
            logger.warning(
                f"Aucun emplacement affecté à un job pour le warehouse {warehouse_id} "
                f"et l'inventaire tournant {inventory.id}"
            )
        else:
            logger.info(
                f"Emplacements affectés trouvés pour le warehouse {warehouse_id}: "
                f"{affected_locations_count} emplacements affectés à des jobs"
            )

