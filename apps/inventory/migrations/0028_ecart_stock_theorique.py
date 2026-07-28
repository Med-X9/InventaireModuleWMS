# Generated manually — table EcartStockTheorique

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0027_inventory_status_en_configuration"),
        ("masterdata", "0019_stock_location_nullable"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EcartStockTheorique",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("reference", models.CharField(max_length=20, unique=True)),
                (
                    "article_cle",
                    models.CharField(
                        help_text="Barcode ou Internal_Product_Code selon le mode de groupement",
                        max_length=255,
                        verbose_name="Clé article",
                    ),
                ),
                (
                    "mode_groupement",
                    models.CharField(
                        max_length=50, verbose_name="Mode de groupement"
                    ),
                ),
                (
                    "designation",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        verbose_name="Désignation",
                    ),
                ),
                (
                    "qte_theorique",
                    models.IntegerField(
                        default=0, verbose_name="Quantité théorique"
                    ),
                ),
                (
                    "qte_pratique",
                    models.IntegerField(
                        default=0, verbose_name="Quantité pratique"
                    ),
                ),
                (
                    "ecart",
                    models.IntegerField(
                        default=0,
                        help_text="théorique - pratique (signe conservé)",
                        verbose_name="Écart",
                    ),
                ),
                (
                    "resultat_final",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Résultat final"
                    ),
                ),
                (
                    "valide",
                    models.BooleanField(default=False, verbose_name="Validé"),
                ),
                (
                    "validated_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Date de validation"
                    ),
                ),
                (
                    "inventory",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ecarts_stock_theorique",
                        to="inventory.inventory",
                        verbose_name="Inventaire",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ecarts_stock_theorique",
                        to="masterdata.product",
                        verbose_name="Produit",
                    ),
                ),
                (
                    "validated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ecarts_stock_valides",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Validé par",
                    ),
                ),
                (
                    "warehouse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ecarts_stock_theorique",
                        to="masterdata.warehouse",
                        verbose_name="Magasin",
                    ),
                ),
            ],
            options={
                "verbose_name": "Écart stock théorique",
                "verbose_name_plural": "Écarts stock théorique",
                "ordering": ["article_cle", "id"],
            },
        ),
        migrations.CreateModel(
            name="HistoricalEcartStockTheorique",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(blank=True, editable=False)),
                ("updated_at", models.DateTimeField(blank=True, editable=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("reference", models.CharField(db_index=True, max_length=20)),
                (
                    "article_cle",
                    models.CharField(
                        help_text="Barcode ou Internal_Product_Code selon le mode de groupement",
                        max_length=255,
                        verbose_name="Clé article",
                    ),
                ),
                (
                    "mode_groupement",
                    models.CharField(
                        max_length=50, verbose_name="Mode de groupement"
                    ),
                ),
                (
                    "designation",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        verbose_name="Désignation",
                    ),
                ),
                (
                    "qte_theorique",
                    models.IntegerField(
                        default=0, verbose_name="Quantité théorique"
                    ),
                ),
                (
                    "qte_pratique",
                    models.IntegerField(
                        default=0, verbose_name="Quantité pratique"
                    ),
                ),
                (
                    "ecart",
                    models.IntegerField(
                        default=0,
                        help_text="théorique - pratique (signe conservé)",
                        verbose_name="Écart",
                    ),
                ),
                (
                    "resultat_final",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Résultat final"
                    ),
                ),
                (
                    "valide",
                    models.BooleanField(default=False, verbose_name="Validé"),
                ),
                (
                    "validated_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Date de validation"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "inventory",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="inventory.inventory",
                        verbose_name="Inventaire",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="masterdata.product",
                        verbose_name="Produit",
                    ),
                ),
                (
                    "validated_by",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Validé par",
                    ),
                ),
                (
                    "warehouse",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="masterdata.warehouse",
                        verbose_name="Magasin",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Écart stock théorique",
                "verbose_name_plural": "historical Écarts stock théorique",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.AddConstraint(
            model_name="ecartstocktheorique",
            constraint=models.UniqueConstraint(
                fields=(
                    "inventory",
                    "warehouse",
                    "article_cle",
                    "mode_groupement",
                ),
                name="uniq_ecart_stock_inv_wh_cle_mode",
            ),
        ),
        migrations.AddIndex(
            model_name="ecartstocktheorique",
            index=models.Index(
                fields=["inventory", "warehouse"], name="est_inv_wh_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="ecartstocktheorique",
            index=models.Index(fields=["valide"], name="est_valide_idx"),
        ),
        migrations.AddIndex(
            model_name="ecartstocktheorique",
            index=models.Index(
                fields=["inventory", "warehouse", "valide"],
                name="est_inv_wh_valide_idx",
            ),
        ),
    ]
