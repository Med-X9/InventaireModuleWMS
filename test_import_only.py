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

print("OK Django configure")

try:
    from apps.inventory.models import CountingDetail
    print("OK Import CountingDetail")
except Exception as e:
    print(f"❌ Erreur import CountingDetail: {e}")

try:
    from apps.inventory.models import NSerieInventory
    print("OK Import NSerieInventory")
except Exception as e:
    print(f"❌ Erreur import NSerie: {e}")

try:
    from apps.masterdata.models import NSerie as MasterNSerie
    print("OK Import MasterNSerie")
except Exception as e:
    print(f"❌ Erreur import MasterNSerie: {e}")

try:
    from apps.masterdata.models import Product
    print("OK Import Product")
except Exception as e:
    print(f"❌ Erreur import Product: {e}")

print("\nFIN Test des imports")
