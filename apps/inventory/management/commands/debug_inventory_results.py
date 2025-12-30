"""
Commande Django pour déboguer les résultats d'inventaire.
Permet de vérifier pourquoi l'endpoint retourne des résultats vides.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from apps.inventory.models import (
    Inventory, Counting, Job, CountingDetail, Setting
)
from apps.masterdata.models import Warehouse
from apps.inventory.repositories.counting_repository import CountingRepository


class Command(BaseCommand):
    help = 'Débogue les résultats d\'inventaire pour identifier pourquoi ils sont vides'

    def add_arguments(self, parser):
        parser.add_argument(
            'inventory_id',
            type=int,
            help='ID de l\'inventaire à déboguer',
        )
        parser.add_argument(
            'warehouse_id',
            type=int,
            help='ID de l\'entrepôt à déboguer',
        )

    def handle(self, *args, **options):
        inventory_id = options['inventory_id']
        warehouse_id = options['warehouse_id']
        
        self.stdout.write(self.style.SUCCESS(f'\n🔍 Débogage des résultats pour inventory_id={inventory_id}, warehouse_id={warehouse_id}\n'))
        
        # 1. Vérifier si l'inventaire existe
        try:
            inventory = Inventory.objects.get(id=inventory_id, is_deleted=False)
            self.stdout.write(self.style.SUCCESS(f'✅ Inventaire trouvé: {inventory.reference}'))
        except Inventory.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Inventaire {inventory_id} non trouvé ou supprimé'))
            return
        
        # 2. Vérifier si l'entrepôt existe
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id, is_deleted=False)
            self.stdout.write(self.style.SUCCESS(f'✅ Entrepôt trouvé: {warehouse.warehouse_name}'))
        except Warehouse.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Entrepôt {warehouse_id} non trouvé ou supprimé'))
            return
        
        # 3. Vérifier si l'entrepôt est associé à l'inventaire
        setting = Setting.objects.filter(inventory_id=inventory_id, warehouse_id=warehouse_id).first()
        if setting:
            self.stdout.write(self.style.SUCCESS(f'✅ Entrepôt associé à l\'inventaire via Setting'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Entrepôt NON associé à l\'inventaire via Setting'))
            associated_warehouses = Setting.objects.filter(inventory_id=inventory_id).values_list('warehouse_id', flat=True)
            self.stdout.write(self.style.WARNING(f'   Entrepôts associés: {list(associated_warehouses)}'))
        
        # 4. Vérifier les Counting pour cet inventaire
        countings = Counting.objects.filter(inventory_id=inventory_id)
        counting_count = countings.count()
        self.stdout.write(self.style.SUCCESS(f'\n📊 Nombre de Counting pour cet inventaire: {counting_count}'))
        if counting_count > 0:
            for counting in countings:
                self.stdout.write(f'   - Counting ID: {counting.id}, Order: {counting.order}, Mode: {counting.count_mode}')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Aucun Counting trouvé pour cet inventaire'))
        
        # 5. Vérifier les Jobs pour cet inventaire et entrepôt
        jobs = Job.objects.filter(inventory_id=inventory_id, warehouse_id=warehouse_id)
        job_count = jobs.count()
        self.stdout.write(self.style.SUCCESS(f'\n📊 Nombre de Jobs pour inventory_id={inventory_id}, warehouse_id={warehouse_id}: {job_count}'))
        if job_count > 0:
            for job in jobs[:5]:  # Afficher les 5 premiers
                self.stdout.write(f'   - Job ID: {job.id}, Reference: {job.reference}')
            if job_count > 5:
                self.stdout.write(f'   ... et {job_count - 5} autres jobs')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Aucun Job trouvé pour cet inventaire et entrepôt'))
        
        # 6. Vérifier les CountingDetail pour cet inventaire
        all_counting_details = CountingDetail.objects.filter(
            counting__inventory_id=inventory_id
        )
        all_count = all_counting_details.count()
        self.stdout.write(self.style.SUCCESS(f'\n📊 Nombre total de CountingDetail pour inventory_id={inventory_id}: {all_count}'))
        
        # 7. Vérifier les CountingDetail pour cet inventaire et entrepôt
        filtered_counting_details = CountingDetail.objects.filter(
            counting__inventory_id=inventory_id,
            job__warehouse_id=warehouse_id
        )
        filtered_count = filtered_counting_details.count()
        self.stdout.write(self.style.SUCCESS(f'📊 Nombre de CountingDetail après filtre warehouse_id={warehouse_id}: {filtered_count}'))
        
        if filtered_count == 0 and all_count > 0:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Problème détecté: Des CountingDetail existent pour l\'inventaire mais pas pour cet entrepôt'))
            # Vérifier les warehouse_id des jobs liés aux CountingDetail
            warehouse_ids = CountingDetail.objects.filter(
                counting__inventory_id=inventory_id
            ).values_list('job__warehouse_id', flat=True).distinct()
            self.stdout.write(self.style.WARNING(f'   Warehouse IDs trouvés dans les CountingDetail: {list(set(warehouse_ids))}'))
        
        # 8. Tester la requête du repository
        self.stdout.write(self.style.SUCCESS(f'\n🔍 Test de la requête du repository:'))
        repository = CountingRepository()
        try:
            results = repository.get_inventory_results_by_warehouse(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Résultats retournés par le repository: {len(results)}'))
            if len(results) > 0:
                self.stdout.write(self.style.SUCCESS(f'   Premier résultat: {results[0]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors de l\'appel au repository: {str(e)}'))
        
        # 9. Vérifier les relations CountingDetail -> Counting -> Inventory
        if filtered_count > 0:
            sample = filtered_counting_details.first()
            self.stdout.write(self.style.SUCCESS(f'\n📋 Exemple de CountingDetail:'))
            self.stdout.write(f'   - ID: {sample.id}')
            self.stdout.write(f'   - Counting ID: {sample.counting.id if sample.counting else None}')
            self.stdout.write(f'   - Counting Order: {sample.counting.order if sample.counting else None}')
            self.stdout.write(f'   - Job ID: {sample.job.id if sample.job else None}')
            self.stdout.write(f'   - Job Warehouse ID: {sample.job.warehouse_id if sample.job else None}')
            self.stdout.write(f'   - Location ID: {sample.location.id if sample.location else None}')
            self.stdout.write(f'   - Product ID: {sample.product.id if sample.product else None}')
            self.stdout.write(f'   - Quantity: {sample.quantity_inventoried}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Débogage terminé\n'))




















