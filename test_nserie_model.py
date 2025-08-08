#!/usr/bin/env python3
"""
Test script pour le modèle NSerie
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.masterdata.models import NSerie, Product, Location, Family, Account
from django.utils import timezone

def test_create_nserie():
    """
    Test de création d'un numéro de série
    """
    print("🧪 Test de création d'un numéro de série")
    print("=" * 50)
    
    try:
        # Créer un compte de test
        account, created = Account.objects.get_or_create(
            reference='ACC-TEST-001',
            defaults={
                'account_name': 'Compte Test',
                'account_statuts': 'ACTIVE',
                'description': 'Compte de test pour les numéros de série'
            }
        )
        
        # Créer une famille de test
        family, created = Family.objects.get_or_create(
            reference='FAM-TEST-001',
            defaults={
                'family_name': 'Famille Test',
                'family_description': 'Famille de test pour les numéros de série',
                'compte': account,
                'family_status': 'ACTIVE'
            }
        )
        
        # Créer un produit de test avec support des numéros de série
        product, created = Product.objects.get_or_create(
            reference='PRD-TEST-001',
            defaults={
                'Internal_Product_Code': 'TEST001',
                'Short_Description': 'Produit Test avec Numéros de Série',
                'Barcode': '1234567890123',
                'Product_Group': 'TEST',
                'Stock_Unit': 'PIECE',
                'Product_Status': 'ACTIVE',
                'Product_Family': family,
                'n_serie': True,  # Activer le support des numéros de série
                'Is_Variant': False,
                'n_lot': False,
                'dlc': False
            }
        )
        
        # Créer un emplacement de test
        from apps.masterdata.models import Zone, SousZone, LocationType
        
        # Créer une zone de test
        zone, created = Zone.objects.get_or_create(
            reference='Z-TEST-001',
            defaults={
                'zone_name': 'Zone Test',
                'zone_status': 'ACTIVE'
            }
        )
        
        # Créer une sous-zone de test
        sous_zone, created = SousZone.objects.get_or_create(
            reference='SZ-TEST-001',
            defaults={
                'sous_zone_name': 'Sous-Zone Test',
                'zone': zone,
                'sous_zone_status': 'ACTIVE'
            }
        )
        
        # Créer un type d'emplacement de test
        location_type, created = LocationType.objects.get_or_create(
            reference='LT-TEST-001',
            defaults={
                'name': 'Type Test',
                'description': 'Type d\'emplacement de test',
                'is_active': True
            }
        )
        
        # Créer un emplacement de test
        location, created = Location.objects.get_or_create(
            reference='LOC-TEST-001',
            defaults={
                'location_reference': 'A-01-01',
                'sous_zone': sous_zone,
                'location_type': location_type,
                'capacity': 100,
                'is_active': True,
                'description': 'Emplacement de test'
            }
        )
        
        # Créer un numéro de série
        nserie = NSerie.objects.create(
            n_serie='NS-001-2024-001',
            product=product,
            status='ACTIVE',
            description='Numéro de série de test',
            date_fabrication=timezone.now().date() - timedelta(days=30),
            date_expiration=timezone.now().date() + timedelta(days=365),
            warranty_end_date=timezone.now().date() + timedelta(days=730),
            location=location,
            stock_quantity=1,
            is_tracked=True,
            notes='Notes de test'
        )
        
        print(f"✅ Numéro de série créé avec succès:")
        print(f"   - ID: {nserie.id}")
        print(f"   - Référence: {nserie.reference}")
        print(f"   - Numéro: {nserie.n_serie}")
        print(f"   - Produit: {nserie.product.Short_Description}")
        print(f"   - Statut: {nserie.status}")
        print(f"   - Emplacement: {nserie.location.location_reference}")
        print(f"   - Quantité: {nserie.stock_quantity}")
        print(f"   - Expiré: {nserie.is_expired}")
        print(f"   - Garantie valide: {nserie.is_warranty_valid}")
        
        return nserie
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {str(e)}")
        return None

def test_nserie_operations(nserie):
    """
    Test des opérations sur le numéro de série
    """
    if not nserie:
        print("❌ Impossible de tester les opérations sans numéro de série")
        return
    
    print("\n🧪 Test des opérations sur le numéro de série")
    print("=" * 50)
    
    try:
        # Test de mise à jour du statut
        print("📝 Test de mise à jour du statut...")
        nserie.status = 'USED'
        nserie.save()
        print(f"   ✅ Statut mis à jour: {nserie.status}")
        
        # Test de déplacement vers un nouvel emplacement
        print("🚚 Test de déplacement...")
        new_location = Location.objects.filter(id__ne=nserie.location.id).first()
        if new_location:
            nserie.location = new_location
            nserie.save()
            print(f"   ✅ Déplacé vers: {nserie.location.location_reference}")
        else:
            print("   ⚠️  Aucun autre emplacement disponible pour le test")
        
        # Test de recherche
        print("🔍 Test de recherche...")
        found_nserie = NSerie.objects.filter(n_serie=nserie.n_serie).first()
        if found_nserie:
            print(f"   ✅ Numéro de série trouvé: {found_nserie.n_serie}")
        
        # Test des propriétés
        print("📊 Test des propriétés...")
        print(f"   - Expiré: {nserie.is_expired}")
        print(f"   - Garantie valide: {nserie.is_warranty_valid}")
        
        # Test des statistiques
        print("📈 Test des statistiques...")
        total_nseries = NSerie.objects.count()
        active_nseries = NSerie.objects.filter(status='ACTIVE').count()
        used_nseries = NSerie.objects.filter(status='USED').count()
        print(f"   - Total: {total_nseries}")
        print(f"   - Actifs: {active_nseries}")
        print(f"   - Utilisés: {used_nseries}")
        
    except Exception as e:
        print(f"❌ Erreur lors des opérations: {str(e)}")

def test_nserie_validation():
    """
    Test de validation des numéros de série
    """
    print("\n🧪 Test de validation des numéros de série")
    print("=" * 50)
    
    try:
        # Créer un produit sans support des numéros de série
        product_no_nserie = Product.objects.create(
            reference='PRD-TEST-NO-NS-001',
            Internal_Product_Code='TESTNO001',
            Short_Description='Produit sans Numéros de Série',
            Barcode='1234567890124',
            Product_Group='TEST',
            Stock_Unit='PIECE',
            Product_Status='ACTIVE',
            Product_Family=Family.objects.first(),
            n_serie=False,  # Désactiver le support des numéros de série
            Is_Variant=False,
            n_lot=False,
            dlc=False
        )
        
        # Tenter de créer un numéro de série pour un produit qui ne le supporte pas
        try:
            invalid_nserie = NSerie.objects.create(
                n_serie='NS-INVALID-001',
                product=product_no_nserie,
                status='ACTIVE'
            )
            print("❌ Erreur: Un numéro de série a été créé pour un produit qui ne le supporte pas")
        except Exception as e:
            print(f"✅ Validation correcte: {str(e)}")
        
        # Test d'unicité du numéro de série
        product_with_nserie = Product.objects.filter(n_serie=True).first()
        if product_with_nserie:
            # Créer un premier numéro de série
            nserie1 = NSerie.objects.create(
                n_serie='NS-DUPLICATE-001',
                product=product_with_nserie,
                status='ACTIVE'
            )
            
            # Tenter de créer un deuxième numéro de série avec le même numéro
            try:
                nserie2 = NSerie.objects.create(
                    n_serie='NS-DUPLICATE-001',
                    product=product_with_nserie,
                    status='ACTIVE'
                )
                print("❌ Erreur: Un numéro de série en double a été créé")
            except Exception as e:
                print(f"✅ Validation d'unicité correcte: {str(e)}")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests de validation: {str(e)}")

def main():
    """
    Fonction principale
    """
    print("🚀 Test du modèle NSerie")
    print("=" * 60)
    
    # Test de création
    nserie = test_create_nserie()
    
    # Test des opérations
    test_nserie_operations(nserie)
    
    # Test de validation
    test_nserie_validation()
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés!")

if __name__ == "__main__":
    main() 