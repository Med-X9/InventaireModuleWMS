#!/usr/bin/env python
"""
Script de debug pour vérifier l'état des assignments pour un comptage spécifique
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting
from django.utils import timezone

def debug_assignment_specific():
    """Debug spécifique pour le comptage CNT10221D46"""
    
    print("=== DEBUG ASSIGNMENT SPÉCIFIQUE ===\n")
    
    # Récupérer le comptage spécifique
    counting = Counting.objects.filter(reference='CNT10221D46').first()
    
    if not counting:
        print("❌ Comptage CNT10221D46 non trouvé")
        return
    
    print(f"1. Comptage CNT10221D46:")
    print(f"   - ID: {counting.id}")
    print(f"   - Référence: {counting.reference}")
    print(f"   - Ordre: {counting.order}")
    print(f"   - Mode: {counting.count_mode}")
    print(f"   - Inventaire: {counting.inventory.reference}")
    
    # Récupérer le job 16
    job = Job.objects.filter(id=16).first()
    
    if not job:
        print("❌ Job 16 non trouvé")
        return
    
    print(f"\n2. Job 16:")
    print(f"   - ID: {job.id}")
    print(f"   - Référence: {job.reference}")
    print(f"   - Statut: {job.status}")
    print(f"   - Inventaire: {job.inventory.reference}")
    
    # Vérifier les assignments pour ce job et ce comptage
    assignment = Assigment.objects.filter(
        job=job,
        counting=counting
    ).first()
    
    print(f"\n3. Assignment pour Job 16 et Comptage CNT10221D46:")
    
    if assignment:
        print(f"   ✅ Assignment trouvé:")
        print(f"   - ID: {assignment.id}")
        print(f"   - Référence: {assignment.reference}")
        print(f"   - Statut: {assignment.status}")
        print(f"   - Session: {assignment.session.username if assignment.session else 'Aucune'}")
        print(f"   - Date début: {assignment.date_start}")
        print(f"   - Date affecté: {assignment.affecte_date}")
        print(f"   - Date prêt: {assignment.pret_date}")
    else:
        print(f"   ❌ Aucun assignment trouvé pour Job 16 et Comptage CNT10221D46")
    
    # Vérifier tous les assignments du job 16
    all_assignments = Assigment.objects.filter(job=job)
    
    print(f"\n4. Tous les assignments du Job 16:")
    print(f"   Total assignments: {all_assignments.count()}")
    
    for assignment in all_assignments:
        print(f"   - Assignment {assignment.id}:")
        print(f"     * Comptage: {assignment.counting.reference} (ordre {assignment.counting.order})")
        print(f"     * Statut: {assignment.status}")
        print(f"     * Session: {assignment.session.username if assignment.session else 'Aucune'}")
        print(f"     * Date début: {assignment.date_start}")
    
    # Vérifier les comptages de l'inventaire
    inventory = job.inventory
    countings = Counting.objects.filter(inventory=inventory).order_by('order')
    
    print(f"\n5. Comptages de l'inventaire {inventory.reference}:")
    for counting in countings:
        print(f"   - Comptage {counting.reference}:")
        print(f"     * Ordre: {counting.order}")
        print(f"     * Mode: {counting.count_mode}")
        
        # Vérifier s'il y a un assignment pour ce comptage
        assignment = Assigment.objects.filter(job=job, counting=counting).first()
        if assignment:
            print(f"     * Assignment: ✅ (statut: {assignment.status}, session: {assignment.session.username if assignment.session else 'Aucune'})")
        else:
            print(f"     * Assignment: ❌ Aucun assignment trouvé")

if __name__ == "__main__":
    debug_assignment_specific() 