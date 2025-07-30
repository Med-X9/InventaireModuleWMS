from typing import Dict, Any, List
from apps.inventory.models import Inventory, Job, JobDetail, Counting
from apps.masterdata.models import Location, RegroupementEmplacement, Stock
from apps.inventory.exceptions import InventoryValidationError, InventoryNotFoundError
from django.db.models import Q
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

class InventoryLaunchValidationUseCase:
    """
    Usecase pour valider le lancement d'un inventaire selon les règles métier.
    """
    def validate(self, inventory_id: int) -> Dict[str, Any]:
        try:
            inventory = Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise InventoryNotFoundError(f"Inventaire {inventory_id} non trouvé.")

        inventory_type = inventory.inventory_type
        account_ids = list(inventory.awi_links.values_list('account_id', flat=True).distinct())
        if not account_ids:
            raise InventoryValidationError("Aucun compte lié à cet inventaire.")
        account_id = account_ids[0]  # On suppose un seul compte par inventaire

        info_messages = []
        errors = []  # Liste pour collecter toutes les erreurs

        logger.info(f"Validation de l'inventaire {inventory_id} de type {inventory_type}")

        # Vérification de l'image de stock pour tous les comptages
        self._validate_stock_image(inventory, errors, info_messages)

        if inventory_type == 'GENERAL':
            self._validate_general_inventory(inventory, account_id, errors, info_messages)
        elif inventory_type == 'TOURNANT':
            self._validate_tournant_inventory(inventory, errors, info_messages)
        else:
            errors.append(f"Type d'inventaire non supporté: {inventory_type}")
            logger.error(f"Type d'inventaire non supporté: {inventory_type}")

        # Si des erreurs ont été collectées, les lever toutes ensemble
        if errors:
            error_message = " | ".join(errors)
            logger.warning(f"Erreurs de validation détectées: {error_message}")
            raise InventoryValidationError(error_message)

        logger.info("Validation réussie pour le lancement de l'inventaire")
        return {"success": True, "message": "Validation OK pour le lancement de l'inventaire.", "infos": info_messages}

    def _validate_stock_image(self, inventory, errors, info_messages):
        stocks_count = Stock.objects.filter(inventory=inventory, is_deleted=False).count()
        stock_error_message = "L'image de stock n'a pas été importée pour cet inventaire."
        stock_info_message = "Pour optimiser le comptage avec quantité et article, veuillez importer l'image de stock."
        all_countings = inventory.countings.all().order_by('order')
        
        # Flag pour éviter d'ajouter le message d'info plusieurs fois
        info_message_added = False
        
        for counting in all_countings:
            # Si le comptage est en mode "image de stock", c'est une erreur
            if counting.count_mode == "image de stock":
                if stocks_count == 0:
                    errors.append(stock_error_message)
                    logger.warning("Aucun stock trouvé pour cet inventaire (mode image de stock)")
                else:
                    logger.info(f"Image de stock importée: {stocks_count} stocks trouvés")
            # Si le comptage a quantity_show=true ou show_product=true, c'est un message d'info
            elif counting.quantity_show or counting.show_product:
                if stocks_count == 0 and not info_message_added:
                    info_messages.append(stock_info_message)
                    info_message_added = True
                    logger.info("Message d'info: Image de stock non importée (quantity_show ou show_product activé)")
                elif stocks_count > 0:
                    logger.info(f"Image de stock importée: {stocks_count} stocks trouvés")
            else:
                # Pour les autres cas, on ne vérifie pas l'image de stock
                logger.info("Pas de vérification d'image de stock pour ce mode de comptage")

    def _validate_general_inventory(self, inventory, account_id, errors, info_messages):
        # 1. Tous les emplacements du compte doivent être affectés à des jobs de l'inventaire
        regroupement = RegroupementEmplacement.objects.filter(account_id=account_id).first()
        if not regroupement:
            errors.append("Aucun regroupement d'emplacement pour ce compte.")
            logger.warning(f"Pas de regroupement d'emplacement pour le compte {account_id}")
        else:
            locations = Location.objects.filter(regroupement=regroupement, is_active=True)
            location_ids = set(locations.values_list('id', flat=True))
            job_ids = Job.objects.filter(inventory=inventory).values_list('id', flat=True)
            job_location_ids = set(JobDetail.objects.filter(job_id__in=job_ids).values_list('location_id', flat=True))
            missing_locations = location_ids - job_location_ids
            if missing_locations:
                errors.append("Tous les emplacements du compte ne sont pas affectés à des jobs.")
                logger.warning(f"Emplacements manquants: {len(missing_locations)} emplacements non affectés")
            else:
                logger.info("Tous les emplacements sont affectés aux jobs")

        # 2. Tous les jobs doivent être PRET
        not_ready_jobs = Job.objects.filter(inventory=inventory).exclude(status='PRET')
        if not_ready_jobs.exists():
            errors.append("Tous les jobs ne sont pas au statut PRET.")
            logger.warning(f"Jobs non prêts: {not_ready_jobs.count()} jobs ne sont pas au statut PRET")
        else:
            logger.info("Tous les jobs sont au statut PRET")

        # Ajout des messages d'information
        info_messages.append("Merci de réceptionner tous les commandes et ranger et clôturer tous les commandes.")

    def _validate_tournant_inventory(self, inventory, errors, info_messages):
        # Au moins un job doit être PRET
        ready_jobs_count = Job.objects.filter(inventory=inventory, status='PRET').count()
        if ready_jobs_count == 0:
            errors.append("Au moins un job doit être au statut PRET pour lancer l'inventaire.")
            logger.warning("Aucun job prêt trouvé pour l'inventaire tournant")
        else:
            logger.info(f"Jobs prêts trouvés: {ready_jobs_count} jobs au statut PRET")

        # Au moins un emplacement doit être affecté à un job
        job_ids = Job.objects.filter(inventory=inventory).values_list('id', flat=True)
        affected_locations_count = JobDetail.objects.filter(job_id__in=job_ids).count()
        if affected_locations_count == 0:
            errors.append("Au moins un emplacement doit être affecté à un job pour lancer l'inventaire.")
            logger.warning("Aucun emplacement affecté à un job pour l'inventaire tournant")
        else:
            logger.info(f"Emplacements affectés trouvés: {affected_locations_count} emplacements affectés à des jobs") 