from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Commande de gestion pour créer (ou mettre à jour) un superutilisateur par défaut.
    """

    help = "Crée un superutilisateur 'mohammed' avec le mot de passe 'admin1234' s'il n'existe pas."

    def handle(self, *args, **options):
        User = get_user_model()

        username = "mohammed"
        password = "admin1234"
        email = "mohammed@smatch.ma"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_superuser": True,
                "is_staff": True,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS("Superutilisateur 'mohammed' créé avec succès."))
        else:
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                updated_fields = ["is_superuser", "is_staff"]
            else:
                updated_fields = []

            if not user.check_password(password):
                user.set_password(password)
                updated_fields.append("password")

            if updated_fields:
                user.save(update_fields=updated_fields)
                self.stdout.write(self.style.WARNING("Superutilisateur 'mohammed' existant mis à jour (droits/mot de passe)."))
            else:
                self.stdout.write(self.style.WARNING("Superutilisateur 'mohammed' existe déjà avec les mêmes informations."))

