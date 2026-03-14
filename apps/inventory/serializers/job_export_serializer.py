from rest_framework import serializers


class JobExportSerializer(serializers.Serializer):
    """
    Serializer pour l'export des jobs prêts
    """
    reference_job = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    code_article = serializers.CharField(read_only=True)
    code_barre = serializers.CharField(read_only=True)
    quantite = serializers.IntegerField(read_only=True)
    session_affectee = serializers.CharField(read_only=True)
    premier_comptage = serializers.IntegerField(read_only=True)
    deuxieme_comptage = serializers.IntegerField(read_only=True)
    ligne_numero = serializers.IntegerField(read_only=True)

