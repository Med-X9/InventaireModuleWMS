"""
Vues pour l'import/export des utilisateurs
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from ..services.user_import_export_service import UserImportExportService
from apps.inventory.utils.response_utils import success_response, error_response

logger = logging.getLogger(__name__)


class UserExportView(APIView):
    """
    Vue pour l'export Excel des utilisateurs
    Exporte par défaut un fichier Excel
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = UserImportExportService()
    
    def get(self, request, account_id=None):
        """
        Exporte les utilisateurs en Excel
        
        Query params:
            account_id (optionnel): ID du compte pour filtrer les utilisateurs
        
        Returns:
            Fichier Excel avec les utilisateurs
        """
        try:
            # Récupérer account_id depuis les query params ou l'URL
            account_id_param = request.query_params.get('account_id')
            if account_id_param:
                account_id = int(account_id_param)
            elif account_id:
                account_id = int(account_id)
            else:
                account_id = None
            
            # Appeler le service pour exporter les utilisateurs en Excel
            excel_buffer = self.service.export_users_to_excel(account_id=account_id)
            
            # Nom du fichier
            filename = "export_utilisateurs.xlsx"
            if account_id:
                filename = f"export_utilisateurs_compte_{account_id}.xlsx"
            
            # Créer la réponse HTTP avec le fichier Excel
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except ValueError as e:
            logger.warning(f"Export Excel échoué - Erreur de validation: {str(e)}")
            return HttpResponse(
                f"Erreur: {str(e)}",
                status=400,
                content_type='text/plain'
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'export Excel: {str(e)}", exc_info=True)
            return HttpResponse(
                f"Erreur lors de l'export: {str(e)}",
                status=500,
                content_type='text/plain'
            )


class UserImportView(APIView):
    """
    Vue pour l'import des utilisateurs depuis un fichier Excel
    Permet l'importation en lot d'utilisateurs avec validation et création/mise à jour
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = UserImportExportService()
    
    def post(self, request, account_id=None):
        """
        Importe des utilisateurs depuis un fichier Excel
        
        Body params:
            file: Le fichier Excel à importer (multipart/form-data)
        
        Query params:
            account_id (optionnel): ID du compte pour assigner tous les utilisateurs
        
        Format attendu du fichier Excel:
        - Colonnes requises: 'Nom d\'utilisateur', 'Nom', 'Prénom', 'Type'
        - Colonnes optionnelles: 'Email', 'Compte', 'Actif', 'Administrateur', 'Mot de passe'
        - 'Type': 'Web' ou 'Mobile'
        - 'Actif': 'Oui', 'Non', 'Yes', 'No', etc.
        - 'Administrateur': 'Oui', 'Non', 'Yes', 'No', etc.
        """
        try:
            # Vérifier qu'un fichier a été fourni
            if 'file' not in request.FILES:
                return error_response(
                    message='Aucun fichier fourni. Utilisez le champ "file" pour uploader le fichier Excel.',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            excel_file = request.FILES['file']
            
            # Vérifier l'extension du fichier
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return error_response(
                    message='Le fichier doit être au format Excel (.xlsx ou .xls)',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer account_id depuis les query params ou l'URL
            account_id_param = request.query_params.get('account_id')
            if account_id_param:
                account_id = int(account_id_param)
            elif account_id:
                account_id = int(account_id)
            else:
                account_id = None
            
            # Appeler le service pour importer les utilisateurs
            result = self.service.import_users_from_excel(
                excel_file=excel_file,
                account_id=account_id
            )
            
            # Préparer la réponse
            summary = {
                'total_rows': result['total_rows'],
                'success': result['success'],
                'errors': result['errors'],
                'created': result['created'],
                'updated': result['updated']
            }
            
            extra_data = {
                'summary': summary
            }
            
            if result.get('errors_details'):
                extra_data['errors_details'] = result['errors_details']
            
            if result['errors'] == 0:
                # Aucune erreur
                return success_response(
                    data=extra_data,
                    message=f"Import réussi: {result['success']} utilisateur(s) traité(s) "
                           f"({result['created']} créé(s), {result['updated']} mis à jour)",
                    status_code=status.HTTP_200_OK
                )
            elif result['success'] > 0:
                # Des erreurs mais aussi des succès
                return success_response(
                    data=extra_data,
                    message=f"Import partiellement réussi: {result['success']} utilisateur(s) traité(s) "
                           f"avec succès, {result['errors']} erreur(s)",
                    status_code=status.HTTP_207_MULTI_STATUS  # 207 Multi-Status pour succès partiel
                )
            else:
                # Toutes les lignes ont des erreurs
                return error_response(
                    message=f"Import échoué: {result['errors']} erreur(s) sur {result['total_rows']} ligne(s)",
                    errors=[detail['error'] for detail in result.get('errors_details', [])],
                    status_code=status.HTTP_400_BAD_REQUEST,
                    **extra_data
                )
            
        except ValueError as e:
            logger.warning(f"Import Excel échoué - Erreur de validation: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'import Excel: {str(e)}", exc_info=True)
            return error_response(
                message=f"Erreur lors de l'import: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

