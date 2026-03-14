"""
Sérialiseurs pour l'import/export des utilisateurs
"""
from rest_framework import serializers
from ..models import UserApp
from apps.masterdata.models import Account


class UserExportSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'export des utilisateurs
    Utilisé uniquement pour le formatage des données d'export
    """
    compte_nom = serializers.CharField(source='compte.account_name', read_only=True, allow_null=True)
    is_active_display = serializers.SerializerMethodField()
    is_staff_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserApp
        fields = [
            'id',
            'username',
            'email',
            'nom',
            'prenom',
            'type',
            'compte_nom',
            'is_active_display',
            'is_staff_display',
        ]
    
    def get_is_active_display(self, obj):
        """Retourne 'Oui' ou 'Non' pour le statut actif"""
        return 'Oui' if obj.is_active else 'Non'
    
    def get_is_staff_display(self, obj):
        """Retourne 'Oui' ou 'Non' pour le statut administrateur"""
        return 'Oui' if obj.is_staff else 'Non'


class UserImportSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'import des utilisateurs
    Utilisé pour valider les données d'import
    """
    username = serializers.CharField(
        max_length=150,
        required=True,
        help_text="Nom d'utilisateur unique"
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Adresse email"
    )
    nom = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Nom de famille"
    )
    prenom = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Prénom"
    )
    type = serializers.ChoiceField(
        choices=UserApp.TYPES,
        required=True,
        help_text="Type d'utilisateur (Web ou Mobile)"
    )
    compte = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Nom du compte"
    )
    compte_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID du compte"
    )
    is_active = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Statut actif"
    )
    is_staff = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Statut administrateur"
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Mot de passe (optionnel lors de l'import)"
    )
    
    def validate_username(self, value):
        """Valide que le nom d'utilisateur n'est pas vide"""
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom d'utilisateur ne peut pas être vide")
        return value.strip()
    
    def validate_compte(self, value):
        """Valide que le compte existe si fourni"""
        if value and value.strip():
            try:
                Account.objects.get(account_name=value.strip())
            except Account.DoesNotExist:
                raise serializers.ValidationError(f"Compte '{value}' non trouvé")
        return value
    
    def validate_compte_id(self, value):
        """Valide que le compte existe si l'ID est fourni"""
        if value:
            try:
                Account.objects.get(id=value)
            except Account.DoesNotExist:
                raise serializers.ValidationError(f"Compte avec l'ID {value} non trouvé")
        return value

