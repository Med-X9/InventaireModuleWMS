import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from ..services.stock_service import StockService
from ..exceptions import (
    InventoryNotFoundError, 
    StockValidationError, 
    StockImportError
)

logger = logging.getLogger(__name__)

class StockImportExcelView(APIView):
    """
    Vue pour importer des stocks depuis un fichier Excel.
    """
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = StockService()

    def post(self, request, inventory_id, *args, **kwargs):
        """
        Importe des stocks depuis un fichier Excel pour un inventaire spécifique.
        
        Endpoint: POST /api/inventory/{inventory_id}/import-stocks/
        
        Paramètres:
        - inventory_id: ID de l'inventaire
        - file: Fichier Excel à importer
        
        Format Excel attendu:
        - article: Référence du produit
        - emplacement: Référence de l'emplacement  
        - quantite: Quantité disponible
        """
        try:
            # Vérifier que le fichier est présent
            if 'file' not in request.FILES:
                return Response({
                    "success": False,
                    "message": "Aucun fichier fourni. Veuillez sélectionner un fichier Excel."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            excel_file = request.FILES['file']
            
            # Vérifier l'extension du fichier
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return Response({
                    "success": False,
                    "message": "Le fichier doit être au format Excel (.xlsx ou .xls)"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Importer les stocks via le service
            result = self.service.import_stocks_from_excel(inventory_id, excel_file)
            
            # Retourner le résultat
            if result['success']:
                return Response({
                    "success": True,
                    "message": result['message'],
                    "data": {
                        "total_rows": result['total_rows'],
                        "valid_rows": result['valid_rows'],
                        "invalid_rows": result['invalid_rows'],
                        "imported_stocks": result['imported_stocks']
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "message": result['message'],
                    "data": {
                        "total_rows": result['total_rows'],
                        "valid_rows": result['valid_rows'],
                        "invalid_rows": result['invalid_rows'],
                        "errors": result['errors']
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de l'import Excel: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except StockValidationError as e:
            logger.warning(f"Erreur de validation lors de l'import Excel: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except StockImportError as e:
            logger.error(f"Erreur d'import Excel: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'import Excel: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite lors de l'import"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 