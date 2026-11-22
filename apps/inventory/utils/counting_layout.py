"""
Organisation des comptages d'un inventaire (mono-comptage ou multi-comptages).

MAGASIN / TOURNANT sont mono-comptage par défaut. Un inventaire MAGASIN en mode
« en vrac » peut être configuré avec 2 comptages (saisie quantité par emplacement) :
il suit alors les règles multi-comptages (consensus, 2 sessions, comptage final).
"""
from typing import Optional

from apps.inventory.constants import InventoryType


def has_multi_counting(inventory) -> bool:
    """True si l'inventaire possède un comptage d'ordre 2 (donc multi-comptages)."""
    from apps.inventory.models import Counting

    pk = getattr(inventory, 'pk', None)
    if not isinstance(pk, int):  # inventaire absent / non enregistré
        return False
    return Counting.objects.filter(inventory_id=inventory.pk, order=2).exists()


def is_single_counting_inventory(inventory) -> bool:
    """Mono-comptage effectif : type MAGASIN/TOURNANT sans comptage d'ordre 2."""
    if inventory is None:
        return False
    if inventory.inventory_type not in InventoryType.SINGLE_COUNTING:
        return False
    return not has_multi_counting(inventory)


def effective_counting_type(inventory) -> Optional[str]:
    """
    Type utilisé pour choisir les stratégies de comptage/écart/session.

    Un MAGASIN/TOURNANT multi-comptages est traité comme GENERAL (consensus).
    """
    if inventory is None:
        return None
    if inventory.inventory_type in InventoryType.SINGLE_COUNTING and has_multi_counting(inventory):
        return InventoryType.GENERAL
    return inventory.inventory_type


# Types de saisie exposés au mobile (champ count_type) — mode « en vrac » uniquement
COUNT_TYPE_QTE_ARTICLE = 'QTE_ARTICLE'          # en vrac : saisie quantité par article (product_id requis)
COUNT_TYPE_QTE_EMPLACEMENT = 'QTE_EMPLACEMENT'  # en vrac : saisie quantité totale par emplacement (sans produit)
COUNT_TYPE_SCAN_UNITE = 'SCAN_UNITE'            # en vrac : scan par unité
COUNT_TYPE_PAR_ARTICLE = 'PAR_ARTICLE'          # mode par article (valeur par défaut = le mode lui-même)
COUNT_TYPE_IMAGE_STOCK = 'IMAGE_STOCK'          # mode image de stock


def counting_count_type(counting) -> str:
    """
    Type de saisie d'un comptage en vrac, dérivé de sa configuration.
    Jamais null : par article -> PAR_ARTICLE, image de stock -> IMAGE_STOCK.

    MAGASIN à 3 comptages : le 2e comptage est « qté par emplacement »,
    les autres (1er, 3e, puis comptages supplémentaires) « qté par article ».
    """
    if counting.count_mode == 'par article':
        return COUNT_TYPE_PAR_ARTICLE
    if counting.count_mode == 'image de stock':
        return COUNT_TYPE_IMAGE_STOCK
    if counting.count_mode != 'en vrac':
        return str(counting.count_mode).upper().replace(' ', '_')
    if counting.unit_scanned:
        return COUNT_TYPE_SCAN_UNITE
    inventory = counting.inventory
    if inventory.inventory_type == InventoryType.MAGASIN and has_multi_counting(inventory):
        return COUNT_TYPE_QTE_EMPLACEMENT if counting.order == 2 else COUNT_TYPE_QTE_ARTICLE
    return COUNT_TYPE_QTE_EMPLACEMENT


def uses_location_ecart(inventory) -> bool:
    """
    True si l'écart est calculé par emplacement (tous articles confondus) :
    MAGASIN avec plusieurs comptages (en vrac). Les autres inventaires gardent
    l'écart par produit + emplacement.
    """
    if inventory is None:
        return False
    return inventory.inventory_type == InventoryType.MAGASIN and has_multi_counting(inventory)
