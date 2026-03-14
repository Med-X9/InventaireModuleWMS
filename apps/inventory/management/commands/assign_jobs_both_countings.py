"""
Commande Django pour affecter des jobs aux comptages 1 et 2 avec des sessions spécifiques.
Crée des assignments avec statut PRET pour les deux comptages.

Exemple d'utilisation:
    python manage.py assign_jobs_both_countings --job-ids 1 2 3 --session-id-1 5 --session-id-2 6
    python manage.py assign_jobs_both_countings --job-references JOB-0001 JOB-0002 --session-id-1 5 --session-id-2 6
    python manage.py assign_jobs_both_countings --inventory-id 1 --session-id-1 5 --session-id-2 6
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import logging

from apps.inventory.models import Job, Counting, Assigment
from apps.users.models import UserApp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Affecte des jobs aux comptages 1 et 2 avec des sessions spécifiques (statut PRET)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-ids',
            nargs='+',
            type=int,
            help='Liste des IDs des jobs à affecter',
        )
        parser.add_argument(
            '--job-references',
            nargs='+',
            type=str,
            help='Liste des références des jobs à affecter (ex: JOB-0001)',
        )
        parser.add_argument(
            '--inventory-id',
            type=int,
            help='ID de l\'inventaire (affecte tous les jobs de cet inventaire)',
        )
        parser.add_argument(
            '--session-id-1',
            type=int,
            required=False,
            help='ID de la session pour le comptage 1 (optionnel)',
        )
        parser.add_argument(
            '--session-id-2',
            type=int,
            required=False,
            help='ID de la session pour le comptage 2 (optionnel)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui sera créé sans créer réellement',
        )

    def get_jobs(self, job_ids=None, job_references=None, inventory_id=None):
        """
        Récupère les jobs selon les critères fournis.
        
        Args:
            job_ids: Liste des IDs des jobs
            job_references: Liste des références des jobs
            inventory_id: ID de l'inventaire
            
        Returns:
            QuerySet des jobs
        """
        if job_ids:
            jobs = Job.objects.filter(id__in=job_ids)
            if jobs.count() != len(job_ids):
                found_ids = set(jobs.values_list('id', flat=True))
                missing_ids = set(job_ids) - found_ids
                raise CommandError(f"Jobs non trouvés avec les IDs: {missing_ids}")
            return jobs
        
        if job_references:
            jobs = Job.objects.filter(reference__in=job_references)
            if jobs.count() != len(job_references):
                found_refs = set(jobs.values_list('reference', flat=True))
                missing_refs = set(job_references) - found_refs
                raise CommandError(f"Jobs non trouvés avec les références: {missing_refs}")
            return jobs
        
        if inventory_id:
            jobs = Job.objects.filter(inventory_id=inventory_id)
            if not jobs.exists():
                raise CommandError(f"Aucun job trouvé pour l'inventaire {inventory_id}")
            return jobs
        
        raise CommandError(
            "Vous devez fournir soit --job-ids, soit --job-references, soit --inventory-id"
        )

    def get_session(self, session_id, counting_order):
        """
        Récupère une session (UserApp de type Mobile).
        
        Args:
            session_id: ID de la session
            counting_order: Ordre du comptage (pour les messages d'erreur)
            
        Returns:
            UserApp object
        """
        if not session_id:
            return None
        
        try:
            session = UserApp.objects.get(id=session_id, type='Mobile', is_active=True)
            return session
        except UserApp.DoesNotExist:
            raise CommandError(
                f"Session avec l'ID {session_id} non trouvée (type Mobile) pour le comptage {counting_order}"
            )

    def assign_jobs_to_countings(
        self,
        jobs,
        session_1=None,
        session_2=None,
        dry_run=False
    ):
        """
        Affecte des jobs aux comptages 1 et 2 avec des sessions spécifiques.
        Crée des assignments avec statut PRET.
        
        Args:
            jobs: QuerySet des jobs
            session_1: Session pour le comptage 1
            session_2: Session pour le comptage 2
            dry_run: Mode test
            
        Returns:
            Dict avec les statistiques de création
        """
        if dry_run:
            return {
                'assignments_created_1': len(list(jobs)),
                'assignments_created_2': len(list(jobs)),
                'assignments_updated_1': 0,
                'assignments_updated_2': 0
            }
        
        # Vérifier que tous les jobs appartiennent au même inventaire
        inventory_ids = set(job.inventory_id for job in jobs)
        if len(inventory_ids) != 1:
            raise CommandError(
                f"Tous les jobs doivent appartenir au même inventaire. "
                f"Inventaires trouvés: {inventory_ids}"
            )
        
        inventory_id = list(inventory_ids)[0]
        
        # Récupérer les comptages 1 et 2
        counting_1 = Counting.objects.filter(inventory_id=inventory_id, order=1).first()
        counting_2 = Counting.objects.filter(inventory_id=inventory_id, order=2).first()
        
        if not counting_1:
            raise CommandError(
                f"Comptage d'ordre 1 non trouvé pour l'inventaire {inventory_id}"
            )
        
        if not counting_2:
            raise CommandError(
                f"Comptage d'ordre 2 non trouvé pour l'inventaire {inventory_id}"
            )
        
        # Créer les assignments avec statut PRET
        assignments_created_1 = []
        assignments_created_2 = []
        assignments_updated_1 = []
        assignments_updated_2 = []
        current_time = timezone.now()
        
        with transaction.atomic():
            for job in jobs:
                # Assignment pour le comptage 1
                if session_1:
                    assignment_1, created_1 = Assigment.objects.get_or_create(
                        job=job,
                        counting=counting_1,
                        defaults={
                            'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                            'session': session_1,
                            'status': 'PRET',
                            'pret_date': current_time,
                            'affecte_date': current_time,
                            'date_start': current_time
                        }
                    )
                    
                    if not created_1:
                        # Mettre à jour l'assignment existant
                        assignment_1.session = session_1
                        assignment_1.status = 'PRET'
                        assignment_1.pret_date = current_time
                        assignment_1.affecte_date = current_time
                        assignment_1.date_start = current_time
                        assignment_1.save()
                        assignments_updated_1.append(assignment_1.id)
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ Assignment {assignment_1.reference} (comptage 1) mis à jour pour le job {job.reference}"
                            )
                        )
                    else:
                        assignments_created_1.append(assignment_1.id)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Assignment {assignment_1.reference} (comptage 1) créé pour le job {job.reference}"
                            )
                        )
                
                # Assignment pour le comptage 2
                if session_2:
                    assignment_2, created_2 = Assigment.objects.get_or_create(
                        job=job,
                        counting=counting_2,
                        defaults={
                            'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                            'session': session_2,
                            'status': 'PRET',
                            'pret_date': current_time,
                            'affecte_date': current_time,
                            'date_start': current_time
                        }
                    )
                    
                    if not created_2:
                        # Mettre à jour l'assignment existant
                        assignment_2.session = session_2
                        assignment_2.status = 'PRET'
                        assignment_2.pret_date = current_time
                        assignment_2.affecte_date = current_time
                        assignment_2.date_start = current_time
                        assignment_2.save()
                        assignments_updated_2.append(assignment_2.id)
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ Assignment {assignment_2.reference} (comptage 2) mis à jour pour le job {job.reference}"
                            )
                        )
                    else:
                        assignments_created_2.append(assignment_2.id)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Assignment {assignment_2.reference} (comptage 2) créé pour le job {job.reference}"
                            )
                        )
        
        return {
            'assignments_created_1': len(assignments_created_1),
            'assignments_created_2': len(assignments_created_2),
            'assignments_updated_1': len(assignments_updated_1),
            'assignments_updated_2': len(assignments_updated_2)
        }

    def handle(self, *args, **options):
        job_ids = options.get('job_ids')
        job_references = options.get('job_references')
        inventory_id = options.get('inventory_id')
        session_id_1 = options.get('session_id_1')
        session_id_2 = options.get('session_id_2')
        dry_run = options['dry_run']
        
        # Validation : au moins une session doit être fournie
        if not session_id_1 and not session_id_2:
            raise CommandError(
                "Au moins une session doit être fournie (--session-id-1 ou --session-id-2)"
            )
        
        self.stdout.write(self.style.SUCCESS('📋 Récupération des jobs...'))
        
        # Récupérer les jobs
        try:
            jobs = self.get_jobs(job_ids, job_references, inventory_id)
            jobs_list = list(jobs)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(jobs_list)} job(s) trouvé(s)'))
            
            # Afficher les jobs
            for job in jobs_list:
                self.stdout.write(f"  • {job.reference} (ID: {job.id}, Inventaire: {job.inventory.reference})")
        except CommandError as e:
            raise CommandError(str(e))
        
        # Vérifier que tous les jobs appartiennent au même inventaire
        inventory_ids = set(job.inventory_id for job in jobs_list)
        if len(inventory_ids) != 1:
            raise CommandError(
                f"Tous les jobs doivent appartenir au même inventaire. "
                f"Inventaires trouvés: {inventory_ids}"
            )
        
        inventory_id_found = list(inventory_ids)[0]
        self.stdout.write(f'  📦 Inventaire: {inventory_id_found}')
        
        # Récupérer les sessions
        self.stdout.write(self.style.SUCCESS('\n👤 Récupération des sessions...'))
        
        session_1 = None
        session_2 = None
        
        if session_id_1:
            try:
                session_1 = self.get_session(session_id_1, 1)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Session 1: {session_1.username} ({session_1.nom} {session_1.prenom})'
                    )
                )
            except CommandError as e:
                raise CommandError(str(e))
        
        if session_id_2:
            try:
                session_2 = self.get_session(session_id_2, 2)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Session 2: {session_2.username} ({session_2.nom} {session_2.prenom})'
                    )
                )
            except CommandError as e:
                raise CommandError(str(e))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 MODE TEST - Aucune donnée ne sera créée\n'))
        
        # Affecter les jobs
        self.stdout.write(self.style.SUCCESS('\n🏭 Affectation des jobs aux comptages...\n'))
        
        try:
            result = self.assign_jobs_to_countings(
                jobs,
                session_1=session_1,
                session_2=session_2,
                dry_run=dry_run
            )
        except Exception as e:
            raise CommandError(f"Erreur lors de l'affectation: {str(e)}")
        
        # Résumé
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODE TEST - Résumé de simulation:'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Résumé de l\'affectation:'))
        
        self.stdout.write(f"  • Jobs traités: {len(jobs_list)}")
        self.stdout.write(f"  • Assignments créés (comptage 1): {result['assignments_created_1']}")
        self.stdout.write(f"  • Assignments mis à jour (comptage 1): {result['assignments_updated_1']}")
        self.stdout.write(f"  • Assignments créés (comptage 2): {result['assignments_created_2']}")
        self.stdout.write(f"  • Assignments mis à jour (comptage 2): {result['assignments_updated_2']}")
        self.stdout.write(self.style.SUCCESS('='*60))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Pour créer réellement les assignments, relancez la commande sans --dry-run'
                )
            )

