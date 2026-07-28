"""
Serializers pour EcartStockTheorique.
"""
from rest_framework import serializers

from apps.inventory.models import EcartStockTheorique


class EcartStockTheoriqueSerializer(serializers.ModelSerializer):
    """Lecture d'une ligne d'écart stock théorique / pratique."""

    warehouse_name = serializers.CharField(
        source="warehouse.warehouse_name", read_only=True
    )
    validated_by_username = serializers.CharField(
        source="validated_by.username", read_only=True, allow_null=True
    )

    class Meta:
        model = EcartStockTheorique
        fields = [
            "id",
            "reference",
            "inventory",
            "warehouse",
            "warehouse_name",
            "article_cle",
            "mode_groupement",
            "designation",
            "product",
            "qte_theorique",
            "qte_pratique",
            "ecart",
            "resultat_final",
            "valide",
            "validated_at",
            "validated_by",
            "validated_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class EcartStockTheoriqueUpdateSerializer(serializers.Serializer):
    """Body PATCH pour saisir le résultat final."""

    resultat_final = serializers.IntegerField()


class EcartStockTheoriqueSyncSerializer(serializers.Serializer):
    """Body optionnel pour la sync."""

    only_nonzero = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Si true, n'importe que les lignes avec écart ≠ 0",
    )


class EcartStockTheoriqueValiderSelectionSerializer(serializers.Serializer):
    """Body POST multi-validation par sélection."""

    ecart_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="IDs des lignes EcartStockTheorique à valider",
    )
