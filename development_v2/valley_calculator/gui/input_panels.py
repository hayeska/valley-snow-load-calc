# input_panels.py - Input panels for Valley Calculator V2.0

import tkinter as tk
from tkinter import ttk
from typing import Dict
from .tooltips import add_tooltip


class InputPanel(ttk.Frame):
    """
    Input panel for snow load calculation parameters.

    Organized into logical sections:
    - Project information
    - Snow load parameters
    - Roof geometry
    - Material properties
    """

    def __init__(self, parent, defaults: Dict, tooltip_manager=None):
        """Initialize the input panel."""
        super().__init__(parent)
        self.defaults = defaults
        self.tooltip_manager = tooltip_manager

        # Create scrollable frame
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create input sections
        self._create_project_section()
        self._create_snow_load_section()
        self._create_geometry_section()
        self._create_material_section()

        # Bind mousewheel to canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _create_project_section(self):
        """Create project information section."""
        frame = ttk.LabelFrame(
            self.scrollable_frame, text="Project Information", padding=10
        )
        frame.pack(fill="x", padx=5, pady=5)

        # Project name
        name_label = ttk.Label(frame, text="Project Name:")
        name_label.grid(row=0, column=0, sticky="w", pady=2)
        self.project_name = tk.StringVar(value="New Valley Project")
        name_entry = ttk.Entry(frame, textvariable=self.project_name)
        name_entry.grid(row=0, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(name_label, "project_name")
            add_tooltip(name_entry, "project_name")

        # Location
        location_label = ttk.Label(frame, text="Location:")
        location_label.grid(row=1, column=0, sticky="w", pady=2)
        self.location = tk.StringVar(value="Site Location")
        location_entry = ttk.Entry(frame, textvariable=self.location)
        location_entry.grid(row=1, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(location_label, "location")
            add_tooltip(location_entry, "location")

        frame.columnconfigure(1, weight=1)

    def _create_snow_load_section(self):
        """Create snow load parameters section."""
        frame = ttk.LabelFrame(
            self.scrollable_frame, text="Snow Load Parameters", padding=10
        )
        frame.pack(fill="x", padx=5, pady=5)

        # Ground snow load
        pg_label = ttk.Label(frame, text="Ground Snow Load pg (psf):")
        pg_label.grid(row=0, column=0, sticky="w", pady=2)
        self.pg = tk.DoubleVar(value=self.defaults["ground_snow_load"])
        pg_entry = ttk.Entry(frame, textvariable=self.pg)
        pg_entry.grid(row=0, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(pg_label, "pg")
            add_tooltip(pg_entry, "pg")

        # Winter wind parameter
        w2_label = ttk.Label(frame, text="Winter Wind Parameter W2:")
        w2_label.grid(row=1, column=0, sticky="w", pady=2)
        self.w2 = tk.DoubleVar(value=self.defaults["winter_wind_parameter"])
        w2_entry = ttk.Entry(frame, textvariable=self.w2)
        w2_entry.grid(row=1, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(w2_label, "w2")
            add_tooltip(w2_entry, "w2")

        # Exposure factor
        ce_label = ttk.Label(frame, text="Exposure Factor Ce:")
        ce_label.grid(row=2, column=0, sticky="w", pady=2)
        self.ce = tk.DoubleVar(value=self.defaults["exposure_factor"])
        ce_entry = ttk.Entry(frame, textvariable=self.ce)
        ce_entry.grid(row=2, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(ce_label, "ce")
            add_tooltip(ce_entry, "ce")

        # Thermal factor
        ct_label = ttk.Label(frame, text="Thermal Factor Ct:")
        ct_label.grid(row=3, column=0, sticky="w", pady=2)
        self.ct = tk.DoubleVar(value=self.defaults["thermal_factor"])
        ct_entry = ttk.Entry(frame, textvariable=self.ct)
        ct_entry.grid(row=3, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(ct_label, "ct")
            add_tooltip(ct_entry, "ct")

        # Importance factor
        is_label = ttk.Label(frame, text="Importance Factor Is:")
        is_label.grid(row=4, column=0, sticky="w", pady=2)
        self.is_factor = tk.DoubleVar(value=self.defaults["importance_factor"])
        is_entry = ttk.Entry(frame, textvariable=self.is_factor)
        is_entry.grid(row=4, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(is_label, "is_factor")
            add_tooltip(is_entry, "is_factor")

        frame.columnconfigure(1, weight=1)

    def _create_geometry_section(self):
        """Create roof geometry section."""
        frame = ttk.LabelFrame(self.scrollable_frame, text="Roof Geometry", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        # North span
        north_span_label = ttk.Label(frame, text="North Span (ft):")
        north_span_label.grid(row=0, column=0, sticky="w", pady=2)
        self.north_span = tk.DoubleVar(value=self.defaults["north_span"])
        north_span_entry = ttk.Entry(frame, textvariable=self.north_span)
        north_span_entry.grid(row=0, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(north_span_label, "north_span")
            add_tooltip(north_span_entry, "north_span")

        # South span
        south_span_label = ttk.Label(frame, text="South Span (ft):")
        south_span_label.grid(row=1, column=0, sticky="w", pady=2)
        self.south_span = tk.DoubleVar(value=self.defaults["south_span"])
        south_span_entry = ttk.Entry(frame, textvariable=self.south_span)
        south_span_entry.grid(row=1, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(south_span_label, "south_span")
            add_tooltip(south_span_entry, "south_span")

        # E-W half width
        ew_label = ttk.Label(frame, text="E-W Half Width (ft):")
        ew_label.grid(row=2, column=0, sticky="w", pady=2)
        self.ew_half_width = tk.DoubleVar(value=self.defaults["ew_half_width"])
        ew_entry = ttk.Entry(frame, textvariable=self.ew_half_width)
        ew_entry.grid(row=2, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(ew_label, "ew_half_width")
            add_tooltip(ew_entry, "ew_half_width")

        # Valley offset
        valley_label = ttk.Label(frame, text="Valley Offset (ft):")
        valley_label.grid(row=3, column=0, sticky="w", pady=2)
        self.valley_offset = tk.DoubleVar(value=self.defaults["valley_offset"])
        valley_entry = ttk.Entry(frame, textvariable=self.valley_offset)
        valley_entry.grid(row=3, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(valley_label, "valley_offset")
            add_tooltip(valley_entry, "valley_offset")

        # North pitch
        pitch_n_label = ttk.Label(frame, text="North Roof Pitch (rise/12):")
        pitch_n_label.grid(row=4, column=0, sticky="w", pady=2)
        self.pitch_north = tk.DoubleVar(value=self.defaults["roof_pitch_north"])
        pitch_n_entry = ttk.Entry(frame, textvariable=self.pitch_north)
        pitch_n_entry.grid(row=4, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(pitch_n_label, "pitch_north")
            add_tooltip(pitch_n_entry, "pitch_north")

        # West pitch
        pitch_w_label = ttk.Label(frame, text="West Roof Pitch (rise/12):")
        pitch_w_label.grid(row=5, column=0, sticky="w", pady=2)
        self.pitch_west = tk.DoubleVar(value=self.defaults["roof_pitch_west"])
        pitch_w_entry = ttk.Entry(frame, textvariable=self.pitch_west)
        pitch_w_entry.grid(row=5, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(pitch_w_label, "pitch_west")
            add_tooltip(pitch_w_entry, "pitch_west")

        frame.columnconfigure(1, weight=1)

    def _create_material_section(self):
        """Create material properties section."""
        frame = ttk.LabelFrame(
            self.scrollable_frame, text="Material Properties", padding=10
        )
        frame.pack(fill="x", padx=5, pady=5)

        # Dead load
        dl_label = ttk.Label(frame, text="Dead Load (psf):")
        dl_label.grid(row=0, column=0, sticky="w", pady=2)
        self.dead_load = tk.DoubleVar(value=self.defaults["dead_load"])
        dl_entry = ttk.Entry(frame, textvariable=self.dead_load)
        dl_entry.grid(row=0, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(dl_label, "dead_load")
            add_tooltip(dl_entry, "dead_load")

        # Beam width
        width_label = ttk.Label(frame, text="Beam Width (in):")
        width_label.grid(row=1, column=0, sticky="w", pady=2)
        self.beam_width = tk.DoubleVar(value=self.defaults["beam_width"])
        width_entry = ttk.Entry(frame, textvariable=self.beam_width)
        width_entry.grid(row=1, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(width_label, "beam_width")
            add_tooltip(width_entry, "beam_width")

        # Beam depth
        depth_label = ttk.Label(frame, text="Beam Depth (in):")
        depth_label.grid(row=2, column=0, sticky="w", pady=2)
        self.beam_depth = tk.DoubleVar(value=self.defaults["beam_depth"])
        depth_entry = ttk.Entry(frame, textvariable=self.beam_depth)
        depth_entry.grid(row=2, column=1, sticky="ew", pady=2)
        if self.tooltip_manager:
            add_tooltip(depth_label, "beam_depth")
            add_tooltip(depth_entry, "beam_depth")

        frame.columnconfigure(1, weight=1)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def get_project_name(self) -> str:
        """Get the project name."""
        return self.project_name.get()

    def get_values(self) -> Dict:
        """Get all input values as a dictionary."""
        return {
            "project_name": self.project_name.get(),
            "location": self.location.get(),
            "pg": self.pg.get(),
            "w2": self.w2.get(),
            "ce": self.ce.get(),
            "ct": self.ct.get(),
            "is": self.is_factor.get(),
            "north_span": self.north_span.get(),
            "south_span": self.south_span.get(),
            "ew_half_width": self.ew_half_width.get(),
            "valley_offset": self.valley_offset.get(),
            "pitch_north": self.pitch_north.get(),
            "pitch_west": self.pitch_west.get(),
            "dead_load": self.dead_load.get(),
            "beam_width": self.beam_width.get(),
            "beam_depth": self.beam_depth.get(),
        }

    def set_values(self, values: Dict):
        """Set input values from a dictionary."""
        self.project_name.set(
            values.get("project_name", self.defaults.get("project_name", "New Project"))
        )
        self.location.set(values.get("location", "Site Location"))
        self.pg.set(values.get("pg", self.defaults["ground_snow_load"]))
        self.w2.set(values.get("w2", self.defaults["winter_wind_parameter"]))
        self.ce.set(values.get("ce", self.defaults["exposure_factor"]))
        self.ct.set(values.get("ct", self.defaults["thermal_factor"]))
        self.is_factor.set(values.get("is", self.defaults["importance_factor"]))
        self.north_span.set(values.get("north_span", self.defaults["north_span"]))
        self.south_span.set(values.get("south_span", self.defaults["south_span"]))
        self.ew_half_width.set(
            values.get("ew_half_width", self.defaults["ew_half_width"])
        )
        self.valley_offset.set(
            values.get("valley_offset", self.defaults["valley_offset"])
        )
        self.pitch_north.set(
            values.get("pitch_north", self.defaults["roof_pitch_north"])
        )
        self.pitch_west.set(values.get("pitch_west", self.defaults["roof_pitch_west"]))
        self.dead_load.set(values.get("dead_load", self.defaults["dead_load"]))
        self.beam_width.set(values.get("beam_width", self.defaults["beam_width"]))
        self.beam_depth.set(values.get("beam_depth", self.defaults["beam_depth"]))
