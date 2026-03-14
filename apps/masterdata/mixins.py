from django.db import models
import hashlib
from datetime import datetime
import base64
import random
import string
import time
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone

class CodeGeneratorMixin(models.Model):
    """
    Mixin pour générer des codes uniques pour les modèles.
    Utilise le created_at et l'ID du modèle pour générer un code unique.
    """
    class Meta:
        abstract = True

    @classmethod
    def generate_unique_code(cls, prefix, created_at=None, id=None, max_length=20):
        """
        Génère un code unique pour le modèle en utilisant created_at et l'ID.
        Format: PREFIX-XXXX où XXXX est un nombre aléatoire
        Si l'ID n'est pas encore disponible, utilise un timestamp et un UUID.
        S'assure que la longueur ne dépasse pas max_length (par défaut 20).
        """
        # Si l'ID n'est pas encore disponible (création), utiliser un timestamp et UUID
        if id is None:
            timestamp = int(timezone.now().timestamp())
            # Utiliser seulement les 4 derniers chiffres du timestamp pour économiser l'espace
            timestamp_short = str(timestamp)[-4:]
            uuid_short = str(uuid.uuid4())[:4].replace('-', '').upper()
            code = f"{prefix}-{timestamp_short}{uuid_short}"
            # S'assurer que la longueur ne dépasse pas max_length
            if len(code) > max_length:
                # Tronquer le UUID si nécessaire
                available_length = max_length - len(prefix) - 1 - 4  # prefix + '-' + timestamp
                if available_length > 0:
                    uuid_short = uuid_short[:available_length]
                    code = f"{prefix}-{timestamp_short}{uuid_short}"
                else:
                    # Si même le timestamp est trop long, utiliser seulement un nombre aléatoire
                    random_num = random.randint(1000, 9999)
                    code = f"{prefix}-{random_num}"
        else:
            # Générer un nombre aléatoire entre 1000 et 9999
            random_num = random.randint(1000, 9999)
            code = f"{prefix}-{random_num}"
        
        # Vérifier si le code existe déjà et en générer un nouveau si nécessaire
        max_attempts = 100
        attempt = 0
        while attempt < max_attempts:
            if not cls.objects.filter(reference=code).exists():
                # S'assurer que la longueur est correcte
                if len(code) <= max_length:
                    return code
            # Générer un nouveau code
            if id is None:
                timestamp = int(timezone.now().timestamp())
                timestamp_short = str(timestamp)[-4:]
                uuid_short = str(uuid.uuid4())[:4].replace('-', '').upper()
                code = f"{prefix}-{timestamp_short}{uuid_short}"
                if len(code) > max_length:
                    available_length = max_length - len(prefix) - 1 - 4
                    if available_length > 0:
                        uuid_short = uuid_short[:available_length]
                        code = f"{prefix}-{timestamp_short}{uuid_short}"
                    else:
                        random_num = random.randint(1000, 9999)
                        code = f"{prefix}-{random_num}"
            else:
                random_num = random.randint(1000, 9999)
                code = f"{prefix}-{random_num}"
            attempt += 1
        
        # Si on n'a pas trouvé de code unique après 100 tentatives, utiliser un timestamp court
        timestamp = int(time.time())
        timestamp_short = str(timestamp)[-4:]
        random_num = random.randint(100, 999)
        code = f"{prefix}-{timestamp_short}{random_num}"
        # Tronquer si nécessaire
        if len(code) > max_length:
            code = code[:max_length]
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
        Surcharge de la méthode save pour générer un code unique si nécessaire.
        Génère la référence AVANT la première sauvegarde pour éviter les violations
        de contrainte unique lors d'imports multiples.
        """
        if not self.reference:
            prefix = getattr(self, 'CODE_PREFIX', self.__class__.__name__[:3].upper())
            # Générer une référence unique AVANT la sauvegarde pour éviter les conflits
            # Utilise un timestamp et UUID si l'ID n'est pas encore disponible
            code = self.generate_unique_code(prefix, created_at=None, id=None)
            self.reference = code
            # Sauvegarder avec la référence déjà générée
            super().save(*args, **kwargs)
            # Optionnel : régénérer avec l'ID réel après la sauvegarde si souhaité
            # (pour l'instant, on garde la référence générée avec timestamp/UUID)
        else:
            super().save(*args, **kwargs) 