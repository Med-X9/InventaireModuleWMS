"""
Sérialiseurs pour l'API de résultats d'inventaire.
"""
from rest_framework import serializers


class InventoryWarehouseResultEntrySerializer(serializers.Serializer):
    """
    Sérialiseur pour une ligne de résultat d'inventaire.

    Les clés dynamiques (ex: "1er comptage", "ecart_1_2") sont conservées telles quelles.
    """

    location = serializers.CharField()
    product = serializers.CharField(required=False, allow_null=True)

    def to_representation(self, instance):
        """
        Retourne la structure telle qu'elle est générée par le service, en conservant
        les clés dynamiques demandées par le métier.
        """
        return instance


class InventoryWarehouseResultSerializer(serializers.Serializer):
    """Sérialiseur racine pour la réponse complète."""

    success = serializers.BooleanField()
    data = InventoryWarehouseResultEntrySerializer(many=True)

