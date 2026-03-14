"""
Commande Django pour clôturer des assignments et jobs en masse.
Usage: python manage.py bulk_close_jobs_assignments --personnes 1,2 [--job-id JOB_ID] [--assignment-id ASSIGNMENT_ID] [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.inventory.models import Job, Assigment, Personne
from apps.mobile.services.assignment_service import AssignmentService


class Command(BaseCommand):
    help = 'Clôture des assignments et jobs en masse en utilisant la même logique que l\'API mobile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--personnes',
            type=str,
            required=True,
            help='IDs des personnes séparés par des virgules (ex: --personnes 1,2)'
        )
        parser.add_argument(
            '--job-id',
            type=int,
            help='ID du job spécifique à clôturer (optionnel)'
        )
        parser.add_argument(
            '--assignment-id',
            type=int,
            help='ID de l\'assignment spécifique à clôturer (optionnel)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui serait fait sans le faire'
        )

    def handle(self, *args, **options):
        # Parser les paramètres
        personnes_str = options['personnes']
        job_id = options.get('job_id')
        assignment_id = options.get('assignment_id')
        dry_run = options['dry_run']

        # Valider et convertir les IDs des personnes
        try:
            personnes_ids = [int(pid.strip()) for pid in personnes_str.split(',') if pid.strip()]
            if not personnes_ids:
                raise ValueError("Aucune personne valide fournie")
        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur dans les IDs des personnes: {str(e)}')
            )
            return

        # Valider que les personnes existent
        personnes_existantes = Personne.objects.filter(id__in=personnes_ids)
        if personnes_existantes.count() != len(personnes_ids):
            found_ids = set(personnes_existantes.values_list('id', flat=True))
            missing_ids = set(personnes_ids) - found_ids
            self.stdout.write(
                self.style.ERROR(f'❌ Personnes non trouvées: {", ".join(map(str, missing_ids))}')
            )
            return

        self.stdout.write(f'👥 Personnes validées: {len(personnes_ids)} trouvée(s)')
        self.stdout.write(f'🔍 Recherche des assignments à clôturer...')

        # Déterminer les assignments à traiter
        assignments_to_close = self._get_assignments_to_close(job_id, assignment_id)

        if not assignments_to_close:
            self.stdout.write(
                self.style.WARNING('⚠️ Aucun assignment trouvé à clôturer.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'📋 {len(assignments_to_close)} assignment(s) trouvé(s) à clôturer'
            )
        )

        if dry_run:
            self.stdout.write('\n📋 MODE TEST - Assignments qui seraient clôturés :')
        else:
            self.stdout.write('\n🔒 Clôture des assignments :')

        successful_closures = 0
        job_closures = 0

        for assignment_data in assignments_to_close:
            assignment = assignment_data['assignment']
            job = assignment.job

            self.stdout.write(
                f'  - Assignment {assignment.reference} (Job: {job.reference})'
            )

            if not dry_run:
                try:
                    # Utiliser le même service que l'API mobile
                    service = AssignmentService()
                    result = service.close_job(
                        job_id=job.id,
                        assignment_id=assignment.id,
                        personnes_ids=personnes_ids,
                        user_id=None  # Pas de vérification utilisateur en mode commande
                    )

                    successful_closures += 1
                    if result.get('job_closure_status', {}).get('job_closed', False):
                        job_closures += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'    ✅ Assignment clôturé avec succès'
                        )
                    )

                    if result.get('job_closure_status', {}).get('job_closed', False):
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'    ✅ Job {job.reference} clôturé également'
                            )
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'    ❌ Erreur lors de la clôture: {str(e)}'
                        )
                    )

        # Résumé final
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Mode test terminé. {len(assignments_to_close)} assignment(s) seraient clôturé(s).'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Opération terminée. {successful_closures} assignment(s) clôturé(s), {job_closures} job(s) clôturé(s).'
                )
            )

    def _get_assignments_to_close(self, job_id=None, assignment_id=None):
        """
        Détermine quels assignments doivent être clôturés.
        """
        assignments = Assigment.objects.select_related('job')

        # Filtrer par assignment spécifique
        if assignment_id:
            assignments = assignments.filter(id=assignment_id)
            if not assignments.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ Assignment avec ID {assignment_id} non trouvé')
                )
                return []
        # Filtrer par job spécifique
        elif job_id:
            assignments = assignments.filter(job_id=job_id)
            if not assignments.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ Job avec ID {job_id} non trouvé')
                )
                return []
        else:
            # Si aucun filtre spécifique, prendre tous les assignments ENTAME
            # (logique par défaut - à adapter selon les besoins)
            assignments = assignments.filter(status='ENTAME')

        # Préparer les données pour traitement
        assignments_data = []
        for assignment in assignments:
            # Vérifier si l'assignment peut être clôturé
            # (tous les JobDetails terminés)
            job_details = assignment.job.countingdetail_set.filter(
                counting=assignment.counting
            )

            if job_details.exists():
                terminated_count = job_details.filter(status='TERMINE').count()
                total_count = job_details.count()

                if terminated_count == total_count:  # Tous les emplacements terminés
                    assignments_data.append({
                        'assignment': assignment,
                        'job': assignment.job,
                        'terminated_locations': terminated_count,
                        'total_locations': total_count
                    })

        return assignments_data
