"""
Vue pour la generation de PDF des jobs d'inventaire
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from ..serializers.job_serializer import InventoryJobsPdfRequestSerializer
from ..usecases.inventory_jobs_pdf import InventoryJobsPdfUseCase
from ..usecases.job_assignment_pdf import JobAssignmentPdfUseCase
import logging

logger = logging.getLogger(__name__)


class InventoryJobsPdfView(APIView):
    """Vue pour generer le PDF des jobs d'inventaire"""
    
    def post(self, request, inventory_id):
        """
        Genere un PDF des jobs d'un inventaire
        
        URL params:
            inventory_id: ID de l'inventaire
        
        Returns:
            PDF file
        """
        # Pas de counting_id - on génère pour tous les comptages
        counting_id = None
        
        # Valider l'inventory_id
        if not inventory_id:
            return Response({
                'success': False,
                'message': 'inventory_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Executer le use case
            use_case = InventoryJobsPdfUseCase()
            result = use_case.execute(inventory_id, counting_id)
            
            if result['success']:
                # Retourner le PDF
                pdf_buffer = result['pdf_buffer']
                
                # Definir le nom du fichier
                filename = f"inventaire_{inventory_id}"
                if counting_id:
                    filename += f"_comptage_{counting_id}"
                filename += ".pdf"
                
                # Creer la reponse HTTP avec le PDF
                response = HttpResponse(
                    pdf_buffer.getvalue(),
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                return response
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors de la generation du PDF'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            logger.error(f"Erreur de validation: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de la generation du PDF: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobAssignmentPdfView(APIView):
    """Vue pour generer le PDF d'un job/assignment/equipe"""
    
    def post(self, request, job_id, assignment_id):
        """
        Genere un PDF pour un job/assignment/equipe specifique
        
        URL params:
            job_id: ID du job
            assignment_id: ID de l'assignment
        
        Body params (optionnel):
            equipe_id: ID de l'equipe (personne ou personne_two)
        
        Returns:
            PDF file
        """
        # Recuperer equipe_id depuis le body si fourni
        equipe_id = request.data.get('equipe_id', None)
        if equipe_id:
            try:
                equipe_id = int(equipe_id)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'message': 'equipe_id doit etre un nombre entier'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider les parametres
        if not job_id:
            return Response({
                'success': False,
                'message': 'job_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not assignment_id:
            return Response({
                'success': False,
                'message': 'assignment_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Executer le use case
            use_case = JobAssignmentPdfUseCase()
            result = use_case.execute(job_id, assignment_id, equipe_id)
            
            if result['success']:
                # Retourner le PDF
                pdf_buffer = result['pdf_buffer']
                
                # Definir le nom du fichier
                filename = f"job_{job_id}_assignment_{assignment_id}"
                if equipe_id:
                    filename += f"_equipe_{equipe_id}"
                filename += ".pdf"
                
                # Creer la reponse HTTP avec le PDF
                response = HttpResponse(
                    pdf_buffer.getvalue(),
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                return response
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors de la generation du PDF'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            logger.error(f"Erreur de validation: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de la generation du PDF: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
