"""
Serializers pour le monitoring (par zone et global)
"""
from rest_framework import serializers


class CountingMonitoringSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques de monitoring d'un comptage
    """
    counting_id = serializers.IntegerField()
    counting_reference = serializers.CharField()
    counting_order = serializers.IntegerField()
    nombre_jobs = serializers.IntegerField()
    nombre_emplacements = serializers.IntegerField()


class ZoneMonitoringSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques de monitoring d'une zone
    """
    zone_id = serializers.IntegerField()
    zone_reference = serializers.CharField()
    zone_name = serializers.CharField()
    status = serializers.CharField()
    nombre_equipes = serializers.IntegerField()
    nombre_jobs = serializers.IntegerField()
    nombre_emplacements = serializers.IntegerField()
    countings = CountingMonitoringSerializer(many=True)


class MonitoringResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse complète du monitoring par zone
    """
    zones = ZoneMonitoringSerializer(many=True)


class CountingGlobalMonitoringSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques globales d'un comptage
    (toutes zones confondues).
    """

    counting_id = serializers.IntegerField()
    counting_order = serializers.IntegerField()
    jobs_termines = serializers.IntegerField()
    jobs_termines_percent = serializers.FloatField()


class GlobalMonitoringSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques globales d'un inventaire / entrepôt.
    """

    total_equipes = serializers.IntegerField()
    total_jobs = serializers.IntegerField()
    countings = CountingGlobalMonitoringSerializer(many=True)

