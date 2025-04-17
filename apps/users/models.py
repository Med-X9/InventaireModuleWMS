from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import Group, Permission
from simple_history.models import HistoricalRecords
from datetime import datetime
# Create your models here.


class UserWebManager(BaseUserManager):
    def create_user(self, username, role, password=None, **extra_fields):
        if not username:
            raise ValueError('Le champ username doit être renseigné.')
        user = self.model(username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, role, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, role, password, **extra_fields)
class UserWeb(AbstractBaseUser, PermissionsMixin, models.Model):  
    ROLES = (
        ('Administrateur', 'Administrateur'),
        ('user', 'User'),
    )
    TYPE_CHOICES = (
        ('web', 'web'),
        ('mobile', 'mobile'),
    )

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True, null=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    role = models.CharField(max_length=100, choices=ROLES)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default="web")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False, verbose_name='Administrateur')
    
    objects = UserWebManager()
    history = HistoricalRecords()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role']

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name='user_web_groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name='user_web_permissions'
    )

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    class Meta:
        verbose_name = 'Utilisateur'
