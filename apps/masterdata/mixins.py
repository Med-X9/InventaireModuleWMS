from django.db import models
import hashlib
from datetime import datetime
import base64
import random
import string
from django.core.exceptions import ValidationError

class CodeGeneratorMixin(models.Model):
    """
    Mixin pour générer des codes uniques pour les modèles.
    Utilise le created_at et l'ID du modèle pour générer un code unique.
    """
    class Meta:
        abstract = True

    @classmethod
    def generate_unique_code(cls, prefix, created_at, id):
        """
        Génère un code unique pour le modèle en utilisant created_at et l'ID.
        Format: PREFIX-TIMESTAMP-ID-HASH
        """
        # Convertir created_at en timestamp
        timestamp = int(created_at.timestamp())
        
        # Créer une chaîne à chiffrer
        data_to_hash = f"{prefix}{timestamp}{id}"
        
        # Chiffrer avec SHA-256 et prendre les 8 premiers caractères
        hash_value = hashlib.sha256(data_to_hash.encode()).hexdigest()[:8].upper()
        
        # Construire le code final
        code = f"{prefix}-{timestamp}-{id}-{hash_value}"
        
        return code

    @classmethod
    def get_code_field_name(cls):
        """
        Retourne le nom du champ qui contient le code.
        Par défaut, cherche un champ contenant 'code' dans son nom.
        """
        for field in cls._meta.fields:
            if 'code' in field.name.lower():
                return field.name
        raise AttributeError(f"No code field found in {cls.__name__}")

    def clean(self):
        """
        Validation pour s'assurer que le code est présent
        """
        code_field = self.get_code_field_name()
        if not getattr(self, code_field):
            raise ValidationError({
                code_field: "Le code est requis"
            })

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour générer un code unique si nécessaire
        """
        code_field = self.get_code_field_name()
        if not getattr(self, code_field):
            prefix = getattr(self, 'CODE_PREFIX', self.__class__.__name__[:3].upper())
            # Sauvegarder d'abord pour obtenir l'ID
            super().save(*args, **kwargs)
            # Générer le code avec created_at et l'ID
            code = self.generate_unique_code(prefix, self.created_at, self.id)
            setattr(self, code_field, code)
            # Sauvegarder à nouveau avec le code
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs) 