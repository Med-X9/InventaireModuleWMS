"""
Exécute la création des inventaires GENERAL / TOURNANT / MAGASIN
sur la base physique (pas la DB de test Django).

Usage:
  python manage.py create_inventory_types_smoke
  python manage.py create_inventory_types_smoke --configure-general
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.inventory.constants import CountMode, InventoryStatus, InventoryType
from apps.inventory.models import Counting, Inventory, Setting
from apps.inventory.usecases.inventory_management import InventoryManagementUseCase
from apps.masterdata.models import Account, Warehouse


class Command(BaseCommand):
    help = (
        "Crée sur la DB physique un inventaire GENERAL, TOURNANT et MAGASIN "
        "sans comptages (création seule). Option --configure-general pour "
        "ajouter les 3 comptages du GENERAL."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--configure-general",
            action="store_true",
            help="Après création, configure exactement 3 comptages pour GENERAL.",
        )
        parser.add_argument(
            "--account-id",
            type=int,
            default=None,
            help="ID compte (sinon premier Account trouvé).",
        )
        parser.add_argument(
            "--warehouse-id",
            type=int,
            default=None,
            help="ID magasin (sinon premier Warehouse ACTIVE trouvé).",
        )

    def handle(self, *args, **options):
        account = self._resolve_account(options.get("account_id"))
        warehouse = self._resolve_warehouse(options.get("warehouse_id"))
        today = timezone.now().date()
        use_case = InventoryManagementUseCase()

        created = []
        for inventory_type, label_suffix in (
            (InventoryType.GENERAL, "GENERAL"),
            (InventoryType.TOURNANT, "TOURNANT"),
            (InventoryType.MAGASIN, "MAGASIN"),
        ):
            label = f"Smoke {label_suffix} {today.isoformat()}"
            payload = {
                "label": label,
                "inventory_type": inventory_type,
                "date": today,
                "account_id": account.id,
                "warehouse": [{"id": warehouse.id, "date": today}],
                "comptages": [],
            }
            result = use_case.create(payload)
            inventory = Inventory.objects.filter(label=label).order_by("-id").first()
            if inventory is None:
                raise CommandError(f"Échec création inventaire {inventory_type}: {result}")

            counting_count = Counting.objects.filter(inventory=inventory).count()
            setting = Setting.objects.filter(inventory=inventory).first()
            created.append(inventory)

            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] {inventory_type} id={inventory.id} ref={inventory.reference} "
                    f"status={inventory.status} countings={counting_count} "
                    f"warehouse_date={getattr(setting, 'warehouse_date', None)}"
                )
            )
            if inventory.status != InventoryStatus.EN_CONFIGURATION:
                raise CommandError(
                    f"{inventory_type} doit être EN CONFIGURATION à la création "
                    f"(trouvé {inventory.status})."
                )
            if counting_count != 0:
                raise CommandError(
                    f"{inventory_type} ne doit pas avoir de comptages à la création "
                    f"(trouvé {counting_count})."
                )

        if options.get("configure_general"):
            general = next(
                inv for inv in created if inv.inventory_type == InventoryType.GENERAL
            )
            comptages = [
                {
                    "order": 1,
                    "count_mode": CountMode.STOCK_IMAGE,
                    "stock_situation": True,
                },
                {
                    "order": 2,
                    "count_mode": CountMode.BY_ARTICLE,
                    "n_lot": False,
                    "dlc": False,
                    "n_serie": False,
                },
                {
                    "order": 3,
                    "count_mode": CountMode.BY_ARTICLE,
                    "n_lot": False,
                    "dlc": False,
                    "n_serie": False,
                },
            ]
            cfg = use_case.configure_general_countings(general.id, comptages)
            general.refresh_from_db()
            count = Counting.objects.filter(inventory=general).count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Config GENERAL id={general.id} status={general.status} "
                    f"countings={count} message={cfg.get('message')}"
                )
            )
            if count != 3:
                raise CommandError(
                    f"GENERAL doit avoir exactement 3 comptages après config (trouvé {count})."
                )
            if general.status != InventoryStatus.EN_PREPARATION:
                raise CommandError(
                    f"GENERAL doit passer en EN PREPARATION après config "
                    f"(trouvé {general.status})."
                )

        self.stdout.write(self.style.SUCCESS("Smoke test DB physique terminé."))

    def _resolve_account(self, account_id: int | None) -> Account:
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist as exc:
                raise CommandError(f"Account id={account_id} introuvable") from exc
        account = Account.objects.order_by("id").first()
        if not account:
            raise CommandError("Aucun Account en base — créez un compte d'abord.")
        return account

    def _resolve_warehouse(self, warehouse_id: int | None) -> Warehouse:
        if warehouse_id:
            try:
                return Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist as exc:
                raise CommandError(f"Warehouse id={warehouse_id} introuvable") from exc
        warehouse = (
            Warehouse.objects.filter(status="ACTIVE").order_by("id").first()
            or Warehouse.objects.order_by("id").first()
        )
        if not warehouse:
            raise CommandError("Aucun Warehouse en base — créez un magasin d'abord.")
        return warehouse
