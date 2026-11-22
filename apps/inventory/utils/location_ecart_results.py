"""
Résultat final par article pour les inventaires à écart par emplacement
(MAGASIN à 3 comptages : 1er / 3e « qté par article », 2e « qté par emplacement »).

L'écart se calcule sur le total de l'emplacement, sans notion de produit. Le résultat
final par article est repris des lignes par article du comptage dont le total égale le
``final_result`` de l'écart (le 1er s'il égale, sinon le suivant, etc.).
"""
from typing import Any, Dict, Optional

from django.db.models import Prefetch, Sum

from apps.inventory.models import ComptageSequence, CountingDetail, EcartComptage
from apps.inventory.utils.counting_layout import uses_location_ecart


def _is_article_counting(counting) -> bool:
    """Comptage en vrac « qté par article » : en vrac, hors scan unitaire, ordre != 2."""
    return counting.count_mode == 'en vrac' and not counting.unit_scanned and counting.order != 2


def location_ecart_results(
    inventory,
    warehouse_id: Optional[int] = None,
    only_resolved: bool = False,
) -> Dict[int, Dict[str, Any]]:
    """
    Résultats par emplacement d'un inventaire à écart par emplacement.

    Returns:
        {location_id: {
            'ecart': EcartComptage,
            'job_id': int,
            'chosen_counting_id': int | None,   # comptage « par article » retenu
            'matches_final_result': bool,       # False si résultat manuel sans comptage égal
            'product_quantities': {product_id: quantité},
        }}
        Dictionnaire vide si l'inventaire n'utilise pas l'écart par emplacement.
    """
    if not uses_location_ecart(inventory):
        return {}

    ecarts = EcartComptage.objects.filter(inventory=inventory)
    if warehouse_id is not None:
        ecarts = ecarts.filter(counting_sequences__counting_detail__job__warehouse_id=warehouse_id)
    if only_resolved:
        ecarts = ecarts.filter(resolved=True, final_result__isnull=False)
    ecarts = ecarts.distinct().prefetch_related(
        Prefetch(
            'counting_sequences',
            queryset=ComptageSequence.objects.select_related(
                'counting_detail__counting'
            ).order_by('sequence_number'),
        )
    )

    results: Dict[int, Dict[str, Any]] = {}
    for ecart in ecarts:
        sequences = list(ecart.counting_sequences.all())
        if not sequences:
            continue
        first_detail = sequences[0].counting_detail
        info: Dict[str, Any] = {
            'ecart': ecart,
            'job_id': first_detail.job_id,
            'chosen_counting_id': None,
            'matches_final_result': False,
            'product_quantities': {},
        }

        article_sequences = [
            s for s in sequences if _is_article_counting(s.counting_detail.counting)
        ]
        chosen = None
        if ecart.final_result is not None:
            chosen = next((s for s in article_sequences if s.quantity == ecart.final_result), None)
            info['matches_final_result'] = chosen is not None
        if chosen is None and article_sequences:
            chosen = article_sequences[-1]  # dernier comptage par article

        if chosen is not None:
            info['chosen_counting_id'] = chosen.counting_detail.counting_id
            rows = (
                CountingDetail.objects.filter(
                    counting_id=chosen.counting_detail.counting_id,
                    location_id=first_detail.location_id,
                    job_id=first_detail.job_id,
                    product__isnull=False,
                )
                .values('product_id')
                .annotate(total=Sum('quantity_inventoried'))
            )
            info['product_quantities'] = {
                int(r['product_id']): int(r['total'] or 0) for r in rows
            }

        results[first_detail.location_id] = info
    return results
