"""
Commande Django pour changer le statut des assignments de ENTAME à TRANSFERT.

Cette commande :
- Lit les références de jobs depuis une liste statique (basée sur data/JOB.txt)
- Filtre les assignments avec counting order 4 et statut ENTAME
- Change leur statut à TRANSFERT
- Met à jour la date de transfert

Exemple d'utilisation:
    python manage.py change_assignment_status_to_transfert
    python manage.py change_assignment_status_to_transfert --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from typing import List
import logging

from apps.inventory.models import Assigment, Job

logger = logging.getLogger(__name__)

# Liste statique des références de jobs
STATIC_JOB_REFERENCES = [
    'JOB-0274',
    'JOB-0275',
    'JOB-0277',
    'JOB-0289',
    'JOB-0313',
    'JOB-0337',
    'JOB-0338',
    'JOB-0339',
    'JOB-0327',
    'JOB-0340',
    'JOB-0341',
    'JOB-0345',
    'JOB-0347',
    'JOB-0350',
]


class Command(BaseCommand):
    help = 'Change le statut des assignments de ENTAME à TRANSFERT pour les jobs spécifiés (counting order 4)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui sera fait sans modifier la base de données',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('📋 Changement de statut des assignments de ENTAME à TRANSFERT'))
        self.stdout.write(f'  📝 {len(STATIC_JOB_REFERENCES)} job(s) à traiter')
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune modification ne sera effectuée'))
        
        # Récupérer les jobs par leurs références
        jobs = Job.objects.filter(reference__in=STATIC_JOB_REFERENCES)
        
        if not jobs.exists():
            self.stdout.write(self.style.WARNING('⚠️  Aucun job trouvé avec les références fournies'))
            return
        
        job_ids = list(jobs.values_list('id', flat=True))
        self.stdout.write(f'  ✅ {jobs.count()} job(s) trouvé(s)')
        
        # Récupérer les assignments avec counting order 4 et statut ENTAME
        assignments = Assigment.objects.filter(
            job_id__in=job_ids,
            counting__order=4,
            status='ENTAME'
        ).select_related(
            'job',
            'counting'
        ).order_by('job__reference', 'counting__order')
        
        total_assignments = assignments.count()
        self.stdout.write(f'  ✅ {total_assignments} assignment(s) trouvé(s) (counting order 4, statut ENTAME)')
        
        if total_assignments == 0:
            self.stdout.write(self.style.WARNING('⚠️  Aucun assignment à traiter'))
            return
        
        # Statistiques
        stats = {
            'total_assignments_found': total_assignments,
            'assignments_updated': 0,
            'assignments_not_found': 0,
            'errors': []
        }
        
        if dry_run:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('SIMULATION - Ce qui sera fait:')
            self.stdout.write('='*60)
        
        now = timezone.now()
        
        # Traiter chaque assignment
        for assignment in assignments:
            try:
                if assignment.status != 'ENTAME':
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Assignment {assignment.reference} ignoré : '
                            f'statut actuel est {assignment.status} (attendu: ENTAME)'
                        )
                    )
                    stats['assignments_not_found'] += 1
                    continue
                
                self.stdout.write(
                    f'\n📦 Assignment: {assignment.reference} '
                    f'(Job: {assignment.job.reference}, Counting: {assignment.counting.reference}, Order: {assignment.counting.order})'
                )
                self.stdout.write(f'  🔄 Changement de statut: ENTAME → TRANSFERT')
                
                if not dry_run:
                    assignment.status = 'TRANSFERT'
                    assignment.transfert_date = now
                    assignment.save()
                
                stats['assignments_updated'] += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ Assignment {assignment.reference} mis à jour avec succès'
                    )
                )
            except Exception as e:
                error_msg = f"Erreur lors du traitement de l'assignment {assignment.reference}: {str(e)}"
                stats['errors'].append(error_msg)
                self.stdout.write(self.style.ERROR(f'  ❌ {error_msg}'))
                logger.error(error_msg, exc_info=True)
        
        # Afficher le résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 RÉSUMÉ'))
        self.stdout.write('='*60)
        self.stdout.write(f"  Assignments trouvés: {stats['total_assignments_found']}")
        self.stdout.write(f"  Assignments mis à jour: {stats['assignments_updated']}")
        self.stdout.write(f"  Assignments ignorés: {stats['assignments_not_found']}")
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"\n  ❌ Erreurs: {len(stats['errors'])}"))
            for error in stats['errors']:
                self.stdout.write(self.style.ERROR(f"    - {error}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODE DRY-RUN : Aucune modification n\'a été effectuée'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Traitement terminé avec succès!'))

