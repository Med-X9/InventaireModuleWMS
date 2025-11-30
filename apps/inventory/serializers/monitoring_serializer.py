"""
Serializers pour le monitoring par zone
"""
from rest_framework import serializers


class CountingMonitoringSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques de monitoring d'un comptage
    """
    counting_id = serializers.IntegerField()
    counting_reference = serializers.CharField()
    counting_order = serializers.IntegerField()
    jobs_en_attente = serializers.DictField()
    jobs_en_cours = serializers.DictField()
    jobs_termines = serializers.DictField()
    total_jobs = serializers.IntegerField()


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
    countings = CountingMonitoringSerializer(many=True)


class MonitoringResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse complète du monitoring par zone
    """
    zones = ZoneMonitoringSerializer(many=True)

