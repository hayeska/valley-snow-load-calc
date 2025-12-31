# pdf_generator.py - PDF report generation for Valley Calculator V2.0

from typing import Dict

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        PageBreak,
    )
    from reportlab.platypus.flowables import KeepTogether

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: ReportLab not available. PDF reports will not be generated.")


class PDFReportGenerator:
    """
    Generate professional PDF reports for valley snow load analysis.
    """

    def __init__(self):
        """Initialize the PDF generator."""
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom styles for the report."""
        if not REPORTLAB_AVAILABLE:
            return

        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=16,
                spaceAfter=20,
                alignment=1,  # Center
            )
        )

        # Section header style
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkblue,
            )
        )

        # ASCE reference style
        self.styles.add(
            ParagraphStyle(
                name="ASCEReference",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.blue,
                fontName="Helvetica-Bold",
            )
        )

    def generate_report(
        self, results: Dict, diagram_figures: list = None, filename: str = None
    ) -> bool:
        """
        Generate a comprehensive PDF report.

        Args:
            results: Complete analysis results dictionary
            diagram_figures: List of matplotlib figures for diagrams
            filename: Output filename (optional)

        Returns:
            Success status
        """
        if not REPORTLAB_AVAILABLE:
            print("Error: ReportLab library not available for PDF generation")
            return False

        if not filename:
            filename = f"valley_snow_load_report_{results.get('timestamp', 'unknown').replace(':', '-')}.pdf"

        try:
            # Create PDF document
            doc = SimpleDocTemplate(filename, pagesize=letter)
            story = []

            # Title page
            story.extend(self._create_title_page(results))

            # Project information
            story.extend(self._create_project_section(results))

            # Snow load analysis
            story.extend(self._create_snow_load_section(results))

            # Geometry analysis
            story.extend(self._create_geometry_section(results))

            # Drift analysis
            story.extend(self._create_drift_section(results))

            # Beam analysis
            story.extend(self._create_beam_analysis_section(results))

            # Diagrams
            if diagram_figures:
                story.extend(self._create_diagrams_section(diagram_figures))

            # ASCE references
            story.extend(self._create_references_section(results))

            # Build PDF
            doc.build(story)
            print(f"PDF report generated: {filename}")
            return True

        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return False

    def _create_title_page(self, results: Dict) -> list:
        """Create the title page."""
        elements = []

        # Main title
        title = Paragraph(
            "Valley Snow Load Analysis Report", self.styles["CustomTitle"]
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5 * inch))

        # Subtitle
        subtitle = Paragraph(
            "ASCE 7-22 Compliant Engineering Analysis", self.styles["Heading3"]
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 0.3 * inch))

        # Project info
        inputs = results.get("inputs", {})
        project_info = [
            ["Project:", inputs.get("project_name", "Unnamed Project")],
            ["Location:", inputs.get("location", "Not specified")],
            ["Analysis Date:", results.get("timestamp", "Unknown")],
            ["ASCE Standard:", "7-22"],
        ]

        table = Table(project_info, colWidths=[1.5 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(PageBreak())

        return elements

    def _create_project_section(self, results: Dict) -> list:
        """Create project information section."""
        elements = []

        header = Paragraph("1. PROJECT INFORMATION", self.styles["SectionHeader"])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))

        inputs = results.get("inputs", {})
        snow_loads = results.get("snow_loads", {})

        project_data = [
            ["Ground Snow Load (pg)", f"{snow_loads.get('pg', 0):.1f} psf"],
            ["Exposure Factor (Ce)", f"{inputs.get('ce', 1.0):.2f}"],
            ["Thermal Factor (Ct)", f"{inputs.get('ct', 1.0):.2f}"],
            ["Importance Factor (Is)", f"{inputs.get('is', 1.0):.2f}"],
            ["North Roof Span", f"{inputs.get('north_span', 0):.1f} ft"],
            ["South Roof Span", f"{inputs.get('south_span', 0):.1f} ft"],
            ["East-West Half Width", f"{inputs.get('ew_half_width', 0):.1f} ft"],
        ]

        table = Table(project_data, colWidths=[2.5 * inch, 1.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_snow_load_section(self, results: Dict) -> list:
        """Create snow load analysis section."""
        elements = []

        header = Paragraph("2. SNOW LOAD ANALYSIS", self.styles["SectionHeader"])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))

        snow_loads = results.get("snow_loads", {})
        slope_params = results.get("slope_parameters", {})

        snow_data = [
            ["Balanced Snow Load (ps)", f"{snow_loads.get('ps_balanced', 0):.1f} psf"],
            ["North Roof Slope", f"{slope_params.get('theta_n', 0):.1f}°"],
            ["West Roof Slope", f"{slope_params.get('theta_w', 0):.1f}°"],
            ["North Slope Factor (Cs)", f"{slope_params.get('Cs_n', 0):.3f}"],
            ["West Slope Factor (Cs)", f"{slope_params.get('Cs_w', 0):.3f}"],
        ]

        table = Table(snow_data, colWidths=[2.5 * inch, 1.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgreen),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_geometry_section(self, results: Dict) -> list:
        """Create geometry analysis section."""
        elements = []

        header = Paragraph("3. GEOMETRY ANALYSIS", self.styles["SectionHeader"])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))

        valley_geom = results.get("valley_geometry", {})

        geom_data = [
            ["Valley Rafter Length", f"{valley_geom.get('rafter_length', 0):.2f} ft"],
            ["North Span", f"{valley_geom.get('north_span', 0):.1f} ft"],
            ["South Span", f"{valley_geom.get('south_span', 0):.1f} ft"],
            ["E-W Half Width", f"{valley_geom.get('ew_half_width', 0):.1f} ft"],
            ["Valley Offset", f"{valley_geom.get('valley_offset', 0):.1f} ft"],
            ["Valley Angle", f"{valley_geom.get('valley_angle', 0):.1f}°"],
        ]

        table = Table(geom_data, colWidths=[2.5 * inch, 1.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightyellow),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_drift_section(self, results: Dict) -> list:
        """Create drift analysis section."""
        elements = []

        header = Paragraph("4. DRIFT ANALYSIS", self.styles["SectionHeader"])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))

        snow_loads = results.get("snow_loads", {})
        drift_loads = snow_loads.get("drift_loads", {})
        valley_drift = drift_loads.get("valley_drift", {})

        drift_data = [
            ["Governing Drift Load", f"{valley_drift.get('pd_max_psf', 0):.1f} psf"],
            ["Drift Height (hd)", f"{valley_drift.get('hd_ft', 0):.2f} ft"],
            ["Drift Width (w)", f"{valley_drift.get('drift_width_ft', 0):.1f} ft"],
            [
                "North Roof Drift Load",
                f"{drift_loads.get('north_drift', {}).get('pd_max_psf', 0):.1f} psf",
            ],
            [
                "West Roof Drift Load",
                f"{drift_loads.get('west_drift', {}).get('pd_max_psf', 0):.1f} psf",
            ],
        ]

        table = Table(drift_data, colWidths=[2.5 * inch, 1.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightcoral),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_beam_analysis_section(self, results: Dict) -> list:
        """Create beam analysis section."""
        elements = []

        header = Paragraph("5. STRUCTURAL ANALYSIS", self.styles["SectionHeader"])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))

        beam_analysis = results.get("beam_analysis", {})
        beam_results = beam_analysis.get("beam_results", {})
        max_values = beam_results.get("max_values", {})
        stress_checks = beam_results.get("stress_checks", {})

        beam_data = [
            ["Maximum Moment", f"{max_values.get('moment_lbft', 0):.0f} lb-ft"],
            ["Maximum Shear", f"{max_values.get('shear_lb', 0):.0f} lb"],
            ["Maximum Deflection", f"{max_values.get('deflection_in', 0):.3f} in"],
            [
                "Bending Stress Check",
                f"{'PASS' if stress_checks.get('bending', {}).get('passes_bending', False) else 'FAIL'}",
            ],
            [
                "Shear Stress Check",
                f"{'PASS' if stress_checks.get('shear', {}).get('passes_shear', False) else 'FAIL'}",
            ],
            [
                "Deflection Check",
                f"{'PASS' if stress_checks.get('deflection', {}).get('passes_deflection', False) else 'FAIL'}",
            ],
            [
                "Overall Result",
                "PASS" if beam_results.get("overall_passes", False) else "FAIL",
            ],
        ]

        table = Table(beam_data, colWidths=[2.5 * inch, 1.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightsteelblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_diagrams_section(self, diagram_figures: list) -> list:
        """Create diagrams section with matplotlib figures."""
        elements = []

        if not diagram_figures:
            return elements

        header = Paragraph("6. ENGINEERING DIAGRAMS", self.styles["SectionHeader"])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))

        diagram_names = [
            "Roof Plan View",
            "North Wind Drift Overlay",
            "Drift Load Profile",
            "Snow Load Distribution",
        ]

        for i, (fig, name) in enumerate(zip(diagram_figures, diagram_names)):
            if fig is None:
                continue

            # Save figure to temporary file
            import io

            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)

            # Create Image object
            img = Image(img_buffer)
            img.drawHeight = 3 * inch
            img.drawWidth = 5 * inch

            # Add diagram title
            title = Paragraph(f"{name}", self.styles["Heading4"])
            elements.append(KeepTogether([title, img]))
            elements.append(Spacer(1, 0.2 * inch))

            if i < len(diagram_figures) - 1:
                elements.append(PageBreak())

        return elements

    def _create_references_section(self, results: Dict) -> list:
        """Create references section."""
        elements = []

        header = Paragraph("7. REFERENCES", self.styles["SectionHeader"])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))

        asce_ref = results.get("asce_reference", "ASCE 7-22")
        ref_text = f"""
        This analysis was performed in accordance with {asce_ref}.

        Key provisions used:
        • Section 7.3 - Balanced Snow Loads
        • Section 7.6.1 - Unbalanced Snow Loads for Hip and Gable Roofs
        • Section 7.7 - Drift Loads on Lower Roofs
        • Section 7.8 - Design Procedures

        Always consult the full ASCE 7-22 standard and local building codes for complete requirements.
        """

        ref_paragraph = Paragraph(ref_text, self.styles["Normal"])
        elements.append(ref_paragraph)
        elements.append(Spacer(1, 0.3 * inch))

        return elements
