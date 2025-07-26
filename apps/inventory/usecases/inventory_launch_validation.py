from typing import Dict, Any
from apps.inventory.models import Inventory, Job, JobDetail
from apps.masterdata.models import Location, RegroupementEmplacement, Stock
from apps.inventory.exceptions import InventoryValidationError, InventoryNotFoundError
from django.db.models import Q

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

        if inventory_type == 'GENERAL':
            # 1. Tous les emplacements du compte doivent être affectés à des jobs de l'inventaire
            regroupement = RegroupementEmplacement.objects.filter(account_id=account_id).first()
            if not regroupement:
                raise InventoryValidationError("Aucun regroupement d'emplacement pour ce compte.")
            locations = Location.objects.filter(regroupement=regroupement, is_active=True)
            location_ids = set(locations.values_list('id', flat=True))
            job_ids = Job.objects.filter(inventory=inventory).values_list('id', flat=True)
            job_location_ids = set(JobDetail.objects.filter(job_id__in=job_ids).values_list('location_id', flat=True))
            missing_locations = location_ids - job_location_ids
            if missing_locations:
                raise InventoryValidationError("Tous les emplacements du compte ne sont pas affectés à des jobs.")
            # 2. Tous les jobs doivent être PRET
            not_ready_jobs = Job.objects.filter(inventory=inventory).exclude(status='PRET')
            if not_ready_jobs.exists():
                raise InventoryValidationError("Tous les jobs ne sont pas au statut PRET.")
            # 3. Image de stock importée (au moins un stock pour cet inventaire)
            if not Stock.objects.filter(inventory=inventory, is_deleted=False).exists():
                raise InventoryValidationError("L'image de stock n'a pas été importée pour cet inventaire.")
            # Ajout des messages d'information
            info_messages.append("Merci de réceptionner tous les commandes et ranger et clôturer tous les commandes.")
        elif inventory_type == 'TOURNANT':
            # Au moins un job doit être PRET
            if not Job.objects.filter(inventory=inventory, status='PRET').exists():
                raise InventoryValidationError("Au moins un job doit être au statut PRET pour lancer l'inventaire.")
        else:
            raise InventoryValidationError(f"Type d'inventaire non supporté: {inventory_type}")
        return {"success": True, "message": "Validation OK pour le lancement de l'inventaire.", "infos": info_messages} 