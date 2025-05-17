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