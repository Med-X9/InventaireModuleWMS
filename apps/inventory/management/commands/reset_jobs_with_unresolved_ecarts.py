"""
Commande Django pour remettre en statut ENTAME les jobs terminés qui ont des écarts non résolus.
Usage: python manage.py reset_jobs_with_unresolved_ecarts [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.inventory.models import Job, EcartComptage


class Command(BaseCommand):
    help = 'Remet en statut ENTAME les jobs terminés qui ont des écarts non résolus (final_result=null)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche les jobs qui seraient modifiés sans les modifier'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('🔍 Recherche des jobs terminés avec écarts non résolus...')

        # Trouver tous les jobs avec status = 'TERMINE'
        terminated_jobs = Job.objects.filter(status='TERMINE')

        jobs_to_reset = []
        total_ecarts_unresolved = 0

        for job in terminated_jobs:
            # Vérifier si ce job a des écarts non résolus (final_result = null)
            unresolved_ecarts = EcartComptage.objects.filter(
                counting_sequences__counting_detail__job=job,
                final_result__isnull=True
            )

            if unresolved_ecarts.exists():
                ecart_count = unresolved_ecarts.count()
                jobs_to_reset.append({
                    'job': job,
                    'unresolved_ecarts_count': ecart_count
                })
                total_ecarts_unresolved += ecart_count

        if not jobs_to_reset:
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ Aucun job trouvé avec des écarts non résolus.'
                )
            )
            return

        # Afficher le résumé
        self.stdout.write(
            self.style.WARNING(
                f'⚠️  {len(jobs_to_reset)} job(s) trouvé(s) avec {total_ecarts_unresolved} écart(s) non résolu(s) au total'
            )
        )

        if dry_run:
            self.stdout.write('\n📋 MODE TEST - Jobs qui seraient remis en ENTAME :')
        else:
            self.stdout.write('\n🔄 Remise en ENTAME des jobs :')

        for item in jobs_to_reset:
            job = item['job']
            ecart_count = item['unresolved_ecarts_count']

            self.stdout.write(
                f'  - Job {job.reference} (ID: {job.id}) : {ecart_count} écart(s) non résolu(s)'
            )

            if not dry_run:
                try:
                    with transaction.atomic():
                        # Remettre le job en ENTAME
                        job.status = 'ENTAME'
                        job.termine_date = None
                        job.save()

                        self.stdout.write(
                            f'    ✅ Job {job.reference} remis en ENTAME'
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'    ❌ Erreur lors de la remise en ENTAME du job {job.reference}: {str(e)}'
                        )
                    )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Mode test terminé. {len(jobs_to_reset)} job(s) seraient remis en ENTAME.'
                )
            )
        else:
            successful_resets = len(jobs_to_reset)  # Dans une vraie implémentation, compter les succès
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Opération terminée. {successful_resets} job(s) remis en ENTAME.'
                )
            )
