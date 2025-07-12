#!/usr/bin/env python
"""
Script pour créer des données de test
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Inventory, Counting
from apps.masterdata.models import Warehouse
from django.utils import timezone

def create_test_data():
    """Crée des données de test"""
    
    # Créer un entrepôt de test
    warehouse, created = Warehouse.objects.get_or_create(
        reference='WH-TEST',
        defaults={
            'warehouse_name': 'Entrepôt de test',
            'warehouse_type': 'CENTRAL',
            'status': 'ACTIVE'
        }
    )
    
    if created:
        print(f"Entrepôt créé: {warehouse.warehouse_name}")
    
    # Créer un inventaire de test
    inventory, created = Inventory.objects.get_or_create(
        reference='INV-TEST',
        defaults={
            'label': 'Inventaire de test',
            'date': timezone.now(),
            'status': 'EN PREPARATION',
            'inventory_type': 'GENERAL',
            'warehouse': warehouse
        }
    )
    
    if created:
        print(f"Inventaire créé: {inventory.label}")
    
    # Créer des comptages de test
    for order in [1, 2]:
        counting, created = Counting.objects.get_or_create(
            reference=f'CNT-TEST-{order}',
            defaults={
                'order': order,
                'count_mode': 'en vrac',
                'inventory': inventory
            }
        )
        
        if created:
            print(f"Comptage créé: {counting.reference} (ordre: {counting.order})")
    
    # Créer des jobs de test
    for i in range(1, 4):
        job, created = Job.objects.get_or_create(
            reference=f'JOB-TEST-{i}',
            defaults={
                'status': 'EN ATTENTE',
                'warehouse': warehouse,
                'inventory': inventory,
                'en_attente_date': timezone.now()
            }
        )
        
        if created:
            print(f"Job créé: {job.reference} (statut: {job.status})")
    
    print("Données de test créées avec succès!")

if __name__ == "__main__":
    create_test_data() 