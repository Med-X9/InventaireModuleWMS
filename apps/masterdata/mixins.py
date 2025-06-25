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
        Format: PREFIX-XXXX où XXXX est un nombre aléatoire
        """
        # Générer un nombre aléatoire entre 1000 et 9999
        random_num = random.randint(1000, 9999)
        
        # Construire le code final
        code = f"{prefix}-{random_num}"
        
        return code

    @classmethod
    def get_code_field_name(cls):
        """
        Retourne le nom du champ qui contient le code.
        Par défaut, retourne 'reference'.
        """
        return 'reference'

    def clean(self):
        """
        Validation pour s'assurer que le code est présent
        """
        code_field = self.get_code_field_name()
        if not getattr(self, code_field):
            # Ne pas lever d'erreur si c'est un nouveau modèle
            if not self.pk:
                return
            raise ValidationError({
                code_field: "Le code est requis"
            })

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour générer un code unique si nécessaire
        """
        if not self.reference:
            prefix = getattr(self, 'CODE_PREFIX', self.__class__.__name__[:3].upper())
            # Sauvegarder d'abord pour obtenir l'ID
            super().save(*args, **kwargs)
            # Générer le code avec created_at et l'ID
            code = self.generate_unique_code(prefix, self.created_at, self.id)
            self.reference = code
            # Sauvegarder à nouveau avec le code
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs) 