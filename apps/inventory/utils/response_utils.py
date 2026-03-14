"""
Utilitaires pour standardiser les formats de réponse API.
"""
from rest_framework.response import Response
from rest_framework import status
from typing import Any, Dict, List, Optional


def success_response(
    data: Any = None,
    message: str = "Opération réussie",
    status_code: int = status.HTTP_200_OK,
    **kwargs
) -> Response:
    """
    Crée une réponse de succès standardisée.
    
    Format:
    {
        "success": true,
        "message": "...",
        "data": ...
    }
    
    Args:
        data: Les données à retourner
        message: Message de succès
        status_code: Code de statut HTTP
        **kwargs: Champs supplémentaires à inclure dans la réponse
    
    Returns:
        Response: Réponse DRF standardisée
    """
    response_data: Dict[str, Any] = {
        "success": True,
        "message": message,
    }
    
    if data is not None:
        response_data["data"] = data
    
    # Ajouter les champs supplémentaires
    response_data.update(kwargs)
    
    return Response(response_data, status=status_code)


def error_response(
    message: str,
    errors: Optional[List[str]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    **kwargs
) -> Response:
    """
    Crée une réponse d'erreur standardisée.
    
    Format:
    {
        "success": false,
        "message": "...",
        "errors": [...]
    }
    
    Args:
        message: Message d'erreur principal
        errors: Liste des erreurs détaillées (optionnel)
        status_code: Code de statut HTTP
        **kwargs: Champs supplémentaires à inclure dans la réponse
    
    Returns:
        Response: Réponse DRF standardisée
    """
    response_data: Dict[str, Any] = {
        "success": False,
        "message": message,
    }
    
    if errors:
        response_data["errors"] = errors
    elif message:
        # Si pas d'erreurs détaillées, utiliser le message comme erreur unique
        response_data["errors"] = [message]
    
    # Ajouter les champs supplémentaires
    response_data.update(kwargs)
    
    return Response(response_data, status=status_code)


def validation_error_response(
    serializer_errors: Dict[str, Any],
    message: str = "Erreur de validation",
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> Response:
    """
    Crée une réponse d'erreur de validation à partir des erreurs d'un serializer.
    
    Args:
        serializer_errors: Erreurs du serializer DRF
        message: Message d'erreur principal
        status_code: Code de statut HTTP
    
    Returns:
        Response: Réponse DRF standardisée
    """
    # Formater les erreurs du serializer en liste de messages
    errors: List[str] = []
    
    for field, field_errors in serializer_errors.items():
        if isinstance(field_errors, list):
            for error in field_errors:
                errors.append(f"{field}: {error}")
        else:
            errors.append(f"{field}: {field_errors}")
    
    return error_response(
        message=message,
        errors=errors,
        status_code=status_code
    )

