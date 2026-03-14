"""
Exemple complet d'API DataTable avec toutes les fonctionnalités :
- Tri multi ou single
- Recherche globale
- Filtres multi ou single
- Exportation Excel et CSV

Ce fichier montre comment utiliser ServerSideDataTableView avec toutes les fonctionnalités.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.core.datatables.mixins import ServerSideDataTableView
from apps.core.datatables.exporters import export_manager
from ..models import Inventory
from ..serializers.inventory_serializer import InventoryDetailSerializer


class InventoryCompleteExampleView(ServerSideDataTableView):
    """
    Exemple complet d'API DataTable avec TOUTES les fonctionnalités
    
    FONCTIONNALITÉS SUPPORTÉES:
    ===========================
    
    1. TRI (Multi ou Single)
    -------------------------
    GET /api/inventory/?ordering=label                    # Tri single par label (asc)
    GET /api/inventory/?ordering=-created_at               # Tri single par date (desc)
    GET /api/inventory/?ordering=label,-date               # Tri multi (label asc, puis date desc)
    
    # Format DataTable
    GET /api/inventory/?order[0][column]=2&order[0][dir]=asc        # Tri single
    GET /api/inventory/?order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc  # Tri multi
    
    2. RECHERCHE GLOBALE
    --------------------
    GET /api/inventory/?search=inventaire                 # Recherche dans tous les search_fields
    GET /api/inventory/?search[value]=test                # Format DataTable
    
    3. FILTRES (Multi ou Single)
    -----------------------------
    # Filtres simples
    GET /api/inventory/?status=EN_PREPARATION             # Filtre single
    GET /api/inventory/?status=EN_PREPARATION&inventory_type=GENERAL  # Filtres multi
    
    # Filtres avec opérateurs
    GET /api/inventory/?label_contains=test               # Contient
    GET /api/inventory/?label_exact=Inventaire 2024       # Exact
    GET /api/inventory/?label_startswith=INV              # Commence par
    GET /api/inventory/?label_endswith=2024               # Termine par
    
    # Filtres de date
    GET /api/inventory/?date_exact=2024-01-15             # Date exacte
    GET /api/inventory/?date_start=2024-01-01&date_end=2024-12-31  # Plage de dates
    GET /api/inventory/?created_at_start=2024-01-01       # Date de création
    
    # Filtres de statut
    GET /api/inventory/?status=EN_PREPARATION            # Statut unique
    GET /api/inventory/?status_in=EN_PREPARATION,TERMINE  # Statuts multiples
    
    # Filtres combinés (multi)
    GET /api/inventory/?status=EN_PREPARATION&date_start=2024-01-01&label_contains=test
    
    4. EXPORTATION
    --------------
    GET /api/inventory/?export=excel                      # Export Excel
    GET /api/inventory/?export=csv                        # Export CSV
    
    # Export avec filtres appliqués
    GET /api/inventory/?status=EN_PREPARATION&export=excel
    GET /api/inventory/?date_start=2024-01-01&export=csv
    
    5. PAGINATION
    -------------
    GET /api/inventory/?page=1&page_size=25              # Format REST
    GET /api/inventory/?start=0&length=25                 # Format DataTable
    
    EXEMPLES COMPLETS:
    ==================
    
    # Tri multi + Recherche + Filtres + Pagination
    GET /api/inventory/?ordering=label,-date&search=test&status=EN_PREPARATION&page=1&page_size=20
    
    # Export avec tous les filtres
    GET /api/inventory/?status=EN_PREPARATION&date_start=2024-01-01&label_contains=test&export=excel
    """
    
    # Configuration minimale
    model = Inventory
    serializer_class = InventoryDetailSerializer
    
    # Configuration optionnelle
    default_order = '-created_at'
    page_size = 20
    
    # Activation de l'export (par défaut activé)
    enable_export = True
    export_formats = ['excel', 'csv']
    export_filename = 'inventaires'
    
    def get_datatable_queryset(self):
        """QuerySet optimisé"""
        queryset = super().get_datatable_queryset()
        return queryset.select_related(
            'awi_links__account',
            'awi_links__warehouse'
        ).prefetch_related('countings')


# =============================================================================
# EXEMPLES D'UTILISATION DÉTAILLÉS
# =============================================================================

"""
EXEMPLE 1: TRI SINGLE
=====================
GET /api/inventory/?ordering=label
→ Trie par label (croissant)

GET /api/inventory/?ordering=-created_at
→ Trie par date de création (décroissant)

GET /api/inventory/?order[0][column]=2&order[0][dir]=asc
→ Format DataTable : trie par colonne index 2 (asc)


EXEMPLE 2: TRI MULTI
=====================
GET /api/inventory/?ordering=label,-date
→ Trie d'abord par label (asc), puis par date (desc)

GET /api/inventory/?order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc
→ Format DataTable : trie par colonne 2 (asc), puis colonne 3 (desc)


EXEMPLE 3: RECHERCHE GLOBALE
=============================
GET /api/inventory/?search=inventaire
→ Recherche "inventaire" dans tous les champs de search_fields

GET /api/inventory/?search[value]=test
→ Format DataTable : recherche "test"


EXEMPLE 4: FILTRE SINGLE
=========================
GET /api/inventory/?status=EN_PREPARATION
→ Filtre uniquement les inventaires avec statut EN_PREPARATION

GET /api/inventory/?label_contains=test
→ Filtre les inventaires dont le label contient "test"


EXEMPLE 5: FILTRES MULTI
=========================
GET /api/inventory/?status=EN_PREPARATION&inventory_type=GENERAL
→ Filtre par statut ET type d'inventaire

GET /api/inventory/?status=EN_PREPARATION&date_start=2024-01-01&label_contains=test
→ Filtre par statut ET date ET label


EXEMPLE 6: FILTRES AVEC OPÉRATEURS
==================================
GET /api/inventory/?label_contains=inventaire      # Contient
GET /api/inventory/?label_exact=Inventaire 2024    # Exact
GET /api/inventory/?label_startswith=INV           # Commence par
GET /api/inventory/?label_endswith=2024             # Termine par
GET /api/inventory/?date_gte=2024-01-01            # Plus grand ou égal
GET /api/inventory/?date_lte=2024-12-31            # Plus petit ou égal


EXEMPLE 7: FILTRES DE DATE
==========================
GET /api/inventory/?date_exact=2024-01-15
→ Date exacte

GET /api/inventory/?date_start=2024-01-01&date_end=2024-12-31
→ Plage de dates

GET /api/inventory/?created_at_start=2024-01-01&created_at_end=2024-12-31
→ Plage de dates pour created_at


EXEMPLE 8: FILTRES DE STATUT
=============================
GET /api/inventory/?status=EN_PREPARATION
→ Statut unique

GET /api/inventory/?status_in=EN_PREPARATION,TERMINE,CLOTURE
→ Statuts multiples (OR)


EXEMPLE 9: EXPORT EXCEL
========================
GET /api/inventory/?export=excel
→ Exporte tous les inventaires en Excel

GET /api/inventory/?status=EN_PREPARATION&export=excel
→ Exporte uniquement les inventaires avec statut EN_PREPARATION

GET /api/inventory/?date_start=2024-01-01&label_contains=test&export=excel
→ Exporte avec filtres appliqués


EXEMPLE 10: EXPORT CSV
======================
GET /api/inventory/?export=csv
→ Exporte tous les inventaires en CSV

GET /api/inventory/?status=TERMINE&export=csv
→ Exporte uniquement les inventaires terminés


EXEMPLE 11: COMBINAISON COMPLÈTE
=================================
GET /api/inventory/?ordering=label,-date&search=test&status=EN_PREPARATION&date_start=2024-01-01&page=1&page_size=20
→ Tri multi + Recherche + Filtres + Pagination

GET /api/inventory/?ordering=-created_at&status=TERMINE&date_start=2024-01-01&export=excel
→ Tri + Filtres + Export Excel


EXEMPLE 12: FORMAT DATATABLE COMPLET
=====================================
GET /api/inventory/?draw=1&start=0&length=25&search[value]=test&order[0][column]=2&order[0][dir]=asc&order[1][column]=3&order[1][dir]=desc&status=EN_PREPARATION
→ Format DataTable complet avec tri multi, recherche et filtres
"""

