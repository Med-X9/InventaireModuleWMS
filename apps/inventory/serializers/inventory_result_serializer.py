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
        Met le code interne du produit dans la clé product.
        """
        # Créer une copie pour ne pas modifier l'instance originale
        result = dict(instance)
        
        # Mettre le code interne dans la clé product si présent
        if 'product_internal_code' in result:
            result['product'] = result.pop('product_internal_code')
        
        return result


class InventoryWarehouseResultSerializer(serializers.Serializer):
    """Sérialiseur racine pour la réponse complète."""

    success = serializers.BooleanField()
    data = InventoryWarehouseResultEntrySerializer(many=True)

