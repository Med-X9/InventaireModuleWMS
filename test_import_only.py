#!/usr/bin/env python3
"""
Test des imports uniquement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

print("✅ Django configuré avec succès")

try:
    from apps.inventory.models import CountingDetail
    print("✅ Import CountingDetail réussi")
except Exception as e:
    print(f"❌ Erreur import CountingDetail: {e}")

try:
    from apps.inventory.models import NSerie
    print("✅ Import NSerie réussi")
except Exception as e:
    print(f"❌ Erreur import NSerie: {e}")

try:
    from apps.masterdata.models import NSerie as MasterNSerie
    print("✅ Import MasterNSerie réussi")
except Exception as e:
    print(f"❌ Erreur import MasterNSerie: {e}")

try:
    from apps.masterdata.models import Product
    print("✅ Import Product réussi")
except Exception as e:
    print(f"❌ Erreur import Product: {e}")

print("\n🏁 Test des imports terminé")
