from rest_framework import serializers
from ..models import Job, JobDetail, Location, Pda
from django.utils import timezone
import datetime

class EmplacementSerializer(serializers.Serializer):
    emplacements = serializers.ListField(child=serializers.IntegerField())

class PdaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nom = serializers.CharField()
    session = serializers.IntegerField()

class JobDetailSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(source='location.id')
    location_name = serializers.CharField(source='location.location_code')
    pda_name = serializers.CharField(source='pda.lebel')
    pda_session = serializers.IntegerField(source='pda.session.id')

    class Meta:
        model = JobDetail
        fields = ['id', 'location_id', 'location_name', 'pda_name', 'pda_session', 'status']

class JobSerializer(serializers.ModelSerializer):
    details = JobDetailSerializer(source='jobdetail_set', many=True, read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'reference', 'status', 'details']

class InventoryJobRetrieveSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    jobs = EmplacementSerializer(many=True)
    pda = PdaSerializer(many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convertir le datetime en date si c'est un objet datetime
        if isinstance(data['date'], (datetime.datetime, datetime.date)):
            data['date'] = data['date'].date()
        return data 

class PdaUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nom = serializers.CharField()
    session = serializers.IntegerField()

class InventoryJobUpdateSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    jobs = serializers.ListField(
        child=serializers.DictField(
            child=serializers.ListField(
                child=serializers.IntegerField()
            )
        )
    )
    pda = PdaUpdateSerializer(many=True, required=False)

class JobAssignmentSerializer(serializers.Serializer):
    """Serializer pour l'affectation des jobs à l'équipe"""
    equipe = serializers.IntegerField()
    jobs = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )

    def validate_jobs(self, value):
        """
        Valide le format des jobs
        Format attendu: [{"id": int, "date": str}]
        """
        for job_data in value:
            if not isinstance(job_data, dict):
                raise serializers.ValidationError("Format de job invalide")
            if 'id' not in job_data or 'date' not in job_data:
                raise serializers.ValidationError("Format de job invalide: id et date requis")
            try:
                int(job_data['id'])  # Vérifier que l'ID est un nombre
            except (ValueError, TypeError):
                raise serializers.ValidationError("ID de job invalide")
        return value

class JobAssignmentRequestSerializer(serializers.Serializer):
    """Serializer pour la requête d'affectation des jobs"""
    assignments = JobAssignmentSerializer(many=True)

class PendingJobSerializer(serializers.ModelSerializer):
    equipe = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'reference', 'status', 'date_estime', 'equipe']

    def get_equipe(self, obj):
        job_detail = obj.jobdetail_set.first()
        if job_detail and job_detail.pda:
            return {
                'id': job_detail.pda.id,
                'nom': job_detail.pda.lebel
            }
        return None 