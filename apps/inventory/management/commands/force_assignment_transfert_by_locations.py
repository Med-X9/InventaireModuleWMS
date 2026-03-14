"""
Commande Django pour forcer le statut des assignments de counting order 4 à TRANSFERT
pour des jobs et emplacements spécifiques listés dans un fichier.

Cette commande :
- Lit un fichier texte avec le format : location_reference<TAB>job_reference<TAB>equipe
- Pour chaque ligne, trouve le job, l'emplacement et la session (équipe)
- Vérifie que le JobDetail existe pour ce job et cet emplacement
- Crée ou met à jour l'assignment de counting order 4 pour ce job
- Affecte à la session correspondant à l'équipe
- Change le statut à TRANSFERT si ENTAME
- Ne traite QUE les emplacements listés dans le fichier

Exemple d'utilisation:
    python manage.py force_assignment_transfert_by_locations --file data/JOB.txt
    python manage.py force_assignment_transfert_by_locations --file data/JOB.txt --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from typing import List, Optional, Set, Dict, Tuple
import logging
import os

from apps.inventory.models import Assigment, Job, JobDetail, Counting
from apps.masterdata.models import Location
from apps.users.models import UserApp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Force le statut des assignments de counting order 4 à TRANSFERT pour des jobs et emplacements spécifiques'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Chemin vers le fichier texte avec le format: location_reference<TAB>job_reference<TAB>equipe',
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
            username: Username de la session (équipe)
            
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
                self.style.WARNING(
                    f'  ⚠️  Session avec le username "{username_lower}" non trouvée (type Mobile, actif)'
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

    def _get_counting_order_4(self, job: Job) -> Optional[Counting]:
        """
        Récupère le counting avec order 4 pour un job.
        
        Args:
            job: Le job
            
        Returns:
            Counting object ou None
        """
        try:
            counting = Counting.objects.get(
                inventory=job.inventory,
                order=4
            )
            return counting
        except Counting.DoesNotExist:
            return None
        except Counting.MultipleObjectsReturned:
            counting = Counting.objects.filter(
                inventory=job.inventory,
                order=4
            ).first()
            return counting

    @transaction.atomic
    def _process_line(self, location_ref: str, job_ref: str, equipe: str, dry_run: bool) -> dict:
        """
        Traite une ligne du fichier.
        
        Args:
            location_ref: Référence de l'emplacement
            job_ref: Référence du job
            equipe: Nom de l'équipe (username de la session)
            dry_run: Si True, ne fait que simuler
            
        Returns:
            Dictionnaire avec les résultats du traitement
        """
        result = {
            'processed': False,
            'job_found': False,
            'location_found': False,
            'job_detail_found': False,
            'session_found': False,
            'counting_found': False,
            'assignment_created': False,
            'assignment_updated': False,
            'error': None
        }
        
        # 1. Trouver le job
        try:
            job = Job.objects.get(reference=job_ref)
            result['job_found'] = True
        except Job.DoesNotExist:
            result['error'] = f'Job {job_ref} non trouvé'
            return result
        except Job.MultipleObjectsReturned:
            job = Job.objects.filter(reference=job_ref).first()
            result['job_found'] = True
        
        # 2. Trouver l'emplacement
        try:
            location = Location.objects.get(location_reference=location_ref)
            result['location_found'] = True
        except Location.DoesNotExist:
            result['error'] = f'Emplacement {location_ref} non trouvé'
            return result
        except Location.MultipleObjectsReturned:
            location = Location.objects.filter(location_reference=location_ref).first()
            result['location_found'] = True
        
        # 3. Vérifier que le JobDetail existe pour ce job et cet emplacement
        job_detail = JobDetail.objects.filter(
            job=job,
            location=location
        ).first()
        
        if not job_detail:
            result['error'] = f'JobDetail non trouvé pour job {job_ref} et emplacement {location_ref}'
            return result
        
        result['job_detail_found'] = True
        
        # 4. Trouver la session (équipe)
        session = self._get_session_by_username(equipe)
        if not session:
            result['error'] = f'Session (équipe) "{equipe}" non trouvée'
            return result
        
        result['session_found'] = True
        
        # 5. Trouver le counting order 4
        counting = self._get_counting_order_4(job)
        if not counting:
            result['error'] = f'Counting order 4 non trouvé pour le job {job_ref}'
            return result
        
        result['counting_found'] = True
        
        # 6. Créer ou mettre à jour l'assignment
        assignment, created = Assigment.objects.get_or_create(
            job=job,
            counting=counting,
            defaults={
                'status': 'TRANSFERT',
                'session': session,
                'transfert_date': timezone.now()
            }
        )
        
        if created:
            result['assignment_created'] = True
            if not dry_run:
                assignment.save()
        else:
            # Mettre à jour l'assignment existant
            if assignment.status == 'ENTAME':
                if not dry_run:
                    assignment.status = 'TRANSFERT'
                    assignment.transfert_date = timezone.now()
                    assignment.session = session
                    assignment.save()
                result['assignment_updated'] = True
            else:
                # Mettre à jour la session même si le statut n'est pas ENTAME
                if not dry_run:
                    assignment.session = session
                    assignment.save()
                result['assignment_updated'] = True
        
        result['processed'] = True
        return result

    def handle(self, *args, **options):
        file_path = options.get('file')
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('📋 Forcer le statut des assignments de counting order 4 à TRANSFERT'))
        self.stdout.write(f'  📄 Fichier: {file_path}')
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune modification ne sera effectuée'))
        
        if not os.path.exists(file_path):
            raise CommandError(f'Le fichier {file_path} n\'existe pas')
        
        # Statistiques
        stats = {
            'total_lines': 0,
            'processed': 0,
            'jobs_found': 0,
            'locations_found': 0,
            'job_details_found': 0,
            'sessions_found': 0,
            'countings_found': 0,
            'assignments_created': 0,
            'assignments_updated': 0,
            'errors': []
        }
        
        if dry_run:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('SIMULATION - Ce qui sera fait:')
            self.stdout.write('='*60)
        
        # Lire le fichier ligne par ligne
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # Ignorer les lignes vides
                        continue
                    
                    stats['total_lines'] += 1
                    
                    # Séparer par tabulation
                    parts = line.split('\t')
                    if len(parts) < 3:
                        error_msg = f'Ligne {line_num} ignorée : format invalide (attendu: location<TAB>job<TAB>equipe)'
                        stats['errors'].append(error_msg)
                        self.stdout.write(self.style.WARNING(f'  ⚠️  {error_msg}'))
                        continue
                    
                    location_ref = parts[0].strip()
                    job_ref = parts[1].strip()
                    equipe = parts[2].strip()
                    
                    if not location_ref or not job_ref or not equipe:
                        error_msg = f'Ligne {line_num} ignorée : données manquantes'
                        stats['errors'].append(error_msg)
                        continue
                    
                    self.stdout.write(
                        f'\n📋 Ligne {line_num}: {location_ref} → {job_ref} (équipe: {equipe})'
                    )
                    
                    # Traiter la ligne
                    result = self._process_line(location_ref, job_ref, equipe, dry_run)
                    
                    if result['processed']:
                        stats['processed'] += 1
                        if result['job_found']:
                            stats['jobs_found'] += 1
                        if result['location_found']:
                            stats['locations_found'] += 1
                        if result['job_detail_found']:
                            stats['job_details_found'] += 1
                        if result['session_found']:
                            stats['sessions_found'] += 1
                        if result['counting_found']:
                            stats['countings_found'] += 1
                        if result['assignment_created']:
                            stats['assignments_created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✅ Assignment créé pour {job_ref} (counting order 4, session: {equipe})'
                                )
                            )
                        if result['assignment_updated']:
                            stats['assignments_updated'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✅ Assignment mis à jour pour {job_ref} (counting order 4, session: {equipe})'
                                )
                            )
                    else:
                        if result['error']:
                            stats['errors'].append(f'Ligne {line_num}: {result["error"]}')
                            self.stdout.write(self.style.ERROR(f'  ❌ {result["error"]}'))
        
        except Exception as e:
            raise CommandError(f'Erreur lors de la lecture du fichier {file_path}: {str(e)}')
        
        # Afficher le résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 RÉSUMÉ'))
        self.stdout.write('='*60)
        self.stdout.write(f"  Lignes totales: {stats['total_lines']}")
        self.stdout.write(f"  Lignes traitées avec succès: {stats['processed']}")
        self.stdout.write(f"  Jobs trouvés: {stats['jobs_found']}")
        self.stdout.write(f"  Emplacements trouvés: {stats['locations_found']}")
        self.stdout.write(f"  JobDetail trouvés: {stats['job_details_found']}")
        self.stdout.write(f"  Sessions trouvées: {stats['sessions_found']}")
        self.stdout.write(f"  Countings trouvés: {stats['countings_found']}")
        self.stdout.write(f"  Assignments créés: {stats['assignments_created']}")
        self.stdout.write(f"  Assignments mis à jour: {stats['assignments_updated']}")
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"\n  ❌ Erreurs: {len(stats['errors'])}"))
            for error in stats['errors'][:10]:  # Afficher les 10 premières erreurs
                self.stdout.write(self.style.ERROR(f"    - {error}"))
            if len(stats['errors']) > 10:
                self.stdout.write(self.style.ERROR(f"    ... et {len(stats['errors']) - 10} autre(s) erreur(s)"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODE DRY-RUN : Aucune modification n\'a été effectuée'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Traitement terminé avec succès!'))
