"""
Request Handler Module - SOLID Single Responsibility

This module handles request detection for QueryModel format.
Follows SOLID principles:
- Single Responsibility: Only handles request detection for QueryModel
- Open/Closed: Can be extended without modification
- Dependency Inversion: Depends on abstractions (interfaces)

KISS: Simple, straightforward request detection
DRY: Centralized request handling logic
"""

import logging
from typing import Optional
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class RequestFormatDetector:
    """
    Detects if a request uses QueryModel format.
    
    SOLID - Single Responsibility: Only detects QueryModel format
    KISS: Simple detection logic
    """
    
    @staticmethod
    def is_query_model_request(request: HttpRequest) -> bool:
        """
        Detects if request uses QueryModel format (nouveau format uniquement).
        
        Args:
            request: HTTP request object
            
        Returns:
            bool: True if QueryModel format detected (page/pageSize)
        """
        # Check POST with JSON body
        if hasattr(request, 'data') and request.data and isinstance(request.data, dict):
            # Nouveau format : page ou pageSize
            if 'page' in request.data or 'pageSize' in request.data or 'page_size' in request.data:
                return True
        
        # Check GET with page or pageSize
        if request.GET.get('page') is not None or request.GET.get('pageSize') is not None:
            return True
        
        return False


class RequestParameterExtractor:
    """
    Extracts parameters from QueryModel requests.
    
    SOLID - Single Responsibility: Only extracts parameters
    KISS: Simple extraction logic
    DRY: Centralized parameter extraction
    """
    
    @staticmethod
    def get_search_value(request: HttpRequest) -> Optional[str]:
        """Extracts search value from request."""
        # Try request.data first (POST)
        if hasattr(request, 'data') and request.data and isinstance(request.data, dict):
            search = request.data.get('search') or request.data.get('searchValue', '')
            if search:
                return search.strip()
        
        # Try GET params
        search = request.GET.get('search') or request.GET.get('searchValue', '')
        return search.strip() if search else None
