# results_display.py - Results display panel for Valley Calculator V2.0

import tkinter as tk
from tkinter import ttk
from typing import Dict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ResultsDisplay(ttk.Frame):
    """
    Results display panel showing calculation results and diagrams.

    Features:
    - Tabbed interface for different result views
    - Interactive diagrams
    - Formatted text results
    - Export capabilities
    """

    def __init__(self, parent):
        """Initialize the results display."""
        super().__init__(parent)

        # Create notebook for tabbed results
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self._create_summary_tab()
        self._create_diagrams_tab()
        self._create_detailed_tab()
        self._create_report_tab()

        # Store current results
        self.current_results = None

    def _create_summary_tab(self):
        """Create the summary results tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Summary")

        # Create scrollable text area
        self.summary_text = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=self.summary_text.yview
        )
        self.summary_text.configure(yscrollcommand=scrollbar.set)

        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_diagrams_tab(self):
        """Create the diagrams tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Diagrams")

        # Create scrollable frame for diagrams
        self.diagrams_canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=self.diagrams_canvas.yview
        )
        self.diagrams_frame = ttk.Frame(self.diagrams_canvas)

        self.diagrams_frame.bind(
            "<Configure>",
            lambda e: self.diagrams_canvas.configure(
                scrollregion=self.diagrams_canvas.bbox("all")
            ),
        )

        self.diagrams_canvas.create_window(
            (0, 0), window=self.diagrams_frame, anchor="nw"
        )
        self.diagrams_canvas.configure(yscrollcommand=scrollbar.set)

        self.diagrams_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Store diagram widgets for cleanup
        self.diagram_widgets = []

    def _create_detailed_tab(self):
        """Create the detailed results tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Detailed Results")

        # Create scrollable text area
        self.detailed_text = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=self.detailed_text.yview
        )
        self.detailed_text.configure(yscrollcommand=scrollbar.set)

        self.detailed_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_report_tab(self):
        """Create the report generation tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Report")

        # Report controls
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            controls_frame,
            text="Generate PDF Report",
            command=self._generate_pdf_report,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            controls_frame,
            text="Generate HTML Report",
            command=self._generate_html_report,
        ).pack(side=tk.LEFT, padx=5)

        # Report preview
        self.report_text = tk.Text(frame, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=self.report_text.yview
        )
        self.report_text.configure(yscrollcommand=scrollbar.set)

        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def display_results(self, results: Dict):
        """Display calculation results in all tabs."""
        self.current_results = results

        # Update summary tab
        self._update_summary_tab(results)

        # Update detailed tab
        self._update_detailed_tab(results)

        # Update diagrams tab
        self._update_diagrams_tab(results)

        # Update report tab
        self._update_report_tab(results)

    def _update_summary_tab(self, results: Dict):
        """Update the summary tab with key results."""
        self.summary_text.delete(1.0, tk.END)

        # Header
        self.summary_text.insert(tk.END, "=" * 60 + "\n")
        self.summary_text.insert(tk.END, "VALLEY SNOW LOAD CALCULATION SUMMARY\n")
        self.summary_text.insert(tk.END, "=" * 60 + "\n\n")

        # Project info
        inputs = results.get("inputs", {})
        self.summary_text.insert(
            tk.END, f"Project: {inputs.get('project_name', 'Unnamed')}\n"
        )
        self.summary_text.insert(
            tk.END, f"Location: {inputs.get('location', 'Unknown')}\n\n"
        )

        # Snow loads
        snow_loads = results.get("snow_loads", {})
        self.summary_text.insert(tk.END, "SNOW LOADS:\n")
        self.summary_text.insert(
            tk.END, f"Ground Snow Load (pg): {snow_loads.get('pg', 0):.1f} psf\n"
        )
        self.summary_text.insert(
            tk.END,
            f"Balanced Snow Load (ps): {snow_loads.get('ps_balanced', 0):.1f} psf\n\n",
        )

        # Drift results
        drifts = snow_loads.get("drift_loads", {})
        governing = drifts.get("governing_drift", {})
        self.summary_text.insert(tk.END, "DRIFT ANALYSIS:\n")
        self.summary_text.insert(
            tk.END, f"Governing Drift Load: {governing.get('pd_max_psf', 0):.1f} psf\n"
        )
        self.summary_text.insert(
            tk.END, f"Drift Height: {governing.get('hd_ft', 0):.2f} ft\n"
        )
        self.summary_text.insert(
            tk.END, f"Drift Width: {governing.get('width_ft', 0):.1f} ft\n\n"
        )

        # Slope analysis
        slope_params = results.get("slope_parameters", {})
        self.summary_text.insert(tk.END, "SLOPE PARAMETERS:\n")
        self.summary_text.insert(
            tk.END,
            f"North Roof: {slope_params.get('theta_n', 0):.1f}° (S_n = {slope_params.get('S_n', 0):.2f})\n",
        )
        self.summary_text.insert(
            tk.END,
            f"West Roof: {slope_params.get('theta_w', 0):.1f}° (S_w = {slope_params.get('S_w', 0):.2f})\n\n",
        )

        # Unbalanced applicability
        unbalanced = results.get("unbalanced_applicability", {})
        self.summary_text.insert(tk.END, "UNBALANCED LOAD APPLICABILITY:\n")
        self.summary_text.insert(
            tk.END,
            f"North Roof: {'APPLIES' if unbalanced.get('north_applies', False) else 'NOT REQUIRED'}\n",
        )
        self.summary_text.insert(
            tk.END,
            f"West Roof: {'APPLIES' if unbalanced.get('west_applies', False) else 'NOT REQUIRED'}\n\n",
        )

        # Beam Analysis Results
        beam_analysis = results.get("beam_analysis", {})
        if beam_analysis:
            self.summary_text.insert(tk.END, "BEAM ANALYSIS RESULTS:\n")
            beam_results = beam_analysis.get("beam_results", {})
            max_values = beam_results.get("max_values", {})

            self.summary_text.insert(
                tk.END,
                f"Maximum Moment: {max_values.get('moment_lbft', 0):.0f} lb-ft\n",
            )
            self.summary_text.insert(
                tk.END, f"Maximum Shear: {max_values.get('shear_lb', 0):.0f} lb\n"
            )
            self.summary_text.insert(
                tk.END,
                f"Maximum Deflection: {max_values.get('deflection_in', 0):.3f} in\n",
            )

            # Stress checks
            stress_checks = beam_results.get("stress_checks", {})
            bending = stress_checks.get("bending", {})
            shear = stress_checks.get("shear", {})
            deflection = stress_checks.get("deflection", {})

            self.summary_text.insert(
                tk.END,
                f"Bending Check: {'PASS' if bending.get('passes_bending', False) else 'FAIL'} ",
            )
            self.summary_text.insert(
                tk.END, f"({bending.get('utilization_ratio', 0):.2f})\n"
            )
            self.summary_text.insert(
                tk.END,
                f"Shear Check: {'PASS' if shear.get('passes_shear', False) else 'FAIL'} ",
            )
            self.summary_text.insert(
                tk.END, f"({shear.get('utilization_ratio', 0):.2f})\n"
            )
            self.summary_text.insert(
                tk.END,
                f"Deflection Check: {'PASS' if deflection.get('passes_deflection', False) else 'FAIL'} ",
            )
            self.summary_text.insert(
                tk.END, f"({deflection.get('utilization_ratio', 0):.2f})\n"
            )

            overall_pass = beam_results.get("overall_passes", False)
            self.summary_text.insert(
                tk.END, f"Overall Result: {'PASS' if overall_pass else 'FAIL'}\n\n"
            )

        # Status
        status = results.get("status", "unknown")
        self.summary_text.insert(tk.END, f"Analysis Status: {status.upper()}\n")
        timestamp = results.get("timestamp", "Unknown")
        self.summary_text.insert(tk.END, f"Completed: {timestamp}\n")
        asce_ref = results.get("asce_reference", "")
        if asce_ref:
            self.summary_text.insert(tk.END, f"Reference: {asce_ref}\n")

    def _update_detailed_tab(self, results: Dict):
        """Update the detailed results tab."""
        self.detailed_text.delete(1.0, tk.END)

        # Format as JSON-like structure for detailed view
        import json

        formatted_results = json.dumps(results, indent=2, default=str)
        self.detailed_text.insert(tk.END, formatted_results)

    def _update_diagrams_tab(self, results: Dict):
        """Update the diagrams tab with matplotlib plots."""
        # Clear existing diagrams
        for widget in self.diagram_widgets:
            widget.destroy()
        self.diagram_widgets.clear()

        # Create actual engineering diagrams
        self._create_engineering_diagrams(results)

    def _create_engineering_diagrams(self, results: Dict):
        """Create actual engineering diagrams using calculation results."""
        try:
            # Extract parameters from results
            inputs = results.get("inputs", {})
            results.get("geometry", {})
            snow_loads = results.get("snow_loads", {})
            results.get("slope_parameters", {})

            # Basic parameters
            north_span = inputs.get("north_span", 16.0)
            south_span = inputs.get("south_span", 16.0)
            ew_half_width = inputs.get("ew_half_width", 42.0)
            valley_offset = inputs.get("valley_offset", 16.0)
            ps_balanced = snow_loads.get("ps_balanced", 20.0)

            # Drift results
            drift_loads = snow_loads.get("drift_loads", {})
            north_drift = drift_loads.get("north_drift", {})

            result_north = {
                "hd_ft": north_drift.get("hd_ft", 0),
                "drift_width_ft": north_drift.get("width_ft", 0),
                "pd_max_psf": north_drift.get("pd_max_psf", 0),
            }

            # Create roof plan view
            fig_plan = self._draw_plan_view(
                north_span, south_span, ew_half_width, valley_offset
            )
            self._embed_diagram(fig_plan, "Roof Plan View")

            # Create north drift diagram
            fig_north_drift = self._draw_north_drift_overlay(
                north_span,
                south_span,
                ew_half_width,
                valley_offset,
                result_north["hd_ft"],
                result_north["drift_width_ft"],
                ps_balanced,
                result_north["pd_max_psf"],
            )
            self._embed_diagram(fig_north_drift, "North Wind Drift")

            # Create drift load profile diagram
            try:
                fig_drift_profile = self._draw_drift_load_profile(
                    north_drift.get("hd_ft", 0),
                    north_drift.get("width_ft", 0),
                    north_drift.get("pd_max_psf", 0),
                )
                self._embed_diagram(fig_drift_profile, "Drift Load Profile")
            except Exception as e:
                self._embed_error_diagram(f"Drift Profile Error: {str(e)}")

            # Create snow load distribution diagram
            try:
                fig_snow_dist = self._draw_snow_load_distribution(
                    north_span,
                    south_span,
                    ps_balanced,
                    north_drift.get("pd_max_psf", 0),
                    south_span,
                )
                self._embed_diagram(fig_snow_dist, "Snow Load Distribution")
            except Exception as e:
                self._embed_error_diagram(f"Snow Distribution Error: {str(e)}")

        except Exception as e:
            # Fallback to simple error diagram
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(
                0.5,
                0.5,
                f"Diagram Error:\n{str(e)}",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=12,
                color="red",
            )
            ax.set_title("Diagram Error")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            self._embed_diagram(fig, "Error")

    def _draw_plan_view(self, north_span, south_span, ew_half_width, valley_offset):
        """Draw the roof plan view diagram."""
        import math

        fig = plt.Figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        total_width = 2 * ew_half_width
        total_height = north_span + south_span
        center_x = ew_half_width

        # Coordinate system: (0,0) at southwest corner (south eave left), Y increasing north (up page)
        # South eave at y=0, north eave at y=total_height

        # Building outline - rotated 180 degrees (south at bottom, north at top)
        ax.plot(
            [0, total_width, total_width, 0, 0],
            [total_height, total_height, 0, 0, total_height],
            "k-",
            linewidth=2,
            label="Building Outline",
        )

        # E-W ridge (horizontal at y = south_span from south eave)
        ax.plot(
            [0, total_width],
            [south_span, south_span],
            "k-",
            linewidth=3,
            label="E-W Ridge",
        )

        # N-S ridge (vertical, centered, from E-W ridge midpoint down to south eave)
        ax.plot(
            [center_x, center_x], [south_span, 0], "k-", linewidth=3, label="N-S Ridge"
        )

        # Valley lines – symmetric, using valley_offset
        # Southwest valley: from south eave corner to ridge intersection
        # Southeast valley: from south eave corner to ridge intersection
        ax.plot(
            [center_x - valley_offset, center_x],
            [0, south_span],
            "r--",
            linewidth=2,
            label="Valley Lines",
        )
        ax.plot(
            [center_x + valley_offset, center_x], [0, south_span], "r--", linewidth=2
        )

        # Labels - repositioned for 180 degree rotation with proper spacing
        ax.text(
            total_width / 2,
            south_span + north_span * 0.75,
            f"North span\n{north_span:.1f} ft\n(lu_north)",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )
        ax.text(
            total_width / 2,
            south_span * 0.25,
            f"South span\n{south_span:.1f} ft",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )
        ax.text(
            center_x * 0.3,
            -4,
            f"{ew_half_width:.1f} ft\n(lu_west)",
            ha="center",
            va="top",
        )
        ax.text(
            total_width - center_x * 0.3,
            -4,
            f"{ew_half_width:.1f} ft\n(lu_west)",
            ha="center",
            va="top",
        )
        ax.text(
            center_x,
            -8,
            f"Valley offset ±{valley_offset:.1f} ft → lv = {math.sqrt(south_span**2 + valley_offset**2):.1f} ft",
            ha="center",
            va="top",
        )

        # North arrow – at top center, separated from 'N' text (reduced size)
        arrow_x = total_width / 2
        arrow_y = total_height + 12
        ax.arrow(arrow_x, arrow_y, 0, 6, head_width=3, head_length=6, fc="k", ec="k")
        ax.text(
            arrow_x,
            arrow_y + 15,
            "N",
            fontsize=12,
            ha="center",
            fontweight="bold",
            va="bottom",
        )

        ax.set_xlim(-15, total_width + 15)
        ax.set_ylim(-25, total_height + 40)  # North at top, south at bottom
        ax.set_axis_off()
        ax.set_title("Roof Plan View")
        ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.0))

        return fig

    def _draw_north_drift_overlay(
        self,
        north_span,
        south_span,
        ew_half_width,
        valley_offset,
        hd_north,
        w_north,
        ps,
        pd_north,
    ):
        """Draw the north wind drift overlay diagram."""
        import math

        fig = plt.Figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        # Copy the exact same roof geometry as in the current draw_plan_view (do not change anything)
        total_width = 2 * ew_half_width
        total_height = north_span + south_span
        center_x = ew_half_width

        # Coordinate system: (0,0) at southwest corner (south eave left), Y increasing north (up page)
        # South eave at y=0, north eave at y=total_height

        # Building outline - rotated 180 degrees (south at bottom, north at top)
        ax.plot(
            [0, total_width, total_width, 0, 0],
            [total_height, total_height, 0, 0, total_height],
            "k-",
            linewidth=2,
            label="Building Outline",
        )

        # E-W ridge (horizontal at y = south_span from south eave)
        ax.plot(
            [0, total_width],
            [south_span, south_span],
            "k-",
            linewidth=3,
            label="E-W Ridge",
        )

        # N-S ridge (vertical, centered, from E-W ridge down to south eave)
        ax.plot(
            [center_x, center_x], [south_span, 0], "k-", linewidth=3, label="N-S Ridge"
        )

        # Valley lines – symmetric, using valley_offset
        # Southwest valley: from south eave corner to ridge intersection
        # Southeast valley: from south eave corner to ridge intersection
        ax.plot(
            [center_x - valley_offset, center_x],
            [0, south_span],
            "r--",
            linewidth=2,
            label="Valley Lines",
        )
        ax.plot(
            [center_x + valley_offset, center_x], [0, south_span], "r--", linewidth=2
        )

        # Labels - repositioned for 180 degree rotation with proper spacing
        ax.text(
            total_width / 2,
            south_span + north_span * 0.75,
            f"North span\n{north_span:.1f} ft\n(lu_north)",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )
        ax.text(
            total_width / 2,
            south_span * 0.25,
            f"South span\n{south_span:.1f} ft",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )
        ax.text(
            center_x * 0.3,
            -8,
            f"{ew_half_width:.1f} ft\n(lu_west)",
            ha="center",
            va="top",
        )
        ax.text(
            total_width - center_x * 0.3,
            -8,
            f"{ew_half_width:.1f} ft\n(lu_west)",
            ha="center",
            va="top",
        )
        ax.text(
            center_x,
            -8,
            f"Valley offset ±{valley_offset:.1f} ft → lv = {math.sqrt(south_span**2 + valley_offset**2):.1f} ft",
            ha="center",
            va="top",
        )

        # === NEW: North-wind leeward drift on south roof plane ===
        # Shaded rectangular area south of E-W ridge line, extending distance = w

        # Limit drift width by available south span if necessary (per code: if w > south_span, truncate)
        effective_w = min(w_north, south_span)

        # Rectangular shaded area south of E-W ridge line, extending distance = w
        # Clearly positioned south (below) of the ridge for leeward drift accumulation
        drift_bottom = south_span - effective_w  # South of ridge (lower y values)
        ax.fill_between(
            [center_x - ew_half_width, center_x + ew_half_width],
            drift_bottom,
            south_span,  # Fill from bottom up to ridge
            color="lightblue",
            alpha=0.7,
            hatch="///",
            edgecolor="navy",
            linewidth=1.5,
            label="North Wind Drift",
        )

        # Annotations for north drift - positioned to avoid overlap with south roof
        ax.text(
            total_width + 10,
            south_span / 2,
            f"North Wind Drift\nhd = {hd_north:.1f} ft\nw = {effective_w:.1f} ft\npd = {pd_north:.0f} psf",
            ha="left",
            va="center",
            bbox=dict(facecolor="white", alpha=0.9, edgecolor="blue"),
        )

        # North arrow – at top center, separated from 'N' text (reduced size)
        arrow_x = total_width / 2
        arrow_y = total_height + 12
        ax.arrow(arrow_x, arrow_y, 0, 6, head_width=3, head_length=6, fc="k", ec="k")
        ax.text(
            arrow_x,
            arrow_y + 15,
            "N",
            fontsize=12,
            ha="center",
            fontweight="bold",
            va="bottom",
        )

        ax.set_xlim(-15, total_width + 60)  # Extended right for info box
        ax.set_ylim(
            -50, total_height + 30
        )  # Extended further downward for moved labels
        ax.set_axis_off()
        ax.set_title("North Wind Leeward Gable Drift (lu_north = north_span)")
        ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.0))

        return fig

    def _draw_drift_load_profile(self, hd: float, w: float, pd_max: float):
        """Draw the drift load profile diagram."""
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))

        if hd > 0 and w > 0 and pd_max > 0:
            # Create drift load profile (triangular distribution)
            x_positions = [0, w / 3, 2 * w / 3, w]
            load_values = [pd_max, pd_max, pd_max / 2, 0]

            ax.plot(x_positions, load_values, "b-", linewidth=3, label="Drift Load")
            ax.fill_between(x_positions, load_values, alpha=0.3, color="lightblue")

            # Add annotations
            ax.text(
                w / 2,
                pd_max / 2,
                f"pd_max = {pd_max:.0f} psf\nhd = {hd:.1f} ft\nw = {w:.1f} ft",
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
            )

            ax.set_xlim(0, w * 1.1)
            ax.set_ylim(0, pd_max * 1.2)

        else:
            # No drift case - show informative message
            ax.text(
                0.5,
                0.5,
                "No Drift Loads\nRoof slope outside unbalanced\nload applicability range\n(0.5/12 to 7/12)",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=12,
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8),
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)

        ax.set_xlabel("Distance from Ridge (ft)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Drift Load (psf)", fontsize=11, fontweight="bold")
        ax.set_title("Drift Load Profile", fontsize=13, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.6)

        if hd > 0 and w > 0 and pd_max > 0:
            ax.legend()

        return fig

    def _draw_snow_load_distribution(
        self,
        north_span: float,
        south_span: float,
        ps_balanced: float,
        drift_load: float,
        drift_width: float,
    ):
        """Draw the snow load distribution diagram."""
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))

        total_height = north_span + south_span

        # Balanced snow load zones (entire roof)
        ax.fill_between(
            [0, total_height],
            ps_balanced,
            ps_balanced,
            color="lightgray",
            alpha=0.5,
            label="Balanced Snow Load",
        )

        # Drift load zone (on south roof only if applicable)
        if drift_load > 0 and drift_width > 0:
            drift_start = south_span - min(drift_width, south_span)
            # Show drift load on south roof
            ax.fill_between(
                [drift_start, south_span],
                ps_balanced + drift_load,
                ps_balanced + drift_load,
                color="lightblue",
                alpha=0.7,
                hatch="///",
                label="Drift Load",
            )

            # Total load annotation
            total_load = ps_balanced + drift_load
            ax.text(
                (drift_start + south_span) / 2,
                ps_balanced + drift_load / 2,
                f"Total: {total_load:.1f} psf",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="navy",
            )

        # Annotations
        ax.text(
            total_height / 2,
            ps_balanced / 2,
            f"ps = {ps_balanced:.1f} psf",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

        if drift_load > 0:
            ax.text(
                south_span * 0.8,
                ps_balanced + drift_load + 5,
                f"Drift surcharge: {drift_load:.0f} psf",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color="blue",
            )
        else:
            ax.text(
                total_height / 2,
                ps_balanced + 10,
                "No drift loads (slope outside applicability range)",
                ha="center",
                va="bottom",
                fontsize=9,
                style="italic",
                color="gray",
            )

        ax.set_xlabel("Distance from South Eave (ft)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Snow Load (psf)", fontsize=11, fontweight="bold")
        ax.set_title("Snow Load Distribution", fontsize=13, fontweight="bold")
        ax.set_xlim(0, total_height)
        ax.set_ylim(0, max(ps_balanced * 1.5, ps_balanced + drift_load + 20))
        ax.grid(True, linestyle="--", alpha=0.6)

        # Add roof zone labels
        ax.axvline(x=south_span, color="red", linestyle="--", alpha=0.7, linewidth=1)
        ax.text(
            south_span / 2,
            ps_balanced + 15,
            "South Roof",
            ha="center",
            fontsize=9,
            color="red",
        )
        ax.text(
            (south_span + total_height) / 2,
            ps_balanced + 15,
            "North Roof",
            ha="center",
            fontsize=9,
            color="red",
        )

        ax.legend(loc="upper right")

        return fig

    def _embed_diagram(self, fig, title: str):
        """Embed a matplotlib figure in the diagrams tab."""
        try:
            canvas = FigureCanvasTkAgg(fig, master=self.diagrams_frame)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.pack(pady=10, fill=tk.BOTH, expand=True)
            self.diagram_widgets.append(widget)
        except Exception as e:
            # Create a simple label as fallback
            import tkinter as tk

            label = tk.Label(
                self.diagrams_frame,
                text=f"Diagram Error: {title}\n{str(e)}",
                bg="lightcoral",
                fg="red",
                font=("Arial", 10),
            )
            label.pack(pady=10)
            self.diagram_widgets.append(label)

    def _embed_error_diagram(self, error_msg: str):
        """Embed an error message diagram."""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(
            0.5,
            0.5,
            error_msg,
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=10,
            color="red",
            wrap=True,
        )
        ax.set_title("Diagram Error")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        self._embed_diagram(fig, "Error")

    def _update_report_tab(self, results: Dict):
        """Update the report tab with formatted report text."""
        self.report_text.delete(1.0, tk.END)

        # Generate formatted report
        report = self._generate_text_report(results)
        self.report_text.insert(tk.END, report)

    def _generate_text_report(self, results: Dict) -> str:
        """Generate a formatted text report."""
        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("VALLEY SNOW LOAD ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Project information
        inputs = results.get("inputs", {})
        report_lines.append(f"Project Name: {inputs.get('project_name', 'N/A')}")
        report_lines.append(f"Location: {inputs.get('location', 'N/A')}")
        report_lines.append(f"Analysis Date: {results.get('timestamp', 'N/A')}")
        report_lines.append("")

        # Input parameters
        report_lines.append("INPUT PARAMETERS:")
        report_lines.append("-" * 30)
        report_lines.append(f"Ground Snow Load (pg): {inputs.get('pg', 0):.1f} psf")
        report_lines.append(f"Winter Wind Parameter (W2): {inputs.get('w2', 0.3):.2f}")
        report_lines.append(f"Exposure Factor (Ce): {inputs.get('ce', 1.0):.2f}")
        report_lines.append(f"Thermal Factor (Ct): {inputs.get('ct', 1.0):.2f}")
        report_lines.append(f"Importance Factor (Is): {inputs.get('is', 1.0):.2f}")
        report_lines.append("")

        # Geometry
        report_lines.append("ROOF GEOMETRY:")
        report_lines.append("-" * 30)
        report_lines.append(f"North Span: {inputs.get('north_span', 0):.1f} ft")
        report_lines.append(f"South Span: {inputs.get('south_span', 0):.1f} ft")
        report_lines.append(f"E-W Half Width: {inputs.get('ew_half_width', 0):.1f} ft")
        report_lines.append(f"Valley Offset: {inputs.get('valley_offset', 0):.1f} ft")
        report_lines.append("")

        # Slope parameters
        slope_params = results.get("slope_parameters", {})
        report_lines.append("SLOPE ANALYSIS:")
        report_lines.append("-" * 30)
        report_lines.append(f"North Roof Pitch: {inputs.get('pitch_north', 0):.1f}/12")
        report_lines.append(f"North Slope Angle: {slope_params.get('theta_n', 0):.1f}°")
        report_lines.append(f"North S Parameter: {slope_params.get('S_n', 0):.2f}")
        report_lines.append("")
        report_lines.append(f"West Roof Pitch: {inputs.get('pitch_west', 0):.1f}/12")
        report_lines.append(f"West Slope Angle: {slope_params.get('theta_w', 0):.1f}°")
        report_lines.append(f"West S Parameter: {slope_params.get('S_w', 0):.2f}")
        report_lines.append("")

        # Snow load results
        snow_loads = results.get("snow_loads", {})
        report_lines.append("SNOW LOAD RESULTS:")
        report_lines.append("-" * 30)
        report_lines.append(
            f"Balanced Snow Load (ps): {snow_loads.get('ps_balanced', 0):.1f} psf"
        )
        report_lines.append("")

        # Drift analysis
        drifts = snow_loads.get("drift_loads", {})
        report_lines.append("DRIFT ANALYSIS:")
        report_lines.append("-" * 30)

        north_drift = drifts.get("north_drift", {})
        report_lines.append("North Roof Drift:")
        report_lines.append(f"  Height: {north_drift.get('hd_ft', 0):.2f} ft")
        report_lines.append(f"  Width: {north_drift.get('width_ft', 0):.1f} ft")
        report_lines.append(f"  Load: {north_drift.get('pd_max_psf', 0):.1f} psf")
        report_lines.append("")

        west_drift = drifts.get("west_drift", {})
        report_lines.append("West Roof Drift:")
        report_lines.append(f"  Height: {west_drift.get('hd_ft', 0):.2f} ft")
        report_lines.append(f"  Width: {west_drift.get('width_ft', 0):.1f} ft")
        report_lines.append(f"  Load: {west_drift.get('pd_max_psf', 0):.1f} psf")
        report_lines.append("")

        governing = drifts.get("governing_drift", {})
        report_lines.append("Governing Drift (Valley Load):")
        report_lines.append(f"  Height: {governing.get('hd_ft', 0):.2f} ft")
        report_lines.append(f"  Width: {governing.get('width_ft', 0):.1f} ft")
        report_lines.append(f"  Load: {governing.get('pd_max_psf', 0):.1f} psf")
        report_lines.append("")

        # Compliance statement
        report_lines.append("COMPLIANCE STATEMENT:")
        report_lines.append("-" * 30)
        report_lines.append("This analysis has been performed in accordance with")
        report_lines.append("ASCE 7-22 Minimum Design Loads and Associated Criteria")
        report_lines.append("Chapter 7 - Snow Loads")
        report_lines.append("")
        report_lines.append(
            "Section 7.6.1 - Unbalanced Snow Loads for Hip and Gable Roofs"
        )
        report_lines.append("Section 7.7 - Drifts on Lower Roofs")
        report_lines.append("")

        # Disclaimer
        report_lines.append("PROFESSIONAL DISCLAIMER:")
        report_lines.append("-" * 30)
        report_lines.append("This analysis is provided for engineering reference only.")
        report_lines.append(
            "Final design must be performed by a licensed professional engineer."
        )
        report_lines.append(
            "Verify all loading conditions and local code requirements."
        )
        report_lines.append("")

        return "\n".join(report_lines)

    def _generate_pdf_report(self):
        """Generate PDF report using the new PDF generator."""
        try:
            from ..reporting import PDFReportGenerator

            if not self.current_results:
                messagebox.showwarning("No Results", "Please run a calculation first.")
                return

            # Get filename from user
            from tkinter import filedialog
            import os

            try:
                default_dir = os.path.expanduser("~/Documents")
                if not os.path.exists(default_dir):
                    default_dir = os.path.expanduser("~/Desktop")
                if not os.path.exists(default_dir):
                    default_dir = os.path.expanduser("~")
            except:
                default_dir = ""

            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Generate PDF Report",
                initialdir=default_dir,
            )

            if not filename:
                return

            # Prepare diagram figures
            diagram_figures = []
            if hasattr(self, "_current_figures") and self._current_figures:
                diagram_figures = self._current_figures

            # Generate PDF
            generator = PDFReportGenerator()
            success = generator.generate_report(
                self.current_results, diagram_figures=diagram_figures, filename=filename
            )

            if success:
                messagebox.showinfo(
                    "Success", f"PDF report generated successfully:\n{filename}"
                )
            else:
                messagebox.showerror("Error", "Failed to generate PDF report.")

        except Exception as e:
            messagebox.showerror("Error", f"PDF generation failed: {str(e)}")

    def _generate_html_report(self):
        """Generate HTML report (placeholder)."""
        if not self.current_results:
            return

        # Placeholder for HTML generation
        print("HTML report generation would be implemented here")
        # Would integrate with reporting.html_generator

    def clear(self):
        """Clear all results displays."""
        self.summary_text.delete(1.0, tk.END)
        self.detailed_text.delete(1.0, tk.END)
        self.report_text.delete(1.0, tk.END)

        # Clear diagrams
        for widget in self.diagram_widgets:
            widget.destroy()
        self.diagram_widgets.clear()

        self.current_results = None
