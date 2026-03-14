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

    # Calculer les écarts pour tous les ordres précédents
    if quantity is not None and previous_quantities:
        # Optimisation : vérifier une seule fois si la quantité actuelle correspond à au moins une précédente
        has_match_with_any_previous = any(
            quantity == prev_qty for prev_qty in previous_quantities.values()
        )

        print(f'\nComptage {order} (valeur: {quantity}):')
        print(f'  Quantités précédentes: {list(previous_quantities.values())}')
        print(f'  Correspondance avec au moins un précédent: {has_match_with_any_previous}')

        # Calculer tous les écarts pour cet ordre
        for prev_order in range(1, order):
            ecart_key = f"ecart_{prev_order}_{order}"
            prev_quantity = previous_quantities.get(prev_order)

            if prev_quantity is not None:
                # Pour ecart_1_2 : afficher la valeur numérique
                if prev_order == 1 and order == 2:
                    ecart_value = abs(quantity - prev_quantity)
                    result_row[ecart_key] = ecart_value
                    print(f'  {ecart_key}: {ecart_value} (valeur numérique)')
                else:
                    # Pour les autres écarts : vérifier si égal à AU MOINS UN comptage précédent
                    result_row[ecart_key] = has_match_with_any_previous
                    print(f'  {ecart_key}: {has_match_with_any_previous} (correspondance)')
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

print('\n=== RÉSUMÉ DES ÉCARTS ===')
print('ecart_1_2: 2 (différence numérique entre 1er et 2ème)')
print('ecart_2_3: true (3ème=10, égal au 1er=10)')
print('ecart_3_4: false (4ème=15, différent de 10 et 12)')
print('ecart_4_5: true (5ème=12, égal au 2ème=12)')
print('ecart_5_6: true (6ème=10, égal au 1er=10 et au 3ème=10)')
