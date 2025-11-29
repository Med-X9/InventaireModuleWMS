"""
Request Handler Module - SOLID Single Responsibility

This module handles request detection and routing for different DataTable formats.
Follows SOLID principles:
- Single Responsibility: Only handles request detection and routing
- Open/Closed: Can be extended without modification
- Dependency Inversion: Depends on abstractions (interfaces)

KISS: Simple, straightforward request detection
DRY: Centralized request handling logic
"""

import logging
from typing import Optional
from django.http import HttpRequest
from rest_framework.request import Request

logger = logging.getLogger(__name__)


class RequestFormatDetector:
    """
    Detects the format of incoming DataTable requests.
    
    SOLID - Single Responsibility: Only detects request format
    KISS: Simple detection logic
    """
    
    @staticmethod
    def is_datatable_request(request: HttpRequest) -> bool:
        """
        Detects if request is in DataTable format.
        
        Args:
            request: HTTP request object
            
        Returns:
            bool: True if DataTable format detected
        """
        if not request or not hasattr(request, 'GET'):
            return False
        
        datatable_params = [
            'draw', 'start', 'length', 
            'order[0][column]', 'order[0][dir]',
            'search[value]', 'search[regex]'
        ]
        
        return any(param in request.GET for param in datatable_params)
    
    @staticmethod
    def is_query_model_request(request: HttpRequest) -> bool:
        """
        Detects if request uses QueryModel format.
        
        Args:
            request: HTTP request object
            
        Returns:
            bool: True if QueryModel format detected
        """
        # Check POST with JSON body
        if hasattr(request, 'data') and request.data and isinstance(request.data, dict):
            if 'sortModel' in request.data or 'filterModel' in request.data:
                return True
            # startRow/endRow dans POST body indique aussi QueryModel
            if 'startRow' in request.data or 'endRow' in request.data:
                return True
        
        # Check GET with sortModel or filterModel
        if request.GET.get('sortModel') or request.GET.get('filterModel'):
            return True
        
        # Check GET with startRow/endRow (indicateurs QueryModel, même sans sortModel/filterModel)
        # Mais seulement si pas de paramètres DataTable (draw, start, length)
        if request.GET.get('startRow') is not None or request.GET.get('endRow') is not None:
            # Si pas de paramètres DataTable, considérer comme QueryModel
            datatable_params = ['draw', 'start', 'length', 'order[0][column]', 'order[0][dir]']
            if not any(param in request.GET for param in datatable_params):
                return True
        
        return False
    
    @staticmethod
    def get_request_format(request: HttpRequest) -> str:
        """
        Determines the request format.
        
        Args:
            request: HTTP request object
            
        Returns:
            str: 'querymodel', 'datatable', or 'rest'
        """
        if RequestFormatDetector.is_query_model_request(request):
            return 'querymodel'
        elif RequestFormatDetector.is_datatable_request(request):
            return 'datatable'
        else:
            return 'rest'


class RequestParameterExtractor:
    """
    Extracts parameters from different request formats.
    
    SOLID - Single Responsibility: Only extracts parameters
    KISS: Simple extraction logic
    DRY: Centralized parameter extraction
    """
    
    @staticmethod
    def get_draw_value(request: HttpRequest) -> int:
        """Extracts draw value from request."""
        if hasattr(request, 'data') and request.data and isinstance(request.data, dict):
            return request.data.get('draw', 1)
        return int(request.GET.get('draw', 1))
    
    @staticmethod
    def get_search_value(request: HttpRequest) -> Optional[str]:
        """Extracts search value from request."""
        # Try request.data first (POST)
        if hasattr(request, 'data') and request.data and isinstance(request.data, dict):
            search = request.data.get('search') or request.data.get('searchValue', '')
            if search:
                return search.strip()
        
        # Try GET params
        search = request.GET.get('search') or request.GET.get('search[value]', '')
        return search.strip() if search else None
    
    @staticmethod
    def get_export_format(request: HttpRequest) -> Optional[str]:
        """Extracts export format from request."""
        if hasattr(request, 'data') and request.data and isinstance(request.data, dict):
            return request.data.get('export')
        return request.GET.get('export')

