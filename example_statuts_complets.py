#!/usr/bin/env python3
"""
Exemple montrant tous les statuts de comptage inclus
"""

# Simulation des données avec statuts pour 6 comptages
quantities = {1: 10, 2: 12, 3: 10, 4: 15, 5: 12, 6: 10}
assignment_statuses = {
    1: "completed",
    2: "completed",
    3: "in_progress",
    4: "pending",
    5: "completed",
    6: "completed"
}

print('=== STATUTS DE COMPTAGE AVANT (seulement 1 et 2) ===')
print('"statut_1er_comptage": "completed"')
print('"statut_2er_comptage": "completed"')

print('\n=== STATUTS DE COMPTAGE APRÈS (tous les comptages) ===')

# Simulation de la nouvelle logique
result_row = {}

for order in range(1, 7):
    # Ajouter le statut de l'assignment pour tous les comptages
    assignment_status = assignment_statuses.get(order)
    if assignment_status is not None:
        status_key = f"statut_{order}er_comptage"
        result_row[status_key] = assignment_status
        print(f'"{status_key}": "{assignment_status}"')

print('\n=== RÉSUMÉ ===')
print('Maintenant tous les statuts de comptage sont inclus :')
for order in range(1, 7):
    status = assignment_statuses.get(order)
    if status:
        print(f'- Comptage {order}: {status}')
