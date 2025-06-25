from django.core.management.base import BaseCommand
from faker import Faker
from apps.masterdata.models import (
    Account, Warehouse, Zone, ZoneType, Location, LocationType,
    Product, Family, UnitOfMeasure, Stock, SousZone
)
import hashlib
from datetime import datetime

class Command(BaseCommand):
    help = 'Génère des données de test pour les modèles de masterdata'

    def clean_database(self):
        """Nettoie toutes les données existantes"""
        self.stdout.write('Nettoyage des données existantes...')
        # Supprimer dans l'ordre inverse des dépendances
        Stock.objects.all().delete()
        Product.objects.all().delete()
        Location.objects.all().delete()
        SousZone.objects.all().delete()
        Zone.objects.all().delete()
        Warehouse.objects.all().delete()
        ZoneType.objects.all().delete()
        Family.objects.all().delete()
        Account.objects.all().delete()
        LocationType.objects.all().delete()
        UnitOfMeasure.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Données existantes supprimées avec succès!'))

    def generate_unique_code(self, prefix, counter):
        """Génère un code unique avec le préfixe donné et un compteur"""
        return f"{prefix}-{counter:04d}"

    def generate_product_reference(self, counter):
        """Génère une référence unique pour un produit"""
        return f"PRD-{counter:04d}"

    def handle(self, *args, **kwargs):
        # Nettoyer la base de données avant de générer les nouvelles données
        self.clean_database()
        
        fake = Faker()
        
        # Compteurs pour chaque type de référence
        account_counter = 1
        family_counter = 1
        zone_type_counter = 1
        warehouse_counter = 1
        zone_counter = 1
        location_type_counter = 1
        location_counter = 1
        unit_counter = 1
        product_counter = 1
        stock_counter = 1
        sous_zone_counter = 1
        
        # Création des comptes
        accounts = []
        for _ in range(5):
            account = Account.objects.create(
                reference=self.generate_unique_code('ACC', account_counter),
                account_name=fake.company(),
                account_statuts='ACTIVE',
                description=fake.text(max_nb_chars=200)
            )
            accounts.append(account)
            account_counter += 1
            self.stdout.write(self.style.SUCCESS(f'Compte créé: {account.account_name}'))

        # Création des familles
        families = []
        for account in accounts:
            for _ in range(3):
                family = Family.objects.create(
                    reference=self.generate_unique_code('FAM', family_counter),
                    family_name=fake.word(),
                    family_description=fake.text(max_nb_chars=200),
                    compte=account,
                    family_status='ACTIVE'
                )
                families.append(family)
                family_counter += 1
                self.stdout.write(self.style.SUCCESS(f'Famille créée: {family.family_name}'))

        # Création des types de zones
        zone_types = []
        for _ in range(3):
            zone_type = ZoneType.objects.create(
                reference=self.generate_unique_code('ZT', zone_type_counter),
                type_name=fake.word(),
                description=fake.text(max_nb_chars=200),
                status='ACTIVE'
            )
            zone_types.append(zone_type)
            zone_type_counter += 1
            self.stdout.write(self.style.SUCCESS(f'Type de zone créé: {zone_type.type_name}'))

        # Création des entrepôts
        warehouses = []
        for _ in range(3):
            warehouse = Warehouse.objects.create(
                reference=self.generate_unique_code('WH', warehouse_counter),
                warehouse_name=fake.company(),
                warehouse_type=fake.random_element(elements=('CENTRAL', 'RECEIVING', 'SHIPPING', 'TRANSIT')),
                description=fake.text(max_nb_chars=200),
                status='ACTIVE',
                address=fake.address()
            )
            warehouses.append(warehouse)
            warehouse_counter += 1
            self.stdout.write(self.style.SUCCESS(f'Entrepôt créé: {warehouse.warehouse_name}'))

        # Création des zones
        zones = []
        for warehouse in warehouses:
            for _ in range(3):
                zone = Zone.objects.create(
                    reference=self.generate_unique_code('Z', zone_counter),
                    warehouse=warehouse,
                    zone_name=fake.word(),
                    zone_type=fake.random_element(zone_types),
                    description=fake.text(max_nb_chars=200),
                    zone_status='ACTIVE'
                )
                zones.append(zone)
                zone_counter += 1
                self.stdout.write(self.style.SUCCESS(f'Zone créée: {zone.zone_name}'))

        # Création des sous zones
        sous_zones = []
        for zone in zones:
            for _ in range(3):
                sous_zone = SousZone.objects.create(
                    reference=self.generate_unique_code('SZ', sous_zone_counter),
                    sous_zone_name=fake.word(),
                    zone=zone,
                    description=fake.text(max_nb_chars=200),
                    sous_zone_status='ACTIVE'
                )
                sous_zones.append(sous_zone)
                sous_zone_counter += 1
                self.stdout.write(self.style.SUCCESS(f'Sous-zone créée: {sous_zone.sous_zone_name}'))

        # Création des types d'emplacements
        location_types = []
        for _ in range(3):
            location_type = LocationType.objects.create(
                reference=self.generate_unique_code('LT', location_type_counter),
                name=fake.word(),
                description=fake.text(max_nb_chars=200),
                is_active=True
            )
            location_types.append(location_type)
            location_type_counter += 1
            self.stdout.write(self.style.SUCCESS(f'Type d\'emplacement créé: {location_type.name}'))

        # Création des emplacements
        locations = []
        for sous_zone in sous_zones:
            for _ in range(5):
                location = Location.objects.create(
                    reference=self.generate_unique_code('LOC', location_counter),
                    location_reference=f"REF-{location_counter:04d}",
                    sous_zone=sous_zone,
                    location_type=fake.random_element(location_types),
                    capacity=fake.random_int(min=10, max=100),
                    is_active=True,
                    description=fake.text(max_nb_chars=200)
                )
                locations.append(location)
                location_counter += 1
                self.stdout.write(self.style.SUCCESS(f'Emplacement créé: {location.reference}'))

        # Création des unités de mesure
        units = []
        for unit_name in ['Pièce', 'Kilogramme', 'Litre', 'Mètre']:
            unit = UnitOfMeasure.objects.create(
                reference=self.generate_unique_code('UOM', unit_counter),
                name=unit_name,
                description=fake.text(max_nb_chars=200)
            )
            units.append(unit)
            unit_counter += 1
            self.stdout.write(self.style.SUCCESS(f'Unité de mesure créée: {unit.name}'))

        # Création des produits
        products = []
        for i in range(50):
            product = Product.objects.create(
                reference=self.generate_product_reference(product_counter),
                Short_Description=fake.catch_phrase(),
                Barcode=f"BAR-{product_counter:04d}",
                Product_Group=f"GRP-{product_counter:03d}",
                Stock_Unit=fake.random_element(elements=('PCE', 'KG', 'L', 'M')),
                Product_Status='ACTIVE',
                Internal_Product_Code=f"INT-{product_counter:04d}",
                Product_Family=fake.random_element(families),
                Is_Variant=fake.boolean()
            )
            products.append(product)
            product_counter += 1
            self.stdout.write(self.style.SUCCESS(f'Produit créé: {product.Short_Description}'))

        # Création des stocks
        # for product in products:
        #     for location in locations:
        #         if fake.boolean():  # 50% de chance de créer un stock
        #             stock = Stock.objects.create(
        #                 reference=self.generate_unique_code('STK', stock_counter),
        #                 location=location,
        #                 product=product,
        #                 quantity_available=fake.random_int(min=0, max=1000),
        #                 quantity_reserved=fake.random_int(min=0, max=100),
        #                 quantity_in_transit=fake.random_int(min=0, max=50),
        #                 quantity_in_receiving=fake.random_int(min=0, max=20),
        #                 unit_of_measure=fake.random_element(units)
        #             )
        #             stock_counter += 1
        #             self.stdout.write(self.style.SUCCESS(f'Stock créé pour {product.Short_Description} à {location.reference}'))

        self.stdout.write(self.style.SUCCESS('Génération des données de test terminée avec succès!')) 