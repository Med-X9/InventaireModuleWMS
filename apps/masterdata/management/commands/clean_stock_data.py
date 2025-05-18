from django.core.management.base import BaseCommand
from apps.masterdata.models import Stock

class Command(BaseCommand):
    help = 'Supprime les enregistrements de stock sans référence'

    def handle(self, *args, **kwargs):
        # Supprimer les stocks sans référence
        stocks_to_delete = Stock.objects.filter(reference__isnull=True)
        count = stocks_to_delete.count()
        stocks_to_delete.delete()
        
        self.stdout.write(self.style.SUCCESS(f'Supprimé {count} enregistrements de stock sans référence')) 