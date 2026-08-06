"""
Prépare et importe les fichiers DLL_INVENTORY (produits L'Oréal).
1) Crée les familles manquantes liées au compte
2) Enrichit chaque fichier (Stock_Unit / Product_Status)
3) Importe via ProductResource
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from django.db import transaction
from import_export.formats.base_formats import XLSX

from apps.masterdata.admin import ProductResource
from apps.masterdata.models import Account, Family, Product

BASE = Path(r"C:\Users\moham\Documents\L'Oreal")
FILES = sorted(BASE.glob("DLL_INVENTORY*.xlsx"))
TMP_DIR = Path("_tmp_dll_import")


def main() -> int:
    if not FILES:
        print("Aucun fichier DLL_INVENTORY*.xlsx trouvé.")
        return 1

    account = Account.objects.order_by("id").first()
    if not account:
        print("Aucun compte en base. Impossible d'importer.")
        return 1

    print(f"Compte: id={account.id} name={account.account_name}")
    print(f"Fichiers ({len(FILES)}):")
    for f in FILES:
        print(f"  - {f}")

    # Collecter familles depuis tous les fichiers
    families: set[str] = set()
    for f in FILES:
        df = pd.read_excel(f)
        col = None
        for c in df.columns:
            if str(c).strip().lower() == "product family":
                col = c
                break
        if col is None:
            print(f"Colonne product family absente dans {f.name}")
            return 1
        for val in df[col].dropna().unique():
            name = str(val).strip()
            if name:
                families.add(name)

    print(f"Familles distinctes: {len(families)}")
    created = 0
    for name in sorted(families):
        existing = Family.objects.filter(family_name__iexact=name).first()
        if existing:
            continue
        fam = Family(
            family_name=name,
            family_status="ACTIVE",
            compte=account,
        )
        fam.save()
        if not fam.reference:
            fam.reference = f"FAM-{fam.id}"
            fam.save(update_fields=["reference"])
        created += 1
    print(f"Familles créées: {created}")

    TMP_DIR.mkdir(exist_ok=True)
    resource = ProductResource()
    file_format = XLSX()
    grand_totals = {"new": 0, "update": 0, "skip": 0, "error": 0}

    for idx, src in enumerate(FILES, start=1):
        print(f"\n=== [{idx}/{len(FILES)}] Préparation {src.name} ===")
        df = pd.read_excel(src)
        # Normaliser en-têtes
        df.columns = [str(c).strip().lower() for c in df.columns]
        if "stock unit" not in df.columns:
            df["stock unit"] = "EA"
        else:
            df["stock unit"] = df["stock unit"].fillna("EA").replace("", "EA")
        if "product status" not in df.columns:
            df["product status"] = "ACTIVE"
        else:
            df["product status"] = df["product status"].fillna("ACTIVE")

        tmp_path = TMP_DIR / f"import_{src.stem}.xlsx"
        df.to_excel(tmp_path, index=False)
        print(f"Lignes: {len(df)} -> {tmp_path}")

        with open(tmp_path, "rb") as fh:
            dataset = file_format.create_dataset(fh.read())

        print("Validation...")
        dry = resource.import_data(dataset, dry_run=True, raise_errors=False)
        if dry.has_errors():
            print("ERREURS de validation:")
            for error in dry.base_errors[:20]:
                print("  base:", error.error)
            for line, errors in list(dry.row_errors())[:30]:
                msgs = ", ".join(str(e.error) for e in errors)
                print(f"  ligne {line}: {msgs}")
            total_err_rows = len(list(dry.row_errors()))
            print(f"Total lignes en erreur: {total_err_rows}")
            return 1

        print("Import...")
        with transaction.atomic():
            result = resource.import_data(dataset, dry_run=False, raise_errors=True)
        totals = result.totals or {}
        for k in grand_totals:
            grand_totals[k] += int(totals.get(k, 0) or 0)
        print(
            f"OK part {idx}: new={totals.get('new', 0)} "
            f"update={totals.get('update', 0)} skip={totals.get('skip', 0)} "
            f"error={totals.get('error', 0)}"
        )

    product_count = Product.objects.count()
    print("\n=== RÉCAP ===")
    print(f"Produits en base: {product_count}")
    print(f"Totals: {grand_totals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
