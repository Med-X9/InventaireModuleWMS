"""
Strategy : feuilles supplémentaires de l'export Excel des résultats (détail).

- Inventaire « en vrac » : une feuille « Emplacement x Article » (tableau d'agrégation, une ligne par
  combinaison emplacement × article, mêmes colonnes que « Résultats ») et une feuille « Matrice » (lignes = articles, colonnes = emplacements,
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


FLAT_SHEET_NAME = 'Emplacement x Article'


def _counting_label(order: int) -> str:
    return f"{order}er Comptage" if order == 1 else f"{order}e Comptage"


def build_flat_table(
    inventory,
    warehouse_id: int,
    retained: Dict[Tuple[int, int], int],
    location_results: Dict[int, Dict[str, Any]] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Tableau d'agrégation : une ligne par combinaison emplacement × article.

    Mêmes colonnes que la feuille « Résultats » (job, statut job, emplacement, produit,
    quantité et statut par comptage, écarts, résultat final, résolu), avec en plus
    « Quantité Retenue » (quantité de l'article retenue pour l'emplacement).

    Args:
        retained: {(product_id, location_id): quantité retenue}
        location_results: résultat d'écart par emplacement (MAGASIN multi-comptages) :
            fournit Résultat Final / Résolu au niveau de l'emplacement.
    """
    from apps.inventory.models import Assigment, Job

    details = (
        CountingDetail.objects.filter(
            counting__inventory_id=inventory.id,
            job__warehouse_id=warehouse_id,
            product__isnull=False,
        )
        .values('location_id', 'product_id', 'job_id', 'counting__order')
        .annotate(total=Sum('quantity_inventoried'))
    )
    by_key: Dict[Tuple[int, int, int], Dict[int, int]] = {}
    for r in details:
        key = (r['location_id'], r['product_id'], r['job_id'])
        by_key.setdefault(key, {})[r['counting__order']] = int(r['total'] or 0)
    # Combinaisons retenues sans ligne article brute (sécurité) : ignorées, la source est CountingDetail
    if not by_key:
        return [], []

    # Tous les comptages de l'inventaire (même sans saisie) pour garder des colonnes stables
    orders = sorted(
        {o for q in by_key.values() for o in q}
        | set(Counting.objects.filter(inventory_id=inventory.id).values_list('order', flat=True))
    )
    job_ids = {k[2] for k in by_key}
    jobs = {j.id: j for j in Job.objects.filter(id__in=job_ids)}
    statuses: Dict[Tuple[int, int], str] = {}
    for a in Assigment.objects.filter(job_id__in=job_ids).select_related('counting'):
        if a.counting:
            statuses[(a.job_id, a.counting.order)] = a.status
    products = {
        p.id: p
        for p in Product.objects.filter(id__in={k[1] for k in by_key}).select_related('Product_Family')
    }
    locations = _location_labels({k[0] for k in by_key})

    columns = ['Référence Job', 'Statut Job', 'Emplacement'] + PRODUCT_COLUMNS
    for o in orders:
        columns += [_counting_label(o), f'Statut Comptage {o}']
        if o >= 2:
            columns += [f'Écart Comptage {o - 1}-{o}'] if (o - 1) in orders else []
    columns += ['Quantité Retenue', 'Résultat Final', 'Résolu']

    rows: List[Dict[str, Any]] = []
    for key in sorted(
        by_key,
        key=lambda k: (locations.get(k[0], ''), products[k[1]].Internal_Product_Code or '', k[2]),
    ):
        location_id, product_id, job_id = key
        quantities = by_key[key]
        job = jobs.get(job_id)
        row: Dict[str, Any] = {
            'Référence Job': job.reference if job else '',
            'Statut Job': job.status if job else '',
            'Emplacement': locations.get(location_id, ''),
            **_product_columns(products[product_id]),
        }
        for o in orders:
            row[_counting_label(o)] = quantities.get(o)
            row[f'Statut Comptage {o}'] = statuses.get((job_id, o))
            if o >= 2 and (o - 1) in orders:
                cur, prev = quantities.get(o), quantities.get(o - 1)
                row[f'Écart Comptage {o - 1}-{o}'] = (
                    cur - prev if cur is not None and prev is not None else None
                )
        last = quantities[max(quantities)]
        row['Quantité Retenue'] = retained.get((product_id, location_id), last)
        info = (location_results or {}).get(location_id)
        if info:
            row['Résultat Final'] = info['ecart'].final_result
            row['Résolu'] = info['ecart'].resolved
        else:
            row['Résultat Final'] = row['Quantité Retenue']
            row['Résolu'] = None
        rows.append(row)
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
        sheets = []
        flat_columns, flat_rows = build_flat_table(inventory, warehouse_id, quantities, results)
        if flat_rows:
            sheets.append((FLAT_SHEET_NAME, flat_columns, flat_rows))
        columns, rows = build_matrix_rows(
            quantities, _location_labels({loc for _, loc in quantities})
        )
        if len(columns) <= MAX_EXCEL_COLUMNS:
            sheets.append((MATRIX_SHEET_NAME, columns, rows))
        return sheets


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
        sheets = []
        flat_columns, flat_rows = build_flat_table(inventory, warehouse_id, quantities)
        if flat_rows:
            sheets.append((FLAT_SHEET_NAME, flat_columns, flat_rows))
        columns, rows = build_matrix_rows(
            quantities, _location_labels({loc for _, loc in quantities})
        )
        if len(columns) <= MAX_EXCEL_COLUMNS:
            sheets.append((MATRIX_SHEET_NAME, columns, rows))
        return sheets


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
