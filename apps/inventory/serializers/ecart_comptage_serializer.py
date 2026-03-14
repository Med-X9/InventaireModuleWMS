from rest_framework import serializers
from apps.inventory.models import EcartComptage, ComptageSequence


class EcartComptageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcartComptage
        fields = [
            'id', 'reference', 'inventory',
            'total_sequences', 'stopped_sequence',
            'final_result', 'justification', 'resolved',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'total_sequences', 'stopped_sequence', 'created_at', 'updated_at']


class ComptageSequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComptageSequence
        fields = [
            'id', 'reference', 'ecart_comptage', 'sequence_number',
            'counting_detail', 'quantity', 'ecart_with_previous',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'sequence_number', 'ecart_with_previous', 'created_at', 'updated_at']


