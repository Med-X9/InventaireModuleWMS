"""
Commande Django pour générer des données de test pour les inventaires.
Permet de tester l'API d'export Excel avec des données réalistes.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
from datetime import timedelta

from apps.inventory.models import (
    Inventory, Counting, Job, CountingDetail, Setting, Planning, EcartComptage, ComptageSequence
)
from apps.masterdata.models import Account, Warehouse, Location, Product
from apps.users.models import UserApp
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Génère des données de test pour les inventaires avec comptages et résultats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inventories',
            type=int,
            default=2,
            help='Nombre d\'inventaires à créer (défaut: 2)',
        )
        parser.add_argument(
            '--locations-per-warehouse',
            type=int,
            default=5,
            help='Nombre d\'emplacements par entrepôt (défaut: 5)',
        )
        parser.add_argument(
            '--products-per-location',
            type=int,
            default=3,
            help='Nombre de produits par emplacement (défaut: 3)',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Supprimer les données existantes avant de générer',
        )

    def create_test_user(self):
        """Crée un utilisateur de test s'il n'existe pas"""
        User = get_user_model()
        username = 'testuser'
        
        if not User.objects.filter(username=username).exists():
            account = Account.objects.first()
            user = User.objects.create_user(
                username=username,
                email='test@example.com',
                password='testpass123',
                type='Web',
                nom='Test',
                prenom='User',
                compte=account,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Utilisateur de test créé: {username} / testpass123'))
            return user
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Utilisateur de test existe déjà: {username}'))
            return User.objects.get(username=username)

    def handle(self, *args, **options):
        fake = Faker('fr_FR')
        num_inventories = options['inventories']
        locations_per_warehouse = options['locations_per_warehouse']
        products_per_location = options['products_per_location']
        
        if options['clean']:
            self.stdout.write(self.style.WARNING('Suppression des données existantes...'))
            self.clean_data()
        
        # Créer un utilisateur de test
        self.create_test_user()
        
        # Vérifier qu'il y a des données de base
        if not Account.objects.exists():
            self.stdout.write(self.style.ERROR('Aucun compte trouvé. Veuillez d\'abord générer des données masterdata.'))
            return
        
        if not Warehouse.objects.exists():
            self.stdout.write(self.style.ERROR('Aucun entrepôt trouvé. Veuillez d\'abord générer des données masterdata.'))
            return
        
        if not Location.objects.exists():
            self.stdout.write(self.style.ERROR('Aucun emplacement trouvé. Veuillez d\'abord générer des données masterdata.'))
            return
        
        if not Product.objects.exists():
            self.stdout.write(self.style.ERROR('Aucun produit trouvé. Veuillez d\'abord générer des données masterdata.'))
            return
        
        accounts = list(Account.objects.all())
        warehouses = list(Warehouse.objects.all())
        locations = list(Location.objects.filter(sous_zone__zone__warehouse__in=warehouses))
        products = list(Product.objects.all())
        
        if not locations:
            self.stdout.write(self.style.ERROR('Aucun emplacement trouvé pour les entrepôts. Veuillez créer des emplacements.'))
            return
        
        if not products:
            self.stdout.write(self.style.ERROR('Aucun produit trouvé. Veuillez créer des produits.'))
            return
        
        # Créer des inventaires
        for inv_idx in range(num_inventories):
            account = random.choice(accounts)
            selected_warehouses = random.sample(warehouses, min(2, len(warehouses)))
            
            # Créer l'inventaire
            inventory = Inventory.objects.create(
                label=f"Inventaire Test {inv_idx + 1} - {fake.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d')}",
                date=timezone.now() - timedelta(days=random.randint(1, 30)),
                status=random.choice(['EN REALISATION', 'TERMINE', 'CLOTURE']),
                inventory_type=random.choice(['GENERAL', 'TOURNANT', 'MAGASIN']),
            )
            
            # Créer les Settings (liens entre inventaire, compte et entrepôts)
            for warehouse in selected_warehouses:
                Setting.objects.create(
                    account=account,
                    warehouse=warehouse,
                    inventory=inventory,
                )
            
            # Créer les comptages (3 comptages par inventaire)
            count_mode = random.choice(['par article', 'en vrac'])
            countings = []
            for order in range(1, 4):
                counting = Counting.objects.create(
                    inventory=inventory,
                    order=order,
                    count_mode=count_mode,
                    unit_scanned=False,
                    entry_quantity=False,
                    stock_situation=False,
                    is_variant=False,
                    n_lot=False,
                    n_serie=False,
                    dlc=False,
                    show_product=(count_mode == 'par article'),
                    quantity_show=True,
                )
                countings.append(counting)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Inventaire créé: {inventory.label} (ID: {inventory.id})'))
            
            # Créer des jobs pour chaque entrepôt
            for warehouse in selected_warehouses:
                # Sélectionner des emplacements pour cet entrepôt
                warehouse_locations = [
                    loc for loc in locations 
                    if loc.sous_zone.zone.warehouse == warehouse
                ][:locations_per_warehouse]
                
                if not warehouse_locations:
                    continue
                
                # Créer un job pour cet entrepôt
                job = Job.objects.create(
                    warehouse=warehouse,
                    inventory=inventory,
                    status=random.choice(['PRET', 'ENTAME', 'VALIDE', 'TERMINE']),
                )
                
                self.stdout.write(self.style.SUCCESS(f'  ✓ Job créé: {job.reference} (Warehouse: {warehouse.warehouse_name})'))
                
                # Créer des CountingDetail pour chaque emplacement
                for location in warehouse_locations:
                    # Sélectionner des produits pour cet emplacement (si mode "par article")
                    location_products = random.sample(products, min(products_per_location, len(products))) if count_mode == 'par article' else [None]
                    
                    for product in location_products:
                        # Créer des CountingDetail pour chaque comptage
                        counting_details = []
                        for counting in countings:
                            # Générer des quantités variées pour chaque comptage
                            base_quantity = random.randint(50, 200)
                            # Ajouter une variation pour simuler des écarts
                            variation = random.randint(-5, 5)
                            quantity = max(0, base_quantity + variation)
                            
                            counting_detail = CountingDetail.objects.create(
                                counting=counting,
                                location=location,
                                product=product,
                                quantity_inventoried=quantity,
                                job=job,
                            )
                            counting_details.append(counting_detail)
                        
                        # Créer un EcartComptage si on a des écarts (optionnel)
                        if random.choice([True, False]):  # 50% de chance
                            # Calculer le final_result (dernière quantité)
                            final_result = counting_details[-1].quantity_inventoried if counting_details else None
                            
                            if final_result is not None:
                                ecart = EcartComptage.objects.create(
                                    inventory=inventory,
                                    total_sequences=len(counting_details),
                                    stopped_sequence=len(counting_details),
                                    final_result=final_result,
                                    resolved=random.choice([True, False]),
                                    stopped_reason=random.choice(['ECART_ZERO', 'RESOLU_MANUEL', None]),
                                )
                                
                                # Créer des ComptageSequence pour chaque CountingDetail
                                for seq_num, cd in enumerate(counting_details, start=1):
                                    previous_quantity = counting_details[seq_num - 2].quantity_inventoried if seq_num > 1 else None
                                    ecart_with_previous = (
                                        cd.quantity_inventoried - previous_quantity 
                                        if previous_quantity is not None 
                                        else None
                                    )
                                    
                                    ComptageSequence.objects.create(
                                        ecart_comptage=ecart,
                                        sequence_number=seq_num,
                                        counting_detail=cd,
                                        quantity=cd.quantity_inventoried,
                                        ecart_with_previous=ecart_with_previous,
                                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'    ✓ {len(warehouse_locations)} emplacements avec données de comptage créés'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Génération terminée! {num_inventories} inventaire(s) créé(s).'))
        
        # Afficher les IDs créés pour faciliter les tests
        inventories = Inventory.objects.all().order_by('-id')[:num_inventories]
        if inventories:
            self.stdout.write(self.style.SUCCESS('\n📋 Inventaires créés:'))
            for inv in inventories:
                warehouses = [s.warehouse for s in inv.awi_links.all()]
                for wh in warehouses:
                    self.stdout.write(self.style.SUCCESS(f'  - Inventory ID: {inv.id}, Warehouse ID: {wh.id}'))
        
        self.stdout.write(self.style.SUCCESS('\n🔗 Vous pouvez maintenant tester l\'API avec:'))
        self.stdout.write(self.style.SUCCESS('  GET /web/api/inventory/{inventory_id}/warehouses/{warehouse_id}/results/'))
        self.stdout.write(self.style.SUCCESS('  GET /web/api/inventory/{inventory_id}/warehouses/{warehouse_id}/results/export/'))
        self.stdout.write(self.style.WARNING('\n⚠️  Authentification requise:'))
        self.stdout.write(self.style.WARNING('  Utilisateur: testuser'))
        self.stdout.write(self.style.WARNING('  Mot de passe: testpass123'))
        self.stdout.write(self.style.WARNING('\n  Pour obtenir un token JWT:'))
        self.stdout.write(self.style.WARNING('  POST /web/api/mobile/auth/login/'))
        self.stdout.write(self.style.WARNING('  Body: {"username": "testuser", "password": "testpass123"}'))
        self.stdout.write(self.style.WARNING('  Puis utilisez le token dans le header: Authorization: Bearer {token}'))

    def clean_data(self):
        """Supprime les données existantes"""
        ComptageSequence.objects.all().delete()
        EcartComptage.objects.all().delete()
        CountingDetail.objects.all().delete()
        Job.objects.all().delete()
        Counting.objects.all().delete()
        Planning.objects.all().delete()
        Setting.objects.all().delete()
        Inventory.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Données supprimées!'))

