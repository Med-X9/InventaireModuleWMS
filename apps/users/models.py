from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import Group, Permission
from simple_history.models import HistoricalRecords
from datetime import datetime
from django.utils.translation import gettext_lazy as _
# Create your models here.


class UserAppManager(BaseUserManager):
    def create_user(self, username, type, password=None, **extra_fields):
        if not username:
            raise ValueError('Le champ username doit être renseigné.')
        user = self.model(username=username, type=type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, type, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, type, password, **extra_fields)
    


class UserApp(AbstractBaseUser, PermissionsMixin, models.Model): 

    TYPES = (
        ('Web', _('Web')),
        ('Mobile', _('Mobile')),

    )

    username = models.CharField(_('Nom d\'utilisateur'), max_length=150, unique=True)
    email = models.EmailField(_('Email'), blank=True, null=True)
    nom = models.CharField(_('Nom'), max_length=255)
    prenom = models.CharField(_('Prénom'), max_length=255)
    type = models.CharField(_('Type'), max_length=100, choices=TYPES)
    is_active = models.BooleanField(_('Actif'), default=True)
    is_staff = models.BooleanField(_('Administrateur'), default=False)
    
    objects = UserAppManager()
    history = HistoricalRecords()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['type']

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groupes'),
        blank=True,
        related_name='user_web_groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions utilisateur'),
        blank=True,
        related_name='user_web_permissions'
    )

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
