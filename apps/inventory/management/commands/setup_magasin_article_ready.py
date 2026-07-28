"""
Purge inventaire/opérations (garde masterdata + users) puis setup inventaire MAGASIN.

- Type MAGASIN, mode « par article », sans options (n_lot/n_serie/dlc off)
- Jobs sur tous les magasins MAG*
- Statuts : EN ATTENTE → VALIDE → AFFECTE (1 session Mobile unique / magasin) → PRET
- Stocks multi-articles par magasin, sans emplacement

Usage:
  python manage.py setup_magasin_article_ready --confirm
  python manage.py setup_magasin_article_ready --confirm --stocks-per-warehouse 20
"""
from __future__ import annotations

import random
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.inventory.constants import CountMode, InventoryType
from apps.inventory.models import (
    Assigment,
    ComptageSequence,
    Counting,
    CountingDetail,
    EcartComptage,
    EcartStockTheorique,
    Inventory,
    InventoryDetailRessource,
    Job,
    JobDetail,
    JobDetailRessource,
    NSerieInventory,
    Planning,
    Setting,
)
from apps.inventory.services.assignment_service import AssignmentService
from apps.inventory.services.job_service import JobService
from apps.inventory.usecases.inventory_management import InventoryManagementUseCase
from apps.inventory.usecases.job_creation import JobCreationUseCase
from apps.masterdata.models import Account, Location, Product, Stock, Warehouse
from apps.users.models import UserApp


class Command(BaseCommand):
    help = (
        "Vide inventaires/jobs/stocks (garde masterdata+users), crée un inventaire "
        "MAGASIN par article prêt à lancer (jobs PRET + stocks multi-articles)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Obligatoire pour exécuter la purge + setup.",
        )
        parser.add_argument(
            "--account-id",
            type=int,
            default=None,
            help="ID Account (défaut: premier trouvé).",
        )
        parser.add_argument(
            "--stocks-per-warehouse",
            type=int,
            default=25,
            help="Nombre d'articles de stock distincts par magasin (défaut 25).",
        )
        parser.add_argument(
            "--purge-only",
            action="store_true",
            help="Purge seulement, sans créer l'inventaire.",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError(
                "Ajoutez --confirm pour purger puis créer l'inventaire MAGASIN."
            )

        account = self._resolve_account(options.get("account_id"))
        magasins = list(
            Warehouse.objects.filter(
                warehouse_name__icontains="Magasin",
                status="ACTIVE",
            ).order_by("id")
        )
        if not magasins:
            raise CommandError("Aucun warehouse 'Magasin *' ACTIVE trouvé.")

        self.stdout.write(self.style.WARNING("=== PURGE inventaire / opérations ==="))
        purged = self._purge_operational_data()
        for key, count in purged.items():
            self.stdout.write(f"  deleted {key}: {count}")

        if options["purge_only"]:
            self.stdout.write(self.style.SUCCESS("Purge terminée (--purge-only)."))
            return

        n_stocks = max(5, int(options["stocks_per_warehouse"]))
        products = self._pick_products(n_stocks * 3)
        if len(products) < n_stocks:
            raise CommandError(
                f"Pas assez de produits masterdata ({len(products)}) pour "
                f"{n_stocks} stocks/magasin."
            )

        self.stdout.write(self.style.WARNING("=== CRÉATION inventaire MAGASIN ==="))
        inventory = self._create_and_configure(account, magasins)
        self.stdout.write(
            self.style.SUCCESS(
                f"Inventaire id={inventory.id} ref={inventory.reference} "
                f"status={inventory.status}"
            )
        )

        self.stdout.write(self.style.WARNING("=== JOBS + STATUTS ==="))
        job_ids_by_wh = self._create_jobs_and_progress(inventory, magasins, account)

        self.stdout.write(
            self.style.WARNING("=== STOCKS multi-articles (sans emplacement) ===")
        )
        stock_count = self._create_stocks(inventory, magasins, products, n_stocks)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== SETUP TERMINÉ ==="))
        self.stdout.write(f"  inventory_id : {inventory.id}")
        self.stdout.write(f"  reference    : {inventory.reference}")
        self.stdout.write(f"  magasins     : {len(magasins)}")
        self.stdout.write(
            f"  jobs         : {sum(len(v) for v in job_ids_by_wh.values())}"
        )
        self.stdout.write(f"  stocks       : {stock_count}")
        self.stdout.write(
            "  Prochaine étape : lancer magasins "
            f"POST /web/api/inventory/{inventory.id}/warehouses/launch/"
        )

    def _resolve_account(self, account_id) -> Account:
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist as exc:
                raise CommandError(f"Account {account_id} introuvable.") from exc
        account = Account.objects.first()
        if not account:
            raise CommandError("Aucun Account en base.")
        return account

    def _purge_operational_data(self) -> dict:
        """Supprime inventaires, jobs, stocks, écarts — pas masterdata/users."""
        counts = {}
        with transaction.atomic():
            for model, label in (
                (ComptageSequence, "ComptageSequence"),
                (NSerieInventory, "NSerieInventory"),
                (CountingDetail, "CountingDetail"),
                (EcartComptage, "EcartComptage"),
                (EcartStockTheorique, "EcartStockTheorique"),
                (Assigment, "Assigment"),
                (JobDetailRessource, "JobDetailRessource"),
                (JobDetail, "JobDetail"),
                (Job, "Job"),
                (InventoryDetailRessource, "InventoryDetailRessource"),
                (Counting, "Counting"),
                (Setting, "Setting"),
                (Planning, "Planning"),
                (Stock, "Stock"),
                (Inventory, "Inventory"),
            ):
                n, _ = model.objects.all().delete()
                counts[label] = n

            try:
                from apps.masterdata.models import ImportTask

                n, _ = ImportTask.objects.all().delete()
                counts["ImportTask"] = n
            except Exception:
                pass

            try:
                from apps.inventory.models import PdfTask

                n, _ = PdfTask.objects.all().delete()
                counts["PdfTask"] = n
            except Exception:
                pass

        return counts

    def _create_and_configure(
        self, account: Account, magasins: List[Warehouse]
    ) -> Inventory:
        today = timezone.now().date()
        use_case = InventoryManagementUseCase()
        label = f"Inventaire MAGASIN article {today.isoformat()}"

        payload = {
            "label": label,
            "inventory_type": InventoryType.MAGASIN,
            "date": today,
            "account_id": account.id,
            "warehouse": [{"id": w.id, "date": today} for w in magasins],
            "comptages": [],
        }
        use_case.create(payload)
        inventory = Inventory.objects.filter(label=label).order_by("-id").first()
        if inventory is None:
            raise CommandError("Échec création inventaire MAGASIN.")

        use_case.configure_magasin_counting(
            inventory.id,
            {
                "count_mode": CountMode.BY_ARTICLE,
                "is_variant": False,
                "n_lot": False,
                "n_serie": False,
                "dlc": False,
                "show_product": True,
                "quantity_show": True,
                "unit_scanned": False,
                "entry_quantity": False,
                "stock_situation": False,
            },
        )
        inventory.refresh_from_db()
        return inventory

    def _create_jobs_and_progress(
        self,
        inventory: Inventory,
        magasins: List[Warehouse],
        account: Account,
    ) -> dict:
        job_uc = JobCreationUseCase()
        job_service = JobService()
        assignment_service = AssignmentService()
        job_ids_by_wh: dict = {}

        for warehouse in magasins:
            location_ids = list(
                Location.objects.filter(
                    sous_zone__zone__warehouse_id=warehouse.id
                ).values_list("id", flat=True)
            )
            if not location_ids:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Skip {warehouse.warehouse_name}: aucun emplacement"
                    )
                )
                continue

            result = job_uc.execute(inventory.id, warehouse.id, location_ids)
            job_id = result.get("job_id") or result.get("id")
            if not job_id:
                job = (
                    Job.objects.filter(inventory=inventory, warehouse=warehouse)
                    .order_by("-id")
                    .first()
                )
                if not job:
                    raise CommandError(
                        f"Job non créé pour {warehouse.warehouse_name}: {result}"
                    )
                job_id = job.id

            job_ids_by_wh[warehouse.id] = [job_id]
            self.stdout.write(
                f"  Job {job_id} créé pour {warehouse.warehouse_name} "
                f"({len(location_ids)} emplacements) — EN ATTENTE"
            )

        all_job_ids = [jid for ids in job_ids_by_wh.values() for jid in ids]
        if not all_job_ids:
            raise CommandError("Aucun job créé.")

        job_service.validate_jobs(all_job_ids)
        self.stdout.write(self.style.SUCCESS(f"  {len(all_job_ids)} jobs → VALIDE"))

        for warehouse in magasins:
            ids = job_ids_by_wh.get(warehouse.id) or []
            if not ids:
                continue
            session = self._get_or_create_session(warehouse, account)
            assignment_service.assign_jobs(
                {
                    "job_ids": ids,
                    "counting_order": 1,
                    "session_id": session.id,
                    "date_start": timezone.now(),
                }
            )
            self.stdout.write(
                f"  {warehouse.warehouse_name} → AFFECTE session={session.username}"
            )

        job_service.make_jobs_ready(all_job_ids)
        # make_jobs_ready ne met que les Assigment en PRET — forcer Job.status=PRET
        Job.objects.filter(id__in=all_job_ids).update(
            status="PRET",
            pret_date=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS(f"  {len(all_job_ids)} jobs → PRET"))

        return job_ids_by_wh

    def _get_or_create_session(
        self, warehouse: Warehouse, account: Account
    ) -> UserApp:
        username = f"sess-mag-{warehouse.id}"
        session = UserApp.objects.filter(username=username, type="Mobile").first()
        if session:
            return session
        return UserApp.objects.create_user(
            username=username,
            password="Magasin123!",
            type="Mobile",
            nom="Session",
            prenom=warehouse.warehouse_name[:50],
            compte=account,
            is_active=True,
        )

    def _pick_products(self, needed: int) -> List[Product]:
        qs = Product.objects.exclude(Barcode__isnull=True).exclude(Barcode="")
        ids = list(qs.values_list("id", flat=True)[: max(needed * 2, 200)])
        random.shuffle(ids)
        picked = []
        seen_barcodes = set()
        for pid in ids:
            p = Product.objects.get(id=pid)
            bc = (p.Barcode or "").strip()
            if not bc or bc in seen_barcodes:
                continue
            seen_barcodes.add(bc)
            picked.append(p)
            if len(picked) >= needed:
                break
        return picked

    def _create_stocks(
        self,
        inventory: Inventory,
        magasins: List[Warehouse],
        products: List[Product],
        n_per_wh: int,
    ) -> int:
        created = 0
        pool = list(products)
        ts = int(timezone.now().timestamp()) % 100000

        for wi, warehouse in enumerate(magasins):
            start = (wi * 3) % max(1, len(pool) - n_per_wh)
            subset = pool[start : start + n_per_wh]
            if len(subset) < n_per_wh:
                subset = (subset + pool)[:n_per_wh]

            for pi, product in enumerate(subset):
                qty = random.randint(1, 80)
                ref = f"STK{ts}{warehouse.id:02d}{pi:03d}"[:20]
                Stock.objects.create(
                    reference=ref,
                    location=None,
                    product=product,
                    quantity_available=qty,
                    inventory=inventory,
                    warehouse=warehouse,
                )
                created += 1

            self.stdout.write(
                f"  {warehouse.warehouse_name}: {n_per_wh} stocks "
                f"(articles mélangés, sans emplacement)"
            )
        return created
