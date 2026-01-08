from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.inventory.models import Job
import os


class Command(BaseCommand):
    help = 'Change le statut des jobs listés dans un fichier texte à ENTAME'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Chemin vers le fichier contenant les références des jobs (une par ligne)'
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

        self.stdout.write(
            self.style.SUCCESS(f'Traitement de {len(job_references)} jobs...')
        )

        # Traiter chaque job
        updated_count = 0
        not_found_count = 0
        already_entame_count = 0

        for reference in job_references:
            try:
                job = Job.objects.get(reference=reference)

                # Vérifier si le job n'est pas déjà ENTAME
                if job.status == 'ENTAME':
                    already_entame_count += 1
                    self.stdout.write(
                        f'Job {reference} : déjà ENTAME'
                    )
                    continue

                # Changer le statut à ENTAME
                old_status = job.status
                job.status = 'ENTAME'
                job.entame_date = timezone.now()
                job.save()

                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Job {reference} : {old_status} → ENTAME'
                    )
                )

            except Job.DoesNotExist:
                not_found_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Job {reference} : NON TROUVÉ')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur avec job {reference}: {str(e)}')
                )

        # Résumé final
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RÉSUMÉ DU TRAITEMENT:')
        self.stdout.write(f'Jobs mis à jour: {updated_count}')
        self.stdout.write(f'Jobs déjà ENTAME: {already_entame_count}')
        self.stdout.write(f'Jobs non trouvés: {not_found_count}')
        self.stdout.write(f'Total traité: {len(job_references)}')

        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ {updated_count} jobs changés avec succès à ENTAME')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n⚠️ Aucun job n\'a été modifié')
            )
