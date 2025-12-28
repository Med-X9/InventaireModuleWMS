"""
Serializer pour les données de job discrepancies.
"""
from rest_framework import serializers


class AssignmentDiscrepancySerializer(serializers.Serializer):
    """
    Serializer pour un assignment dans le contexte de discrepancies.

    Format simplifié : status, counting_order, username uniquement.
    """
    status = serializers.CharField(allow_null=True)
    counting_order = serializers.IntegerField(allow_null=True)
    username = serializers.CharField(allow_null=True)


class JobDiscrepancySerializer(serializers.Serializer):
    """
    Serializer pour les données de job avec écarts.

    Supporte tous les comptages standardisés (1er, 2ème, 3ème, n-ème).
    Format simplifié avec discrepancy_count_3er et discrepancy_count_4er.
    """
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()
    job_status = serializers.CharField()
    assignments = AssignmentDiscrepancySerializer(many=True)
    discrepancy_count = serializers.IntegerField()
    discrepancy_rate = serializers.FloatField()
    discrepancy_count_3er = serializers.IntegerField(allow_null=True, required=False)
    discrepancy_count_4er = serializers.IntegerField(allow_null=True, required=False)


class JobByCountingSerializer(serializers.Serializer):
    """Serializer pour un job avec ses informations d'écarts dans un groupe de comptage."""
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()
    current_max_counting = serializers.IntegerField()
    has_unresolved_discrepancies = serializers.BooleanField()
    discrepancies_locations_count = serializers.IntegerField()


class CountingJobsDiscrepancySerializer(serializers.Serializer):
    """
    Serializer pour « jobs nécessitant un prochain comptage groupés par numéro de comptage ».
    """
    next_counting_order = serializers.IntegerField()
    jobs = JobByCountingSerializer(many=True)

