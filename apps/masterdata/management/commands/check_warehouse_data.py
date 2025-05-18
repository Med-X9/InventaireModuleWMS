from django.core.management.base import BaseCommand
from apps.masterdata.models import Warehouse, Zone, Location

class Command(BaseCommand):
    help = 'Vérifie les données des entrepôts, zones et locations'

    def handle(self, *args, **kwargs):
        # Vérifier les entrepôts
        warehouses = Warehouse.objects.all()
        self.stdout.write(f"Nombre total d'entrepôts: {warehouses.count()}")
        
        for warehouse in warehouses:
            self.stdout.write(f"\nEntrepôt: {warehouse.warehouse_name} (ID: {warehouse.id})")
            
            # Vérifier les zones de cet entrepôt
            zones = Zone.objects.filter(warehouse=warehouse)
            self.stdout.write(f"  Nombre de zones: {zones.count()}")
            
            for zone in zones:
                self.stdout.write(f"  Zone: {zone.zone_name} (ID: {zone.id})")
                
                # Vérifier les locations de cette zone
                locations = Location.objects.filter(zone=zone)
                self.stdout.write(f"    Nombre de locations: {locations.count()}")
                
                for location in locations:
                    self.stdout.write(f"    Location: {location.location_code} (ID: {location.id})") 