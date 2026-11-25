"""
Strategy : feuilles supplémentaires de l'export Excel des résultats (détail).

- Inventaire « en vrac » : une feuille « Matrice » (lignes = articles, colonnes = emplacements,
  cellule = quantité retenue de l'article dans l'emplacement) en plus de la feuille « Résultats ».
  * MAGASIN multi-comptages (écart par emplacement) → MagasinLocationMatrixStrategy
    (quantités reprises du comptage « par article » égal au résultat final de l'emplacement).
  * Autre inventaire en vrac → EnVracMatrixStrategy (quantités du dernier comptage de chaque emplacement).
- Tous les autres (GENERAL par article, …) → NoExtraSheetsStrategy : export inchangé.

La feuille « Résultats » existante n'est jamais modifiée (mêmes colonnes).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from django.db.models import Sum

from apps.inventory.models import Counting, CountingDetail
from apps.masterdata.models import Product

from ..utils.counting_layout import uses_location_ecart

MATRIX_SHEET_NAME = 'Matrice'
MAX_EXCEL_COLUMNS = 16384
PRODUCT_COLUMNS = ['Code Barre', 'Code Interne', 'BarCode', 'Désignation', 'Famille']
TOTAL_COLUMNS = ['Total', 'Nb emplacements']


def _product_columns(product: Product) -> Dict[str, Any]:
    """Colonnes produit identiques à la feuille « Résultats »."""
    barcode = (product.Barcode or '').strip()
    internal = (product.Internal_Product_Code or '').strip()
    return {
        'Code Barre': barcode if barcode and barcode != internal else (internal or barcode),
        'Code Interne': internal or barcode,
        'BarCode': barcode,
        'Désignation': product.Short_Description or '',
        'Famille': product.Product_Family.family_name if product.Product_Family else '',
    }


def build_matrix_rows(
    quantities: Dict[Tuple[int, int], int],
    locations: Dict[int, str],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Construit la matrice articles × emplacements.

    Args:
        quantities: {(product_id, location_id): quantité}
        locations: {location_id: libellé d'emplacement}
    Returns:
        (colonnes dans l'ordre, lignes)
    """
    product_ids = sorted({p for p, _ in quantities})
    products = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids).select_related('Product_Family')
    }
    used_locations = sorted(
        {loc for _, loc in quantities}, key=lambda loc_id: (locations.get(loc_id, ''), loc_id)
    )
    labels: Dict[int, str] = {}
    seen: Dict[str, int] = {}
    for loc_id in used_locations:
        base = locations.get(loc_id) or f'Emplacement {loc_id}'
        seen[base] = seen.get(base, 0) + 1
        labels[loc_id] = base if seen[base] == 1 else f'{base} ({seen[base]})'

    rows: List[Dict[str, Any]] = []
    for product_id in sorted(
        products, key=lambda pid: (products[pid].Internal_Product_Code or '', pid)
    ):
        row: Dict[str, Any] = _product_columns(products[product_id])
        total = 0
        count = 0
        for loc_id in used_locations:
            qty = quantities.get((product_id, loc_id))
            row[labels[loc_id]] = qty if qty is not None else ''
            if qty is not None:
                total += qty
                count += 1
        row['Total'] = total
        row['Nb emplacements'] = count
        rows.append(row)

    columns = PRODUCT_COLUMNS + [labels[loc_id] for loc_id in used_locations] + TOTAL_COLUMNS
    return columns, rows


def _location_labels(location_ids) -> Dict[int, str]:
    from apps.masterdata.models import Location

    return {
        loc.id: loc.location_reference or loc.reference
        for loc in Location.objects.filter(id__in=list(location_ids))
    }


class ResultsExportStrategy(ABC):
    """Feuilles supplémentaires (nom, colonnes, lignes) de l'export des résultats."""

    @abstractmethod
    def extra_sheets(
        self, inventory, warehouse_id: int
    ) -> List[Tuple[str, List[str], List[Dict[str, Any]]]]:
        ...


class NoExtraSheetsStrategy(ResultsExportStrategy):
    """GENERAL / par article : export inchangé."""

    def extra_sheets(self, inventory, warehouse_id: int):
        return []


class MagasinLocationMatrixStrategy(ResultsExportStrategy):
    """MAGASIN multi-comptages en vrac : quantités par article de chaque emplacement (résultat retenu)."""

    def extra_sheets(self, inventory, warehouse_id: int):
        from ..utils.location_ecart_results import location_ecart_results

        results = location_ecart_results(
            inventory, warehouse_id=warehouse_id, only_resolved=False
        )
        quantities: Dict[Tuple[int, int], int] = {}
        for location_id, info in results.items():
            for product_id, qty in info['product_quantities'].items():
                quantities[(product_id, location_id)] = qty
        if not quantities:
            return []
        columns, rows = build_matrix_rows(
            quantities, _location_labels({loc for _, loc in quantities})
        )
        if len(columns) > MAX_EXCEL_COLUMNS:
            return []
        return [(MATRIX_SHEET_NAME, columns, rows)]


class EnVracMatrixStrategy(ResultsExportStrategy):
    """Autre inventaire en vrac : quantités du dernier comptage saisi pour chaque emplacement."""

    def extra_sheets(self, inventory, warehouse_id: int):
        details = (
            CountingDetail.objects.filter(
                counting__inventory_id=inventory.id,
                counting__count_mode='en vrac',
                job__warehouse_id=warehouse_id,
                product__isnull=False,
            )
            .values('location_id', 'counting__order', 'product_id')
            .annotate(total=Sum('quantity_inventoried'))
        )
        last_order: Dict[int, int] = {}
        rows_raw = list(details)
        for r in rows_raw:
            loc = r['location_id']
            last_order[loc] = max(last_order.get(loc, 0), r['counting__order'])
        quantities: Dict[Tuple[int, int], int] = {}
        for r in rows_raw:
            if r['counting__order'] == last_order[r['location_id']]:
                quantities[(r['product_id'], r['location_id'])] = int(r['total'] or 0)
        if not quantities:
            return []
        columns, rows = build_matrix_rows(
            quantities, _location_labels({loc for _, loc in quantities})
        )
        if len(columns) > MAX_EXCEL_COLUMNS:
            return []
        return [(MATRIX_SHEET_NAME, columns, rows)]


class ResultsExportDispatcher:
    """Sélectionne la stratégie d'export (Open/Closed)."""

    def get_strategy(self, inventory) -> ResultsExportStrategy:
        if inventory is None:
            return NoExtraSheetsStrategy()
        if uses_location_ecart(inventory):
            return MagasinLocationMatrixStrategy()
        if Counting.objects.filter(inventory_id=inventory.id, count_mode='en vrac').exists():
            return EnVracMatrixStrategy()
        return NoExtraSheetsStrategy()
