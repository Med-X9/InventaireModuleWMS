"""
Serializer pour les données de job discrepancies.
"""
from rest_framework import serializers


class AssignmentDiscrepancySerializer(serializers.Serializer):
    """Serializer pour un assignment dans le contexte de discrepancies"""
    id = serializers.IntegerField()
    reference = serializers.CharField()
    status = serializers.CharField()
    counting_reference = serializers.CharField(allow_null=True)
    counting_order = serializers.IntegerField(allow_null=True)
    personne_nom = serializers.CharField(allow_null=True)
    personne_two_nom = serializers.CharField(allow_null=True)


class JobDiscrepancySerializer(serializers.Serializer):
    """Serializer pour les données de job avec écarts"""
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()
    job_status = serializers.CharField()
    assignments = AssignmentDiscrepancySerializer(many=True)
    discrepancy_count = serializers.IntegerField()
    discrepancy_rate = serializers.FloatField()
    total_lines_counting_1 = serializers.IntegerField()
    total_lines_counting_2 = serializers.IntegerField()
    common_lines_count = serializers.IntegerField()

