#!/usr/bin/env python3
"""
Exemple montrant le statut du job ajouté dans la réponse
"""

# Simulation des données avec statut du job
job_info = {
    "id": 456,
    "reference": "JOB-2024-001",
    "status": "ENTAME"
}

print('=== DONNÉES DU JOB ===')
print(f'ID: {job_info["id"]}')
print(f'Référence: {job_info["reference"]}')
print(f'Statut: {job_info["status"]}')

print('\n=== RÉSULTAT DANS LA RÉPONSE JSON ===')

# Simulation du traitement dans le service
result_row = {}

if job_info and job_info.get("id") is not None:
    result_row["job_id"] = job_info["id"]
    job_reference = job_info.get("reference")
    if job_reference:
        result_row["job_reference"] = job_reference
    job_status = job_info.get("status")
    if job_status:
        result_row["job_status"] = job_status

print('{')
for key, value in result_row.items():
    print(f'  "{key}": "{value}",')
print('}')

print('\n=== STATUTS POSSIBLES DU JOB ===')
job_statuses = [
    'EN ATTENTE',
    'AFFECTE',
    'PRET',
    'TRANSFERT',
    'ENTAME',
    'VALIDE',
    'TERMINE',
    'SAISIE MANUELLE',
    'ANNULE'
]

for status in job_statuses:
    print(f'- {status}')
