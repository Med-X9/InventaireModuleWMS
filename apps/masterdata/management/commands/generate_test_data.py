from django.core.management.base import BaseCommand
from faker import Faker
from apps.masterdata.models import (
    Account, Warehouse, Zone, ZoneType, Location, LocationType,
    Product, Family, UnitOfMeasure, Stock,SousZone
)
import hashlib
from datetime import datetime

class Command(BaseCommand):
    help = 'Génère des données de test pour les modèles de masterdata'

    def generate_unique_code(self, prefix, existing_codes):
        """Génère un code unique avec le préfixe donné"""
        while True:
            code = f"{prefix}-{Faker().bothify('####')}"
            if code not in existing_codes:
                existing_codes.add(code)
                return code

    def generate_product_reference(self, product_id, created_at):
        """Génère une référence unique pour un produit"""
        timestamp = int(created_at.timestamp())
        data_to_hash = f"PRD{product_id}{timestamp}"
        hash_value = hashlib.sha256(data_to_hash.encode()).hexdigest()[:8].upper()
        return f"PRD-{timestamp}-{product_id}-{hash_value}"

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        # Ensembles séparés pour chaque type de code
        account_codes = set()
        family_codes = set()
        zone_type_codes = set()
        warehouse_codes = set()
        zone_codes = set()
        location_type_codes = set()
        location_codes = set()
        unit_codes = set()
        product_codes = set()
        stock_codes = set()
        sous_zone_codes = set()
        
        # Création des comptes
        accounts = []
        for _ in range(5):
            account = Account.objects.create(
                account_code=self.generate_unique_code('ACC', account_codes),
                account_name=fake.company(),
                account_statuts='ACTIVE',
                description=fake.text(max_nb_chars=200)
            )
            accounts.append(account)
            self.stdout.write(self.style.SUCCESS(f'Compte créé: {account.account_name}'))

        # Création des familles
        families = []
        for account in accounts:
            for _ in range(3):
                family = Family.objects.create(
                    family_code=self.generate_unique_code('FAM', family_codes),
                    family_name=fake.word(),
                    family_description=fake.text(max_nb_chars=200),
                    compte=account,
                    family_status='ACTIVE'
                )
                families.append(family)
                self.stdout.write(self.style.SUCCESS(f'Famille créée: {family.family_name}'))

        # Création des types de zones
        zone_types = []
        for _ in range(3):
            zone_type = ZoneType.objects.create(
                type_code=self.generate_unique_code('ZT', zone_type_codes),
                type_name=fake.word(),
                description=fake.text(max_nb_chars=200),
                status='ACTIVE'
            )
            zone_types.append(zone_type)
            self.stdout.write(self.style.SUCCESS(f'Type de zone créé: {zone_type.type_name}'))

        # Création des entrepôts
        warehouses = []
        for _ in range(3):
            warehouse = Warehouse.objects.create(
                warehouse_code=self.generate_unique_code('WH', warehouse_codes),
                warehouse_name=fake.company(),
                warehouse_type=fake.random_element(elements=('CENTRAL', 'RECEIVING', 'SHIPPING', 'TRANSIT')),
                description=fake.text(max_nb_chars=200),
                status='ACTIVE',
                address=fake.address()
            )
            warehouses.append(warehouse)
            self.stdout.write(self.style.SUCCESS(f'Entrepôt créé: {warehouse.warehouse_name}'))

        # Création des zones
        zones = []
        for warehouse in warehouses:
            for _ in range(3):
                zone = Zone.objects.create(
                    zone_code=self.generate_unique_code('Z', zone_codes),
                    warehouse=warehouse,
                    zone_name=fake.word(),
                    zone_type=fake.random_element(zone_types),
                    description=fake.text(max_nb_chars=200),
                    zone_status='ACTIVE'
                )
                zones.append(zone)
                self.stdout.write(self.style.SUCCESS(f'Zone créée: {zone.zone_name}'))
        # Création des sous zones
        sous_zones = []
        for zone in zones:
            for _ in range(3):
                sous_zone = SousZone.objects.create(
                    sous_zone_code=self.generate_unique_code('SZ', sous_zone_codes),
                    zone=zone,
                    sous_zone_name=fake.word(),
                    description=fake.text(max_nb_chars=200),
                    sous_zone_status='ACTIVE'
                )
                sous_zones.append(sous_zone)
                self.stdout.write(self.style.SUCCESS(f'Zone créée: {zone.zone_name}'))

        # Création des types d'emplacements
        location_types = []
        for _ in range(3):
            location_type = LocationType.objects.create(
                code=self.generate_unique_code('LT', location_type_codes),
                name=fake.word(),
                description=fake.text(max_nb_chars=200),
                is_active=True
            )
            location_types.append(location_type)
            self.stdout.write(self.style.SUCCESS(f'Type d\'emplacement créé: {location_type.name}'))

        # Création des emplacements
        locations = []
        for sous_zone in sous_zones:
            for _ in range(5):
                timestamp = int(datetime.now().timestamp())
                random_str = fake.bothify('????').upper()
                location_reference = f"LOC-{timestamp}-{random_str}"
                
                location = Location.objects.create(
                    location_code=self.generate_unique_code('LOC', location_codes),
                    location_reference=location_reference,
                    sous_zone=sous_zone,
                    location_type=fake.random_element(location_types),
                    capacity=fake.random_int(min=10, max=100),
                    is_active=True,
                    description=fake.text(max_nb_chars=200)
                )
                locations.append(location)
                self.stdout.write(self.style.SUCCESS(f'Emplacement créé: {location.location_code}'))

        # Création des unités de mesure
        units = []
        for unit_name in ['Pièce', 'Kilogramme', 'Litre', 'Mètre']:
            unit = UnitOfMeasure.objects.create(
                code=self.generate_unique_code('UOM', unit_codes),
                name=unit_name,
                description=fake.text(max_nb_chars=200)
            )
            units.append(unit)
            self.stdout.write(self.style.SUCCESS(f'Unité de mesure créée: {unit.name}'))

        # Création des produits
        products = []
        for i in range(50):
            # Générer une référence unique basée sur l'index et le timestamp actuel
            timestamp = int(datetime.now().timestamp())
            data_to_hash = f"PRD{i}{timestamp}"
            hash_value = hashlib.sha256(data_to_hash.encode()).hexdigest()[:8].upper()
            reference = f"PRD-{timestamp}-{i}-{hash_value}"
            
            product = Product.objects.create(
                reference=reference,
                Short_Description=fake.catch_phrase(),
                Barcode=self.generate_unique_code('BAR', product_codes),
                Product_Group=self.generate_unique_code('GRP', product_codes),
                Stock_Unit=fake.random_element(elements=('PCE', 'KG', 'L', 'M')),
                Product_Status='ACTIVE',
                Internal_Product_Code=self.generate_unique_code('PROD', product_codes),
                Product_Family=fake.random_element(families),
                Is_Variant=fake.boolean()
            )
            products.append(product)
            self.stdout.write(self.style.SUCCESS(f'Produit créé: {product.Short_Description}'))

        # Création des stocks
        for product in products:
            for location in locations:
                if fake.boolean():  # 50% de chance de créer un stock
                    stock = Stock.objects.create(
                        reference=self.generate_unique_code('STK', stock_codes),
                        location=location,
                        product=product,
                        quantity_available=fake.random_int(min=0, max=1000),
                        quantity_reserved=fake.random_int(min=0, max=100),
                        quantity_in_transit=fake.random_int(min=0, max=50),
                        quantity_in_receiving=fake.random_int(min=0, max=20),
                        unit_of_measure=fake.random_element(units)
                    )
                    self.stdout.write(self.style.SUCCESS(f'Stock créé pour {product.Short_Description} à {location.location_code}'))

        self.stdout.write(self.style.SUCCESS('Génération des données de test terminée avec succès!')) 