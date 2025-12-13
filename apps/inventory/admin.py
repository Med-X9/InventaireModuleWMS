from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import (
    CountingDetail,
    NSerieInventory,
    ComptageSequence,
    Counting,
    Job,
)


class CountingDetailResource(resources.ModelResource):
    """Resource d'import/export pour CountingDetail."""

    counting = fields.Field(
        column_name="counting_reference",
        attribute="counting",
        widget=ForeignKeyWidget(Counting, "reference"),
    )
    job = fields.Field(
        column_name="job_reference",
        attribute="job",
        widget=ForeignKeyWidget(Job, "reference"),
    )
    location = fields.Field(
        column_name="location_reference",
        attribute="location",
        widget=ForeignKeyWidget(
            "apps.masterdata.Location", "location_reference"
        ),
    )
    product = fields.Field(
        column_name="product_reference",
        attribute="product",
        widget=ForeignKeyWidget(
            "apps.masterdata.Product", "reference"
        ),
    )

    class Meta:
        model = CountingDetail
        fields = (
            "reference",
            "quantity_inventoried",
            "dlc",
            "n_lot",
            "counting",
            "job",
            "location",
            "product",
            "last_synced_at",
        )
        import_id_fields = ("reference",)


class NSerieInventoryInline(admin.TabularInline):
    """Inline des numéros de série liés à un détail de comptage."""

    model = NSerieInventory
    extra = 0


class ComptageSequenceInline(admin.TabularInline):
    """Inline des séquences de comptage liées à un détail de comptage."""

    model = ComptageSequence
    extra = 0


@admin.register(CountingDetail)
class CountingDetailAdmin(ImportExportModelAdmin):
    """Configuration de l'admin pour la table CountingDetail."""

    resource_class = CountingDetailResource
    list_display = (
        "reference",
        "counting",
        "job",
        "location",
        "product",
        "quantity_inventoried",
        "dlc",
        "n_lot",
        "last_synced_at",
    )
    list_filter = (
        "counting",
        "job",
        "location",
        "product",
        "dlc",
        "last_synced_at",
    )
    search_fields = (
        "reference",
        "n_lot",
        "job__reference",
        "counting__reference",
    )
    raw_id_fields = ("product", "location", "counting", "job")
    inlines = (NSerieInventoryInline, ComptageSequenceInline)


@admin.register(NSerieInventory)
class NSerieInventoryAdmin(admin.ModelAdmin):
    """Admin pour la gestion des numéros de série d'inventaire."""

    list_display = ("reference", "counting_detail", "n_serie")
    list_filter = ("counting_detail",)
    search_fields = ("reference", "n_serie")
    raw_id_fields = ("counting_detail",)


@admin.register(ComptageSequence)
class ComptageSequenceAdmin(admin.ModelAdmin):
    """Admin pour la gestion des séquences de comptage."""

    list_display = (
        "reference",
        "ecart_comptage",
        "sequence_number",
        "counting_detail",
        "quantity",
        "ecart_with_previous",
    )
    list_filter = ("ecart_comptage", "counting_detail")
    search_fields = ("reference",)
    raw_id_fields = ("ecart_comptage", "counting_detail")
