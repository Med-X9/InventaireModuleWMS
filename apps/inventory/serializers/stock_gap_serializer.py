"""
Serializers pour l'API stock-gaps (lecture table EcartStockTheorique).
"""
from rest_framework import serializers


class StockGapLineSerializer(serializers.Serializer):
    """Ligne écart stock persistée (sans regroupement exposé)."""

    ecart_id = serializers.IntegerField()
    cle = serializers.CharField()
    designation = serializers.CharField(allow_blank=True)
    qte_theorique = serializers.IntegerField()
    qte_inventoriee = serializers.IntegerField()
    ecart = serializers.IntegerField()
    resultat_final = serializers.IntegerField(allow_null=True)
    valide = serializers.BooleanField()


class StockGapTotalsSerializer(serializers.Serializer):
    """Totaux."""

    qte_theorique = serializers.IntegerField()
    qte_inventoriee = serializers.IntegerField()
    ecart = serializers.IntegerField()
    nombre_lignes = serializers.IntegerField()
