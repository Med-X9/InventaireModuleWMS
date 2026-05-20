from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.masterdata.models import TimeStampedModel


class Device(TimeStampedModel):
    """
    Terminal PDA — dernier signal via heartbeat HTTP (pas de statut online stocké).
    """

    device_id = models.CharField(max_length=128, unique=True, db_index=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pda_devices",
    )
    battery_level = models.PositiveSmallIntegerField(null=True, blank=True)
    is_charging = models.BooleanField(default=False)
    app_version = models.CharField(max_length=20, blank=True, null=True)
    last_seen_at = models.DateTimeField(db_index=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    warehouse = models.ForeignKey(
        "masterdata.Warehouse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pda_devices",
    )
    inventory = models.ForeignKey(
        "inventory.Inventory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pda_devices",
    )

    class Meta:
        verbose_name = _("Terminal PDA")
        verbose_name_plural = _("Terminaux PDA")
        indexes = [
            models.Index(fields=["-last_seen_at"], name="device_last_seen_idx"),
            models.Index(fields=["user"], name="device_user_idx"),
        ]

    def __str__(self):
        return self.label or self.device_id
