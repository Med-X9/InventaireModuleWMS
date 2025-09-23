#!/usr/bin/env python3
"""
Script pour vérifier la base de données et générer des données de test.
"""

import os
import sys
import django
import json

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.masterdata.models import Location, Product, Account
from apps.inventory.models import Counting, Assigment
from apps.users.models import UserApp

def check_database():
    """Vérifie la base de données et affiche les enregistrements disponibles."""
    
    print("🔍 VÉRIFICATION DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    # Vérifier les comptages
    print("\n📊 COMPTAGES:")
    countings = Counting.objects.all()
    if countings.exists():
        for counting in countings[:10]:
            print(f"  - ID: {counting.id}, Référence: {counting.reference}, Mode: {counting.count_mode}")
        if countings.count() > 10:
            print(f"  ... et {countings.count() - 10} autres")
    else:
        print("  ❌ Aucun comptage trouvé")
    
    # Vérifier les emplacements
    print("\n📍 EMPLACEMENTS:")
    locations = Location.objects.all()
    if locations.exists():
        for location in locations[:10]:
            print(f"  - ID: {location.id}, Référence: {location.reference}, Description: {location.description or 'N/A'}")
        if locations.count() > 10:
            print(f"  ... et {locations.count() - 10} autres")
    else:
        print("  ❌ Aucun emplacement trouvé")
    
    # Vérifier les produits
    print("\n📦 PRODUITS:")
    products = Product.objects.all()
    if products.exists():
        for product in products[:10]:
            print(f"  - ID: {product.id}, Référence: {product.reference}, Description: {product.Short_Description}")
        if products.count() > 10:
            print(f"  ... et {products.count() - 10} autres")
    else:
        print("  ❌ Aucun produit trouvé")
    
    # Vérifier les assignments
    print("\n👤 ASSIGNMENTS:")
    assignments = Assigment.objects.all()
    if assignments.exists():
        for assignment in assignments[:10]:
            user_name = assignment.session.username if assignment.session else "N/A"
            print(f"  - ID: {assignment.id}, Utilisateur: {user_name}, Statut: {assignment.status}")
        if assignments.count() > 10:
            print(f"  ... et {assignments.count() - 10} autres")
    else:
        print("  ❌ Aucun assignment trouvé")
    
    # Vérifier les utilisateurs
    print("\n👥 UTILISATEURS:")
    users = UserApp.objects.all()
    if users.exists():
        for user in users[:10]:
            print(f"  - ID: {user.id}, Username: {user.username}, Type: {user.type}")
        if users.count() > 10:
            print(f"  ... et {users.count() - 10} autres")
    else:
        print("  ❌ Aucun utilisateur trouvé")
    
    return {
        'countings': countings,
        'locations': locations,
        'products': products,
        'assignments': assignments,
        'users': users
    }

def generate_test_data(count=500):
    """Génère des données de test pour le nombre spécifié."""
    
    print(f"\n🎯 GÉNÉRATION DE DONNÉES DE TEST POUR {count} LIGNES")
    print("=" * 50)
    
    # Récupérer les données de la base
    data = check_database()
    
    # Vérifier qu'on a assez de données
    if not data['countings'].exists():
        print("❌ Erreur: Aucun comptage trouvé. Créez d'abord un comptage.")
        return None
    
    if not data['locations'].exists():
        print("❌ Erreur: Aucun emplacement trouvé. Créez d'abord des emplacements.")
        return None
    
    if not data['products'].exists():
        print("❌ Erreur: Aucun produit trouvé. Créez d'abord des produits.")
        return None
    
    if not data['assignments'].exists():
        print("❌ Erreur: Aucun assignment trouvé. Créez d'abord des assignments.")
        return None
    
    # Convertir en listes pour faciliter l'accès
    countings_list = list(data['countings'])
    locations_list = list(data['locations'])
    products_list = list(data['products'])
    assignments_list = list(data['assignments'])
    
    # Générer les données de test
    test_data = []
    
    for i in range(count):
        # Sélectionner des données aléatoires
        counting = countings_list[i % len(countings_list)]
        location = locations_list[i % len(locations_list)]
        product = products_list[i % len(products_list)]
        assignment = assignments_list[i % len(assignments_list)]
        
        # Créer l'enregistrement de test
        record = {
            "counting_id": counting.id,
            "location_id": location.id,
            "quantity_inventoried": (i % 50) + 1,  # Quantité entre 1 et 50
            "assignment_id": assignment.id,
            "product_id": product.id,
        }
        
        # Ajouter des champs optionnels selon l'index
        if i % 3 == 0:  # Un tiers avec DLC
            record["dlc"] = "2024-12-31"
        
        if i % 4 == 0:  # Un quart avec numéro de lot
            record["n_lot"] = f"LOT{i:06d}"
        
        if i % 5 == 0:  # Un cinquième avec numéros de série
            record["numeros_serie"] = [
                {"n_serie": f"NS{i:06d}A"},
                {"n_serie": f"NS{i:06d}B"}
            ]
        
        test_data.append(record)
    
    print(f"✅ {len(test_data)} enregistrements de test générés")
    
    return test_data

def save_test_data_to_file(test_data, filename="test_data_500_lines.json"):
    """Sauvegarde les données de test dans un fichier JSON."""
    
    import json
    
    # Structure pour Postman
    postman_data = {
        "batch": True,
        "data": test_data
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(postman_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Données sauvegardées dans {filename}")
    
    return filename

def main():
    """Fonction principale."""
    
    # Vérifier la base de données
    data = check_database()
    
    # Générer des données de test
    test_data = generate_test_data(500)
    
    if test_data:
        # Sauvegarder dans un fichier
        filename = save_test_data_to_file(test_data)
        
        print(f"\n🎉 SUCCÈS!")
        print(f"📁 Fichier créé: {filename}")
        print(f"📊 Nombre d'enregistrements: {len(test_data)}")
        print(f"\n📋 PROCHAINES ÉTAPES:")
        print(f"1. Importez le fichier {filename} dans Postman")
        print(f"2. Utilisez l'endpoint POST /mobile/api/counting-detail/")
        print(f"3. Configurez l'authentification JWT")
        print(f"4. Lancez le test!")
        
        # Afficher un exemple d'enregistrement
        print(f"\n📝 EXEMPLE D'ENREGISTREMENT:")
        print(json.dumps(test_data[0], indent=2, ensure_ascii=False))
    
    else:
        print("\n❌ Impossible de générer les données de test.")
        print("Vérifiez que votre base de données contient les enregistrements nécessaires.")

if __name__ == "__main__":
    main()
