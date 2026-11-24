"""
Serializers pour le monitoring (par zone et global)
"""
from rest_framework import serializers


class AssignmentDetailSerializer(serializers.Serializer):
    """
    Serializer pour les détails d'un assignment avec son statut et pourcentage
    """
    status = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class LocationProgressSerializer(serializers.Serializer):
    """
    Avancement des emplacements d'un comptage (par article ou en vrac).
    """
    count_mode = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    total_emplacements = serializers.IntegerField(required=False)
    emplacements_termines = serializers.IntegerField(required=False)
    emplacements_termines_percent = serializers.FloatField(required=False)
    emplacements_en_attente = serializers.IntegerField(required=False)
    emplacements_en_attente_percent = serializers.FloatField(required=False)


class CountingMonitoringSerializer(LocationProgressSerializer):
    """
    Serializer pour les statistiques de monitoring d'un comptage
    """
    counting_id = serializers.IntegerField()
    counting_reference = serializers.CharField()
    counting_order = serializers.IntegerField()
    nombre_jobs = serializers.IntegerField()
    assignments = AssignmentDetailSerializer(many=True)


class ZoneMonitoringSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques de monitoring d'une zone
    """
    zone_id = serializers.IntegerField()
    zone_reference = serializers.CharField()
    zone_name = serializers.CharField()
    nombre_jobs = serializers.IntegerField()
    nombre_emplacements = serializers.IntegerField()
    countings = CountingMonitoringSerializer(many=True)


class MonitoringResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse complète du monitoring par zone
    """
    zones = ZoneMonitoringSerializer(many=True)


class CountingGlobalMonitoringSerializer(LocationProgressSerializer):
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

