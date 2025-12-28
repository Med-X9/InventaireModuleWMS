"""
Serializer pour les données de job discrepancies.
"""
from rest_framework import serializers


class AssignmentDiscrepancySerializer(serializers.Serializer):
    """
    Serializer pour un assignment dans le contexte de discrepancies.
    
    Note: Ne contient pas id, reference, personne_nom, personne_two_nom
    selon les spécifications.
    """
    status = serializers.CharField(allow_null=True)
    counting_reference = serializers.CharField(allow_null=True)
    counting_order = serializers.IntegerField(allow_null=True)
    username = serializers.CharField(allow_null=True)
    discrepancy_count = serializers.IntegerField(allow_null=True, required=False)
    discrepancy_rate = serializers.FloatField(allow_null=True, required=False)


class JobDiscrepancySerializer(serializers.Serializer):
    """
    Serializer pour les données de job avec écarts.

    Supporte tous les comptages standardisés (1er, 2ème, 3ème, n-ème).
    Les assignments sont standardisés : si un job a moins de comptages,
    des assignments vides sont ajoutés.
    """
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()
    job_status = serializers.CharField()
    assignments = AssignmentDiscrepancySerializer(many=True)

    # Écarts entre 1er et 2ème comptage
    discrepancy_count_1_2 = serializers.IntegerField()
    discrepancy_rate_1_2 = serializers.FloatField()

    # Écarts pour le Nème comptage (par rapport au 1er comptage)
    discrepancy_count_n = serializers.IntegerField(required=False, allow_null=True)

    total_lines_counting_1 = serializers.IntegerField()
    total_lines_counting_2 = serializers.IntegerField()
    common_lines_count = serializers.IntegerField()
    total_emplacements = serializers.IntegerField(required=False)


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

