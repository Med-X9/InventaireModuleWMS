"""
Commande Django pour mettre les jobs et assignments au statut PRET
pour un inventaire et warehouse spécifiques.

Exemple d'utilisation:
    python manage.py set_jobs_assignments_pret --inventory-id 2 --warehouse-id 1
    python manage.py set_jobs_assignments_pret --inventory-id 2 --warehouse-id 1 --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
import logging

from apps.inventory.models import Job, Assigment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Met les jobs et assignments au statut PRET pour un inventaire et warehouse spécifiques'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inventory-id',
            type=int,
            required=True,
            help='ID de l\'inventaire',
        )
        parser.add_argument(
            '--warehouse-id',
            type=int,
            required=True,
            help='ID de l\'entrepôt',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui sera modifié sans modifier réellement',
        )
        parser.add_argument(
            '--job-status-filter',
            type=str,
            nargs='+',
            help='Filtrer les jobs par statut avant modification (ex: --job-status-filter EN_ATTENTE AFFECTE)',
        )
        parser.add_argument(
            '--assignment-status-filter',
            type=str,
            nargs='+',
            help='Filtrer les assignments par statut avant modification (ex: --assignment-status-filter EN_ATTENTE AFFECTE)',
        )

    def handle(self, *args, **options):
        inventory_id = options['inventory_id']
        warehouse_id = options['warehouse_id']
        dry_run = options['dry_run']
        job_status_filter = options.get('job_status_filter')
        assignment_status_filter = options.get('assignment_status_filter')
        
        self.stdout.write(self.style.SUCCESS('📋 Mise à jour des statuts vers PRET'))
        self.stdout.write(f'  📦 Inventaire ID: {inventory_id}')
        self.stdout.write(f'  🏭 Warehouse ID: {warehouse_id}')
        
        # Valider que l'inventaire et le warehouse existent
        try:
            from apps.inventory.models import Inventory
            from apps.masterdata.models import Warehouse
            
            inventory = Inventory.objects.get(id=inventory_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
            
            self.stdout.write(f'  ✓ Inventaire: {inventory.reference} - {inventory.label}')
            self.stdout.write(f'  ✓ Warehouse: {warehouse.reference} - {warehouse.warehouse_name}')
        except Inventory.DoesNotExist:
            raise CommandError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        except Warehouse.DoesNotExist:
            raise CommandError(f"Entrepôt avec l'ID {warehouse_id} non trouvé")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 MODE TEST - Aucune donnée ne sera modifiée\n'))
        
        current_time = timezone.now()
        
        # Récupérer les jobs
        jobs_query = Job.objects.filter(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        )
        
        if job_status_filter:
            jobs_query = jobs_query.filter(status__in=job_status_filter)
            self.stdout.write(f'  🔍 Filtre jobs: statut IN {job_status_filter}')
        
        jobs = jobs_query.all()
        total_jobs = jobs.count()
        
        self.stdout.write(f'\n📊 Jobs trouvés: {total_jobs}')
        
        if total_jobs == 0:
            self.stdout.write(self.style.WARNING('  ⚠ Aucun job trouvé avec ces critères'))
            return
        
        # Récupérer les assignments
        assignments_query = Assigment.objects.filter(
            job__inventory_id=inventory_id,
            job__warehouse_id=warehouse_id
        )
        
        if assignment_status_filter:
            assignments_query = assignments_query.filter(status__in=assignment_status_filter)
            self.stdout.write(f'  🔍 Filtre assignments: statut IN {assignment_status_filter}')
        
        assignments = assignments_query.all()
        total_assignments = assignments.count()
        
        self.stdout.write(f'📊 Assignments trouvés: {total_assignments}')
        
        if dry_run:
            # Afficher ce qui sera modifié
            self.stdout.write(self.style.WARNING('\n🔍 Jobs qui seront modifiés:'))
            for job in jobs[:10]:  # Limiter à 10 pour l'affichage
                self.stdout.write(f'  • {job.reference} (statut actuel: {job.status})')
            if total_jobs > 10:
                self.stdout.write(f'  ... et {total_jobs - 10} autres jobs')
            
            self.stdout.write(self.style.WARNING('\n🔍 Assignments qui seront modifiés:'))
            for assignment in assignments[:10]:  # Limiter à 10 pour l'affichage
                self.stdout.write(
                    f'  • {assignment.reference} - Job: {assignment.job.reference} '
                    f'(statut actuel: {assignment.status})'
                )
            if total_assignments > 10:
                self.stdout.write(f'  ... et {total_assignments - 10} autres assignments')
            
            # Mode dry-run : afficher le résumé
            self.stdout.write(self.style.WARNING('\n' + '='*60))
            self.stdout.write(self.style.WARNING('🔍 MODE TEST - Résumé de simulation:'))
            self.stdout.write(f'  • Jobs qui seraient modifiés: {total_jobs}')
            self.stdout.write(f'  • Assignments qui seraient modifiés: {total_assignments}')
            self.stdout.write(self.style.WARNING('='*60))
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Pour modifier réellement les statuts, relancez la commande sans --dry-run'
                )
            )
        else:
            # Mettre à jour les jobs
            jobs_updated = 0
            jobs_already_pret = 0
            
            self.stdout.write(self.style.SUCCESS('\n🏭 Mise à jour des jobs...'))
            
            with transaction.atomic():
                for job in jobs:
                    if job.status == 'PRET':
                        jobs_already_pret += 1
                        continue
                    
                    old_status = job.status
                    job.status = 'PRET'
                    # Mettre à jour la date de PRET si le champ existe
                    if hasattr(job, 'pret_date'):
                        job.pret_date = current_time
                    job.save()
                    jobs_updated += 1
                    
                    self.stdout.write(
                        f'  ✓ Job {job.reference}: {old_status} → PRET'
                    )
            
            # Mettre à jour les assignments
            assignments_updated = 0
            assignments_already_pret = 0
            
            self.stdout.write(self.style.SUCCESS('\n🏭 Mise à jour des assignments...'))
            
            with transaction.atomic():
                for assignment in assignments:
                    if assignment.status == 'PRET':
                        assignments_already_pret += 1
                        continue
                    
                    old_status = assignment.status
                    assignment.status = 'PRET'
                    assignment.pret_date = current_time
                    assignment.affecte_date = current_time if not assignment.affecte_date else assignment.affecte_date
                    assignment.date_start = current_time if not assignment.date_start else assignment.date_start
                    assignment.save()
                    assignments_updated += 1
                    
                    self.stdout.write(
                        f'  ✓ Assignment {assignment.reference} - Job {assignment.job.reference}: '
                        f'{old_status} → PRET'
                    )
            
            # Résumé
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('✅ Résumé de la mise à jour:'))
            self.stdout.write(f'  • Jobs modifiés: {jobs_updated}')
            self.stdout.write(f'  • Jobs déjà PRET: {jobs_already_pret}')
            self.stdout.write(f'  • Assignments modifiés: {assignments_updated}')
            self.stdout.write(f'  • Assignments déjà PRET: {assignments_already_pret}')
            self.stdout.write(f'  • Total jobs: {total_jobs}')
            self.stdout.write(f'  • Total assignments: {total_assignments}')
            self.stdout.write(self.style.SUCCESS('='*60))

