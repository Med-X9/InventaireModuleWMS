"""
Service pour la generation de PDF des jobs d'inventaire
"""
from typing import Optional
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from django.conf import settings
import os
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
        
        # Recuperer les infos de l'inventaire (warehouse, account)
        warehouse_info = self._get_warehouse_info(inventory)
        account_info = self._get_account_info(inventory)
        
        # Calculer la pagination avant de construire le contenu
        page_info_map = {}
        page_counter = 0
        
        for counting in countings:
            jobs = self.repository.get_jobs_by_counting(inventory, counting)
            if jobs:
                jobs_by_user = self._group_jobs_by_user(jobs)
                for user, user_jobs in jobs_by_user.items():
                    for job in user_jobs:
                        all_job_details = self.repository.get_job_details_by_job(job)
                        job_details = [jd for jd in all_job_details if jd.counting_id is None or jd.counting_id == counting.id]
                        if job_details:
                            all_table_rows = self._prepare_table_rows(job_details, counting, job)
                            if all_table_rows:
                                lines_per_page = 20
                                total_pages = (len(all_table_rows) + lines_per_page - 1) // lines_per_page
                                for page_num in range(total_pages):
                                    page_counter += 1
                                    page_info_map[page_counter] = {
                                        'current': page_num + 1,
                                        'total': total_pages,
                                        'job_ref': job.reference
                                    }
        
        # Creer le buffer PDF
        buffer = BytesIO()
        
        # Construire le contenu
        story = []
        
        # Pour chaque comptage
        for counting in countings:
            # Recuperer TOUS les jobs pour ce comptage avec filtre PRET et TRANSFERT
            jobs = self.repository.get_jobs_by_counting(inventory, counting)
            
            if jobs:
                # Grouper les jobs par utilisateur
                jobs_by_user = self._group_jobs_by_user(jobs)
                
                # Pour chaque utilisateur et chaque job
                for user, user_jobs in jobs_by_user.items():
                    for job in user_jobs:
                        # Construire les pages pour ce job (avec pagination de 20 lignes)
                        story.extend(self._build_job_pages(
                            job, counting, user, inventory, warehouse_info, account_info
                        ))
        
        # Creer le document PDF avec marges ajustées
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,  # Marge normale pour le contenu
            topMargin=1*cm,  # Seulement 1cm en haut
            bottomMargin=0*cm  # Pas de marge en bas, footer fixe à y=0
        )
        
        # Stocker les infos de pagination dans le document
        doc.page_info_map = page_info_map
        
        # Construire le PDF avec header (logo) et footer (pagination) personnalisés
        doc.build(story, 
                 onFirstPage=self._add_page_header_and_footer, 
                 onLaterPages=self._add_page_header_and_footer)
        
        # Reinitialiser le buffer
        buffer.seek(0)
        return buffer
    
    def _get_warehouse_info(self, inventory):
        """Récupère les informations du warehouse via les jobs ou settings"""
        from ..models import Job
        # Essayer via les jobs
        jobs = Job.objects.filter(inventory=inventory).select_related('warehouse').first()
        if jobs and jobs.warehouse:
            return {
                'name': jobs.warehouse.warehouse_name,
                'reference': jobs.warehouse.warehouse_reference if hasattr(jobs.warehouse, 'warehouse_reference') else None
            }
        # Sinon via settings
        settings = inventory.awi_links.select_related('warehouse').first()
        if settings and settings.warehouse:
            return {
                'name': settings.warehouse.warehouse_name,
                'reference': settings.warehouse.warehouse_reference if hasattr(settings.warehouse, 'warehouse_reference') else None
            }
        return {'name': '-', 'reference': None}
    
    def _get_account_info(self, inventory):
        """Récupère les informations du compte via settings"""
        settings = inventory.awi_links.select_related('account').first()
        if settings and settings.account:
            return {
                'name': settings.account.account_name,
                'reference': settings.account.account_reference if hasattr(settings.account, 'account_reference') else None
            }
        return {'name': '-', 'reference': None}
    
    def _get_logo_path(self):
        """Récupère le chemin du logo"""
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo_app.png')
        if os.path.exists(logo_path):
            return logo_path
        # Fallback vers staticfiles
        logo_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'logo_app.png')
        if os.path.exists(logo_path):
            return logo_path
        return None
    
    def _add_page_header_and_footer(self, canvas_obj, doc):
        """Ajoute le logo en haut à gauche et la pagination en bas à droite"""
        # Ajouter le logo en haut à gauche (position absolue - maximum gauche et haut)
        logo_path = self._get_logo_path()
        if logo_path:
            try:
                canvas_obj.saveState()
                # Dimensions du logo agrandies
                logo_width = 4*cm  # Agrandi de 3cm à 5cm
                logo_height = 2*cm  # Agrandi de 1.5cm à 2.5cm
                
                # Position: maximum à gauche et en haut (0.2cm de marge minimale)
                x = 0.02*cm  # Presque au bord gauche
                y = doc.pagesize[1] - 0.2*cm - logo_height  # Presque au bord supérieur
                
                canvas_obj.drawImage(logo_path, x, y, width=logo_width, height=logo_height, preserveAspectRatio=True)
                canvas_obj.restoreState()
            except Exception as e:
                # Si erreur de chargement du logo, continuer sans logo
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Impossible de charger le logo: {str(e)}")
        
        # Ajouter la pagination en bas à droite
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        
        if page_info:
            current = page_info.get('current', 1)
            total = page_info.get('total', 1)
            
            # Positionner en bas à droite (0 du bas, aligné à droite)
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            # Position: largeur page - marge droite - largeur texte, y=0.5cm du bas
            text = f"Page {current}/{total}"
            text_width = canvas_obj.stringWidth(text, "Helvetica", 9)
            x = doc.pagesize[0] - doc.rightMargin - text_width
            y = 0.5*cm  # 0.5cm du bas absolu
            
            canvas_obj.drawString(x, y, text)
            canvas_obj.restoreState()
    
    def _add_page_header_and_footer_with_signatures(self, canvas_obj, doc):
        """Ajoute le logo en haut à gauche, la pagination en bas à droite et les signatures en bas"""
        # Ajouter le logo en haut à gauche
        logo_path = self._get_logo_path()
        if logo_path:
            try:
                canvas_obj.saveState()
                logo_width = 4*cm
                logo_height = 2*cm
                x = 0.02*cm
                y = doc.pagesize[1] - 0.2*cm - logo_height
                canvas_obj.drawImage(logo_path, x, y, width=logo_width, height=logo_height, preserveAspectRatio=True)
                canvas_obj.restoreState()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Impossible de charger le logo: {str(e)}")
        
        # Ajouter la pagination en bas à droite
        page_num = canvas_obj.getPageNumber()
        page_info = getattr(doc, 'page_info_map', {}).get(page_num, {})
        
        if page_info:
            current = page_info.get('current', 1)
            total = page_info.get('total', 1)
            
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            
            text = f"Page {current}/{total}"
            text_width = canvas_obj.stringWidth(text, "Helvetica", 9)
            x = doc.pagesize[0] - doc.rightMargin - text_width
            y = 0.5*cm
            canvas_obj.drawString(x, y, text)
            canvas_obj.restoreState()
        
        # Ajouter les signatures en bas de page
        personne_info = getattr(doc, 'personne_info', {})
        personne = personne_info.get('personne')
        personne_two = personne_info.get('personne_two')
        
        if personne or personne_two:
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.black)
            canvas_obj.setStrokeColor(colors.black)
            canvas_obj.setLineWidth(0.5)
            
            # Hauteur pour les lignes de signature (1.5cm du bas)
            line_y = 1.5*cm
            # Hauteur pour le texte des noms (0.3cm du bas)
            text_y = 0.3*cm
            
            # Si deux personnes, les placer côte à côte
            if personne and personne_two:
                # Personne 1 à gauche
                x1 = doc.leftMargin
                line_width = 6*cm
                canvas_obj.line(x1, line_y, x1 + line_width, line_y)
                canvas_obj.setFont("Helvetica", 8)
                canvas_obj.drawString(x1, text_y, f"Signature: {personne}")
                
                # Personne 2 à droite
                x2 = doc.pagesize[0] - doc.rightMargin - line_width
                canvas_obj.line(x2, line_y, x2 + line_width, line_y)
                canvas_obj.drawString(x2, text_y, f"Signature: {personne_two}")
            elif personne:
                # Une seule personne, à gauche
                x = doc.leftMargin
                line_width = 6*cm
                canvas_obj.line(x, line_y, x + line_width, line_y)
                canvas_obj.setFont("Helvetica", 8)
                canvas_obj.drawString(x, text_y, f"Signature: {personne}")
            elif personne_two:
                # Une seule personne, à gauche
                x = doc.leftMargin
                line_width = 6*cm
                canvas_obj.line(x, line_y, x + line_width, line_y)
                canvas_obj.setFont("Helvetica", 8)
                canvas_obj.drawString(x, text_y, f"Signature: {personne_two}")
            
            canvas_obj.restoreState()
    
    def _build_job_pages(self, job, counting, user, inventory, warehouse_info, account_info):
        """Construit les pages pour un job avec pagination de 20 lignes par page"""
        elements = []
        
        # Récupérer tous les job details du job pour ce counting
        all_job_details = self.repository.get_job_details_by_job(job)
        job_details = []
        for jd in all_job_details:
            if jd.counting_id is None or jd.counting_id == counting.id:
                job_details.append(jd)
        
        if not job_details:
            return elements
        
        # Construire toutes les lignes du tableau d'abord (pour calculer le total)
        all_table_rows = self._prepare_table_rows(job_details, counting, job)
        
        if not all_table_rows:
            return elements
        
        # Paginer par groupes de 20 lignes
        lines_per_page = 20
        total_pages = (len(all_table_rows) + lines_per_page - 1) // lines_per_page
        
        for page_num in range(total_pages):
            start_idx = page_num * lines_per_page
            end_idx = min(start_idx + lines_per_page, len(all_table_rows))
            page_rows = all_table_rows[start_idx:end_idx]
            
            # En-tête de page avec infos inventaire + job + user
            elements.extend(self._build_page_header(
                inventory, job, user, counting, warehouse_info, account_info, page_num + 1, total_pages
            ))
            
            # Tableau des détails du job (max 20 lignes) avec pagination en bas
            elements.extend(self._build_table_from_rows(page_rows, counting, page_num + 1, total_pages))
            
            # Saut de page si ce n'est pas la dernière page de ce job
            if page_num < total_pages - 1:
                elements.append(PageBreak())
            # Saut de page aussi après le dernier job pour séparer les jobs
            else:
                elements.append(PageBreak())
        
        return elements
    
    def _prepare_table_rows(self, job_details, counting, job):
        """Prépare toutes les lignes du tableau avec quantité théorique et physique"""
        rows = []
        
        for job_detail in job_details:
            location = job_detail.location
            stocks = self.repository.get_stocks_by_location_and_inventory(location, job.inventory)
            has_stock_for_location = len(stocks) > 0 if stocks else False
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                if has_stock_for_location and stocks:
                    # Une ligne par produit
                    for stock in stocks:
                        row = {
                            'location': location.location_reference,
                            'barcode': stock.product.Barcode if stock.product and stock.product.Barcode else '-',
                            'designation': stock.product.Short_Description if stock.product else '-',
                            'quantite_theorique': stock.quantity_available,
                            'quantite_physique': '',  # Vide pour saisie manuelle
                            'dlc': stock.product and stock.product.dlc if stock.product else False,
                            'n_lot': stock.product and stock.product.n_lot if stock.product else False,
                            'is_variant': stock.product and stock.product.Is_Variant if stock.product else False,
                        }
                        rows.append(row)
                else:
                    # Pas de stock - une ligne vide
                    row = {
                        'location': location.location_reference,
                        'barcode': '-',
                        'designation': '-',
                        'quantite_theorique': '-',
                        'quantite_physique': '',  # Vide pour saisie
                        'dlc': False,
                        'n_lot': False,
                        'is_variant': False,
                    }
                    rows.append(row)
            else:
                # Mode vrac
                if has_stock_for_location and stocks:
                    total_quantite_theorique = sum(s.quantity_available for s in stocks)
                    row = {
                        'location': location.location_reference,
                        'quantite_theorique': total_quantite_theorique,
                        'quantite_physique': '',  # Vide pour saisie manuelle
                    }
                else:
                    row = {
                        'location': location.location_reference,
                        'quantite_theorique': '-',
                        'quantite_physique': '',  # Vide pour saisie
                    }
                rows.append(row)
        
        return rows
    
    def _build_table_from_rows(self, rows, counting, page_num, total_pages):
        """Construit le tableau à partir des lignes préparées avec pagination en bas"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Déterminer si on affiche la quantité théorique
        show_theorique = counting.quantity_show or counting.stock_situation
        
        # Construire les en-têtes selon la configuration
        headers = ['Emplacement']
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article
            if counting.show_product:
                headers.append('Article')  # Code barre
                headers.append('Désignation')  # Toujours si show_product
            headers.append('Quantité physique')  # Toujours présent
            
            if show_theorique:
                headers.append('Quantité théorique')
            
            # Colonnes optionnelles
            if counting.dlc:
                headers.append('DLC')
            if counting.n_lot:
                headers.append('N° Lot')
            if counting.is_variant:
                headers.append('Variante')
        else:
            # Mode vrac
            headers.append('Quantité physique')  # Toujours présent
            
            if show_theorique:
                headers.append('Quantité théorique')
        
        # Construire les données
        data = [headers]
        
        for row in rows:
            table_row = [row['location']]
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                if counting.show_product:
                    # Article (code barre)
                    table_row.append(row.get('barcode', '-'))
                    # Désignation
                    table_row.append(row.get('designation', '-'))
                # Si show_product = False, pas de colonnes Article/Désignation
                
                # Quantité physique (toujours)
                table_row.append(row.get('quantite_physique', ''))
                
                # Quantité théorique (si configuré)
                if show_theorique:
                    quantite_theorique = row.get('quantite_theorique', '-')
                    table_row.append(quantite_theorique if quantite_theorique != '' else '-')
                
                # Colonnes optionnelles
                if counting.dlc:
                    table_row.append('Oui' if row.get('dlc', False) else '-')
                if counting.n_lot:
                    table_row.append('Oui' if row.get('n_lot', False) else '-')
                if counting.is_variant:
                    table_row.append('Oui' if row.get('is_variant', False) else '-')
            else:
                # Mode vrac
                # Quantité physique (toujours)
                table_row.append(row.get('quantite_physique', ''))
                
                # Quantité théorique (si configuré)
                if show_theorique:
                    quantite_theorique = row.get('quantite_theorique', '-')
                    table_row.append(quantite_theorique if quantite_theorique != '' else '-')
            
            data.append(table_row)
        
        if len(data) == 1:  # Seulement les headers
            return elements
        
        # Créer le tableau
        col_widths = self._calculate_merged_column_widths(headers, A4[0])
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style du tableau
        table_style = [
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Emplacement centré
        ]
        
        # Aligner les quantités à droite
        quantite_physique_idx = headers.index('Quantité physique')
        table_style.append(('ALIGN', (quantite_physique_idx, 1), (quantite_physique_idx, -1), 'RIGHT'))
        
        if 'Quantité théorique' in headers:
            quantite_theorique_idx = headers.index('Quantité théorique')
            table_style.append(('ALIGN', (quantite_theorique_idx, 1), (quantite_theorique_idx, -1), 'RIGHT'))
        
        # Ajouter les lignes de séparation entre toutes les colonnes
        table_style.extend([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Ligne plus épaisse sous l'en-tête
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ])
        
        table.setStyle(TableStyle(table_style))
        
        elements.append(table)
        
        # Pas de pagination ici, elle sera dans le footer fixe
        return elements
    
    def _build_page_header(self, inventory, job, user, counting, warehouse_info, account_info, page_num, total_pages):
        """Construit l'en-tête de chaque page avec champs côte à côte"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Style pour les labels (en gras)
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#000000'),
            spaceAfter=0,
            spaceBefore=0,
            alignment=0,  # Left
        )
        
        # Style pour les valeurs (normal)
        value_style = ParagraphStyle(
            'ValueStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#000000'),
            spaceAfter=0,
            spaceBefore=0,
            alignment=0,  # Left
        )
        
        # Style pour le titre
        title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Heading4'],
            fontSize=14,
            textColor=colors.HexColor('#000000'),
            spaceAfter=8,
            alignment=1,  # Center
        )
        
        # Titre en gras
        elements.append(Paragraph("<b>FICHE DE COMPTAGE</b>", title_style))
        elements.append(Spacer(1, 0.15*cm))
        
        # Informations de l'inventaire - Ligne 1: Référence Inventaire | Type | Magasin
        info_row1_data = [
            Paragraph(f"<b>Référence Inventaire:</b> {inventory.reference}", label_style),
            Paragraph(f"<b>Type:</b> {inventory.inventory_type}", label_style),
            Paragraph(f"<b>Magasin:</b> {warehouse_info['name']}", label_style),
        ]
        
        info_row1_table = Table([info_row1_data], colWidths=[5.5*cm, 5.5*cm, 5*cm])
        info_row1_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(info_row1_table)
        
        # Informations - Ligne 2: Date Inventaire | Compte | Référence Job
        info_row2_data = [
            Paragraph(f"<b>Date Inventaire:</b> {inventory.date.strftime('%d/%m/%Y') if inventory.date else '-'}", label_style),
            Paragraph(f"<b>Compte:</b> {account_info['name']}", label_style),
            Paragraph(f"<b>Référence Job:</b> {job.reference}", label_style),
        ]
        
        info_row2_table = Table([info_row2_data], colWidths=[5.5*cm, 5.5*cm, 5*cm])
        info_row2_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(info_row2_table)
        
        # Informations - Ligne 3: Utilisateur
        info_row3_data = [
            Paragraph(f"<b>Utilisateur:</b> {user if user else 'Non affecté'}", label_style),
        ]
        
        info_row3_table = Table([info_row3_data], colWidths=[16*cm])
        info_row3_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(info_row3_table)
        elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _build_job_details_table(self, job_details, counting, job):
        """Construit le tableau des détails du job (JobDetail)"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Construire les en-têtes selon la configuration
        headers = ['Emplacement']
        
        has_stock = self._inventory_has_stock(job.inventory)
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article
            if counting.show_product:
                headers.append('Article')
            headers.append('Quantité')
            if counting.dlc:
                headers.append('DLC')
            if counting.n_lot:
                headers.append('N° Lot')
            if counting.is_variant:
                headers.append('Variante')
        else:
            # Mode vrac
            headers.append('Quantité')
        
        # Construire les données
        data = [headers]
        
        for job_detail in job_details:
            location = job_detail.location
            row = [location.location_reference]
            
            # Récupérer les stocks
            stocks = self.repository.get_stocks_by_location_and_inventory(location, job.inventory)
            has_stock_for_location = len(stocks) > 0 if stocks else False
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                if has_stock_for_location and stocks:
                    # Une ligne par produit
                    for stock in stocks:
                        product_row = [location.location_reference]
                        if counting.show_product:
                            product_row.append(stock.product.Short_Description if stock.product else '-')
                        product_row.append(stock.quantity_available)
                        if counting.dlc:
                            product_row.append('Oui' if (stock.product and stock.product.dlc) else '-')
                        if counting.n_lot:
                            product_row.append('Oui' if (stock.product and stock.product.n_lot) else '-')
                        if counting.is_variant:
                            product_row.append('Oui' if (stock.product and stock.product.Is_Variant) else '-')
                        data.append(product_row)
                else:
                    # Pas de stock
                    row_data = [location.location_reference]
                    if counting.show_product:
                        row_data.append('-')
                    row_data.append('-')
                    if counting.dlc:
                        row_data.append('-')
                    if counting.n_lot:
                        row_data.append('-')
                    if counting.is_variant:
                        row_data.append('-')
                    data.append(row_data)
            else:
                # Mode vrac
                if has_stock_for_location and stocks:
                    total_quantity = sum(s.quantity_available for s in stocks)
                    row.append(total_quantity)
                else:
                    row.append('-')
                data.append(row)
        
        if len(data) == 1:  # Seulement les headers
            return elements
        
        # Créer le tableau
        col_widths = self._calculate_merged_column_widths(headers, A4[0])
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style du tableau
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Emplacement centré
            
            # Aligner Quantité à droite
            ('ALIGN', (headers.index('Quantité'), 1), (headers.index('Quantité'), -1), 'RIGHT'),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*cm))
        
        return elements
    
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
        """Construit une section pour un utilisateur avec un tableau fusionné de tous les jobs"""
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
        
        # Construire un seul tableau fusionné pour tous les jobs
        elements.extend(self._build_merged_jobs_table(jobs, counting))
        
        return elements
    
    def _build_merged_jobs_table(self, jobs, counting):
        """Construit un tableau fusionné pour tous les jobs d'un utilisateur"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Collecter tous les job_details de tous les jobs
        all_job_details_data = []
        
        for job in jobs:
            # Vérifier si le job a un assignment pour ce comptage
            assignments = self.repository.get_assignments_by_job(job)
            has_assignment_for_counting = any(a.counting_id == counting.id for a in assignments)
            
            if not has_assignment_for_counting:
                continue
            
            # Récupérer tous les job details du job
            all_job_details = self.repository.get_job_details_by_job(job)
            
            # Filtrer les job_details
            job_details = []
            for jd in all_job_details:
                if jd.counting_id is None or jd.counting_id == counting.id:
                    job_details.append((job, jd))
            
            # Collecter les données pour chaque job_detail
            for job, job_detail in job_details:
                location = job_detail.location
                
                # Récupérer les stocks pour cet emplacement
                stocks = self.repository.get_stocks_by_location_and_inventory(
                    location,
                    job.inventory
                )
                
                has_stock = len(stocks) > 0 if stocks else False
                
                if 'vrac' in counting.count_mode.lower():
                    # Mode vrac
                    if has_stock:
                        total_quantity = sum(s.quantity_available for s in stocks)
                        all_job_details_data.append({
                            'job_reference': job.reference,
                            'job_status': job.status,
                            'location': location.location_reference,
                            'quantity': total_quantity
                        })
                    else:
                        all_job_details_data.append({
                            'job_reference': job.reference,
                            'job_status': job.status,
                            'location': location.location_reference,
                            'quantity': '-'
                        })
                else:
                    # Mode par article
                    if has_stock:
                        for stock in stocks:
                            all_job_details_data.append({
                                'job_reference': job.reference,
                                'job_status': job.status,
                                'location': location.location_reference,
                                'article': stock.product.Short_Description if stock.product else '-',
                                'quantity': stock.quantity_available,
                                'dlc': counting.dlc and stock.product and stock.product.dlc,
                                'n_lot': counting.n_lot and stock.product and stock.product.n_lot,
                                'is_variant': counting.is_variant and stock.product and stock.product.Is_Variant,
                                'stock': stock
                            })
                    else:
                        all_job_details_data.append({
                            'job_reference': job.reference,
                            'job_status': job.status,
                            'location': location.location_reference,
                            'article': '-',
                            'quantity': '-',
                            'dlc': False,
                            'n_lot': False,
                            'is_variant': False
                        })
        
        if not all_job_details_data:
            no_detail_style = ParagraphStyle(
                'NoDetail',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                spaceAfter=10,
            )
            elements.append(Paragraph("<i>Aucun emplacement trouvé</i>", no_detail_style))
            elements.append(Spacer(1, 0.3*cm))
            return elements
        
        # Construire les en-têtes selon la configuration
        headers = ['Job', 'Emplacement']
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article
            # Colonne Article seulement si show_product est activé
            if counting.show_product:
                headers.append('Article')
            
            headers.append('Quantité')
            
            # Colonnes optionnelles selon la configuration du counting
            if counting.dlc:
                headers.append('DLC')
            if counting.n_lot:
                headers.append('N° Lot')
            if counting.is_variant:
                headers.append('Variante')
        else:
            # Mode vrac
            headers.append('Quantité')
        
        # Construire les données du tableau
        data = [headers]
        
        for detail_data in all_job_details_data:
            row = [
                detail_data['job_reference'],
                detail_data['location']
            ]
            
            if 'vrac' not in counting.count_mode.lower():
                # Mode par article
                # Ajouter Article seulement si show_product est activé
                if counting.show_product:
                    row.append(detail_data.get('article', '-'))
                
                row.append(detail_data.get('quantity', '-'))
                
                # Colonnes optionnelles selon la configuration
                if counting.dlc:
                    row.append('Oui' if detail_data.get('dlc', False) else '-')
                if counting.n_lot:
                    row.append('Oui' if detail_data.get('n_lot', False) else '-')
                if counting.is_variant:
                    row.append('Oui' if detail_data.get('is_variant', False) else '-')
            else:
                # Mode vrac
                row.append(detail_data.get('quantity', '-'))
            
            data.append(row)
        
        # Créer le tableau
        col_widths = self._calculate_merged_column_widths(headers, A4[0])
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style du tableau
        table.setStyle(TableStyle([
            # En-tête
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
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Emplacement centré
            
            # Aligner la colonne Quantité à droite (trouver son index)
            ('ALIGN', (headers.index('Quantité'), 1), (headers.index('Quantité'), -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _build_job_table(self, job, counting, user=None):
        """Construit le tableau pour un job"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Ajouter un titre pour le job avec sa référence et statut
        job_title_style = ParagraphStyle(
            'JobTitle',
            parent=styles['Heading4'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=5,
            spaceBefore=8,
        )
        job_title = Paragraph(
            f"<b>Job:</b> {job.reference} | <b>Statut:</b> {job.status}",
            job_title_style
        )
        elements.append(job_title)
        elements.append(Spacer(1, 0.2*cm))
        
        # Vérifier si le job a un assignment pour ce comptage
        assignments = self.repository.get_assignments_by_job(job)
        has_assignment_for_counting = any(a.counting_id == counting.id for a in assignments)
        
        if not has_assignment_for_counting:
            # Le job n'a pas d'assignment pour ce comptage, ne pas l'afficher
            return elements
        
        # Recuperer tous les job details du job
        # Le job est déjà filtré par counting via l'assignement, donc on prend tous les job_details
        all_job_details = self.repository.get_job_details_by_job(job)
        
        # Si certains job_details ont un counting défini, filtrer ceux qui correspondent ou sont null
        # Sinon, prendre tous les job_details
        job_details = []
        for jd in all_job_details:
            # Si le counting du job_detail est null OU correspond au counting recherché
            if jd.counting_id is None or jd.counting_id == counting.id:
                job_details.append(jd)
        
        if not job_details:
            # Afficher un message si aucun job detail trouvé
            no_detail_style = ParagraphStyle(
                'NoDetail',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                spaceAfter=10,
            )
            elements.append(Paragraph("<i>Aucun emplacement trouvé pour ce job</i>", no_detail_style))
            elements.append(Spacer(1, 0.3*cm))
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
    
    def _calculate_merged_column_widths(self, headers, page_width, margins=4*cm):
        """Calcule la largeur des colonnes pour le tableau fusionné"""
        available_width = page_width - margins
        num_headers = len(headers)
        
        if num_headers == 0:
            return []
        
        # Colonnes fixes: Job (18%), Emplacement (20%)
        fixed_widths = {
            'Job': 0.18,
            'Emplacement': 0.20
        }
        
        # Calculer les largeurs
        widths = []
        used_percentage = 0
        
        # Colonnes fixes en premier
        for header in headers:
            if header in fixed_widths:
                widths.append(available_width * fixed_widths[header])
                used_percentage += fixed_widths[header]
            else:
                # Pour les colonnes variables, on calculera après
                widths.append(None)
        
        # Répartir l'espace restant pour les colonnes variables
        remaining_percentage = 1.0 - used_percentage
        variable_headers_count = sum(1 for w in widths if w is None)
        
        if variable_headers_count > 0:
            width_per_variable = remaining_percentage / variable_headers_count
            widths = [w if w is not None else available_width * width_per_variable for w in widths]
        
        return widths
    
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
    
    def generate_job_assignment_pdf(
        self,
        job_id: int,
        assignment_id: int,
        equipe_id: Optional[int] = None
    ) -> BytesIO:
        """
        Genere un PDF pour un job/assignment/equipe specifique
        Utilise les donnees de CountingDetail au lieu de Stock
        
        Args:
            job_id: ID du job
            assignment_id: ID de l'assignment
            equipe_id: ID de l'equipe (personne ou personne_two) - optionnel
            
        Returns:
            BytesIO: Le contenu du PDF en memoire
        """
        # Recuperer l'assignment
        assignment = self.repository.get_assignment_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment avec l'ID {assignment_id} non trouve")
        
        # Verifier que l'assignment correspond au job
        if assignment.job_id != job_id:
            raise ValueError(f"L'assignment {assignment_id} n'appartient pas au job {job_id}")
        
        # Recuperer le job
        job = assignment.job
        if not job:
            raise ValueError(f"Job avec l'ID {job_id} non trouve")
        
        # Recuperer l'inventaire
        inventory = job.inventory
        if not inventory:
            raise ValueError(f"Inventaire non trouve pour le job {job_id}")
        
        # Recuperer le counting depuis l'assignment
        counting = assignment.counting
        if not counting:
            raise ValueError(f"Comptage non trouve pour l'assignment {assignment_id}")
        
        # Recuperer les infos du warehouse et account
        warehouse_info = self._get_warehouse_info(inventory)
        account_info = self._get_account_info(inventory)
        
        # Recuperer les personnes de l'equipe
        personne = assignment.personne
        personne_two = assignment.personne_two
        
        # Si equipe_id est fourni, filtrer par cette personne
        if equipe_id:
            if personne and personne.id == equipe_id:
                equipe_nom = f"{personne.nom} {personne.prenom}"
            elif personne_two and personne_two.id == equipe_id:
                equipe_nom = f"{personne_two.nom} {personne_two.prenom}"
            else:
                raise ValueError(f"L'equipe {equipe_id} n'est pas associee a l'assignment {assignment_id}")
        else:
            # Construire le nom de l'equipe a partir des deux personnes
            equipe_parts = []
            if personne:
                equipe_parts.append(f"{personne.nom} {personne.prenom}")
            if personne_two:
                equipe_parts.append(f"{personne_two.nom} {personne_two.prenom}")
            equipe_nom = " / ".join(equipe_parts) if equipe_parts else "Non affecte"
        
        # Recuperer les counting details pour ce job et ce counting
        counting_details = self.repository.get_counting_details_by_job_and_counting(job, counting)
        
        if not counting_details:
            raise ValueError(f"Aucun detail de comptage trouve pour le job {job_id} et le comptage {counting.id}")
        
        # Creer le buffer PDF
        buffer = BytesIO()
        
        # Construire le contenu
        story = []
        
        # Construire les pages pour ce job avec les counting details
        story.extend(self._build_job_pages_from_counting_details(
            job, counting, equipe_nom, inventory, warehouse_info, account_info, counting_details
        ))
        
        # Creer le document PDF avec marges ajustees
        # Marge du bas augmentee pour laisser de la place aux signatures (4cm)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1*cm,
            bottomMargin=4*cm  # Espace pour les signatures
        )
        
        # Calculer la pagination
        page_info_map = {}
        lines_per_page = 20
        total_rows = len(counting_details)
        total_pages = (total_rows + lines_per_page - 1) // lines_per_page if total_rows > 0 else 1
        
        for page_num in range(total_pages):
            page_info_map[page_num + 1] = {
                'current': page_num + 1,
                'total': total_pages,
                'job_ref': job.reference
            }
        
        # Stocker les infos de pagination dans le document
        doc.page_info_map = page_info_map
        
        # Stocker les informations des personnes pour la signature
        doc.personne_info = {
            'personne': f"{personne.nom} {personne.prenom}" if personne else None,
            'personne_two': f"{personne_two.nom} {personne_two.prenom}" if personne_two else None
        }
        
        # Construire le PDF avec header (logo) et footer (pagination + signatures) personnalises
        doc.build(story, 
                 onFirstPage=self._add_page_header_and_footer_with_signatures, 
                 onLaterPages=self._add_page_header_and_footer_with_signatures)
        
        # Reinitialiser le buffer
        buffer.seek(0)
        return buffer
    
    def _build_job_pages_from_counting_details(
        self, 
        job, 
        counting, 
        equipe_nom, 
        inventory, 
        warehouse_info, 
        account_info, 
        counting_details
    ):
        """Construit les pages pour un job avec les counting details (pagination de 20 lignes par page)"""
        elements = []
        
        if not counting_details:
            return elements
        
        # Construire toutes les lignes du tableau d'abord
        all_table_rows = self._prepare_table_rows_from_counting_details(counting_details, counting)
        
        if not all_table_rows:
            return elements
        
        # Paginer par groupes de 20 lignes
        lines_per_page = 20
        total_pages = (len(all_table_rows) + lines_per_page - 1) // lines_per_page
        
        for page_num in range(total_pages):
            start_idx = page_num * lines_per_page
            end_idx = min(start_idx + lines_per_page, len(all_table_rows))
            page_rows = all_table_rows[start_idx:end_idx]
            
            # En-tete de page avec infos inventaire + job + equipe
            elements.extend(self._build_page_header(
                inventory, job, equipe_nom, counting, warehouse_info, account_info, page_num + 1, total_pages
            ))
            
            # Tableau des details du job (max 20 lignes) avec pagination en bas
            elements.extend(self._build_table_from_rows(page_rows, counting, page_num + 1, total_pages))
            
            # Saut de page si ce n'est pas la derniere page
            if page_num < total_pages - 1:
                elements.append(PageBreak())
        
        return elements
    
    def _prepare_table_rows_from_counting_details(self, counting_details, counting):
        """Prepare toutes les lignes du tableau a partir des CountingDetail"""
        rows = []
        
        if 'vrac' not in counting.count_mode.lower():
            # Mode par article - une ligne par CountingDetail
            for counting_detail in counting_details:
                location = counting_detail.location
                product = counting_detail.product
                quantity = counting_detail.quantity_inventoried
                
                row = {
                    'location': location.location_reference,
                    'barcode': product.Barcode if product and product.Barcode else '-',
                    'designation': product.Short_Description if product else '-',
                    'quantite_physique': quantity,
                    'quantite_theorique': '-',  # Pas de quantite theorique dans CountingDetail
                    'dlc': counting_detail.dlc.strftime('%d/%m/%Y') if counting_detail.dlc else '-',
                    'n_lot': counting_detail.n_lot if counting_detail.n_lot else '-',
                    'is_variant': product and product.Is_Variant if product else False,
                }
                rows.append(row)
        else:
            # Mode vrac - grouper par location et sommer les quantites
            location_quantities = {}
            for counting_detail in counting_details:
                location_ref = counting_detail.location.location_reference
                quantity = counting_detail.quantity_inventoried
                
                if location_ref in location_quantities:
                    location_quantities[location_ref] += quantity
                else:
                    location_quantities[location_ref] = quantity
            
            # Creer une ligne par location
            for location_ref, total_quantity in location_quantities.items():
                row = {
                    'location': location_ref,
                    'quantite_physique': total_quantity,
                    'quantite_theorique': '-',  # Pas de quantite theorique dans CountingDetail
                }
                rows.append(row)
        
        return rows

