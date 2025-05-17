from django.core.management.base import BaseCommand
from apps.masterdata.models import Warehouse, Zone, Location
from django.db.models import Count
from django.db import connection

class Command(BaseCommand):
    help = 'Vérifie les relations entre warehouse, zones et locations'

    def add_arguments(self, parser):
        parser.add_argument('warehouse_id', type=int, help='ID de l\'entrepôt')

    def handle(self, *args, **kwargs):
        warehouse_id = kwargs['warehouse_id']

        # 1. Vérifier l'entrepôt
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            self.stdout.write(f"\nEntrepôt: {warehouse.warehouse_name} (ID: {warehouse.id})")
            self.stdout.write(f"Code: {warehouse.warehouse_code}")
            self.stdout.write(f"Type: {warehouse.warehouse_type}")
            self.stdout.write(f"Status: {warehouse.status}")
        except Warehouse.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"L'entrepôt avec l'ID {warehouse_id} n'existe pas"))
            return

        # 2. Vérifier les zones avec leur requête SQL
        zones_query = Zone.objects.filter(warehouse=warehouse)
        self.stdout.write(f"\nRequête SQL pour les zones:")
        self.stdout.write(str(zones_query.query))
        
        zones = list(zones_query)
        self.stdout.write(f"\nZones trouvées: {len(zones)}")
        
        for zone in zones:
            self.stdout.write(f"\nZone: {zone.zone_name} (ID: {zone.id})")
            self.stdout.write(f"  Code: {zone.zone_code}")
            self.stdout.write(f"  Status: {zone.zone_status}")
            self.stdout.write(f"  Type: {zone.zone_type.type_name if zone.zone_type else 'Non défini'}")
            
            # 3. Vérifier les locations de cette zone avec leur requête SQL
            locations_query = Location.objects.filter(zone=zone)
            self.stdout.write(f"\n  Requête SQL pour les locations de la zone {zone.zone_name}:")
            self.stdout.write(str(locations_query.query))
            
            locations = list(locations_query)
            self.stdout.write(f"  Locations trouvées: {len(locations)}")
            
            for location in locations:
                self.stdout.write(f"    Location: {location.location_code}")
                self.stdout.write(f"      Référence: {location.location_reference}")
                self.stdout.write(f"      Type: {location.location_type.name if location.location_type else 'Non défini'}")
                self.stdout.write(f"      Active: {location.is_active}")

        # 4. Vérifier les locations directement liées à l'entrepôt via les zones
        locations_query = Location.objects.filter(zone__warehouse=warehouse)
        self.stdout.write(f"\nRequête SQL pour toutes les locations de l'entrepôt:")
        self.stdout.write(str(locations_query.query))
        
        locations = list(locations_query)
        self.stdout.write(f"\nTotal des locations pour l'entrepôt: {len(locations)}")
        
        # 5. Vérifier les statistiques
        self.stdout.write("\nStatistiques:")
        self.stdout.write(f"  Nombre total de zones: {len(zones)}")
        self.stdout.write(f"  Nombre total de locations: {len(locations)}")
        self.stdout.write(f"  Moyenne de locations par zone: {len(locations) / len(zones) if zones else 0}")

        # 6. Afficher les requêtes SQL exécutées
        self.stdout.write("\nRequêtes SQL exécutées:")
        for query in connection.queries:
            self.stdout.write(f"\n{query['sql']}")
            self.stdout.write(f"Temps: {query['time']}") 