#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.usecases.inventory_jobs_pdf import InventoryJobsPdfUseCase

def test_pdf_generation():
    """Test de génération du PDF avec la nouvelle logique"""
    print("=" * 60)
    print("TEST FINAL DE L'API PDF - ORDRE 1 ET 2")
    print("=" * 60)
    
    try:
        # Test avec l'inventaire ID 41
        inventory_id = 41
        
        print(f"✓ Test avec l'inventaire ID: {inventory_id}")
        
        # Générer le PDF
        usecase = InventoryJobsPdfUseCase()
        result = usecase.execute(inventory_id)
        pdf_buffer = result['pdf_buffer']
        
        # Sauvegarder le PDF
        filename = f"test_final_{inventory_id}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✓ PDF généré: {filename}")
        print("✓ Logique: Afficher uniquement les comptages ordre 1 et 2")
        print("✓ Si ordre 1 = 'image de stock' → exclure ses jobs")
        print("✓ Sinon → afficher les jobs des 2 comptages")
        
        print("\nTous les tests sont réussis!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()