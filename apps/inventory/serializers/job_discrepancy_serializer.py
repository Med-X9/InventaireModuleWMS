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


class SimplifiedAssignmentSerializer(serializers.Serializer):
    """
    Serializer simplifié pour les assignments : counting_order, status, username.
    """
    counting_order = serializers.IntegerField()
    status = serializers.CharField()
    username = serializers.CharField()


class JobDiscrepancySerializer(serializers.Serializer):
    """
    Serializer simplifié pour les données de job avec écarts.

    Format demandé par l'utilisateur.
    """
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()
    job_status = serializers.CharField()
    assignments = SimplifiedAssignmentSerializer(many=True)
    nombre_comptage = serializers.IntegerField()
    ecart_1_vs_2_count = serializers.IntegerField()
    ecart_1_vs_2_rate = serializers.FloatField()
    nombre_ecart_3er = serializers.IntegerField()
    # Champs pour compatibilité DataTable
    discrepancy_count = serializers.IntegerField()
    discrepancy_rate = serializers.FloatField()
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

