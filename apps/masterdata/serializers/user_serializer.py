from rest_framework import serializers
from apps.users.models import UserApp

class MobileUserSerializer(serializers.ModelSerializer):
    """
    Serializer pour les utilisateurs de type Mobile
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserApp
        fields = [
            'id',
            'username',
            'email',
            'nom',
            'prenom',
            'full_name',
            'type',
            'is_active',
            'is_staff',
            'date_joined',
            'last_login'
        ]
        read_only_fields = ['date_joined', 'last_login']

    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        return f"{obj.prenom} {obj.nom}"

class MobileUserListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des utilisateurs mobile (version simplifiée)
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserApp
        fields = [
            'id',
            'username',
            'full_name',
            'type',
            'is_active',
            'date_joined'
        ]
        read_only_fields = ['date_joined']

    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        return f"{obj.prenom} {obj.nom}" 