"""
Commande Django pour supprimer les JobDetail selon l'inventaire et l'ordre du comptage.

Cette commande :
- Filtre les JobDetail par inventaire et ordre du comptage
- Supprime les JobDetail correspondants
- Affiche un résumé des suppressions

Exemple d'utilisation:
    python manage.py delete_job_details_by_counting_order --inventory-id 2 --counting-order 3
    python manage.py delete_job_details_by_counting_order --inventory-id 2 --counting-order 3 --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import logging
from typing import Optional

from apps.inventory.models import JobDetail, Inventory, Counting

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Supprime les JobDetail selon l\'inventaire et l\'ordre du comptage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inventory-id',
            type=int,
            required=True,
            help='ID de l\'inventaire',
        )
        parser.add_argument(
            '--counting-order',
            type=int,
            required=True,
            help='Ordre du comptage (ex: 3)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui sera supprimé sans supprimer réellement',
        )

    def handle(self, *args, **options):
        inventory_id = options.get('inventory_id')
        counting_order = options.get('counting_order')
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS(
            f'🗑️  Suppression des JobDetail pour l\'inventaire {inventory_id} avec counting order {counting_order}'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune suppression ne sera effectuée'))
        
        # Vérifier que l'inventaire existe
        try:
            inventory = Inventory.objects.get(id=inventory_id)
            self.stdout.write(f'  📦 Inventaire: {inventory.reference} ({inventory.label})')
        except Inventory.DoesNotExist:
            raise CommandError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        
        # Vérifier que le comptage avec cet ordre existe pour cet inventaire
        counting = Counting.objects.filter(inventory_id=inventory_id, order=counting_order).first()
        if not counting:
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Aucun comptage avec l\'ordre {counting_order} trouvé pour l\'inventaire {inventory_id}'
                )
            )
        else:
            self.stdout.write(f'  🔢 Comptage: {counting.reference} (ordre {counting.order})')
        
        # Récupérer les JobDetail à supprimer
        job_details = JobDetail.objects.filter(
            job__inventory_id=inventory_id,
            counting__order=counting_order
        ).select_related('job', 'counting', 'location')
        
        total_count = job_details.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Aucun JobDetail trouvé pour l\'inventaire {inventory_id} avec counting order {counting_order}'
                )
            )
            return
        
        self.stdout.write(f'\n📊 {total_count} JobDetail(s) trouvé(s) à supprimer')
        
        # Afficher les détails si en mode dry-run ou pour information
        if dry_run or total_count <= 20:
            self.stdout.write('\n📋 Détails des JobDetail à supprimer:')
            for job_detail in job_details[:50]:  # Limiter à 50 pour l'affichage
                counting_ref = job_detail.counting.reference if job_detail.counting else 'N/A'
                location_ref = job_detail.location.location_reference if job_detail.location else 'N/A'
                self.stdout.write(
                    f'  - {job_detail.reference} (Job: {job_detail.job.reference}, '
                    f'Location: {location_ref}, Counting: {counting_ref}, Status: {job_detail.status})'
                )
            if total_count > 50:
                self.stdout.write(f'  ... et {total_count - 50} autre(s) JobDetail(s)')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  MODE DRY-RUN : {total_count} JobDetail(s) seraient supprimé(s)'
                )
            )
            return
        
        # Demander confirmation
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  ATTENTION : Vous êtes sur le point de supprimer {total_count} JobDetail(s)'
            )
        )
        
        # Supprimer les JobDetail
        try:
            with transaction.atomic():
                deleted_count, _ = job_details.delete()
                
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('📊 RÉSULTAT'))
                self.stdout.write('='*60)
                self.stdout.write(f"  ✅ JobDetail supprimés: {deleted_count}")
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✅ Suppression terminée avec succès!'
                    )
                )
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {str(e)}", exc_info=True)
            raise CommandError(f"Erreur lors de la suppression: {str(e)}")

