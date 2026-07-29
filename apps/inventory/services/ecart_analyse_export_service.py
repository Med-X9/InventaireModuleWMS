"""
Service d'export analyse écarts stock théorique (Excel) et PDF recomptage.
"""
from __future__ import annotations

import logging
from io import BytesIO
from typing import Any, Dict, List, Optional, Set, Tuple

from apps.inventory.exceptions.inventory_exceptions import InventoryNotFoundError
from apps.inventory.exceptions.warehouse_exceptions import WarehouseNotFoundError
from apps.inventory.models import Inventory
from apps.inventory.repositories.ecart_stock_theorique_repository import (
    EcartStockTheoriqueRepository,
)
from apps.masterdata.models import Stock, Warehouse

logger = logging.getLogger(__name__)


class EcartAnalyseExportService:
    """
    Exports liés à l'analyse magasin (EcartStockTheorique).

    - Excel : toutes les lignes d'analyse (théorique / pratique / écart)
    - PDF : uniquement écart ≠ 0, tableau recomptage
      (emplacement, désignation, barcode, qté vide) + header magasin
    """

    def __init__(
        self,
        repository: Optional[EcartStockTheoriqueRepository] = None,
    ) -> None:
        self.repository = repository or EcartStockTheoriqueRepository()

    def _get_inventory_and_warehouse(
        self, inventory_id: int, warehouse_id: int
    ) -> Tuple[Inventory, Warehouse]:
        try:
            inventory = Inventory.objects.get(id=inventory_id, is_deleted=False)
        except Inventory.DoesNotExist as exc:
            raise InventoryNotFoundError(
                f"Inventaire avec l'ID {inventory_id} non trouvé"
            ) from exc
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist as exc:
            raise WarehouseNotFoundError(
                f"Entrepôt avec l'ID {warehouse_id} non trouvé"
            ) from exc
        return inventory, warehouse

    def generate_analyse_excel(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> BytesIO:
        """
        Génère un Excel de toutes les lignes EcartStockTheorique du magasin.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise ValueError(
                "pandas est requis pour l'export Excel. "
                "Installez-le avec: pip install pandas"
            ) from exc

        inventory, warehouse = self._get_inventory_and_warehouse(
            inventory_id, warehouse_id
        )
        qs = self.repository.get_for_inventory_warehouse(
            inventory_id, warehouse_id
        )
        rows: List[Dict[str, Any]] = []
        for ecart in qs:
            barcode = ""
            if ecart.product_id and ecart.product:
                barcode = ecart.product.Barcode or ""
            if not barcode:
                barcode = ecart.article_cle or ""
            rows.append(
                {
                    "Désignation": ecart.designation or "",
                    "Barcode": barcode,
                    "Qté théorique": ecart.qte_theorique,
                    "Qté inventoriée": ecart.qte_pratique,
                    "Écart": ecart.ecart,
                    "Résultat final": (
                        ecart.resultat_final
                        if ecart.resultat_final is not None
                        else ""
                    ),
                    "Validé": "Oui" if ecart.valide else "Non",
                }
            )

        if not rows:
            raise ValueError(
                f"Aucune donnée d'analyse pour inventaire {inventory.reference} "
                f"/ magasin {warehouse.warehouse_name}"
            )

        df = pd.DataFrame(rows)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Analyse")
        buffer.seek(0)
        logger.info(
            "Export Excel analyse: %s lignes (inv=%s wh=%s)",
            len(rows),
            inventory_id,
            warehouse_id,
        )
        return buffer

    def get_pdf_recount_rows(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> Tuple[Warehouse, Inventory, List[Dict[str, str]]]:
        """
        Lignes PDF : écart ≠ 0, une ligne par emplacement stock trouvé.

        Colonnes : emplacement, designation, barcode, qte (toujours vide).
        """
        inventory, warehouse = self._get_inventory_and_warehouse(
            inventory_id, warehouse_id
        )
        ecarts = list(
            self.repository.get_nonzero_ecarts(inventory_id, warehouse_id)
        )
        if not ecarts:
            raise ValueError(
                "Aucune ligne avec écart à exporter pour ce magasin"
            )

        product_ids: Set[int] = {
            e.product_id for e in ecarts if e.product_id is not None
        }
        stocks_by_product: Dict[int, List[Stock]] = {pid: [] for pid in product_ids}
        if product_ids:
            stock_qs = (
                Stock.objects.filter(
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id,
                    product_id__in=product_ids,
                )
                .select_related("location", "product")
                .order_by("location__location_reference", "id")
            )
            for stock in stock_qs:
                stocks_by_product.setdefault(stock.product_id, []).append(stock)

        rows: List[Dict[str, str]] = []
        seen: Set[Tuple[str, str, str]] = set()

        for ecart in ecarts:
            barcode = ""
            if ecart.product_id and ecart.product:
                barcode = (ecart.product.Barcode or "").strip()
            if not barcode:
                barcode = (ecart.article_cle or "").strip()
            designation = (ecart.designation or "").strip()

            stock_list = (
                stocks_by_product.get(ecart.product_id, [])
                if ecart.product_id
                else []
            )
            if stock_list:
                for stock in stock_list:
                    emplacement = (
                        stock.location.location_reference
                        if stock.location_id and stock.location
                        else ""
                    )
                    key = (emplacement, barcode, designation)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "emplacement": emplacement,
                            "designation": designation,
                            "barcode": barcode,
                            "qte": "",
                        }
                    )
            else:
                key = ("", barcode, designation)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "emplacement": "",
                        "designation": designation,
                        "barcode": barcode,
                        "qte": "",
                    }
                )

        rows.sort(
            key=lambda r: (
                r["emplacement"] or "zzz",
                r["barcode"] or "",
                r["designation"] or "",
            )
        )
        return warehouse, inventory, rows

    def generate_ecart_pdf(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> BytesIO:
        """
        PDF tableau recomptage des lignes avec écart.
        Header : nom du magasin.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        warehouse, inventory, rows = self.get_pdf_recount_rows(
            inventory_id, warehouse_id
        )

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "EcartPdfTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=6,
            alignment=1,
        )
        subtitle_style = ParagraphStyle(
            "EcartPdfSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            spaceAfter=12,
            alignment=1,
        )

        story = []
        story.append(
            Paragraph(
                f"Magasin : {warehouse.warehouse_name}",
                title_style,
            )
        )
        story.append(
            Paragraph(
                f"Inventaire : {inventory.label} ({inventory.reference}) — "
                f"Lignes avec écart théorique / physique",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 0.4 * cm))

        table_data = [["Emplacement", "Désignation", "Barcode", "Qté"]]
        cell_style = ParagraphStyle(
            "EcartCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
        )
        for row in rows:
            table_data.append(
                [
                    Paragraph(row["emplacement"] or "—", cell_style),
                    Paragraph(row["designation"] or "—", cell_style),
                    Paragraph(row["barcode"] or "—", cell_style),
                    Paragraph("", cell_style),
                ]
            )

        col_widths = [4.5 * cm, 12 * cm, 5 * cm, 3 * cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ALIGN", (3, 1), (3, -1), "CENTER"),
                ]
            )
        )
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        logger.info(
            "Export PDF écarts: %s lignes (inv=%s wh=%s)",
            len(rows),
            inventory_id,
            warehouse_id,
        )
        return buffer
