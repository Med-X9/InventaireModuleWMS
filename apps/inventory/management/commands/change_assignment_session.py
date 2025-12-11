"""
Commande Django pour changer l'affectation (session) des assignments.

Cette commande :
- Trouve les jobs spécifiés
- Trouve les assignments avec counting order spécifié
- Trouve la session par username
- Met à jour les assignments pour les affecter à cette session

Exemple d'utilisation:
    python manage.py change_assignment_session --job-refs JOB-0558 JOB-0585 --counting-order 3 --session-username equipe-25
    python manage.py change_assignment_session --job-refs JOB-0558 --counting-order 3 --session-username equipe-25 --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from typing import Optional
import logging

from apps.inventory.models import Assigment, Job
from apps.users.models import UserApp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Change l\'affectation (session) des assignments pour des jobs et counting order spécifiés'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-refs',
            nargs='+',
            type=str,
            required=True,
            help='Liste des références de jobs (ex: JOB-0558 JOB-0585)',
        )
        parser.add_argument(
            '--counting-order',
            type=int,
            required=True,
            help='Ordre du counting (ex: 3)',
        )
        parser.add_argument(
            '--session-username',
            type=str,
            required=True,
            help='Username de la session (ex: equipe-25)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui sera fait sans modifier la base de données',
        )

    def _get_session_by_username(self, username: str) -> Optional[UserApp]:
        """
        Récupère la session (UserApp de type Mobile) par username.
        Convertit le username en lowercase avant la recherche.
        
        Args:
            username: Username de la session
            
        Returns:
            UserApp object ou None
        """
        if not username:
            return None
        
        username_lower = username.strip().lower()
        
        try:
            session = UserApp.objects.get(
                username__iexact=username_lower,
                type='Mobile',
                is_active=True
            )
            return session
        except UserApp.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'  ❌ Session avec le username "{username_lower}" non trouvée (type Mobile, actif)'
                )
            )
            return None
        except UserApp.MultipleObjectsReturned:
            session = UserApp.objects.filter(
                username__iexact=username_lower,
                type='Mobile',
                is_active=True
            ).first()
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Plusieurs sessions trouvées pour "{username_lower}", utilisation de la première: {session.username} (ID: {session.id})'
                )
            )
            return session

    def handle(self, *args, **options):
        job_refs = options.get('job_refs')
        counting_order = options.get('counting_order')
        session_username = options.get('session_username')
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('📋 Changement d\'affectation des assignments'))
        self.stdout.write(f'  📝 Jobs: {", ".join(job_refs)}')
        self.stdout.write(f'  🔢 Counting order: {counting_order}')
        self.stdout.write(f'  👤 Session username: {session_username}')
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune modification ne sera effectuée'))
        
        # Récupérer la session
        session = self._get_session_by_username(session_username)
        if not session:
            raise CommandError(f'Session avec username "{session_username}" non trouvée')
        
        self.stdout.write(f'  ✅ Session trouvée: {session.username} (ID: {session.id})')
        
        # Récupérer les jobs
        jobs = Job.objects.filter(reference__in=job_refs).select_related('inventory', 'warehouse')
        
        found_refs = set(jobs.values_list('reference', flat=True))
        missing_refs = set(job_refs) - found_refs
        
        if missing_refs:
            self.stdout.write(self.style.ERROR(
                f'❌ Jobs non trouvés: {", ".join(sorted(missing_refs))}'
            ))
        
        if not jobs.exists():
            self.stdout.write(self.style.ERROR('❌ Aucun job trouvé'))
            return
        
        self.stdout.write(f'  ✅ {jobs.count()} job(s) trouvé(s)')
        
        # Récupérer les assignments avec counting order spécifié
        assignments = Assigment.objects.filter(
            job__in=jobs,
            counting__order=counting_order
        ).select_related('job', 'counting', 'session')
        
        total_assignments = assignments.count()
        self.stdout.write(f'  ✅ {total_assignments} assignment(s) trouvé(s) (counting order {counting_order})')
        
        if total_assignments == 0:
            self.stdout.write(self.style.WARNING('⚠️  Aucun assignment à traiter'))
            return
        
        # Statistiques
        stats = {
            'total_assignments_found': total_assignments,
            'assignments_updated': 0,
            'assignments_already_assigned': 0,
            'errors': []
        }
        
        if dry_run:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('SIMULATION - Ce qui sera fait:')
            self.stdout.write('='*60)
        
        # Traiter chaque assignment
        for assignment in assignments:
            try:
                current_session = assignment.session
                current_session_name = current_session.username if current_session else "Aucune"
                
                self.stdout.write(
                    f'\n📦 Assignment: {assignment.reference} '
                    f'(Job: {assignment.job.reference}, Counting: {assignment.counting.reference}, Order: {assignment.counting.order})'
                )
                self.stdout.write(f'  📍 Session actuelle: {current_session_name}')
                
                if current_session and current_session.id == session.id:
                    stats['assignments_already_assigned'] += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Assignment déjà affecté à la session {session.username}'
                        )
                    )
                    continue
                
                self.stdout.write(f'  🔄 Changement de session: {current_session_name} → {session.username}')
                
                if not dry_run:
                    assignment.session = session
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
        self.stdout.write(f"  Assignments déjà affectés: {stats['assignments_already_assigned']}")
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"\n  ❌ Erreurs: {len(stats['errors'])}"))
            for error in stats['errors']:
                self.stdout.write(self.style.ERROR(f"    - {error}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODE DRY-RUN : Aucune modification n\'a été effectuée'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Traitement terminé avec succès!'))

