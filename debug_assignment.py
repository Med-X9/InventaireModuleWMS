#!/usr/bin/env python
"""
Script de debug pour analyser le problème d'affectation
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting, Inventory
from apps.inventory.services.assignment_service import AssignmentService
from apps.masterdata.models import Warehouse
from django.utils import timezone

def debug_assignment():
    """Debug le processus d'affectation"""
    
    print("=== DEBUG AFFECTATION ===")
    
    # 1. Vérifier les jobs existants
    jobs = Job.objects.all()
    print(f"\n1. Jobs existants ({jobs.count()}):")
    for job in jobs:
        print(f"   - {job.reference}: {job.status}")
    
    # 2. Vérifier les inventaires
    inventories = Inventory.objects.all()
    print(f"\n2. Inventaires existants ({inventories.count()}):")
    for inv in inventories:
        print(f"   - {inv.reference}: {inv.label}")
    
    # 3. Vérifier les comptages
    countings = Counting.objects.all()
    print(f"\n3. Comptages existants ({countings.count()}):")
    for cnt in countings:
        print(f"   - {cnt.reference}: ordre {cnt.order}, mode {cnt.count_mode}")
    
    # 4. Vérifier les affectations existantes
    assignments = Assigment.objects.all()
    print(f"\n4. Affectations existantes ({assignments.count()}):")
    for ass in assignments:
        session_info = f"session {ass.session.id}" if ass.session else "pas de session"
        print(f"   - {ass.reference}: job {ass.job.reference}, counting {ass.counting.reference}, {session_info}, statut {ass.status}")
    
    # 5. Tester la logique should_update_job_status_to_affecte
    if jobs.exists():
        job = jobs.first()
        inventory_id = job.inventory.id
        print(f"\n5. Test de should_update_job_status_to_affecte pour job {job.reference}:")
        
        service = AssignmentService()
        should_update = service.should_update_job_status_to_affecte(job.id, inventory_id)
        print(f"   should_update = {should_update}")
        
        # Détails de la vérification
        countings = Counting.objects.filter(inventory_id=inventory_id, order__in=[1, 2])
        print(f"   Comptages trouvés: {countings.count()}")
        for cnt in countings:
            print(f"     - {cnt.reference}: ordre {cnt.order}")
        
        assignments_with_session = Assigment.objects.filter(
            job_id=job.id,
            counting__in=countings,
            session__isnull=False
        ).values_list('counting__order', flat=True).distinct()
        
        print(f"   Affectations avec session: {list(assignments_with_session)}")

if __name__ == "__main__":
    debug_assignment() 