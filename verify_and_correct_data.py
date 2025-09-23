#!/usr/bin/env python3
"""
Script pour vérifier et corriger les données avant de les envoyer à l'API.
"""

import os
import sys
import django
import json

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.masterdata.models import Location, Product
from apps.inventory.models import Counting, Assigment, JobDetail

def verify_and_correct_data():
    """Vérifie et corrige les données pour qu'elles soient valides."""
    
    # Données originales
    original_data = [
        {
            "counting_id": 17,
            "location_id": 3930,
            "quantity_inventoried": 10,
            "assignment_id": 55,
            "product_id": 13118,
            "dlc": "2024-12-31",
            "n_lot": "LOT123",
            "numeros_serie": [{"n_serie": "1234trew"}]
        },
        {
            "counting_id": 16,
            "location_id": 3596,
            "quantity_inventoried": 10,
            "assignment_id": 52,
            "product_id": 11329,
            "dlc": "2024-12-31",
            "n_lot": "LOT001",
            "numeros_serie": [{"n_serie": "NS001"}]
        },
        {
            "counting_id": 3,
            "location_id": 3597,
            "quantity_inventoried": 5,
            "assignment_id": 53,
            "product_id": 11330
        },
        {
            "counting_id": 4,
            "location_id": 3942,
            "quantity_inventoried": 3,
            "assignment_id": 56,
            "product_id": 11331,
            "numeros_serie": [
                {"n_serie": "NS002"},
                {"n_serie": "NS003"}
            ]
        },
        {
            "counting_id": 5,
            "location_id": 3598,
            "quantity_inventoried": 8,
            "assignment_id": 33,
            "product_id": 11332,
            "dlc": "2024-11-30",
            "n_lot": "LOT002"
        },
        {
            "counting_id": 6,
            "location_id": 3599,
            "quantity_inventoried": 12,
            "assignment_id": 54,
            "product_id": 11333
        },
        {
            "counting_id": 7,
            "location_id": 3600,
            "quantity_inventoried": 15,
            "assignment_id": 34,
            "product_id": 11334,
            "dlc": "2025-01-15",
            "n_lot": "LOT003"
        },
        {
            "counting_id": 8,
            "location_id": 3601,
            "quantity_inventoried": 7,
            "assignment_id": 55,
            "product_id": 11335,
            "numeros_serie": [{"n_serie": "NS004"}]
        },
        {
            "counting_id": 9,
            "location_id": 3602,
            "quantity_inventoried": 20,
            "assignment_id": 52,
            "product_id": 11336,
            "dlc": "2024-10-31"
        },
        {
            "counting_id": 10,
            "location_id": 3603,
            "quantity_inventoried": 6,
            "assignment_id": 53,
            "product_id": 11337,
            "n_lot": "LOT004",
            "numeros_serie": [
                {"n_serie": "NS005"},
                {"n_serie": "NS006"}
            ]
        },
        {
            "counting_id": 11,
            "location_id": 3604,
            "quantity_inventoried": 9,
            "assignment_id": 56,
            "product_id": 11338,
            "dlc": "2024-12-31",
            "n_lot": "LOT005"
        }
    ]
    
    print("🔍 VÉRIFICATION ET CORRECTION DES DONNÉES")
    print("=" * 60)
    
    corrected_data = []
    errors = []
    
    for i, record in enumerate(original_data):
        print(f"\n📝 Enregistrement {i}:")
        
        # Vérifier le comptage
        try:
            counting = Counting.objects.get(id=record['counting_id'])
            print(f"  ✅ Counting {record['counting_id']}: {counting.reference}")
        except Counting.DoesNotExist:
            print(f"  ❌ Counting {record['counting_id']}: NON TROUVÉ")
            errors.append(f"Index {i}: Counting {record['counting_id']} non trouvé")
            continue
        
        # Vérifier l'emplacement
        try:
            location = Location.objects.get(id=record['location_id'])
            print(f"  ✅ Location {record['location_id']}: {location.reference}")
        except Location.DoesNotExist:
            print(f"  ❌ Location {record['location_id']}: NON TROUVÉ")
            errors.append(f"Index {i}: Location {record['location_id']} non trouvé")
            continue
        
        # Vérifier le produit
        try:
            product = Product.objects.get(id=record['product_id'])
            print(f"  ✅ Product {record['product_id']}: {product.reference}")
        except Product.DoesNotExist:
            print(f"  ❌ Product {record['product_id']}: NON TROUVÉ")
            errors.append(f"Index {i}: Product {record['product_id']} non trouvé")
            continue
        
        # Vérifier l'assignment
        try:
            assignment = Assigment.objects.get(id=record['assignment_id'])
            print(f"  ✅ Assignment {record['assignment_id']}: {assignment.reference}")
        except Assigment.DoesNotExist:
            print(f"  ❌ Assignment {record['assignment_id']}: NON TROUVÉ")
            errors.append(f"Index {i}: Assignment {record['assignment_id']} non trouvé")
            continue
        
        # Vérifier le JobDetail
        try:
            job_detail = JobDetail.objects.filter(
                job=assignment.job, 
                counting=counting
            ).first()
            
            if job_detail:
                print(f"  ✅ JobDetail: {job_detail.reference}")
                corrected_data.append(record)
            else:
                print(f"  ❌ JobDetail: NON TROUVÉ pour assignment {record['assignment_id']} et counting {record['counting_id']}")
                errors.append(f"Index {i}: JobDetail non trouvé pour assignment {record['assignment_id']} et counting {record['counting_id']}")
                
                # Essayer de trouver un JobDetail valide pour cet assignment
                alternative_job_details = JobDetail.objects.filter(
                    job=assignment.job
                ).first()
                
                if alternative_job_details:
                    print(f"  🔄 Alternative trouvée: JobDetail {alternative_job_details.reference} pour counting {alternative_job_details.counting.id}")
                    corrected_record = record.copy()
                    corrected_record['counting_id'] = alternative_job_details.counting.id
                    corrected_data.append(corrected_record)
                    print(f"  ✅ Correction appliquée: counting_id changé de {record['counting_id']} à {alternative_job_details.counting.id}")
                else:
                    print(f"  ❌ Aucun JobDetail trouvé pour cet assignment")
                
        except Exception as e:
            print(f"  ❌ Erreur lors de la vérification du JobDetail: {str(e)}")
            errors.append(f"Index {i}: Erreur JobDetail - {str(e)}")
    
    print(f"\n📊 RÉSULTATS:")
    print(f"  - Total original: {len(original_data)}")
    print(f"  - Corrigés: {len(corrected_data)}")
    print(f"  - Erreurs: {len(errors)}")
    
    if errors:
        print(f"\n❌ ERREURS DÉTECTÉES:")
        for error in errors:
            print(f"  - {error}")
    
    # Générer les données corrigées
    if corrected_data:
        print(f"\n✅ DONNÉES CORRIGÉES POUR L'API:")
        
        # Version pour POST (création)
        post_data = {
            "batch": True,
            "data": corrected_data
        }
        
        # Version pour PUT (validation)
        put_data = {
            "data": corrected_data
        }
        
        # Sauvegarder les fichiers
        with open('corrected_data_post.json', 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        with open('corrected_data_put.json', 'w', encoding='utf-8') as f:
            json.dump(put_data, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Fichiers créés:")
        print(f"  - corrected_data_post.json (pour POST)")
        print(f"  - corrected_data_put.json (pour PUT)")
        
        # Afficher un exemple
        print(f"\n📝 EXEMPLE DE DONNÉES CORRIGÉES:")
        print(json.dumps(corrected_data[0], indent=2, ensure_ascii=False))
        
        return corrected_data
    else:
        print(f"\n❌ Aucune donnée valide trouvée")
        return []

def show_available_data():
    """Affiche les données disponibles dans la base."""
    
    print(f"\n📋 DONNÉES DISPONIBLES DANS LA BASE:")
    print("=" * 50)
    
    # Compages
    print(f"\n📊 COMPTAGES:")
    countings = Counting.objects.all()[:10]
    for c in countings:
        print(f"  - ID: {c.id}, Référence: {c.reference}, Mode: {c.count_mode}")
    
    # Assignments
    print(f"\n👤 ASSIGNMENTS:")
    assignments = Assigment.objects.all()[:10]
    for a in assignments:
        print(f"  - ID: {a.id}, Référence: {a.reference}, Job: {a.job.reference}")
    
    # JobDetails
    print(f"\n📋 JOB DETAILS:")
    job_details = JobDetail.objects.select_related('job', 'counting').all()[:10]
    for jd in job_details:
        print(f"  - ID: {jd.id}, Job: {jd.job.reference}, Counting: {jd.counting.reference}")
    
    # Locations
    print(f"\n📍 LOCATIONS:")
    locations = Location.objects.all()[:10]
    for l in locations:
        print(f"  - ID: {l.id}, Référence: {l.reference}")
    
    # Products
    print(f"\n📦 PRODUCTS:")
    products = Product.objects.all()[:10]
    for p in products:
        print(f"  - ID: {p.id}, Référence: {p.reference}")

if __name__ == "__main__":
    show_available_data()
    corrected_data = verify_and_correct_data()
    
    if corrected_data:
        print(f"\n🎉 Données corrigées avec succès !")
        print(f"Vous pouvez maintenant utiliser les fichiers JSON générés pour tester l'API.")
    else:
        print(f"\n❌ Impossible de corriger les données.")
        print(f"Vérifiez que votre base de données contient les enregistrements nécessaires.")
