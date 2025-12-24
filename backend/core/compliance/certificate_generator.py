"""
PDF Certificate Generator for Compliance Reports

Generates professional compliance certificates with RadiKal branding.
"""

import io
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.pdfgen import canvas


class ComplianceCertificateGenerator:
    """
    Generates professional PDF compliance certificates.
    """
    
    def __init__(self, output_dir: str = "exports/certificates"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a56db'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#374151'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1f2937'),
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        
        self.body_style = ParagraphStyle(
            'BodyStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4b5563'),
            spaceAfter=12
        )
    
    def generate_certificate(
        self,
        certificate_id: str,
        analysis_id: Optional[str],
        defect_type: str,
        defect_measurements: dict,
        material_type: Optional[str],
        material_thickness: Optional[float],
        standard_code: str,
        standard_name: str,
        compliance_status: str,
        severity: str,
        pass_fail: bool,
        recommended_action: str,
        reasons: list,
        inspector_name: str,
        issue_date: Optional[datetime] = None,
    ) -> str:
        """
        Generate a compliance certificate PDF.
        
        Returns:
            str: Path to generated PDF file
        """
        if issue_date is None:
            issue_date = datetime.now()
        
        # Generate filename
        filename = f"certificate_{certificate_id}_{issue_date.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add logo (placeholder - using text for now)
        logo_text = Paragraph(
            "<b>RadiKal</b> XAI Quality Control",
            self.title_style
        )
        elements.append(logo_text)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Certificate title
        cert_title = Paragraph(
            "COMPLIANCE CERTIFICATE",
            self.subtitle_style
        )
        elements.append(cert_title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Certificate ID and date
        info_data = [
            ["Certificate ID:", certificate_id],
            ["Issue Date:", issue_date.strftime("%B %d, %Y at %H:%M UTC")],
            ["Inspector:", inspector_name],
        ]
        
        if analysis_id:
            info_data.insert(1, ["Analysis ID:", analysis_id])
        
        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#6b7280')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Divider
        elements.append(self._create_divider())
        elements.append(Spacer(1, 0.2 * inch))
        
        # Standard section
        elements.append(Paragraph("<b>Welding Standard Applied</b>", self.header_style))
        standard_text = f"{standard_code} - {standard_name}"
        elements.append(Paragraph(standard_text, self.body_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Material information
        if material_type or material_thickness:
            elements.append(Paragraph("<b>Material Information</b>", self.header_style))
            material_data = []
            if material_type:
                material_data.append(["Material Type:", material_type])
            if material_thickness:
                material_data.append(["Material Thickness:", f"{material_thickness} mm"])
            
            material_table = Table(material_data, colWidths=[2 * inch, 4 * inch])
            material_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4b5563')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(material_table)
            elements.append(Spacer(1, 0.15 * inch))
        
        # Defect details
        elements.append(Paragraph("<b>Defect Details</b>", self.header_style))
        defect_data = [["Defect Type:", self._format_defect_type(defect_type)]]
        
        if defect_measurements.get('length_mm'):
            defect_data.append(["Length:", f"{defect_measurements['length_mm']:.2f} mm"])
        if defect_measurements.get('width_mm'):
            defect_data.append(["Width:", f"{defect_measurements['width_mm']:.2f} mm"])
        if defect_measurements.get('depth_mm'):
            defect_data.append(["Depth:", f"{defect_measurements['depth_mm']:.2f} mm"])
        if defect_measurements.get('density_percent'):
            defect_data.append(["Density:", f"{defect_measurements['density_percent']:.1f}%"])
        if defect_measurements.get('location'):
            defect_data.append(["Location:", defect_measurements['location']])
        
        defect_table = Table(defect_data, colWidths=[2 * inch, 4 * inch])
        defect_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4b5563')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(defect_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Compliance result - prominent section
        elements.append(self._create_divider())
        elements.append(Spacer(1, 0.2 * inch))
        
        elements.append(Paragraph("<b>Compliance Result</b>", self.header_style))
        
        # Status with color coding
        status_color = colors.HexColor('#059669') if pass_fail else colors.HexColor('#dc2626')
        status_text = "PASS ✓" if pass_fail else "FAIL ✗"
        
        result_data = [
            ["Status:", status_text],
            ["Compliance:", compliance_status.upper()],
            ["Severity:", severity.upper()],
        ]
        
        result_table = Table(result_data, colWidths=[2 * inch, 4 * inch])
        result_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
            ('TEXTCOLOR', (1, 0), (1, 0), status_color),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(result_table)
        elements.append(Spacer(1, 0.15 * inch))
        
        # Recommended action
        elements.append(Paragraph("<b>Recommended Action</b>", self.header_style))
        elements.append(Paragraph(recommended_action, self.body_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Reasons (if any)
        if reasons:
            elements.append(Paragraph("<b>Assessment Details</b>", self.header_style))
            for reason in reasons:
                bullet = Paragraph(f"• {reason}", self.body_style)
                elements.append(bullet)
            elements.append(Spacer(1, 0.2 * inch))
        
        # Footer
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(self._create_divider())
        elements.append(Spacer(1, 0.1 * inch))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9ca3af'),
            alignment=TA_CENTER
        )
        
        footer_text = (
            f"This certificate was generated by RadiKal XAI Quality Control System<br/>"
            f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S UTC')}<br/>"
            f"For questions or verification, contact your quality assurance department"
        )
        elements.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(elements)
        
        return str(filepath)
    
    def _create_divider(self):
        """Create a horizontal divider line."""
        line_data = [["" for _ in range(1)]]
        line_table = Table(line_data, colWidths=[6.5 * inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb')),
        ]))
        return line_table
    
    def _format_defect_type(self, defect_type: str) -> str:
        """Format defect type code to human-readable name."""
        defect_names = {
            'CR': 'Crack',
            'PO': 'Porosity',
            'IN': 'Inclusion',
            'LF': 'Lack of Fusion',
            'LP': 'Lack of Penetration',
            'UN': 'Undercut',
            'SL': 'Slag Line',
        }
        return defect_names.get(defect_type, defect_type)
