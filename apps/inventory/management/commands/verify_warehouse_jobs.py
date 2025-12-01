"""
Commande Django pour vérifier les jobs d'inventaire pour un warehouse spécifique.
Analyse la base de données pour comprendre la structure et les relations.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q, Count, Prefetch
from apps.inventory.models import (
    Inventory, Counting, Job, JobDetail, Assigment, Setting
)
from apps.masterdata.models import Warehouse, Location
from apps.inventory.repositories.job_repository import JobRepository


class Command(BaseCommand):
    help = 'Vérifie les jobs d\'inventaire pour un warehouse spécifique et analyse la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            'inventory_id',
            type=int,
            help='ID de l\'inventaire à vérifier',
        )
        parser.add_argument(
            'warehouse_id',
            type=int,
            help='ID de l\'entrepôt à vérifier',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Affiche des détails supplémentaires sur chaque job',
        )

    def handle(self, *args, **options):
        inventory_id = options['inventory_id']
        warehouse_id = options['warehouse_id']
        detailed = options['detailed']
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*80}\n'
            f'🔍 VÉRIFICATION DES JOBS D\'INVENTAIRE\n'
            f'   Inventory ID: {inventory_id}\n'
            f'   Warehouse ID: {warehouse_id}\n'
            f'{"="*80}\n'
        ))
        
        # ========================================
        # 1. VÉRIFICATION DE L'INVENTAIRE
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n📦 1. VÉRIFICATION DE L\'INVENTAIRE'))
        self.stdout.write('-' * 80)
        try:
            inventory = Inventory.objects.get(id=inventory_id)
            self.stdout.write(self.style.SUCCESS(f'✅ Inventaire trouvé:'))
            self.stdout.write(f'   - ID: {inventory.id}')
            self.stdout.write(f'   - Référence: {inventory.reference}')
            self.stdout.write(f'   - Label: {inventory.label}')
            self.stdout.write(f'   - Statut: {inventory.status}')
            self.stdout.write(f'   - Supprimé: {inventory.is_deleted}')
            self.stdout.write(f'   - Créé le: {inventory.created_at}')
        except Inventory.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Inventaire {inventory_id} non trouvé'))
            return
        
        # ========================================
        # 2. VÉRIFICATION DE L'ENTREPÔT
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n🏭 2. VÉRIFICATION DE L\'ENTREPÔT'))
        self.stdout.write('-' * 80)
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            self.stdout.write(self.style.SUCCESS(f'✅ Entrepôt trouvé:'))
            self.stdout.write(f'   - ID: {warehouse.id}')
            self.stdout.write(f'   - Nom: {warehouse.warehouse_name}')
            self.stdout.write(f'   - Référence: {getattr(warehouse, "reference", "N/A")}')
            self.stdout.write(f'   - Supprimé: {warehouse.is_deleted}')
        except Warehouse.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Entrepôt {warehouse_id} non trouvé'))
            return
        
        # ========================================
        # 3. VÉRIFICATION DE L'ASSOCIATION INVENTAIRE-ENTREPÔT
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n🔗 3. VÉRIFICATION DE L\'ASSOCIATION INVENTAIRE-ENTREPÔT'))
        self.stdout.write('-' * 80)
        setting = Setting.objects.filter(inventory_id=inventory_id, warehouse_id=warehouse_id).first()
        if setting:
            self.stdout.write(self.style.SUCCESS(f'✅ Association trouvée via Setting'))
            self.stdout.write(f'   - Setting ID: {setting.id}')
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Aucune association Setting trouvée'))
            associated_warehouses = Setting.objects.filter(inventory_id=inventory_id).values_list('warehouse_id', flat=True)
            if associated_warehouses:
                self.stdout.write(f'   Entrepôts associés à cet inventaire: {list(associated_warehouses)}')
        
        # ========================================
        # 4. RÉCUPÉRATION DES JOBS VIA LE REPOSITORY
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n📋 4. JOBS RÉCUPÉRÉS VIA LE REPOSITORY'))
        self.stdout.write('-' * 80)
        repository = JobRepository()
        queryset = repository.get_jobs_for_inventory_warehouse_datatable(inventory_id, warehouse_id)
        jobs_count = queryset.count()
        
        self.stdout.write(self.style.SUCCESS(f'✅ Nombre total de jobs: {jobs_count}'))
        
        if jobs_count == 0:
            self.stdout.write(self.style.WARNING('\n⚠️  Aucun job trouvé pour cette combinaison inventory/warehouse'))
            
            # Vérifier s'il y a des jobs pour cet inventaire (tous entrepôts confondus)
            all_jobs = Job.objects.filter(inventory_id=inventory_id)
            all_jobs_count = all_jobs.count()
            if all_jobs_count > 0:
                self.stdout.write(f'\n📊 Jobs trouvés pour cet inventaire (tous entrepôts): {all_jobs_count}')
                warehouse_ids = all_jobs.values_list('warehouse_id', flat=True).distinct()
                self.stdout.write(f'   Entrepôts avec des jobs: {list(warehouse_ids)}')
            
            # Vérifier s'il y a des jobs pour cet entrepôt (tous inventaires confondus)
            warehouse_jobs = Job.objects.filter(warehouse_id=warehouse_id)
            warehouse_jobs_count = warehouse_jobs.count()
            if warehouse_jobs_count > 0:
                self.stdout.write(f'\n📊 Jobs trouvés pour cet entrepôt (tous inventaires): {warehouse_jobs_count}')
                inventory_ids = warehouse_jobs.values_list('inventory_id', flat=True).distinct()
                self.stdout.write(f'   Inventaires avec des jobs: {list(inventory_ids)}')
            
            return
        
        # ========================================
        # 5. STATISTIQUES PAR STATUT
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n📊 5. STATISTIQUES PAR STATUT'))
        self.stdout.write('-' * 80)
        status_counts = queryset.values('status').annotate(count=Count('id')).order_by('-count')
        for stat in status_counts:
            self.stdout.write(f'   - {stat["status"]}: {stat["count"]} job(s)')
        
        # ========================================
        # 6. DÉTAILS DES JOBS
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n📝 6. DÉTAILS DES JOBS'))
        self.stdout.write('-' * 80)
        
        jobs_list = list(queryset[:20])  # Limiter à 20 pour l'affichage
        
        for idx, job in enumerate(jobs_list, 1):
            self.stdout.write(f'\n   Job #{idx}:')
            self.stdout.write(f'   - ID: {job.id}')
            self.stdout.write(f'   - Référence: {job.reference}')
            self.stdout.write(f'   - Statut: {job.status}')
            self.stdout.write(f'   - Créé le: {job.created_at}')
            
            if detailed:
                # Compter les JobDetail
                job_details_count = job.jobdetail_set.count()
                self.stdout.write(f'   - Nombre d\'emplacements (JobDetail): {job_details_count}')
                
                # Compter les Assignments
                assignments_count = job.assigment_set.count()
                self.stdout.write(f'   - Nombre d\'assignments: {assignments_count}')
                
                # Afficher quelques emplacements
                if job_details_count > 0:
                    job_details = job.jobdetail_set.select_related('location').all()[:5]
                    self.stdout.write(f'   - Emplacements (premiers 5):')
                    for jd in job_details:
                        location_ref = jd.location.location_reference if jd.location else 'N/A'
                        self.stdout.write(f'     • {jd.reference} - Location: {location_ref} - Statut: {jd.status}')
                    if job_details_count > 5:
                        self.stdout.write(f'     ... et {job_details_count - 5} autres')
        
        if jobs_count > 20:
            self.stdout.write(f'\n   ... et {jobs_count - 20} autres jobs (total: {jobs_count})')
        
        # ========================================
        # 7. VÉRIFICATION DES RELATIONS
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n🔗 7. VÉRIFICATION DES RELATIONS'))
        self.stdout.write('-' * 80)
        
        # Jobs avec JobDetail
        jobs_with_details = queryset.annotate(details_count=Count('jobdetail')).filter(details_count__gt=0)
        jobs_with_details_count = jobs_with_details.count()
        self.stdout.write(f'   - Jobs avec emplacements (JobDetail): {jobs_with_details_count}/{jobs_count}')
        
        # Jobs avec Assignments
        jobs_with_assignments = queryset.annotate(assignments_count=Count('assigment')).filter(assignments_count__gt=0)
        jobs_with_assignments_count = jobs_with_assignments.count()
        self.stdout.write(f'   - Jobs avec assignments: {jobs_with_assignments_count}/{jobs_count}')
        
        # Total des emplacements
        total_locations = JobDetail.objects.filter(job__in=queryset).count()
        self.stdout.write(f'   - Total des emplacements (JobDetail): {total_locations}')
        
        # ========================================
        # 8. COMPARAISON AVEC LA REQUÊTE DIRECTE
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n🔍 8. COMPARAISON AVEC REQUÊTE DIRECTE'))
        self.stdout.write('-' * 80)
        
        # Requête directe sans repository
        direct_query = Job.objects.filter(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        )
        direct_count = direct_query.count()
        self.stdout.write(f'   - Jobs via requête directe: {direct_count}')
        self.stdout.write(f'   - Jobs via repository: {jobs_count}')
        
        if direct_count != jobs_count:
            self.stdout.write(self.style.WARNING(f'   ⚠️  Différence détectée entre les deux méthodes!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✅ Les deux méthodes retournent le même nombre'))
        
        # ========================================
        # 9. VÉRIFICATION DES COMPTAGES
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n🔢 9. VÉRIFICATION DES COMPTAGES'))
        self.stdout.write('-' * 80)
        countings = Counting.objects.filter(inventory_id=inventory_id)
        countings_count = countings.count()
        self.stdout.write(f'   - Nombre de comptages pour cet inventaire: {countings_count}')
        if countings_count > 0:
            for counting in countings:
                self.stdout.write(f'     • Counting ID: {counting.id}, Order: {counting.order}, Mode: {counting.count_mode}')
        
        # ========================================
        # 10. RÉSUMÉ
        # ========================================
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('📋 RÉSUMÉ'))
        self.stdout.write('='*80)
        self.stdout.write(f'   ✅ Inventaire: {inventory.reference} (ID: {inventory_id})')
        self.stdout.write(f'   ✅ Entrepôt: {warehouse.warehouse_name} (ID: {warehouse_id})')
        self.stdout.write(f'   ✅ Jobs trouvés: {jobs_count}')
        self.stdout.write(f'   ✅ Emplacements totaux: {total_locations}')
        self.stdout.write(f'   ✅ Comptages: {countings_count}')
        self.stdout.write('='*80 + '\n')

