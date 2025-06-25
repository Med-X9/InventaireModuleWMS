from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import UserApp

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserAppSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle UserApp
    """
    class Meta:
        model = UserApp
        fields = ['id', 'username', 'email', 'nom', 'prenom', 'role']

class MobileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
           
        ] 