#!/usr/bin/env python3
"""
Exemple complet avec 6 comptages pour illustrer la logique des écarts
"""

# Simulation des données pour 6 comptages
quantities = {1: 10, 2: 12, 3: 10, 4: 15, 5: 12, 6: 10}

print('=== DONNÉES D\'ENTRÉE ===')
for i in range(1, 7):
    print(f'{i}er comptage: {quantities.get(i, "None")}')

print('\n=== CALCUL DES ÉCARTS SELON LA NOUVELLE LOGIQUE ===')

# Simulation de la logique du service
previous_quantities = {}
result_row = {}

for order in range(1, 7):
    quantity = quantities.get(order)
    quantity_key = f"{order}er comptage"
    result_row[quantity_key] = quantity if quantity is not None else None

    # Calculer les écarts pour tous les ordres précédents (entier signé : q_actuel - q_précédent)
    if quantity is not None:
        print(f'\nComptage {order} (valeur: {quantity}):')
        for prev_order in range(1, order):
            ecart_key = f"ecart_{prev_order}_{order}"
            prev_quantity = previous_quantities.get(prev_order)

            if prev_quantity is not None:
                ecart_value = quantity - prev_quantity
                result_row[ecart_key] = ecart_value
                print(f'  {ecart_key}: {ecart_value} (entier signé: {quantity} - {prev_quantity})')
            else:
                result_row[ecart_key] = None

    # Stocker la quantité actuelle pour les calculs suivants
    if quantity is not None:
        previous_quantities[order] = quantity

print('\n=== RÉSULTAT FINAL (ligne de données) ===')
print('{')
for key, value in result_row.items():
    if value is not None:
        print(f'  "{key}": {value},')
    else:
        print(f'  "{key}": null,')
print('}')

print('\n=== RÉSUMÉ DES ÉCARTS (entiers signés: q_actuel - q_précédent) ===')
print('ecart_1_2: 2 (12 - 10)')
print('ecart_2_3: -2 (10 - 12)')
print('ecart_3_4: 5 (15 - 10)')
print('ecart_4_5: -3 (12 - 15)')
print('ecart_5_6: -2 (10 - 12)')
