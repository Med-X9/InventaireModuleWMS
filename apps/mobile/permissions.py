"""
Permissions pour l'application mobile.

Règles :
- Groupe **admin** : accès à toutes les APIs mobile.
- Groupe **operateur** : accès à toutes les APIs sauf :
  - job/<id>/results/
  - inventory/<id>/warehouse/<id>/jobs/both-countings-terminated/
"""
from rest_framework.permissions import BasePermission


# Noms des URLs réservées au groupe admin (opérateur refusé)
RESTRICTED_URL_NAMES = frozenset({
    "mobile_job_results",
    "mobile_jobs_both_countings_terminated",
})

# Noms des groupes (comparaison insensible à la casse)
GROUP_ADMIN = "admin"
GROUP_OPERATEUR = "operateur"


def _user_group_names(user):
    """Retourne l'ensemble des noms de groupes de l'utilisateur (minuscules)."""
    if not user or not user.is_authenticated:
        return set()
    try:
        if not hasattr(user, "groups"):
            return set()
        return {g.name.strip().lower() for g in user.groups.all()}
    except Exception:
        return set()


def is_admin(user):
    """True si l'utilisateur appartient au groupe admin."""
    return GROUP_ADMIN in _user_group_names(user)


def is_operateur(user):
    """True si l'utilisateur appartient au groupe operateur."""
    return GROUP_OPERATEUR in _user_group_names(user)


class MobileGroupPermission(BasePermission):
    """
    Permission basée sur les groupes (admin / operateur).

    - Utilisateur authentifié dans le groupe **admin** : accès à tout.
    - Utilisateur authentifié dans le groupe **operateur** : accès à tout
      sauf aux endpoints dont le nom d'URL est dans RESTRICTED_URL_NAMES.
    - Utilisateur sans groupe admin/operateur : pas d'accès aux APIs mobile
      protégées par cette permission.
    """

    message = (
        "Vous n'avez pas la permission d'accéder à cette ressource. "
        "Assurez-vous que votre utilisateur appartient au groupe « admin » ou « operateur »."
    )

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        groups = _user_group_names(request.user)

        # Superusers ont tous les droits
        if getattr(request.user, "is_superuser", False):
            return True

        if GROUP_ADMIN in groups:
            return True

        if GROUP_OPERATEUR in groups:
            url_name = getattr(
                getattr(request, "resolver_match", None),
                "url_name",
                None,
            )
            if url_name in RESTRICTED_URL_NAMES:
                return False
            return True

        # Ni admin ni operateur
        return False


class MobileAdminOnlyPermission(BasePermission):
    """
    Permission réservée au groupe admin uniquement.

    À utiliser sur les endpoints que les opérateurs ne doivent pas appeler
    (ex. résultats de job, jobs both-countings-terminated).
    """

    message = "Cette ressource est réservée aux utilisateurs du groupe admin."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return is_admin(request.user)
