from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.inventory.models import Job, Assigment, JobDetail
import os


class Command(BaseCommand):
    help = 'Change le statut des assignments ENTAME à TERMINE pour les jobs listés dans un fichier. Utilisez --dry-run pour tester sans modifier les données.'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Chemin vers le fichier contenant les références des jobs (une par ligne)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : simule les changements sans les appliquer réellement'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']

        # Vérifier si le fichier existe
        if not os.path.exists(file_path):
            self.stderr.write(
                self.style.ERROR(f'Le fichier {file_path} n\'existe pas.')
            )
            return

        # Lire le fichier et récupérer les références des jobs
        job_references = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    reference = line.strip()
                    if reference:  # Ignorer les lignes vides
                        job_references.append(reference)
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Erreur lors de la lecture du fichier: {str(e)}')
            )
            return

        if not job_references:
            self.stdout.write(
                self.style.WARNING('Aucune référence de job trouvée dans le fichier.')
            )
            return

        mode_text = "en mode TEST (DRY-RUN)" if options['dry_run'] else "en mode RÉEL"
        self.stdout.write(
            self.style.SUCCESS(f'Traitement de {len(job_references)} jobs {mode_text}...')
        )

        # Traiter chaque job
        total_assignments_processed = 0
        assignments_changed = 0
        assignments_blocked = 0
        jobs_not_found = 0
        jobs_terminated = 0

        for reference in job_references:
            try:
                job = Job.objects.get(reference=reference)
                self.stdout.write(f'\n🟡 Traitement du job {reference}...')

                # Récupérer tous les assignments ENTAME de ce job
                assignments_entame = Assigment.objects.filter(
                    job=job,
                    status='ENTAME'
                )

                if not assignments_entame.exists():
                    self.stdout.write(f'  ℹ️ Aucun assignment ENTAME trouvé pour ce job')
                    continue

                job_assignments_changed = 0
                job_assignments_blocked = 0

                # Traiter chaque assignment ENTAME
                for assignment in assignments_entame:
                    total_assignments_processed += 1

                    # Vérifier la condition : tous les JobDetail liés doivent être TERMINE
                    can_terminate = self.check_assignment_can_be_terminated(assignment)

                    if can_terminate:
                        if options['dry_run']:
                            # Mode test : afficher seulement
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✅ [DRY-RUN] Assignment {assignment.reference} : SERAIT changé ENTAME → TERMINE'
                                )
                            )
                        else:
                            # Mode réel : changer le statut en utilisant une transaction
                            with transaction.atomic():
                                assignment.status = 'TERMINE'
                                assignment.termine_date = timezone.now()
                                assignment.save()

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✅ Assignment {assignment.reference} : ENTAME → TERMINE'
                                )
                            )

                        assignments_changed += 1
                        job_assignments_changed += 1
                    else:
                        assignments_blocked += 1
                        job_assignments_blocked += 1

                        self.stdout.write(
                            self.style.WARNING(
                                f'  ❌ Assignment {assignment.reference} : BLOQUÉ (JobDetail non terminés)'
                            )
                        )

                # Vérifier si le job peut maintenant être terminé (si ses 2 assignments sont TERMINE)
                job_can_be_terminated = self.check_job_can_be_terminated(job)
                if job_can_be_terminated:
                    if options['dry_run']:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  🎯 [DRY-RUN] Job {reference} : SERAIT changé à TERMINE (2 assignments terminés)'
                            )
                        )
                    else:
                        with transaction.atomic():
                            job.status = 'TERMINE'
                            job.termine_date = timezone.now()
                            job.save()

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  🎯 Job {reference} : changé à TERMINE (2 assignments terminés)'
                            )
                        )

                    jobs_terminated += 1

                # Résumé par job
                job_status = " (JOB TERMINE)" if job_can_be_terminated and not options['dry_run'] else ""
                self.stdout.write(
                    f'  📊 Job {reference}{job_status} : {job_assignments_changed} assignment(s) changé(s), '
                    f'{job_assignments_blocked} bloqué(s)'
                )

            except Job.DoesNotExist:
                jobs_not_found += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Job {reference} : NON TROUVÉ')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur avec job {reference}: {str(e)}')
                )

        # Résumé final
        mode = "[DRY-RUN] " if options['dry_run'] else ""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'{mode}RÉSUMÉ FINAL DU TRAITEMENT:')
        self.stdout.write(f'Jobs traités: {len(job_references) - jobs_not_found}')
        self.stdout.write(f'Jobs non trouvés: {jobs_not_found}')
        self.stdout.write(f'Assignments traités: {total_assignments_processed}')
        self.stdout.write(f'Assignments qui {"" if options["dry_run"] else ""}changeraient ENTAME → TERMINE: {assignments_changed}')
        self.stdout.write(f'Assignments bloqués (condition non remplie): {assignments_blocked}')
        self.stdout.write(f'Jobs qui {"" if options["dry_run"] else ""}changeraient à TERMINE: {jobs_terminated}')

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'\n🔍 [DRY-RUN] {assignments_changed} assignments SERAIENT changés à TERMINE')
            )
            if jobs_terminated > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'🔍 [DRY-RUN] {jobs_terminated} jobs SERAIENT changés à TERMINE')
                )
            self.stdout.write(
                self.style.WARNING('💡 Utilisez la commande sans --dry-run pour appliquer réellement les changements')
            )
        else:
            success_messages = []
            if assignments_changed > 0:
                success_messages.append(f'{assignments_changed} assignments changés avec succès à TERMINE')
            if jobs_terminated > 0:
                success_messages.append(f'{jobs_terminated} jobs changés avec succès à TERMINE')

            if success_messages:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ {", ".join(success_messages)}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('\n⚠️ Aucun changement n\'a été effectué')
                )

    def check_assignment_can_be_terminated(self, assignment):
        """
        Vérifie si un assignment peut passer d'ENTAME à TERMINE.

        Condition: TOUS les JobDetail liés à cet assignment
        (même job_id et counting_id) doivent être TERMINE.
        """
        # Récupérer tous les JobDetail pour ce job et ce counting
        job_details = JobDetail.objects.filter(
            job_id=assignment.job_id,
            counting_id=assignment.counting_id
        )

        # S'il n'y a pas de JobDetail, impossible à terminer
        if not job_details.exists():
            return False

        # Vérifier que TOUS les JobDetail sont TERMINE
        for job_detail in job_details:
            if job_detail.status != 'TERMINE':
                return False

        return True

    def check_job_can_be_terminated(self, job):
        """
        Vérifie si un job peut être terminé.

        Condition: Les 2 assignments du job doivent être TERMINE.
        Sachant que chaque job contient 2 assignments.
        """
        # Récupérer tous les assignments du job
        all_assignments = Assigment.objects.filter(job=job)

        # Vérifier qu'il y a exactement 2 assignments
        if all_assignments.count() != 2:
            return False

        # Vérifier que les 2 assignments sont TERMINE
        terminated_assignments = all_assignments.filter(status='TERMINE').count()

        return terminated_assignments == 2
