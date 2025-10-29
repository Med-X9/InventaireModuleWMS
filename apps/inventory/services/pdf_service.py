"""
Service pour la generation de PDF des jobs d'inventaire
"""
from typing import Optional
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from django.utils import timezone
from ..interfaces.pdf_interface import PDFServiceInterface
from ..repositories.pdf_repository import PDFRepository


class PDFService(PDFServiceInterface):
    """Service pour la generation de PDF"""
    
    def __init__(self):
        self.repository = PDFRepository()
    
    def generate_inventory_jobs_pdf(
        self, 
        inventory_id: int, 
        counting_id: Optional[int] = None
    ) -> BytesIO:
        """
        Genere un PDF des jobs d'un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            counting_id: ID du comptage (optionnel) - non utilise, on genere pour tous
            
        Returns:
            BytesIO: Le contenu du PDF en memoire
        """
        # Recuperer l'inventaire
        inventory = self.repository.get_inventory_by_id(inventory_id)
        if not inventory:
            raise ValueError(f"Inventaire avec l'ID {inventory_id} non trouve")
        
        # Recuperer tous les comptages de l'inventaire
        all_countings = self.repository.get_countings_by_inventory(inventory)
        
        if not all_countings:
            raise ValueError(f"Aucun comptage trouve pour l'inventaire {inventory_id}")
        
        # Filtrer uniquement les comptages avec ordre 1 et 2
        target_countings = [c for c in all_countings if c.order in [1, 2]]
        
        if not target_countings:
            raise ValueError(f"Aucun comptage avec ordre 1 ou 2 trouve pour l'inventaire {inventory_id}")
        
        # Trier par ordre
        target_countings.sort(key=lambda x: x.order)
        
        # Si le comptage ordre 1 a le mode "image de stock", ne pas l'afficher
        counting_order_1 = target_countings[0] if target_countings else None
        
        if counting_order_1 and ('image' in counting_order_1.count_mode.lower() and 'stock' in counting_order_1.count_mode.lower()):
            # Ne garder que le comptage ordre 2
            countings = [c for c in target_countings if c.order == 2]
        else:
            # Afficher les deux comptages (ordre 1 et 2)
            countings = target_countings
        
        if not countings:
            raise ValueError(f"Aucun comptage valide trouve pour l'inventaire {inventory_id}")
        
        # Creer le buffer PDF
        buffer = BytesIO()
        
        # Creer le document PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,
            bottomMargin=2*cm
        )
        
        # Variables pour stocker l'utilisateur actuel de chaque page
        doc.current_user = None
        
        # Construire le contenu
        story = []
        
        # En-tete principal avec les informations de l'inventaire
        story.extend(self._build_main_header(inventory))
        story.append(Spacer(1, 0.5*cm))
        
        # Pour chaque comptage
        for counting in countings:
            # En-tete du comptage avec mode et ordre
            story.extend(self._build_counting_header(counting))
            story.append(Spacer(1, 0.3*cm))
            
            # Recuperer TOUS les jobs pour ce comptage
            jobs = self.repository.get_jobs_by_counting(inventory, counting)
            
            if jobs:
                # Grouper les jobs par utilisateur
                jobs_by_user = self._group_jobs_by_user(jobs)
                
                # Pour chaque utilisateur
                for user, user_jobs in jobs_by_user.items():
                    # Titre de l'utilisateur
                    story.extend(self._build_user_section(user, user_jobs, counting))
                    story.append(Spacer(1, 0.5*cm))
            
            # Ajouter un separateur entre les comptages
            if counting != countings[-1]:
                story.append(PageBreak())
        
        # Construire le PDF
        doc.build(story)
        
        # Reinitialiser le buffer
        buffer.seek(0)
        return buffer
    
    def _build_main_header(self, inventory):
        """Construit l'en-tete principal du PDF avec les informations de l'inventaire"""
        styles = getSampleStyleSheet()
        
        elements = []
        
        # Style pour le titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#000000'),
            spaceAfter=20,
            alignment=1,
        )
        
        # Titre
        title = Paragraph(f"<b>Jobs d'Inventaire</b>", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.4*cm))
        
        # Informations de l'inventaire
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=5,
            alignment=1,
        )
        
        elements.append(Paragraph(f"<b>Libelle:</b> {inventory.label}", info_style))
        elements.append(Paragraph(f"<b>Reference:</b> {inventory.reference}", info_style))
        elements.append(Paragraph(
            f"<b>Date de generation:</b> {timezone.now().strftime('%d/%m/%Y a %H:%M')}", 
            info_style
        ))
        
        return elements
    
    def _build_counting_header(self, counting):
        """Construit l'en-tete pour un comptage avec mode et ordre"""
        styles = getSampleStyleSheet()
        
        elements = []
        
        # Style pour le titre du comptage
        counting_title_style = ParagraphStyle(
            'CountingTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#000000'),
            spaceAfter=10,
            leftIndent=0,
        )
        
        # Titre du comptage
        counting_title = Paragraph(
            f"<b>Comptage {counting.order}: {counting.count_mode.upper()}</b>", 
            counting_title_style
        )
        elements.append(counting_title)
        
        return elements
    
    def _build_user_section(self, user, jobs, counting):
        """Construit une section pour un utilisateur"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre utilisateur
        if user:
            user_title = f"<b>Affecte a: {user}</b>"
        else:
            user_title = "<b>Non affecte</b>"
        
        user_style = ParagraphStyle(
            'UserTitle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#000000'),
            spaceAfter=8,
        )
        elements.append(Paragraph(user_title, user_style))
        elements.append(Spacer(1, 0.2*cm))
        
        # Pour chaque job, construire le tableau
        for job in jobs:
            elements.extend(self._build_job_table(job, counting, user))
        
        return elements
    
    def _build_job_table(self, job, counting, user=None):
        """Construit le tableau pour un job"""
        elements = []
        
        # Recuperer les job details du job avec le comptage
        job_details = [
            jd for jd in self.repository.get_job_details_by_job(job)
            if jd.counting_id == counting.id
        ]
        
        if not job_details:
            return elements
        
        # Determiner les colonnes selon le mode de comptage
        if 'vrac' in counting.count_mode.lower():
            # Mode vrac: pas de colonnes article, dlc, n_lot, variante
            headers = ['Emplacement', 'Quantite']
        else:
            # Mode par article: toutes les colonnes
            headers = ['Emplacement', 'Article', 'Quantite', 'DLC', 'N° Lot', 'Variante']
        
        # Recuperer les stocks de l'inventaire
        has_stock = self._inventory_has_stock(job.inventory)
        
        # Construire les donnees du tableau
        data = [headers]
        
        for job_detail in job_details:
            location = job_detail.location
            row_data = [location.location_reference]
            
            # Recuperer les stocks pour cet emplacement
            stocks = self.repository.get_stocks_by_location_and_inventory(
                location,
                job.inventory
            )
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                if has_stock and stocks:
                    # Afficher chaque produit du stock
                    for stock in stocks:
                        article = stock.product.Short_Description if stock.product else '-'
                        quantity = stock.quantity_available
                        
                        dlc = '-'
                        if counting.dlc and stock.product and stock.product.dlc:
                            dlc = 'Oui'
                        
                        n_lot = '-'
                        if counting.n_lot and stock.product and stock.product.n_lot:
                            n_lot = 'Oui'
                        
                        is_variant = '-'
                        if counting.is_variant and stock.product and stock.product.Is_Variant:
                            is_variant = 'Oui'
                        
                        row_data = [location.location_reference, article, quantity, dlc, n_lot, is_variant]
                        data.append(row_data)
                else:
                    # Pas de stock, afficher juste l'emplacement
                    row_data.extend(['-', '-', '-', '-', '-'])
                    data.append(row_data)
            else:
                # Mode vrac: juste la quantite
                if has_stock and stocks:
                    # Somme des quantites
                    total_quantity = sum(s.quantity_available for s in stocks)
                    row_data.append(total_quantity)
                else:
                    row_data.append('-')
                data.append(row_data)
        
        # Creer le tableau
        col_widths = self._calculate_column_widths(headers, A4[0])
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style simple du tableau
        table.setStyle(TableStyle([
            # En-tete
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _calculate_column_widths(self, headers, page_width, margins=4*cm):
        """Calcule la largeur des colonnes"""
        available_width = page_width - margins
        
        if len(headers) == 2:
            # Mode vrac: 2 colonnes
            return [available_width * 0.6, available_width * 0.4]
        else:
            # Mode par article: 6 colonnes
            return [available_width * 0.15, available_width * 0.30, available_width * 0.12,
                   available_width * 0.12, available_width * 0.14, available_width * 0.17]
    
    def _group_jobs_by_user(self, jobs):
        """Groupe les jobs par utilisateur"""
        jobs_by_user = {}
        
        for job in jobs:
            assignments = self.repository.get_assignments_by_job(job)
            user = None
            
            # Chercher l'utilisateur dans les assignments
            for assignment in assignments:
                if assignment.session:
                    user = assignment.session.username
                    break
            
            if user not in jobs_by_user:
                jobs_by_user[user] = []
            
            jobs_by_user[user].append(job)
        
        return jobs_by_user
    
    def _inventory_has_stock(self, inventory):
        """Verifie si l'inventaire a des stocks"""
        from apps.masterdata.models import Stock
        return Stock.objects.filter(inventory=inventory).exists()

