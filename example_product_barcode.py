#!/usr/bin/env python3
"""
Exemple montrant que le champ product contient le code-barres
"""

# Simulation des données d'un produit
product_data = {
    "reference": "ART001",
    "barcode": "1234567890123",
    "description": "Stylo bille bleu",
    "internal_code": "INT001"
}

print('=== DONNÉES DU PRODUIT ===')
print(f'Référence: {product_data["reference"]}')
print(f'Code-barres: {product_data["barcode"]}')
print(f'Description: {product_data["description"]}')
print(f'Code interne: {product_data["internal_code"]}')

print('\n=== VALEUR DU CHAMP "product" AVANT (code interne) ===')
print('"product": "INT001"')

print('\n=== VALEUR DU CHAMP "product" APRÈS (code-barres) ===')
print('"product": "1234567890123"')

print('\n=== STRUCTURE COMPLÈTE DE LA RÉPONSE ===')

# Simulation de la structure complète
result_row = {
    "location": "A01-01-01",
    "location_id": 123,
    "product": product_data["barcode"],  # Code-barres
    "product_description": product_data["description"],
    "product_internal_code": product_data["internal_code"],
    "1er comptage": 10,
    "2er comptage": 12,
    "ecart_1_2": 2
}

print('{')
for key, value in result_row.items():
    if isinstance(value, str):
        print(f'  "{key}": "{value}",')
    else:
        print(f'  "{key}": {value},')
print('}')

print('\n=== EXPLICATION ===')
print('[OK] Le champ "product" contient maintenant le code-barres')
print('[OK] Le code interne est conserve dans "product_internal_code"')
print('[OK] La description reste dans "product_description"')
