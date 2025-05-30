from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class MobileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'date_joined',
            'last_login'
        ] 