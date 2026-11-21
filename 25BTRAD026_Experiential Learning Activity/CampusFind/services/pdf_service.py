from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

class PDFService:
    def _get_doc(self, filename):
        from config import EXPORTS_DIR, APP_NAME
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = EXPORTS_DIR / filename
        doc = SimpleDocTemplate(str(path), pagesize=A4,
                                rightMargin=1.5*cm, leftMargin=1.5*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        return doc, str(path)
    
    def _header_elements(self, title: str):
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Title'],
            textColor=colors.HexColor('#2d7a2d'), fontSize=18, spaceAfter=6)
        sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
            textColor=colors.HexColor('#6b8f6b'), fontSize=10, spaceAfter=12)
        elements = []
        elements.append(Paragraph("CampusFind", title_style))
        elements.append(Paragraph("Smart College Lost and Found Management System", sub_style))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2d7a2d')))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(title, ParagraphStyle('ReportTitle', parent=styles['Heading1'],
            textColor=colors.HexColor('#1a3a1a'), fontSize=14, spaceAfter=4)))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", sub_style))
        elements.append(Spacer(1, 0.5*cm))
        return elements
    
    def _make_table(self, headers, rows, col_widths=None):
        data = [headers] + rows
        t = Table(data, colWidths=col_widths)
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d7a2d')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5fdf5')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c8')),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('PADDING', (0,0), (-1,-1), 6),
        ])
        t.setStyle(style)
        return t
    
    def generate_lost_items_report(self, items: list, filename: str = None) -> str:
        if not filename:
            filename = f"lost_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc, path = self._get_doc(filename)
        elements = self._header_elements("Lost Items Report")
        
        headers = ['ID', 'Item Name', 'Category', 'Location', 'Date', 'Status', 'Reported By']
        rows = []
        for item in items:
            rows.append([
                str(item.get('item_id', '')),
                str(item.get('item_name', ''))[:30],
                str(item.get('category', '')),
                str(item.get('location', '')),
                str(item.get('item_date', '')),
                str(item.get('status', '')).upper(),
                str(item.get('full_name', item.get('user_id', '')))[:20],
            ])
        if not rows:
            rows = [['No items found', '', '', '', '', '', '']]
        
        col_widths = [1*cm, 4*cm, 3*cm, 3*cm, 2.5*cm, 2*cm, 3*cm]
        elements.append(self._make_table(headers, rows, col_widths))
        elements.append(Spacer(1, 0.5*cm))
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f"Total Records: {len(items)}", styles['Normal']))
        doc.build(elements)
        return path
    
    def generate_found_items_report(self, items: list, filename: str = None) -> str:
        if not filename:
            filename = f"found_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc, path = self._get_doc(filename)
        elements = self._header_elements("Found Items Report")
        
        headers = ['ID', 'Item Name', 'Category', 'Location', 'Date', 'Status']
        rows = []
        for item in items:
            rows.append([
                str(item.get('item_id', '')),
                str(item.get('item_name', ''))[:30],
                str(item.get('category', '')),
                str(item.get('location', '')),
                str(item.get('item_date', '')),
                str(item.get('status', '')).upper(),
            ])
        if not rows:
            rows = [['No items found', '', '', '', '', '']]
        
        col_widths = [1.5*cm, 5*cm, 3.5*cm, 3.5*cm, 2.5*cm, 2.5*cm]
        elements.append(self._make_table(headers, rows, col_widths))
        elements.append(Spacer(1, 0.5*cm))
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f"Total Records: {len(items)}", styles['Normal']))
        doc.build(elements)
        return path
    
    def generate_claim_history(self, claims: list, filename: str = None) -> str:
        if not filename:
            filename = f"claims_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc, path = self._get_doc(filename)
        elements = self._header_elements("Claim History Report")
        
        headers = ['Claim ID', 'Lost Item', 'Found Item', 'Claimant', 'Status', 'Date']
        rows = []
        for c in claims:
            rows.append([
                str(c.get('claim_id', '')),
                str(c.get('lost_item_name', c.get('lost_item_id', '')))[:25],
                str(c.get('found_item_name', c.get('found_item_id', '')))[:25],
                str(c.get('claimant_name', c.get('claimant_id', '')))[:20],
                str(c.get('claim_status', '')).upper(),
                str(c.get('created_at', ''))[:10],
            ])
        if not rows:
            rows = [['No claims found', '', '', '', '', '']]
        
        col_widths = [2*cm, 3.5*cm, 3.5*cm, 3*cm, 2.5*cm, 3*cm]
        elements.append(self._make_table(headers, rows, col_widths))
        styles = getSampleStyleSheet()
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(f"Total Claims: {len(claims)}", styles['Normal']))
        doc.build(elements)
        return path
    
    def generate_monthly_report(self, month: str, lost_items: list, found_items: list, claims: list) -> str:
        filename = f"monthly_{month}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc, path = self._get_doc(filename)
        elements = self._header_elements(f"Monthly Report - {month}")
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph("Summary", styles['Heading2']))
        summary_data = [
            ['Metric', 'Count'],
            ['Lost Items Reported', str(len(lost_items))],
            ['Found Items Reported', str(len(found_items))],
            ['Claims Submitted', str(len(claims))],
        ]
        t = Table(summary_data, colWidths=[8*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d7a2d')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c8')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(t)
        doc.build(elements)
        return path
    
    def generate_analytics_report(self, analytics_data: dict) -> str:
        filename = f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc, path = self._get_doc(filename)
        elements = self._header_elements("Analytics Report")
        styles = getSampleStyleSheet()
        
        # Claim stats
        claim_stats = analytics_data.get('claim_stats', {})
        elements.append(Paragraph("Claim Statistics", styles['Heading2']))
        claim_data = [['Status', 'Count']] + [[k.title(), str(v)] for k, v in claim_stats.items()]
        if len(claim_data) > 1:
            t = Table(claim_data, colWidths=[8*cm, 4*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d7a2d')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c8')),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            elements.append(t)
        
        doc.build(elements)
        return path
    
    def generate_user_report(self, user: dict, lost_items: list, found_items: list, claims: list) -> str:
        filename = f"user_report_{user.get('user_id', 'x')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc, path = self._get_doc(filename)
        elements = self._header_elements(f"Student Report - {user.get('full_name', 'Unknown')}")
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph(f"USN: {user.get('usn', '')}", styles['Normal']))
        elements.append(Paragraph(f"Department: {user.get('department', '')}", styles['Normal']))
        elements.append(Paragraph(f"Email: {user.get('email', '')}", styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Lost Items: {len(lost_items)} | Found Items: {len(found_items)} | Claims: {len(claims)}", styles['Normal']))
        
        doc.build(elements)
        return path

pdf_service = PDFService()
