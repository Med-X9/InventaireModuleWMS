#!/usr/bin/env python
"""
Script pour migrer tous les numéros de personnes existants
vers le nouveau format fixe : opr-000X
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

def migrate_personne_numero(personne):
    """Migre le numéro d'une personne vers le nouveau format opr-000X."""
    numero_str = personne.numero

    # Extraire le numéro brut (compatible avec tous les anciens formats)
    match = re.match(r'opr-(\d+)', numero_str)
    if not match:
        print(f"Numero invalide pour {personne}: {numero_str}")
        return False

    numero_brut = int(match.group(1))

    # Générer le nouveau format fixe
    nouveau_numero = f'opr-000{numero_brut}'

    if nouveau_numero != numero_str:
        print(f"Migration: {numero_str} -> {nouveau_numero}")
        personne.numero = nouveau_numero
        personne.save(update_fields=['numero'])
        return True

    return False

def main():
    print("Migration vers le nouveau format fixe opr-000X...")
    print("=" * 50)

    personnes = Personne.objects.all().order_by('id')
    migrated_count = 0
    total_count = 0

    for personne in personnes:
        total_count += 1
        if migrate_personne_numero(personne):
            migrated_count += 1

    print("=" * 50)
    print(f"Migration terminee: {migrated_count}/{total_count} numeros migres")

    # Vérification finale
    print("\nEchantillon des numeros migres:")
    echantillon = Personne.objects.all()[:10]
    for p in echantillon:
        print(f"  {p.numero}")

if __name__ == '__main__':
    main()
