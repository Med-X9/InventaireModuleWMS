#!/usr/bin/env python
"""
Script pour corriger la table historique users_historicaluserapp
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def fix_historical_table():
    """
    Ajoute la colonne compte_id manquante dans users_historicaluserapp
    """
    with connection.cursor() as cursor:
        print("=== Correction de la table historique users_historicaluserapp ===\n")
        
        # Vérifier si la colonne compte_id existe dans la table historique
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users_historicaluserapp' 
            AND column_name LIKE '%compte%';
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Colonnes 'compte' trouvées dans users_historicaluserapp: {columns}")
        
        if 'compte_id' not in columns:
            print("\nAjout de la colonne compte_id à users_historicaluserapp...")
            try:
                # Ajouter la colonne compte_id dans la table historique
                cursor.execute("""
                    ALTER TABLE users_historicaluserapp 
                    ADD COLUMN compte_id INTEGER;
                """)
                print("✓ Colonne compte_id ajoutée avec succès à la table historique")
                
                # Optionnel: Mettre à jour les enregistrements existants si nécessaire
                print("Mise à jour des enregistrements historiques existants...")
                cursor.execute("""
                    UPDATE users_historicaluserapp h
                    SET compte_id = u.compte_id
                    FROM users_userapp u
                    WHERE h.id = u.id AND u.compte_id IS NOT NULL;
                """)
                print("✓ Enregistrements historiques mis à jour")
                
            except Exception as e:
                print(f"Erreur lors de l'ajout de la colonne: {e}")
                # Si la colonne existe déjà, ce n'est pas grave
                if "already exists" in str(e) or "déjà" in str(e):
                    print("La colonne existe déjà, continuons...")
                else:
                    raise
        else:
            print("La colonne compte_id existe déjà dans la table historique")

def verify_table_structure():
    """
    Vérifie la structure des tables users pour s'assurer de la cohérence
    """
    with connection.cursor() as cursor:
        print("\n=== Vérification de la structure des tables ===\n")
        
        # Structure de users_userapp
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users_userapp' 
            ORDER BY ordinal_position;
        """)
        
        main_columns = cursor.fetchall()
        print("Structure de users_userapp:")
        for col in main_columns:
            print(f"  {col[0]} - {col[1]} - Nullable: {col[2]}")
        
        # Structure de users_historicaluserapp
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users_historicaluserapp' 
            ORDER BY ordinal_position;
        """)
        
        hist_columns = cursor.fetchall()
        print("\nStructure de users_historicaluserapp:")
        for col in hist_columns:
            print(f"  {col[0]} - {col[1]} - Nullable: {col[2]}")

if __name__ == "__main__":
    try:
        fix_historical_table()
        verify_table_structure()
        
        print("\n=== Correction terminée ===")
        print("La table historique devrait maintenant fonctionner correctement.")
        print("Testez votre application pour vérifier que l'erreur est résolue.")
        
    except Exception as e:
        print(f"Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 