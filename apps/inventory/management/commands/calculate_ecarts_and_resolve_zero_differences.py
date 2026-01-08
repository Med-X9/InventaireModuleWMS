from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.inventory.models import Job, Assigment, EcartComptage, ComptageSequence, CountingDetail, Inventory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calcule les écarts entre 1er et 2ème comptage pour tous les jobs liés à un inventaire, et résout automatiquement les écarts = 0'

    def add_arguments(self, parser):
        parser.add_argument(
            'inventory_id',
            type=int,
            help='ID de l\'inventaire pour lequel traiter tous les jobs liés'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : simule les changements sans les appliquer réellement'
        )

    def handle(self, *args, **options):
        inventory_id = options['inventory_id']
        dry_run = options['dry_run']

        try:
            # Valider que l'inventaire existe
            inventory = Inventory.objects.get(id=inventory_id)
            self.stdout.write(f'🟡 Inventaire {inventory.reference} (ID: {inventory.id})')

            # Récupérer tous les jobs liés à cet inventaire
            jobs = Job.objects.filter(inventory=inventory)

            if not jobs.exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Aucun job trouvé pour l\'inventaire {inventory.reference}')
                )
                return

            self.stdout.write(f'🟡 Traitement de {jobs.count()} jobs liés à l\'inventaire {inventory.reference}')

            # Statistiques globales
            total_jobs_processed = 0
            total_assignments_found = 0
            total_ecarts_processed = 0
            total_ecarts_resolved = 0

            # Traiter chaque job
            for job in jobs:
                total_jobs_processed += 1
                self.stdout.write(f'\n🏭 Job {job.reference} (ID: {job.id})')

                # Récupérer tous les assignments de ce job
                assignments = Assigment.objects.filter(job=job)

                if not assignments.exists():
                    self.stdout.write(f'  ℹ️ Aucun assignment trouvé pour ce job')
                    continue

                total_assignments_found += len(assignments)
                self.stdout.write(f'  📋 {len(assignments)} assignment(s) trouvé(s)')

                # Récupérer tous les EcartComptage liés au job via les ComptageSequence
                ecarts_comptage = EcartComptage.objects.filter(
                    counting_sequences__counting_detail__job=job
                ).distinct().prefetch_related(
                    'counting_sequences__counting_detail__counting',
                    'counting_sequences__counting_detail__product',
                    'counting_sequences__counting_detail__location'
                )

                if not ecarts_comptage.exists():
                    self.stdout.write(f'  ⚠️ Aucun EcartComptage trouvé pour ce job')
                    continue

                self.stdout.write(f'  📊 {ecarts_comptage.count()} EcartComptage trouvé(s)')

                # Traiter chaque EcartComptage de ce job
                job_ecarts_resolved = 0
                job_ecarts_processed = 0

                for ecart in ecarts_comptage:
                    job_ecarts_processed += 1
                    total_ecarts_processed += 1

                    # Calculer l'écart pour cet EcartComptage
                    ecart_result = self.calculate_ecart_difference(ecart)

                    if ecart_result['has_difference']:
                        difference = ecart_result['difference']

                        # Si écart = 0 et pas encore résolu
                        if difference == 0 and ecart.final_result is None:
                            if dry_run:
                                self.stdout.write(
                                    f'  ✅ [DRY-RUN] {ecart.reference} : écart = {difference}, SERAIT résolu'
                                )
                            else:
                                with transaction.atomic():
                                    ecart.final_result = 0
                                    ecart.resolved = True
                                    ecart.manual_result = False
                                    ecart.justification = "Écart automatiquement résolu (différence = 0)"
                                    ecart.save()

                                self.stdout.write(
                                    f'  ✅ {ecart.reference} : écart = {difference}, RÉSOLU'
                                )
                            job_ecarts_resolved += 1
                            total_ecarts_resolved += 1
                        elif ecart.final_result is not None:
                            self.stdout.write(
                                f'  ⏭️ {ecart.reference} : écart = {difference}, déjà résolu'
                            )
                        else:
                            self.stdout.write(
                                f'  ⏭️ {ecart.reference} : écart = {difference}, résolution manuelle requise'
                            )
                    else:
                        self.stdout.write(
                            f'  ⚠️ {ecart.reference} : {ecart_result["reason"]}'
                        )

                # Résumé par job
                self.stdout.write(
                    f'  📈 Job {job.reference} : {job_ecarts_processed} écart(s) traité(s), '
                    f'{job_ecarts_resolved} résolu(s)'
                )

            # Résumé final
            self.stdout.write('\n' + '='*60)
            mode = "[DRY-RUN] " if dry_run else ""
            self.stdout.write(f'{mode}RÉSUMÉ GLOBAL DU CALCUL D\'ÉCARTS:')
            self.stdout.write(f'Jobs traités: {total_jobs_processed}')
            self.stdout.write(f'Assignments trouvés: {total_assignments_found}')
            self.stdout.write(f'EcartComptage traités: {total_ecarts_processed}')
            self.stdout.write(f'EcartComptage résolus (écart = 0): {total_ecarts_resolved}')

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'\n🔍 [DRY-RUN] {total_ecarts_resolved} EcartComptage SERAIENT résolus')
                )
            else:
                if total_ecarts_resolved > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'\n✅ {total_ecarts_resolved} EcartComptage résolus automatiquement')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('\n⚠️ Aucun EcartComptage n\'a été résolu')
                    )

        except Inventory.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'❌ Inventaire avec ID {inventory_id} non trouvé')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'❌ Erreur inattendue: {str(e)}')
            )
            logger.error(f"Erreur lors du calcul des écarts: {str(e)}", exc_info=True)

    def calculate_ecart_difference(self, ecart_comptage):
        """
        Calcule l'écart entre les séquences de comptage 1 et 2 pour un EcartComptage.

        Returns:
            dict: {
                'has_difference': bool,
                'difference': int or None,
                'seq1_quantity': int or None,
                'seq2_quantity': int or None,
                'reason': str (si pas de différence)
            }
        """
        # Récupérer toutes les séquences pour cet écart, triées par numéro de séquence
        sequences = ecart_comptage.counting_sequences.all().order_by('sequence_number')

        if sequences.count() < 2:
            return {
                'has_difference': False,
                'difference': None,
                'seq1_quantity': None,
                'seq2_quantity': None,
                'reason': f'Sequences insuffisantes ({sequences.count()}/2 minimum)'
            }

        # Prendre les 2 premières séquences (normalement sequence_number 1 et 2)
        seq1 = sequences[0]  # Séquence 1 (1er comptage)
        seq2 = sequences[1]  # Séquence 2 (2ème comptage)

        # Calculer l'écart: quantité_seq2 - quantité_seq1
        difference = seq2.quantity - seq1.quantity

        return {
            'has_difference': True,
            'difference': difference,
            'seq1_quantity': seq1.quantity,
            'seq2_quantity': seq2.quantity,
            'reason': None
        }
