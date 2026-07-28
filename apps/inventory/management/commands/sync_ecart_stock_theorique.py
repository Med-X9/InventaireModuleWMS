"""
Resynchronise la table EcartStockTheorique depuis les comptages (final_result).

Usage:
  python manage.py sync_ecart_stock_theorique --inventory-id 24 --confirm
  python manage.py sync_ecart_stock_theorique --inventory-id 24 --warehouse-id 5 --confirm
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.inventory.models import EcartStockTheorique, Job, Setting
from apps.inventory.services.ecart_stock_theorique_service import (
    EcartStockTheoriqueService,
)


class Command(BaseCommand):
    help = (
        "Recalcule et upsert EcartStockTheorique (qte_theorique / qte_pratique / "
        "resultat_final) depuis Stock + final_result des comptages."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Obligatoire pour lancer la synchronisation.",
        )
        parser.add_argument(
            "--inventory-id",
            type=int,
            required=True,
            help="ID inventaire.",
        )
        parser.add_argument(
            "--warehouse-id",
            type=int,
            default=None,
            help="Magasin unique (défaut: tous les magasins de l'inventaire).",
        )
        parser.add_argument(
            "--only-nonzero",
            action="store_true",
            help="N'inclure que les lignes avec écart != 0 dans le calcul source.",
        )
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Supprime les lignes existantes avant sync (non validées uniquement).",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Ajoutez --confirm pour synchroniser.")

        inventory_id = options["inventory_id"]
        warehouse_id = options["warehouse_id"]
        only_nonzero = options["only_nonzero"]

        if warehouse_id:
            warehouse_ids = [warehouse_id]
        else:
            warehouse_ids = list(
                Job.objects.filter(inventory_id=inventory_id)
                .values_list("warehouse_id", flat=True)
                .distinct()
            )
            if not warehouse_ids:
                warehouse_ids = list(
                    Setting.objects.filter(inventory_id=inventory_id)
                    .values_list("warehouse_id", flat=True)
                    .distinct()
                )

        if not warehouse_ids:
            raise CommandError(f"Aucun magasin trouvé pour inventaire {inventory_id}.")

        service = EcartStockTheoriqueService()
        total_created = 0
        total_updated = 0

        for wid in sorted(warehouse_ids):
            if options["purge"]:
                deleted, _ = (
                    EcartStockTheorique.objects.filter(
                        inventory_id=inventory_id,
                        warehouse_id=wid,
                        valide=False,
                    ).delete()
                )
                self.stdout.write(f"  wh={wid}: {deleted} ligne(s) non validée(s) supprimée(s)")

            result = service.sync_from_compute(
                inventory_id,
                wid,
                only_nonzero=only_nonzero,
            )
            total_created += result["created"]
            total_updated += result["updated"]
            self.stdout.write(
                f"  wh={wid}: créés={result['created']} maj={result['updated']} "
                f"lignes={result['total_compute_lines']} "
                f"totaux={result['totaux']}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync terminée — {total_created} créés, {total_updated} mis à jour "
                f"({len(warehouse_ids)} magasin(s))."
            )
        )
