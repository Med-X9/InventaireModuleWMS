"""
Règle métier partagée : calcul du résultat de consensus pour un écart de comptage.

Utilisée par counting_detail_service, ecart_comptage_service, assignment_service
et ecart_comptage_automatic_processing pour éviter la duplication de la même logique.
"""
from typing import List, Optional


def calculate_ecart_consensus_result(
    quantities: List[int],
    current_result: Optional[int],
) -> Optional[int]:
    """
    Détermine le résultat final (final_result) d'un écart selon les règles métier.

    Règles :
    1. Moins de 2 comptages → pas de consensus (None).
    2. Dernière quantité égale à au moins une quantité précédente → consensus = cette quantité.
    3. Exactement 2 comptages et pas d'égalité → pas de consensus (None).
    4. Plus de 2 comptages et dernière différente de toutes les précédentes → conserver current_result.

    Args:
        quantities: Liste des quantités par ordre chronologique (index 0 = 1er comptage).
        current_result: Résultat actuel de l'écart (peut être None).

    Returns:
        La valeur à enregistrer dans final_result, ou None si pas de consensus.
    """
    if len(quantities) < 2:
        return None

    quantite_actuelle = quantities[-1]
    quantites_precedentes = quantities[:-1]

    if quantite_actuelle in quantites_precedentes:
        return quantite_actuelle

    if len(quantities) == 2:
        return None

    return current_result
