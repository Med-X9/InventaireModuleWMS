from django.core.management.base import BaseCommand
from apps.masterdata.models import Warehouse, Zone, ZoneType, Location, LocationType
from faker import Faker
import hashlib
from datetime import datetime

class Command(BaseCommand):
    help = 'Ajoute des zones et locations de test pour un entrepôt spécifique'

    def add_arguments(self, parser):
        parser.add_argument('warehouse_id', type=int, help='ID de l\'entrepôt')

    def handle(self, *args, **kwargs):
        warehouse_id = kwargs['warehouse_id']
        fake = Faker()

        # 1. Vérifier si l'entrepôt existe
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            self.stdout.write(f"Entrepôt trouvé: {warehouse.warehouse_name}")
        except Warehouse.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"L'entrepôt avec l'ID {warehouse_id} n'existe pas"))
            return

        # 2. Créer un type de zone si nécessaire
        zone_type, created = ZoneType.objects.get_or_create(
            type_code='ZT-TEST',
            defaults={
                'type_name': 'Zone de test',
                'description': 'Zone créée pour les tests',
                'status': 'ACTIVE'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Type de zone créé: {zone_type.type_name}"))

        # 3. Créer des zones pour l'entrepôt
        zones = []
        for i in range(3):  # Créer 3 zones
            zone = Zone.objects.create(
                zone_code=f"Z-TEST-{i+1}",
                warehouse=warehouse,
                zone_name=f"Zone de test {i+1}",
                zone_type=zone_type,
                description=f"Zone de test {i+1} pour {warehouse.warehouse_name}",
                zone_status='ACTIVE'
            )
            zones.append(zone)
            self.stdout.write(self.style.SUCCESS(f"Zone créée: {zone.zone_name}"))

        # 4. Créer un type de location si nécessaire
        location_type, created = LocationType.objects.get_or_create(
            code='LT-TEST',
            defaults={
                'name': 'Location de test',
                'description': 'Location créée pour les tests',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Type de location créé: {location_type.name}"))

        # 5. Créer des locations pour chaque zone
        for zone in zones:
            for j in range(5):  # 5 locations par zone
                timestamp = int(datetime.now().timestamp())
                random_str = fake.bothify('????').upper()
                location_reference = f"LOC-{timestamp}-{random_str}"
                
                location = Location.objects.create(
                    location_code=f"LOC-TEST-{zone.id}-{j+1}",
                    location_reference=location_reference,
                    zone=zone,
                    location_type=location_type,
                    capacity=100,
                    is_active=True,
                    description=f"Location de test {j+1} dans {zone.zone_name}"
                )
                self.stdout.write(self.style.SUCCESS(f"Location créée: {location.location_code}"))

        self.stdout.write(self.style.SUCCESS(f"Données de test ajoutées avec succès pour l'entrepôt {warehouse.warehouse_name}")) 