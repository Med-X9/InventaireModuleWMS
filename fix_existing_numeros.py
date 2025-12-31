#!/usr/bin/env python
"""
Script pour corriger TOUS les numéros existants vers le format fixe opr-XXXXXX
"""
import os
import sys
import django

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Personne
import re

def fix_all_existing_numeros():
    """Corrige tous les numéros existants vers le format fixe"""
    print("="*60)
    print("CORRECTION DE TOUS LES NUMEROS EXISTANTS")
    print("="*60)

    personnes = Personne.objects.all().order_by('id')
    total_count = personnes.count()
    corrected_count = 0

    print(f"Total de personnes à vérifier: {total_count}")

    for personne in personnes:
        numero_actuel = personne.numero

        # Extraire le numéro brut
        match = re.match(r'opr-(\d+)', numero_actuel)
        if not match:
            print(f"ERREUR: Format invalide pour {personne}: {numero_actuel}")
            continue

        numero_brut = int(match.group(1))

        # Générer le nouveau format fixe
        nouveau_numero = f'opr-{str(numero_brut).zfill(6)}'

        if nouveau_numero != numero_actuel:
            print(f"CORRECTION: {numero_actuel} -> {nouveau_numero}")
            personne.numero = nouveau_numero
            personne.save(update_fields=['numero'])
            corrected_count += 1
        else:
            print(f"DEJA CORRECT: {numero_actuel}")

    print("="*60)
    print(f"RÉSULTAT: {corrected_count}/{total_count} numéros corrigés")

    # Vérification finale
    print("\nVÉRIFICATION FINALE (10 premiers):")
    echantillon = Personne.objects.all()[:10]
    for p in echantillon:
        numero = p.numero
        if numero.startswith('opr-'):
            suffix = numero[4:]
            if suffix.isdigit() and len(suffix) == 6:
                status = "OK"
            else:
                status = f"ERREUR (longueur: {len(suffix)})"
        else:
            status = "ERREUR (format invalide)"
        print(f"  {numero}: {status}")

    print("="*60)

if __name__ == '__main__':
    fix_all_existing_numeros()
