"""
Upsert heartbeat + calcul online/offline à la lecture (seuil 120 s par défaut).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone

from apps.devices.constants import HEARTBEAT_MIN_INTERVAL_SECONDS, OFFLINE_THRESHOLD_SECONDS
from apps.devices.models import Device

User = get_user_model()


def compute_device_status(last_seen_at: Optional[datetime], now: datetime) -> str:
    if last_seen_at is None:
        return "offline"
    delta = (now - last_seen_at).total_seconds()
    return "online" if delta <= OFFLINE_THRESHOLD_SECONDS else "offline"


def _client_ip(request) -> Optional[str]:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class DevicePresenceService:
    def upsert_heartbeat(self, user, validated_data: dict, request) -> dict:
        device_id = validated_data["device_id"]
        now = timezone.now()

        existing = Device.objects.filter(device_id=device_id).first()
        if existing and existing.last_seen_at:
            elapsed = (now - existing.last_seen_at).total_seconds()
            if elapsed < HEARTBEAT_MIN_INTERVAL_SECONDS:
                return {
                    "device_id": device_id,
                    "last_seen_at": existing.last_seen_at.isoformat(),
                    "server_offline_threshold_seconds": OFFLINE_THRESHOLD_SECONDS,
                    "throttled": True,
                }

        warehouse = None
        inventory = None
        if validated_data.get("warehouse_id"):
            from apps.masterdata.models import Warehouse

            warehouse = Warehouse.objects.filter(
                pk=validated_data["warehouse_id"], is_deleted=False
            ).first()
        if validated_data.get("inventory_id"):
            from apps.inventory.models import Inventory

            inventory = Inventory.objects.filter(
                pk=validated_data["inventory_id"], is_deleted=False
            ).first()

        defaults = {
            "user": user,
            "battery_level": validated_data.get("battery_level"),
            "is_charging": validated_data.get("is_charging", False),
            "app_version": (validated_data.get("app_version") or "")[:20] or None,
            "last_seen_at": now,
            "last_ip": _client_ip(request),
            "warehouse": warehouse,
            "inventory": inventory,
        }

        device, _created = Device.objects.update_or_create(
            device_id=device_id,
            defaults=defaults,
        )

        return {
            "device_id": device.device_id,
            "last_seen_at": device.last_seen_at.isoformat(),
            "server_offline_threshold_seconds": OFFLINE_THRESHOLD_SECONDS,
            "throttled": False,
        }

    def list_with_status(
        self,
        *,
        warehouse_id: Optional[int] = None,
        inventory_id: Optional[int] = None,
        status_filter: str = "all",
    ) -> dict[str, Any]:
        now = timezone.now()
        qs: QuerySet[Device] = (
            Device.objects.filter(is_deleted=False)
            .select_related("user", "warehouse", "inventory")
            .order_by("-last_seen_at")
        )

        if warehouse_id is not None:
            qs = qs.filter(warehouse_id=warehouse_id)
        if inventory_id is not None:
            qs = qs.filter(inventory_id=inventory_id)

        rows = []
        online_count = 0
        offline_count = 0

        for device in qs:
            status = compute_device_status(device.last_seen_at, now)
            if status_filter == "online" and status != "online":
                continue
            if status_filter == "offline" and status != "offline":
                continue

            if status == "online":
                online_count += 1
            else:
                offline_count += 1

            seconds_since = int((now - device.last_seen_at).total_seconds())
            rows.append(self._serialize_device_row(device, status, seconds_since))

        return {
            "meta": {
                "total": len(rows),
                "online_count": online_count,
                "offline_count": offline_count,
                "offline_threshold_seconds": OFFLINE_THRESHOLD_SECONDS,
                "generated_at": now.isoformat(),
            },
            "data": rows,
        }

    def _serialize_device_row(
        self, device: Device, status: str, seconds_since: int
    ) -> dict[str, Any]:
        user_payload = None
        if device.user_id and device.user:
            u = device.user
            display = " ".join(
                p for p in [getattr(u, "prenom", None), getattr(u, "nom", None)] if p
            ).strip()
            user_payload = {
                "id": u.id,
                "username": u.username,
                "display_name": display or u.username,
            }

        warehouse_payload = None
        if device.warehouse_id and device.warehouse:
            w = device.warehouse
            warehouse_payload = {
                "id": w.id,
                "reference": w.reference,
                "name": w.warehouse_name,
            }

        inventory_payload = None
        if device.inventory_id and device.inventory:
            inv = device.inventory
            inventory_payload = {
                "id": inv.id,
                "reference": inv.reference,
                "label": inv.label,
            }

        return {
            "device_id": device.device_id,
            "label": device.label,
            "status": status,
            "last_seen_at": device.last_seen_at.isoformat(),
            "seconds_since_last_seen": seconds_since,
            "battery_level": device.battery_level,
            "is_charging": device.is_charging,
            "app_version": device.app_version,
            "user": user_payload,
            "warehouse": warehouse_payload,
            "inventory": inventory_payload,
        }
