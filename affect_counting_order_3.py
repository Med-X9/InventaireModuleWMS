#!/usr/bin/env python
"""
Script pour affecter le comptage d'ordre 3 au job 16
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, Assigment, Counting
from apps.inventory.services.assignment_service import AssignmentService
from django.utils import timezone

def affect_counting_order_3():
    """Affecte le comptage d'ordre 3 au job 16"""
    
    print("=== AFFECTATION COMPTAGE ORDRE 3 ===\n")
    
    # Récupérer le job 16
    job = Job.objects.filter(id=16).first()
    
    if not job:
        print("❌ Job 16 non trouvé")
        return
    
    print(f"1. Job 16:")
    print(f"   - ID: {job.id}")
    print(f"   - Référence: {job.reference}")
    print(f"   - Statut: {job.status}")
    print(f"   - Inventaire: {job.inventory.reference}")
    
    # Récupérer le comptage d'ordre 3
    counting = Counting.objects.filter(
        inventory=job.inventory,
        order=3
    ).first()
    
    if not counting:
        print("❌ Comptage d'ordre 3 non trouvé pour cet inventaire")
        return
    
    print(f"\n2. Comptage d'ordre 3:")
    print(f"   - ID: {counting.id}")
    print(f"   - Référence: {counting.reference}")
    print(f"   - Ordre: {counting.order}")
    print(f"   - Mode: {counting.count_mode}")
    
    # Vérifier s'il y a déjà une affectation
    existing_assignment = Assigment.objects.filter(
        job=job,
        counting=counting
    ).first()
    
    if existing_assignment:
        print(f"\n3. Assignment existant trouvé:")
        print(f"   - ID: {existing_assignment.id}")
        print(f"   - Statut: {existing_assignment.status}")
        print(f"   - Session: {existing_assignment.session.username if existing_assignment.session else 'Aucune'}")
        return
    
    # Créer une nouvelle affectation
    print(f"\n3. Création d'une nouvelle affectation...")
    
    # Créer une session de test (ou utiliser une existante)
    from apps.users.models import UserApp
    session = UserApp.objects.filter(type='Mobile').first()
    
    if not session:
        print("❌ Aucune session mobile trouvée")
        return
    
    print(f"   Session utilisée: {session.username}")
    
    # Créer l'affectation
    assignment = Assigment.objects.create(
        job=job,
        counting=counting,
        session=session,
        status='AFFECTE',
        date_start=timezone.now(),
        affecte_date=timezone.now()
    )
    
    print(f"\n4. Assignment créé avec succès:")
    print(f"   - ID: {assignment.id}")
    print(f"   - Référence: {assignment.reference}")
    print(f"   - Statut: {assignment.status}")
    print(f"   - Session: {assignment.session.username}")
    print(f"   - Date début: {assignment.date_start}")
    print(f"   - Date affecté: {assignment.affecte_date}")
    
    # Vérifier tous les assignments du job
    all_assignments = Assigment.objects.filter(job=job)
    print(f"\n5. Tous les assignments du Job 16 ({all_assignments.count()}):")
    
    for ass in all_assignments:
        print(f"   - {ass.reference}: comptage {ass.counting.reference} (ordre {ass.counting.order})")
        print(f"     * Statut: {ass.status}")
        print(f"     * Session: {ass.session.username if ass.session else 'Aucune'}")
    
    print(f"\n✅ Le job 16 devrait maintenant pouvoir être marqué comme PRET !")

if __name__ == "__main__":
    affect_counting_order_3() 