from django.core.management.base import BaseCommand
from apps.masterdata.models import Stock
import hashlib

class Command(BaseCommand):
    help = 'Met à jour les références des stocks existants'

    def handle(self, *args, **kwargs):
        stocks = Stock.objects.filter(reference__isnull=True)
        count = 0
        
        for stock in stocks:
            timestamp = int(stock.created_at.timestamp())
            data_to_hash = f"STK{stock.id}{timestamp}"
            hash_value = hashlib.sha256(data_to_hash.encode()).hexdigest()[:8].upper()
            stock.reference = f"STK-{timestamp}-{stock.id}-{hash_value}"
            stock.save()
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Mis à jour {count} références de stocks')) 