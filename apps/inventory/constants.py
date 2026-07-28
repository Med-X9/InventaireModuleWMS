"""
Constantes de domaine partagées pour l'application inventory.

Centralise les magic strings (modes de comptage, statuts, types)
afin d'éviter la duplication et les incohérences.
"""
from typing import Final, Tuple


# ---------------------------------------------------------------------------
# Modes de comptage
# ---------------------------------------------------------------------------
class CountMode:
    """Modes de comptage supportés."""

    IN_BULK: Final[str] = "en vrac"
    BY_ARTICLE: Final[str] = "par article"
    STOCK_IMAGE: Final[str] = "image de stock"
    STOCK_IMAGE_ALIAS: Final[str] = "image stock"

    ALL: Final[Tuple[str, ...]] = (IN_BULK, BY_ARTICLE, STOCK_IMAGE)
    ALL_WITH_ALIASES: Final[Tuple[str, ...]] = (
        IN_BULK,
        BY_ARTICLE,
        STOCK_IMAGE,
        STOCK_IMAGE_ALIAS,
    )


# ---------------------------------------------------------------------------
# Statuts Inventaire
# ---------------------------------------------------------------------------
class InventoryStatus:
    EN_CONFIGURATION: Final[str] = "EN CONFIGURATION"
    EN_PREPARATION: Final[str] = "EN PREPARATION"
    EN_REALISATION: Final[str] = "EN REALISATION"
    TERMINE: Final[str] = "TERMINE"
    CLOTURE: Final[str] = "CLOTURE"

    ALL: Final[Tuple[str, ...]] = (
        EN_CONFIGURATION,
        EN_PREPARATION,
        EN_REALISATION,
        TERMINE,
        CLOTURE,
    )


# ---------------------------------------------------------------------------
# Types d'inventaire
# ---------------------------------------------------------------------------
class InventoryType:
    TOURNANT: Final[str] = "TOURNANT"
    GENERAL: Final[str] = "GENERAL"
    MAGASIN: Final[str] = "MAGASIN"

    ALL: Final[Tuple[str, ...]] = (TOURNANT, GENERAL, MAGASIN)
    # Types à un seul comptage (créés sans comptages — config ultérieure)
    SINGLE_COUNTING: Final[Tuple[str, ...]] = (TOURNANT, MAGASIN)
    # Lancement warehouse : couverture complète (tous emplacements + tous jobs PRET)
    FULL_COVERAGE_LAUNCH: Final[Tuple[str, ...]] = (GENERAL, MAGASIN)


# ---------------------------------------------------------------------------
# Statuts Setting (lien compte / entrepôt / inventaire)
# ---------------------------------------------------------------------------
class SettingStatus:
    EN_ATTENTE: Final[str] = "EN ATTENTE"
    LANCEE: Final[str] = "LANCEE"
    TERMINEE: Final[str] = "TERMINEE"
    ANALYSER: Final[str] = "ANALYSER"
    CLOTURE: Final[str] = "CLOTURE"


# ---------------------------------------------------------------------------
# Statuts Job
# ---------------------------------------------------------------------------
class JobStatus:
    EN_ATTENTE: Final[str] = "EN ATTENTE"
    AFFECTE: Final[str] = "AFFECTE"
    PRET: Final[str] = "PRET"
    TRANSFERT: Final[str] = "TRANSFERT"
    ENTAME: Final[str] = "ENTAME"
    VALIDE: Final[str] = "VALIDE"
    TERMINE: Final[str] = "TERMINE"
    SAISIE_MANUELLE: Final[str] = "SAISIE MANUELLE"
    ANNULE: Final[str] = "ANNULE"

    ACTIVE_FOR_TRANSFER: Final[Tuple[str, ...]] = (PRET, TRANSFERT, ENTAME)


# ---------------------------------------------------------------------------
# Statuts Assignment
# ---------------------------------------------------------------------------
class AssignmentStatus:
    EN_ATTENTE: Final[str] = "EN ATTENTE"
    AFFECTE: Final[str] = "AFFECTE"
    PRET: Final[str] = "PRET"
    TRANSFERT: Final[str] = "TRANSFERT"
    ENTAME: Final[str] = "ENTAME"
    TERMINE: Final[str] = "TERMINE"
    BLOQUE: Final[str] = "BLOQUE"
    DEBLOQUE: Final[str] = "DEBLOQUE"


# ---------------------------------------------------------------------------
# Statuts JobDetail
# ---------------------------------------------------------------------------
class JobDetailStatus:
    EN_ATTENTE: Final[str] = "EN ATTENTE"
    TERMINE: Final[str] = "TERMINE"
    ANNULE: Final[str] = "ANNULE"


# ---------------------------------------------------------------------------
# Types de session / ressource
# ---------------------------------------------------------------------------
class SessionType:
    MOBILE: Final[str] = "Mobile"
    WEB: Final[str] = "Web"


class ResourceLabel:
    INVENTAIRE: Final[str] = "inventaire"
    JOB: Final[str] = "job"


# ---------------------------------------------------------------------------
# Statuts compte utilisateur
# ---------------------------------------------------------------------------
class AccountStatus:
    ACTIVE: Final[str] = "ACTIVE"
    INACTIVE: Final[str] = "INACTIVE"


# ---------------------------------------------------------------------------
# Statuts entrepôt (masterdata)
# ---------------------------------------------------------------------------
class WarehouseStatus:
    ACTIVE: Final[str] = "ACTIVE"
    INACTIVE: Final[str] = "INACTIVE"


# ---------------------------------------------------------------------------
# Groupement écart stock théorique
# ---------------------------------------------------------------------------
class StockGapGrouping:
    """Clé de consolidation article selon Counting.is_variant."""

    BY_INTERNAL_CODE: Final[str] = "internal_product_code"
    BY_BARCODE: Final[str] = "barcode"
    # Alias historique
    BY_REFERENCE: Final[str] = BY_INTERNAL_CODE

    # Code produit test exclu des consolidations (aligné export Excel)
    EXCLUDED_INTERNAL_CODE: Final[str] = "111111111111111"


# ---------------------------------------------------------------------------
# Alias rétrocompatibles (imports plats)
# ---------------------------------------------------------------------------
COUNT_MODE_IN_BULK = CountMode.IN_BULK
COUNT_MODE_BY_ARTICLE = CountMode.BY_ARTICLE
COUNT_MODE_STOCK_IMAGE = CountMode.STOCK_IMAGE
SUPPORTED_COUNT_MODES = CountMode.ALL
