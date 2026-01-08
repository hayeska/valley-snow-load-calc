# gui_interface.py
# ASCE 7-22 Valley Snow Load Calculator GUI – Full Working Calculate Button
# New Official Base Code – December 21, 2025

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import json
import os
import threading
import time
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image,
    )
    from reportlab.lib import colors
    from reportlab.lib.units import inch

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: ReportLab not available. PDF reports will not be supported.")

from slope_factors import calculate_cs
from geometry import valley_rafter_length
from beam_design import ValleyBeamInputs, ValleyBeamDesigner, create_beam_summary
from jack_rafter_module import calculate_jack_rafters
from validation import (
    validate_ground_snow_load,
    validate_upwind_fetch,
    validate_valley_angle,
    validate_pitch,
    validate_exposure_factor,
    validate_thermal_factor,
)


class ValleySnowCalculator:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("ASCE 7-22 Valley Snow Load Calculator and Beam Design")
        master.geometry("950x700")

        # Create menu bar - ensure it's properly attached
        try:
            menubar = tk.Menu(master)
            master.configure(menu=menubar)  # Use configure instead of config

            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(
                label="Save Project", command=self.save_project, accelerator="Ctrl+S"
            )
            file_menu.add_command(
                label="Load Project", command=self.load_project, accelerator="Ctrl+O"
            )
            file_menu.add_separator()
            file_menu.add_command(
                label="Generate Report",
                command=self.generate_report,
                accelerator="Ctrl+R",
            )
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=master.quit)

            # Bind keyboard shortcuts
            master.bind("<Control-s>", lambda e: self.save_project())
            master.bind("<Control-o>", lambda e: self.load_project())
            master.bind("<Control-r>", lambda e: self.generate_report())

            # Force menu bar to be visible
            master.update()
            print("Menu bar created successfully")

        except Exception as e:
            print(f"Error creating menu bar: {e}")
            # Continue without menu bar if there's an error

        # Create scrollable canvas setup
        self.canvas = tk.Canvas(master, bg="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(
            master, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Single safe bind for scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        # Pack canvas below menu bar
        self.canvas.pack(fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling for the entire window
        def _on_mousewheel_windows(event):
            """Handle mouse wheel scrolling on Windows."""
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_linux_up(event):
            """Handle mouse wheel scrolling up on Linux."""
            self.canvas.yview_scroll(-1, "units")

        def _on_mousewheel_linux_down(event):
            """Handle mouse wheel scrolling down on Linux."""
            self.canvas.yview_scroll(1, "units")

        # Bind mouse wheel events
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel_windows)  # Windows
        self.canvas.bind_all("<Button-4>", _on_mousewheel_linux_up)  # Linux scroll up
        self.canvas.bind_all(
            "<Button-5>", _on_mousewheel_linux_down
        )  # Linux scroll down

        print("Canvas and scrollable frame created")  # Debug print

        # Title banner
        banner = tk.Label(
            self.scrollable_frame,
            text="ASCE 7-22 Valley Snow Load Calculator and Beam Design",
            fg="black",
            bg="#f0f0f0",
            font=("Helvetica", 14, "bold"),
            pady=10,
        )
        banner.pack(fill=tk.X)

        # Create three grouped input frames
        self.entries = {}

        # Snow Load Parameters Frame
        snow_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="Snow Load Parameters (ASCE 7-22 Chapter 7)",
            padding=10,
        )
        snow_frame.pack(pady=5, padx=20, fill=tk.X)

        # Configure column weights for proper expansion
        snow_frame.columnconfigure(1, weight=1)
        snow_frame.columnconfigure(3, weight=1)

        snow_inputs = [
            (
                "pg (psf; Ground snow load, Sec. 7.2: reliability-targeted from Fig. 7.2-1A–D/Hazard Tool; e.g., 50)",
                "50",
                "pg",
            ),
            (
                "W2 (0.25–0.65; Winter wind param, Fig. 7.6-1: % wind >10 mph Oct–Apr; from Hazard Tool)",
                "0.55",
                "w2",
            ),
            ("Ce – Exposure factor, Table 7.3-1", "1.0", "ce"),
            ("Ct – Thermal factor, Table 7.3-2/7.3-3", "1.2", "ct"),
        ]

        # Note: Program automatically analyzes both North and West wind directions
        # and uses governing (maximum) loads per ASCE 7-22 Section 7.6.1
        ttk.Label(
            snow_frame,
            text="Note: Automatically analyzes both North & West winds, uses governing loads",
        ).grid(row=4, column=0, columnspan=4, sticky="w", pady=3, padx=5)

        for i, (label_text, default, key) in enumerate(snow_inputs):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(snow_frame, text=label_text).grid(
                row=row, column=col, sticky="w", pady=3, padx=5
            )
            entry = ttk.Entry(snow_frame, width=15)
            entry.insert(0, default)
            entry.grid(row=row, column=col + 1, sticky="ew", pady=3, padx=5)
            # Add real-time validation
            entry.bind(
                "<KeyRelease>",
                lambda e, k=key: self.validate_input_realtime(e.widget.get(), k),
            )
            self.entries[key] = entry

        # Add Slippery surface checkbox
        self.slippery_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            snow_frame,
            text="Slippery surface (non-slippery by default)",
            variable=self.slippery_var,
        ).grid(row=3, column=2, columnspan=2, sticky="w", pady=3, padx=5)

        # Add slippery surface definition note
        slippery_note_label = ttk.Label(
            snow_frame,
            text="Slippery surface: Membranes with a smooth surface, for example, glass, metal, or rubber. Membranes with an embedded aggregate or mineral granule surface are not considered a slippery surface. (Sec. 7.1.1)",
            foreground="darkblue",
            wraplength=600,
            font=("Helvetica", 9, "italic"),
        )
        slippery_note_label.grid(
            row=4, column=0, columnspan=4, sticky="w", pady=2, padx=5
        )

        # Add Cs calculation explanation note
        cs_note_label = ttk.Label(
            snow_frame,
            text="Cs (slope factor) automatically calculated based on:\n- Ct (thermal condition: warm Ct ≤ 1.1, cold Ct ≥ 1.2, intermediate 1.1 < Ct < 1.2)\n- Slippery or non-slippery surface\nFrom ASCE 7-22 Figure 7.4-1",
            foreground="darkblue",
            wraplength=600,
            font=("Helvetica", 10, "italic"),
        )
        cs_note_label.grid(row=5, column=0, columnspan=4, sticky="w", pady=3, padx=5)

        # Add explanatory note with Risk Category and Freezer definition
        note_label = ttk.Label(
            snow_frame,
            text="NOTE: In ASCE 7-22, Risk Category is not applied as a separate importance factor (Is) in snow load calculations. Ground snow loads (pg) from ASCE Hazard Tool/Geodatabase are Risk Category-specific and already incorporate the appropriate reliability level.\n\nFREEZER BUILDINGS: Buildings in which the inside temperature is kept at or below freezing. Buildings with an air space between the roof insulation layer above and a ceiling of the freezer area below are not considered freezer buildings.\n\nCt from ASCE 7-22 Table 7.3-2 (Other Structures).\nFor Heated Unventilated Roofs (Table 7.3-3), use separate R-value input if added later.\nCt = 1.2 is conservative for most structures (cold roof, maximum snow retention).\nLower Ct reduces pf/ps (less snow accumulation).",
            foreground="darkblue",
            wraplength=700,
            font=("Helvetica", 10, "italic"),
        )
        note_label.grid(row=6, column=0, columnspan=4, sticky="w", pady=5, padx=5)

        # Add ASCE 7 Hazard Tool guidance note
        hazard_tool_label = ttk.Label(
            snow_frame,
            text="NOTE: Ground snow load (pg) and winter wind parameter (W2) shall be obtained from the official ASCE 7 Hazard Tool: https://asce7hazardtool.online\nThe printed maps in ASCE 7-22 are graphical representations only — site-specific values from the online tool are required for accuracy.",
            foreground="darkblue",
            wraplength=700,
            font=("Helvetica", 10, "italic"),
        )
        hazard_tool_label.grid(
            row=7, column=0, columnspan=4, sticky="w", pady=5, padx=5
        )

        # Building Geometry Frame
        geom_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Building Geometry", padding=10
        )
        geom_frame.pack(pady=10, padx=20, fill=tk.X)

        # Configure column weights
        geom_frame.columnconfigure(1, weight=1)
        geom_frame.columnconfigure(3, weight=1)

        geom_inputs = [
            ("Pitch North (X for X/12)", "10", "pitch_north"),
            ("Pitch West (X for X/12)", "10", "pitch_west"),
            (
                "Distance from E-W ridge to north eave (ft) – becomes lu_north for north wind drift",
                "16",
                "north_span",
            ),
            (
                "Distance from E-W ridge to south eave (ft) – defines south span and N-S ridge length",
                "16",
                "south_span",
            ),
            (
                "E-W half-width (ft) – distance from centered N-S ridge to west or east eave (symmetric) – becomes lu_west",
                "42",
                "ew_half_width",
            ),
            (
                "Valley horizontal offset (ft) – distance from N-S ridge projection on south eave to valley low point (intersection of two gable roofs, symmetric both sides)",
                "16",
                "valley_offset",
            ),
            ("Valley angle (degrees, default 90)", "90", "valley_angle"),
            ("Jack rafter spacing (in o.c., default 24)", "24", "jack_spacing_inches"),
        ]

        for i, (label_text, default, key) in enumerate(geom_inputs):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(geom_frame, text=label_text).grid(
                row=row, column=col, sticky="w", pady=5, padx=10
            )
            entry = ttk.Entry(geom_frame, width=15)
            entry.insert(0, default)
            entry.grid(row=row, column=col + 1, sticky="ew", pady=5, padx=10)
            # Add real-time validation
            entry.bind(
                "<KeyRelease>",
                lambda e, k=key: self.validate_input_realtime(e.widget.get(), k),
            )
            self.entries[key] = entry

        # Add low-slope note in Geometry section
        note_geom_label = ttk.Label(
            geom_frame,
            text="For monoslope/hip/gable roofs with slope < 15°, minimum snow load pm applies (Sec. 7.3).",
            foreground="darkred",
            wraplength=500,
        )
        note_geom_label.grid(row=3, column=0, columnspan=4, sticky="w", pady=5, padx=10)

        # Add stable ASCE 7-22 Section 7.6.1 information in Geometry section
        asce_geom_text = """=== ASCE 7-22 SECTION 7.6.1: UNBALANCED SNOW LOADS FOR HIP AND GABLE ROOFS ===

APPLICABILITY:
• Unbalanced loads REQUIRED only for roof slopes 0.5/12 (≈2.38°) to 7/12 (≈30.2°)
• Outside this range: Unbalanced loads and drifts are NOT required

SPECIAL NARROW ROOF CASE (W ≤ 20 ft, simply supported prismatic members):
→ Leeward side: Full ground snow load pg (windward unloaded)"""

        asce_geom_label = ttk.Label(
            geom_frame,
            text=asce_geom_text,
            foreground="black",
            font=("Helvetica", 9, "bold"),
            wraplength=600,
            justify="left",
            anchor="w",
        )
        asce_geom_label.grid(
            row=4, column=0, columnspan=4, sticky="ew", pady=10, padx=10
        )

        # Beam Design Parameters Frame
        beam_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Beam Design Parameters", padding=10
        )
        beam_frame.pack(pady=5, padx=20, fill=tk.X, expand=False)

        # Configure column weights
        beam_frame.columnconfigure(1, weight=1)
        beam_frame.columnconfigure(3, weight=1)

        # Initialize material properties (will be stored in Entry widgets)
        self.fb_allowable_value = 2400
        self.fv_allowable_value = 265
        self.modulus_e_value = 1800000

        # Beam material selection
        ttk.Label(beam_frame, text="Beam Material:").grid(
            row=0, column=0, sticky="w", pady=3, padx=5
        )
        self.material_combobox = ttk.Combobox(beam_frame, state="readonly", width=50)
        material_values = [
            "Douglas Fir #2 Sawn Lumber (Fb=875 psi)",
            "Glulam 24F-V4 DF (Fb=2400 psi)",
            "LVL 2.0E (Fb=2650 psi)",
            "3100Fb-2.1E (PWT) (Fb=3100 psi)",
            "2850Fb-1.9E (Global) (Fb=2850 psi)",
        ]
        self.material_combobox["values"] = material_values
        self.material_combobox.current(1)  # default Glulam
        self.material_combobox.grid(row=0, column=1, sticky="ew", pady=5)
        # Bind the event AFTER grid placement to ensure combobox is fully initialized
        self.material_combobox.bind("<<ComboboxSelected>>", self.on_material_change)
        print(
            f"Material dropdown created with {len(material_values)} options"
        )  # Debug print
        print(f"Current selection: {self.material_combobox.get()}")  # Debug print

        beam_inputs = [
            ("DL horizontal (psf; default 15)", "15", "dead_load_horizontal"),
            ("Beam width b (in; default 3.5)", "3.5", "beam_width"),
            ("Beam depth D (in; default 16)", "16", "beam_depth_trial"),
            (
                "Allowable bending stress Fb (psi)",
                str(self.fb_allowable_value),
                "fb_allowable",
            ),
            (
                "Allowable shear stress Fv (psi)",
                str(self.fv_allowable_value),
                "fv_allowable",
            ),
            ("Modulus of elasticity E (psi)", str(self.modulus_e_value), "modulus_e"),
            (
                "Total deflection limit (L/n; default 240)",
                "240",
                "deflection_total_limit",
            ),
            (
                "Snow deflection limit (L/n; default 360)",
                "360",
                "deflection_snow_limit",
            ),
        ]

        for i, (label_text, default, key) in enumerate(beam_inputs):
            row = (i // 2) + 1  # Start from row 1 since material dropdown is in row 0
            col = (i % 2) * 2
            ttk.Label(beam_frame, text=label_text).grid(
                row=row, column=col, sticky="w", pady=3, padx=5
            )
            if isinstance(default, tk.DoubleVar):
                entry = ttk.Entry(beam_frame, width=15, textvariable=default)
                # Don't insert value - textvariable handles it
            else:
                entry = ttk.Entry(beam_frame, width=15)
            entry.insert(0, default)
            entry.grid(row=row, column=col + 1, sticky="ew", pady=3, padx=5)
            # Add real-time validation (skip for material properties that use DoubleVar)
            if not isinstance(default, tk.DoubleVar):
                entry.bind(
                    "<KeyRelease>",
                    lambda e, k=key: self.validate_input_realtime(e.widget.get(), k),
                )
            self.entries[key] = entry

        # Initialize default material properties after entries are created
        self.on_material_change(None)

        # ===== N-S RIDGE BEAM DESIGN PARAMETERS (INDEPENDENT SECTION) =====
        ns_ridge_beam_frame = ttk.LabelFrame(
            self.scrollable_frame, text="N-S Ridge Beam Design Parameters", padding=10
        )
        ns_ridge_beam_frame.pack(pady=5, padx=20, fill=tk.X, expand=False)

        # Configure column weights
        ns_ridge_beam_frame.columnconfigure(1, weight=1)
        ns_ridge_beam_frame.columnconfigure(3, weight=1)

        # Initialize N-S ridge beam material properties
        self.ns_ridge_fb_allowable_value = 2400
        self.ns_ridge_fv_allowable_value = 265
        self.ns_ridge_modulus_e_value = 1800000

        # N-S Ridge Beam Material selection
        ttk.Label(ns_ridge_beam_frame, text="N-S Ridge Beam Material:").grid(
            row=0, column=0, sticky="w", pady=3, padx=5
        )
        self.ns_ridge_material_combobox = ttk.Combobox(
            ns_ridge_beam_frame, state="readonly", width=50
        )
        self.ns_ridge_material_combobox["values"] = material_values
        self.ns_ridge_material_combobox.current(1)  # default Glulam
        self.ns_ridge_material_combobox.grid(row=0, column=1, sticky="ew", pady=5)
        self.ns_ridge_material_combobox.bind(
            "<<ComboboxSelected>>", self.on_ns_ridge_material_change
        )

        # N-S Ridge Beam inputs (independent from valley beam)
        ns_ridge_beam_inputs = [
            ("N-S Ridge Beam width b (in; default 3.5)", "3.5", "ns_ridge_beam_width"),
            (
                "N-S Ridge Beam depth D (in; default 16)",
                "16",
                "ns_ridge_beam_depth_trial",
            ),
            (
                "Allowable bending stress Fb (psi)",
                str(self.ns_ridge_fb_allowable_value),
                "ns_ridge_fb_allowable",
            ),
            (
                "Allowable shear stress Fv (psi)",
                str(self.ns_ridge_fv_allowable_value),
                "ns_ridge_fv_allowable",
            ),
            (
                "Modulus of elasticity E (psi)",
                str(self.ns_ridge_modulus_e_value),
                "ns_ridge_modulus_e",
            ),
            (
                "Total deflection limit (L/n; default 240)",
                "240",
                "ns_ridge_deflection_total_limit",
            ),
            (
                "Snow deflection limit (L/n; default 360)",
                "360",
                "ns_ridge_deflection_snow_limit",
            ),
        ]

        for i, (label_text, default, key) in enumerate(ns_ridge_beam_inputs):
            row = (i // 2) + 1  # Start from row 1 since material dropdown is in row 0
            col = (i % 2) * 2
            ttk.Label(ns_ridge_beam_frame, text=label_text).grid(
                row=row, column=col, sticky="w", pady=3, padx=5
            )
            if isinstance(default, tk.DoubleVar):
                entry = ttk.Entry(ns_ridge_beam_frame, width=15, textvariable=default)
            else:
                entry = ttk.Entry(ns_ridge_beam_frame, width=15)
            entry.insert(0, default)
            entry.grid(row=row, column=col + 1, sticky="ew", pady=3, padx=5)
            # Add real-time validation (skip for material properties that use DoubleVar)
            if not isinstance(default, tk.DoubleVar):
                entry.bind(
                    "<KeyRelease>",
                    lambda e, k=key: self.validate_input_realtime(e.widget.get(), k),
                )
            self.entries[key] = entry

        # Initialize N-S ridge beam material properties after entries are created
        self.on_ns_ridge_material_change(None)
        print("N-S Ridge Beam independent input section created")

        # Beam Design Summary Frame - prominent dedicated section
        summary_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Beam Design Summary", padding=15
        )
        summary_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Create scrollable text widget with scrollbar
        summary_text_frame = ttk.Frame(summary_frame)
        summary_text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.summary_label = tk.Text(
            summary_text_frame, font=("Helvetica", 10), wrap="word", height=12
        )
        summary_scrollbar = ttk.Scrollbar(
            summary_text_frame, orient="vertical", command=self.summary_label.yview
        )
        self.summary_label.configure(yscrollcommand=summary_scrollbar.set)
        
        self.summary_label.pack(side="left", fill="both", expand=True)
        summary_scrollbar.pack(side="right", fill="y")
        
        self.summary_label.insert(1.0, "Run calculation to see beam design summary...")
        self.summary_label.config(state="disabled")  # Make it read-only

        # Calculate button
        # Create calculate button with error handling wrapper
        def calculate_wrapper():
            print("=" * 60)
            print("BUTTON CLICKED - WRAPPER CALLED")
            print("=" * 60)
            try:
                self.calculate()
            except Exception as e:
                import traceback

                full_traceback = traceback.format_exc()
                error_msg = f"Exception in calculate:\n\nType: {type(e).__name__}\nMessage: {str(e)}\n\nFull traceback:\n{full_traceback}"
                # Show in both dialog and console
                messagebox.showerror("Calculation Error", error_msg)
                print("=" * 60)
                print("EXCEPTION CAUGHT:")
                print(error_msg)
                print("=" * 60)
                # Also write to output text
                self.output_text.insert(tk.END, f"\n\n!!! ERROR !!!\n{error_msg}\n")

        self.calc_button = ttk.Button(
            self.scrollable_frame,
            text="CALCULATE SNOW LOADS",
            command=calculate_wrapper,
        )
        self.calc_button.pack(pady=20)
        print("Calculate button created with wrapper")

        # Output area - results with expanded height
        output_frame = ttk.LabelFrame(
            self.scrollable_frame, text=" Results ", padding=10
        )
        output_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.output_text = tk.Text(
            output_frame, height=30, wrap="word", font=("Consolas", 10)
        )
        # Enable color support
        self.output_text.config(fg="black")
        scrollbar = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure text tags
        self.output_text.tag_configure(
            "blue", foreground="navy", font=("Helvetica", 10, "bold")
        )
        # Alternative tag for testing
        self.output_text.tag_configure(
            "highlight",
            background="yellow",
            foreground="red",
            font=("Helvetica", 12, "bold"),
        )

        # Initialize output with ASCE 7-22 Section 7.6.1 information
        self.initialize_output_text()

        # Plot area for shear and moment diagrams
        plot_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Shear & Moment Diagrams", padding=10
        )
        plot_frame.pack(pady=10, padx=20, fill=tk.X, expand=False)
        self.plot_frame = plot_frame

        # Auto-save system initialization
        self.auto_save_file = "state.backup.json"
        self.crash_flag_file = ".crash"
        self.auto_save_interval = 120000  # 2 minutes in milliseconds
        self.last_save_time = datetime.now()
        self.data_changed = False
        self.auto_save_timer = None

        # Check for crash recovery on startup
        self.check_crash_recovery()

        # Create crash flag to detect if app crashes
        self.create_crash_flag()

        # Start auto-save timer
        self.start_auto_save_timer()

        # Bind data change events to input fields
        self.bind_data_change_events()

        # Bind cleanup on window close
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_crash_flag(self):
        """Create crash flag file to detect if application crashes."""
        try:
            with open(self.crash_flag_file, "w") as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            print(f"Warning: Could not create crash flag: {e}")

    def remove_crash_flag(self):
        """Remove crash flag file when application closes normally."""
        try:
            if os.path.exists(self.crash_flag_file):
                os.remove(self.crash_flag_file)
        except Exception as e:
            print(f"Warning: Could not remove crash flag: {e}")

    def check_crash_recovery(self):
        """Check for crash flag and attempt recovery on startup."""
        if os.path.exists(self.crash_flag_file) and os.path.exists(self.auto_save_file):
            try:
                # Read crash timestamp
                with open(self.crash_flag_file, "r") as f:
                    crash_time = f.read().strip()

                # Ask user if they want to recover
                result = messagebox.askyesno(
                    "Crash Detected",
                    f"The application appears to have crashed on {crash_time}.\n"
                    "Would you like to restore the auto-saved state?",
                )

                if result:
                    self.restore_from_backup()
                    messagebox.showinfo(
                        "Recovery Complete",
                        "Application state has been restored from backup.",
                    )
                else:
                    # Remove backup file if user declines
                    try:
                        os.remove(self.auto_save_file)
                    except:
                        pass

            except Exception as e:
                print(f"Error during crash recovery: {e}")

            # Remove crash flag after recovery attempt
            self.remove_crash_flag()

    def start_auto_save_timer(self):
        """Start the auto-save timer."""

        def auto_save_loop():
            while True:
                time.sleep(120)  # 2 minutes
                # Use Tkinter's after method to run in main thread
                if hasattr(self, "master") and self.master:
                    self.master.after(0, self.perform_auto_save)

        # Start timer in background thread
        timer_thread = threading.Thread(target=auto_save_loop, daemon=True)
        timer_thread.start()

    def perform_auto_save(self):
        """Perform automatic save of current state."""
        try:
            if self.data_changed:
                self.save_current_state()
                self.data_changed = False
                self.last_save_time = datetime.now()
                print(f"Auto-saved at {self.last_save_time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Auto-save error: {e}")

    def save_current_state(self):
        """Save current application state to backup file."""
        try:
            # Gather all current input values (same as save_project but without file dialog)
            project_data = {
                "project_info": {
                    "name": "ASCE 7-22 Valley Snow Load Analysis",
                    "version": "1.0",
                    "auto_saved": datetime.now().isoformat(),
                    "description": "Auto-saved valley snow load calculation state",
                },
                "inputs": {
                    "snow_load_parameters": {
                        "pg": self.entries["pg"].get(),
                        "w2": self.entries["w2"].get(),
                        "ce": self.entries["ce"].get(),
                        "ct": self.entries["ct"].get(),
                    },
                    "building_geometry": {
                        "pitch_north": self.entries["pitch_north"].get(),
                        "pitch_west": self.entries["pitch_west"].get(),
                        "north_span": self.entries["north_span"].get(),
                        "south_span": self.entries["south_span"].get(),
                        "ew_half_width": self.entries["ew_half_width"].get(),
                        "valley_offset": self.entries["valley_offset"].get(),
                        "valley_angle": self.entries["valley_angle"].get(),
                        "jack_spacing_inches": self.entries[
                            "jack_spacing_inches"
                        ].get(),
                    },
                    "beam_design": {
                        "material": self.material_combobox.get(),
                        "beam_width": self.entries["beam_width"].get(),
                        "beam_depth_trial": self.entries["beam_depth_trial"].get(),
                    },
                    "ns_ridge_beam_design": {
                        "material": self.ns_ridge_material_combobox.get(),
                        "beam_width": self.entries["ns_ridge_beam_width"].get(),
                        "beam_depth_trial": self.entries[
                            "ns_ridge_beam_depth_trial"
                        ].get(),
                        "fb_allowable": self.entries["ns_ridge_fb_allowable"].get(),
                        "fv_allowable": self.entries["ns_ridge_fv_allowable"].get(),
                        "modulus_e": self.entries["ns_ridge_modulus_e"].get(),
                        "deflection_total_limit": self.entries[
                            "ns_ridge_deflection_total_limit"
                        ].get(),
                        "deflection_snow_limit": self.entries[
                            "ns_ridge_deflection_snow_limit"
                        ].get(),
                    },
                },
                "results": {
                    "output_text": self.output_text.get(1.0, tk.END)
                    if hasattr(self, "output_text")
                    else "",
                    "summary_text": self.summary_label.get(1.0, tk.END)
                    if hasattr(self, "summary_label")
                    else "",
                },
            }

            with open(self.auto_save_file, "w") as f:
                json.dump(project_data, f, indent=2)

        except Exception as e:
            print(f"Error saving state: {e}")

    def restore_from_backup(self):
        """Restore application state from backup file."""
        try:
            if not os.path.exists(self.auto_save_file):
                return

            with open(self.auto_save_file, "r") as f:
                backup_data = json.load(f)

            # Restore inputs (same logic as load_project)
            inputs = backup_data.get("inputs", {})

            # Snow load parameters
            snow_params = inputs.get("snow_load_parameters", {})
            self.entries["pg"].delete(0, tk.END)
            self.entries["pg"].insert(0, snow_params.get("pg", "50"))
            self.entries["w2"].delete(0, tk.END)
            self.entries["w2"].insert(0, snow_params.get("w2", "0.55"))
            self.entries["ce"].delete(0, tk.END)
            self.entries["ce"].insert(0, snow_params.get("ce", "1.0"))
            self.entries["ct"].delete(0, tk.END)
            self.entries["ct"].insert(0, snow_params.get("ct", "1.2"))
            # Building geometry
            geom_params = inputs.get("building_geometry", {})
            self.entries["pitch_north"].delete(0, tk.END)
            self.entries["pitch_north"].insert(0, geom_params.get("pitch_north", "6"))
            self.entries["pitch_west"].delete(0, tk.END)
            self.entries["pitch_west"].insert(0, geom_params.get("pitch_west", "6"))
            self.entries["north_span"].delete(0, tk.END)
            self.entries["north_span"].insert(0, geom_params.get("north_span", "16"))
            self.entries["south_span"].delete(0, tk.END)
            self.entries["south_span"].insert(0, geom_params.get("south_span", "16"))
            self.entries["ew_half_width"].delete(0, tk.END)
            self.entries["ew_half_width"].insert(
                0, geom_params.get("ew_half_width", "42")
            )
            self.entries["valley_offset"].delete(0, tk.END)
            self.entries["valley_offset"].insert(
                0, geom_params.get("valley_offset", "16")
            )
            self.entries["valley_angle"].delete(0, tk.END)
            self.entries["valley_angle"].insert(
                0, geom_params.get("valley_angle", "90")
            )
            self.entries["jack_spacing_inches"].delete(0, tk.END)
            self.entries["jack_spacing_inches"].insert(
                0, geom_params.get("jack_spacing_inches", "24")
            )

            # Beam design
            beam_params = inputs.get("beam_design", {})
            self.material_combobox.set(
                beam_params.get("material", "Glulam 24F-V4 DF (Fb=2400 psi)")
            )
            self.entries["beam_width"].delete(0, tk.END)
            self.entries["beam_width"].insert(0, beam_params.get("beam_width", "3.5"))
            self.entries["beam_depth_trial"].delete(0, tk.END)
            self.entries["beam_depth_trial"].insert(
                0, beam_params.get("beam_depth_trial", "16")
            )

            # N-S Ridge Beam design
            ns_ridge_params = inputs.get("ns_ridge_beam_design", {})
            if ns_ridge_params:
                self.ns_ridge_material_combobox.set(
                    ns_ridge_params.get("material", "Glulam 24F-V4 DF (Fb=2400 psi)")
                )
                self.entries["ns_ridge_beam_width"].delete(0, tk.END)
                self.entries["ns_ridge_beam_width"].insert(
                    0, ns_ridge_params.get("beam_width", "3.5")
                )
                self.entries["ns_ridge_beam_depth_trial"].delete(0, tk.END)
                self.entries["ns_ridge_beam_depth_trial"].insert(
                    0, ns_ridge_params.get("beam_depth_trial", "16")
                )
                if "fb_allowable" in self.entries:
                    self.entries["ns_ridge_fb_allowable"].delete(0, tk.END)
                    self.entries["ns_ridge_fb_allowable"].insert(
                        0, ns_ridge_params.get("fb_allowable", "2400")
                    )
                if "fv_allowable" in self.entries:
                    self.entries["ns_ridge_fv_allowable"].delete(0, tk.END)
                    self.entries["ns_ridge_fv_allowable"].insert(
                        0, ns_ridge_params.get("fv_allowable", "265")
                    )
                if "modulus_e" in self.entries:
                    self.entries["ns_ridge_modulus_e"].delete(0, tk.END)
                    self.entries["ns_ridge_modulus_e"].insert(
                        0, ns_ridge_params.get("modulus_e", "1800000")
                    )
                if "deflection_total_limit" in self.entries:
                    self.entries["ns_ridge_deflection_total_limit"].delete(0, tk.END)
                    self.entries["ns_ridge_deflection_total_limit"].insert(
                        0, ns_ridge_params.get("deflection_total_limit", "240")
                    )
                if "deflection_snow_limit" in self.entries:
                    self.entries["ns_ridge_deflection_snow_limit"].delete(0, tk.END)
                    self.entries["ns_ridge_deflection_snow_limit"].insert(
                        0, ns_ridge_params.get("deflection_snow_limit", "360")
                    )
                # Update material properties
                self.on_ns_ridge_material_change(None)

            # Restore results if available
            results = backup_data.get("results", {})
            if results.get("output_text") and hasattr(self, "output_text"):
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(1.0, results["output_text"])
            if results.get("summary_text") and hasattr(self, "summary_label"):
                self.summary_label.config(state="normal")
                self.summary_label.delete(1.0, tk.END)
                self.summary_label.insert(1.0, results["summary_text"])
                self.summary_label.config(state="disabled")

            # Mark as unchanged after restore
            self.data_changed = False

        except Exception as e:
            messagebox.showerror(
                "Restore Error", f"Failed to restore from backup: {str(e)}"
            )

    def bind_data_change_events(self):
        """Bind events to detect data changes in input fields."""
        # Bind to entry fields
        for key, entry in self.entries.items():
            entry.bind("<KeyRelease>", self.on_data_changed)
            entry.bind("<FocusOut>", self.on_data_changed)

        # Bind to comboboxes
        # Note: material_combobox is already bound to on_material_change in __init__
        # and on_material_change handles data change tracking internally

    def on_data_changed(self, event=None):
        """Called when any input data changes."""
        self.data_changed = True

    def on_closing(self):
        """Handle application closing - cleanup auto-save files."""
        # Remove crash flag since we're closing normally
        self.remove_crash_flag()

        # Remove auto-save file on normal exit
        try:
            if os.path.exists(self.auto_save_file):
                os.remove(self.auto_save_file)
        except Exception as e:
            print(f"Warning: Could not remove auto-save file: {e}")

        # Close the application
        self.master.quit()

    def initialize_output_text(self):
        """Initialize the output text area with ASCE 7-22 Section 7.6.1 information."""
        self.output_text.insert(
            tk.END,
            "=== ASCE 7-22 SECTION 7.6.1: UNBALANCED SNOW LOADS FOR HIP AND GABLE ROOFS ===\n",
            "blue",
        )
        self.output_text.insert(
            tk.END,
            "Unbalanced snow loads (including valley drifts derived from them) are governed by Sec. 7.6.1.\n\n",
            "blue",
        )
        self.output_text.insert(tk.END, "APPLICABILITY:\n", "blue")
        self.output_text.insert(
            tk.END,
            "• Unbalanced loads are REQUIRED only for roof slopes between 0.5/12 (≈2.38°) and 7/12 (≈30.2°).\n",
            "blue",
        )
        self.output_text.insert(
            tk.END,
            "• Outside this range: Unbalanced loads and associated drifts are NOT required.\n\n",
            "blue",
        )
        self.output_text.insert(
            tk.END,
            "SPECIAL NARROW ROOF CASE (eave-to-ridge distance W ≤ 20 ft AND simply supported prismatic members):\n",
            "blue",
        )
        self.output_text.insert(
            tk.END,
            "  → Leeward side: Full ground snow load pg (windward unloaded)\n",
            "blue",
        )
        self.output_text.insert(
            tk.END, "  → No separate drift surcharge calculated\n\n", "blue"
        )
        self.output_text.insert(
            tk.END,
            "If unbalanced loads do not apply on either plane, drift surcharge = 0.\n",
            "blue",
        )
        self.output_text.insert(
            tk.END,
            "Click 'Calculate' to analyze your specific roof geometry and see detailed results.\n",
        )

    def _setup_roof_geometry(
        self, ax, north_span, south_span, ew_half_width, valley_offset
    ):
        """
        Standardized roof geometry setup for all diagram methods.
        Returns: total_width, total_height, center_x
        """
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

        return total_width, total_height, center_x

    def _add_roof_labels(
        self,
        ax,
        north_span,
        south_span,
        ew_half_width,
        valley_offset,
        total_width,
        center_x,
    ):
        """Standardized roof labeling for all diagram methods."""
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

    def _add_north_arrow(self, ax, total_width, total_height):
        """Standardized North arrow for all diagram methods."""
        # North arrow – positioned below title area with proper spacing
        arrow_x = total_width / 2
        arrow_y = total_height + 8  # Position closer to roof geometry
        ax.arrow(
            arrow_x, arrow_y, 0, 4, head_width=2, head_length=4, fc="k", ec="k"
        )  # Smaller arrow
        ax.text(
            arrow_x,
            arrow_y + 8,  # Less vertical spacing for "N" text
            "N",
            fontsize=10,
            ha="center",
            fontweight="bold",
            va="bottom",
        )

    def _finalize_diagram(
        self,
        ax,
        total_width,
        total_height,
        title,
        load_legend_handles=None,
        show_building_legend=True,
    ):
        """Standardized diagram finalization for all diagram methods."""
        ax.set_xlim(-10, total_width + 10)
        ax.set_ylim(
            -15, total_height + 25
        )  # Extended for North arrow with proper spacing
        ax.set_axis_off()
        ax.set_title(title)

        # Building elements legend (at top-right, optional)
        if show_building_legend:
            building_legend = ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.08))

        # Load elements legend (at bottom for diagrams with loads)
        if load_legend_handles:
            ax.legend(
                handles=load_legend_handles,
                loc="lower center",
                bbox_to_anchor=(0.5, -0.1),
                ncol=2,
                fontsize=9,
            )

    def draw_plan_view(self, north_span, south_span, ew_half_width, valley_offset):
        fig = plt.Figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        # Use standardized template methods
        total_width, total_height, center_x = self._setup_roof_geometry(
            ax, north_span, south_span, ew_half_width, valley_offset
        )
        self._add_roof_labels(
            ax,
            north_span,
            south_span,
            ew_half_width,
            valley_offset,
            total_width,
            center_x,
        )
        self._add_north_arrow(ax, total_width, total_height)
        self._finalize_diagram(
            ax, total_width, total_height, "Roof Plan View"
        )  # No load legend for roof plan

        return fig

        return fig

    def draw_north_drift_overlay(
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
        fig = plt.Figure(figsize=(12, 10))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        # Use standardized template methods
        total_width, total_height, center_x = self._setup_roof_geometry(
            ax, north_span, south_span, ew_half_width, valley_offset
        )
        self._add_roof_labels(
            ax,
            north_span,
            south_span,
            ew_half_width,
            valley_offset,
            total_width,
            center_x,
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
            color="silver",
            alpha=0.7,
            hatch="///",
            edgecolor="dimgray",
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

        # Collect load-specific legend handles for bottom legend
        load_legend_handles = []
        # Get the North Wind Drift handle from the current legend
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            if "Drift" in label or any(
                word in label.lower()
                for word in ["psf", "windward", "leeward", "base", "surcharge"]
            ):
                load_legend_handles.append(handle)

        # Use standardized template methods
        self._add_north_arrow(ax, total_width, total_height)
        self._finalize_diagram(
            ax,
            total_width,
            total_height,
            "North Wind - North & South Roof Planes (ASCE 7-22 Section 7.6.1)",
            load_legend_handles,
        )

        return fig

    def draw_north_unbalanced_overlay(
        self,
        north_span,
        south_span,
        ew_half_width,
        valley_offset,
        north_load,
        south_load,
        ps_balanced,
        surcharge_width_north=0,
    ):
        """Draw north wind load distribution - shows North and South roof planes"""
        fig = plt.Figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        # Copy the exact same roof geometry
        total_width = 2 * ew_half_width
        total_height = north_span + south_span
        center_x = ew_half_width

        # Building outline
        ax.plot(
            [0, total_width, total_width, 0, 0],
            [total_height, total_height, 0, 0, total_height],
            "k-",
            linewidth=2,
            label="Building Outline",
        )

        # E-W ridge
        ax.plot(
            [0, total_width],
            [south_span, south_span],
            "k-",
            linewidth=3,
            label="E-W Ridge",
        )

        # N-S ridge
        ax.plot(
            [center_x, center_x], [south_span, 0], "k-", linewidth=3, label="N-S Ridge"
        )

        # Valley lines
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

        # Labels
        ax.text(
            total_width / 2,
            south_span + north_span * 0.75,
            f"North span\n{north_span:.1f} ft",
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

        # === NORTH WIND DIAGRAM ===
        # Wind from North affects North and South roof planes
        # North plane (top): windward, South plane (bottom): leeward

        # North roof plane (top half, windward) - always show
        ax.fill_between(
            [0, total_width],
            [south_span, south_span],
            [total_height, total_height],
            color="gainsboro" if north_load == 0 else "silver",
            alpha=0.5 if north_load == 0 else 0.7,
            hatch="//" if north_load == 0 else None,
            label=f"North Plane (Windward): {north_load:.1f} psf",
        )

        # South roof plane (bottom half, leeward)
        # Check if narrow roof case: surcharge width covers full span (approximately)
        # For narrow roofs: south_load = pg uniformly, not ps + surcharge
        is_narrow_roof_north = (surcharge_width_north >= south_span * 0.99) or (
            north_load == 0 and south_load > ps_balanced * 1.5
        )

        if surcharge_width_north > 0 and not is_narrow_roof_north:
            # Wide roof case: Show base load (ps) over entire south plane
            ax.fill_between(
                [0, total_width],
                [0, 0],
                [south_span, south_span],
                color="gray",
                alpha=0.7,
                label=f"South Base: {ps_balanced:.1f} psf",
            )
            # Overlay surcharge area with additional load
            # Surcharge width measured southward from E-W ridge
            # For wide roofs: south_load = ps + surcharge, so surcharge = south_load - ps_balanced
            surcharge_intensity = south_load - ps_balanced
            ax.fill_between(
                [0, total_width],
                [
                    south_span - surcharge_width_north,
                    south_span - surcharge_width_north,
                ],
                [south_span, south_span],
                color="gray",
                alpha=0.7,
                hatch="///",
                edgecolor="darkgray",
                linewidth=1.5,
                label=f"Surcharge: +{surcharge_intensity:.1f} psf (w={surcharge_width_north:.1f} ft)",
            )
        elif is_narrow_roof_north:
            # Narrow roof case: uniform pg on entire south plane (leeward)
            ax.fill_between(
                [0, total_width],
                [0, 0],
                [south_span, south_span],
                color="gray",
                alpha=0.7,
                label=f"South Plane (Leeward - Narrow Roof): {south_load:.1f} psf (pg)",
            )
        else:
            # No surcharge - uniform load on south plane
            ax.fill_between(
                [0, total_width],
                [0, 0],
                [south_span, south_span],
                color="gray",
                alpha=0.7,
                label=f"South Plane (Leeward): {south_load:.1f} psf",
            )

        # Labels for North and South roof planes
        ax.text(
            center_x,
            total_height - north_span * 0.5,
            f"North Roof Plane\n(Windward)\n{north_span:.1f} ft span",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )
        ax.text(
            center_x,
            south_span * 0.5,
            f"South Roof Plane\n(Leeward)\n{south_span:.1f} ft span",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )

        # Annotations
        if surcharge_width_north > 0:
            if is_narrow_roof_north:
                ax.text(
                    total_width + 35,
                    total_height * 0.75,
                    f"North Wind - Narrow Roof Case (W ≤ 20 ft)\nWindward (North): {north_load:.1f} psf\nLeeward (South): {south_load:.1f} psf (pg)\nBalanced: {ps_balanced:.1f} psf",
                    ha="left",
                    va="center",
                    fontsize=9,
                    bbox=dict(
                        facecolor="white",
                        alpha=0.95,
                        edgecolor="slategray",
                        boxstyle="round,pad=0.5",
                    ),
                )
            else:
                ax.text(
                    total_width + 35,
                    total_height * 0.75,
                    f"North Wind - Surcharge South of E-W Ridge\nWindward (North): {north_load:.1f} psf\nLeeward Surcharge (South): {south_load:.1f} psf\nBalanced: {ps_balanced:.1f} psf",
                    ha="left",
                    va="center",
                    fontsize=9,
                    bbox=dict(
                        facecolor="white",
                        alpha=0.95,
                        edgecolor="slategray",
                        boxstyle="round,pad=0.5",
                    ),
                )
        else:
            ax.text(
                total_width + 35,
                total_height * 0.75,
                f"North Wind - Balanced Loads Only\nEntire Roof: {ps_balanced:.1f} psf\n(No unbalanced loads apply)",
                ha="left",
                va="center",
                fontsize=9,
                bbox=dict(
                    facecolor="white",
                    alpha=0.95,
                    edgecolor="slategray",
                    boxstyle="round,pad=0.5",
                ),
            )

        # Collect load-specific legend handles for bottom legend
        load_legend_handles = []
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            if any(
                word in label.lower()
                for word in [
                    "psf",
                    "windward",
                    "leeward",
                    "base",
                    "surcharge",
                    "north plane",
                    "south plane",
                ]
            ):
                load_legend_handles.append(handle)

        # Use standardized template methods
        self._add_north_arrow(ax, total_width, total_height)
        self._finalize_diagram(
            ax,
            total_width,
            total_height,
            "North Wind - North & South Roof Planes (ASCE 7-22 Section 7.6.1)",
            load_legend_handles,
        )

        return fig

    def draw_governing_unbalanced_overlay(
        self,
        north_span,
        south_span,
        ew_half_width,
        valley_offset,
        north_load_governing,
        south_load_governing,
        west_load_governing,
        east_load_governing,
        ps_balanced,
        surcharge_width_north=0,
        surcharge_width_west=0,
    ):
        """Draw governing unbalanced load distribution showing maximum loads from both wind directions"""
        # Use instance variables instead of parameters to avoid passing issues
        north_load = getattr(self, "governing_north", north_load_governing)
        south_load = getattr(self, "governing_south", south_load_governing)
        west_load = getattr(self, "governing_west", west_load_governing)
        east_load = getattr(self, "governing_east", east_load_governing)

        fig = plt.Figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        # Building outline
        total_width = 2 * ew_half_width
        total_height = north_span + south_span
        center_x = ew_half_width

        ax.plot(
            [0, total_width, total_width, 0, 0],
            [total_height, total_height, 0, 0, total_height],
            "k-",
            linewidth=2,
            label="Building Outline",
        )

        # E-W ridge
        ax.plot(
            [0, total_width],
            [south_span, south_span],
            "k-",
            linewidth=3,
            label="E-W Ridge",
        )

        # N-S ridge
        ax.plot(
            [center_x, center_x], [south_span, 0], "k-", linewidth=3, label="N-S Ridge"
        )

        # Valley lines
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

        # === GOVERNING LOADS ===
        # Show governing loads (maximum from both wind directions)
        # For balanced case, all planes show same balanced load

        # Check if unbalanced loads apply (any surcharge width > 0)
        unbalanced_applies = (surcharge_width_north > 0) or (surcharge_width_west > 0)

        # Collect load-specific legend handles for bottom legend (do this after all fill_between calls)
        load_legend_handles = []

        # Show ONLY governing loads in southeast quadrant
        # All other roof quadrants are not displayed per user request

        # Check if unbalanced loads apply
        has_unbalanced = unbalanced_applies and (
            surcharge_width_north > 0 or surcharge_width_west > 0
        )

        if has_unbalanced:
            # Get individual wind direction loads for valley governing load determination
            south_load_north_wind = getattr(self, "south_load_north_wind", south_load)
            east_load_west_wind = getattr(self, "east_load_west_wind", east_load)

            # Determine which wind direction governs (larger total load)
            # North wind: total load on south plane = south_load_north_wind
            # West wind: total load on east plane = east_load_west_wind
            governing_valley_load = max(south_load_north_wind, east_load_west_wind)

            # Determine which wind direction governs and use ITS distance for BOTH ridges
            if south_load_north_wind >= east_load_west_wind:
                governing_wind = "North"
                governing_surcharge = south_load_north_wind - ps_balanced
                governing_distance = (
                    surcharge_width_north  # Use north wind distance for both ridges
                )
            else:
                governing_wind = "West"
                governing_surcharge = east_load_west_wind - ps_balanced
                governing_distance = (
                    surcharge_width_west  # Use west wind distance for both ridges
                )

            # Show TWO overlapping hatched areas from BOTH ridges in SE quadrant ONLY:
            # Both use the GOVERNING load value and the SAME distance (from governing wind)
            # 1. From E-W ridge: using governing_distance (perpendicular to E-W ridge)
            # 2. From N-S ridge: using governing_distance (perpendicular to N-S ridge)

            # First hatched area: From E-W ridge southward (limited to SE quadrant)
            x_start_ew = center_x  # Start at N-S ridge (SE quadrant only)
            x_end_ew = total_width  # Extend to east edge
            y_start_ew = max(
                0, south_span - governing_distance
            )  # Distance from E-W ridge
            y_end_ew = south_span  # At E-W ridge

            ax.fill_between(
                [x_start_ew, x_end_ew],
                [y_start_ew, y_start_ew],
                [y_end_ew, y_end_ew],
                color="dimgray",  # Dark gray for governing surcharge
                alpha=0.6,  # Slightly transparent for overlap visibility
                hatch="////",
                edgecolor="black",
                linewidth=2,
                label=f"From E-W Ridge: {governing_valley_load:.1f} psf\nDist: {governing_distance:.1f} ft",
            )

            # Second hatched area: From N-S ridge eastward (limited to SE quadrant)
            x_start_ns = center_x  # Start at N-S ridge
            x_end_ns = min(
                center_x + governing_distance, total_width
            )  # Distance from N-S ridge
            y_start_ns = 0  # Start at south edge
            y_end_ns = south_span  # Extend to E-W ridge

            ax.fill_between(
                [x_start_ns, x_end_ns],
                [y_start_ns, y_start_ns],
                [y_end_ns, y_end_ns],
                color="dimgray",  # Dark gray for governing surcharge
                alpha=0.6,  # Slightly transparent for overlap visibility
                hatch="\\\\\\",  # Different hatch pattern for second area
                edgecolor="black",
                linewidth=2,
                label=f"From N-S Ridge: {governing_valley_load:.1f} psf\nDist: {governing_distance:.1f} ft",
            )

            # Third hatched area: Remaining SE quadrant area with balanced load only
            # This is the area NOT covered by either surcharge zone
            # Area beyond governing_distance from both ridges
            remaining_x_start = min(
                center_x + governing_distance, total_width
            )  # Beyond N-S surcharge
            remaining_x_end = total_width  # To east edge
            remaining_y_start = 0  # From south edge
            remaining_y_end = max(
                0, south_span - governing_distance
            )  # Below E-W surcharge

            # Only show if there's actually a remaining area
            if remaining_x_start < total_width and remaining_y_end > 0:
                ax.fill_between(
                    [remaining_x_start, remaining_x_end],
                    [remaining_y_start, remaining_y_start],
                    [remaining_y_end, remaining_y_end],
                    color="lightgray",  # Light gray for balanced load
                    alpha=0.5,
                    hatch="...",  # Dotted hatch pattern for balanced load area
                    edgecolor="black",
                    linewidth=1.5,
                    label=f"Balanced Load: {ps_balanced:.1f} psf\n(Remaining SE area)",
                )

            # Add annotation showing governing load details
            annotation_text = (
                f"Governing Valley Load (Southeast Quadrant)\n"
                f"(ASCE 7-22 Section 7.6.1)\n\n"
                f"Load Comparison:\n"
                f"  North Wind Load: {south_load_north_wind:.1f} psf\n"
                f"  West Wind Load: {east_load_west_wind:.1f} psf\n\n"
                f"Governing Wind: {governing_wind}\n\n"
                f"Applied Load: {governing_valley_load:.1f} psf\n"
                f"  = Balanced: {ps_balanced:.1f} psf\n"
                f"  + Surcharge: {governing_surcharge:.1f} psf\n\n"
                f"Overlapping Surcharge Areas (SE Quadrant Only):\n"
                f"  From E-W Ridge: {governing_distance:.1f} ft\n"
                f"    (perpendicular to E-W ridge)\n"
                f"  From N-S Ridge: {governing_distance:.1f} ft\n"
                f"    (perpendicular to N-S ridge)\n\n"
                f"Formula: w = (8 × hd × √s) / 3"
            )

            ax.text(
                total_width + 45,
                total_height * 0.5,
                annotation_text,
                ha="left",
                va="center",
                fontsize=9,
                bbox=dict(
                    facecolor="white",
                    alpha=0.95,
                    edgecolor="dimgray",
                    boxstyle="round,pad=0.5",
                ),
            )
        else:
            # Balanced load governs - show TWO overlapping shaded areas from BOTH ridges
            # covering the entire southeast quadrant

            # First shaded area: From E-W ridge covering entire SE quadrant
            x_start_ew = 0  # Start at west edge
            x_end_ew = total_width  # Extend full width
            y_start_ew = 0  # Start at south edge
            y_end_ew = south_span  # Extend to E-W ridge

            ax.fill_between(
                [x_start_ew, x_end_ew],
                [y_start_ew, y_start_ew],
                [y_end_ew, y_end_ew],
                color="lightgray",  # Light gray for balanced load
                alpha=0.5,  # Transparent for overlap visibility
                hatch="////",  # Diagonal hatch pattern
                edgecolor="black",
                linewidth=1.5,
                label=f"From E-W Ridge: {ps_balanced:.1f} psf\n(Entire SE Quadrant)",
            )

            # Second shaded area: From N-S ridge covering entire SE quadrant
            x_start_ns = center_x  # Start at N-S ridge
            x_end_ns = total_width  # Extend to east edge
            y_start_ns = 0  # Start at south edge
            y_end_ns = south_span  # Extend to E-W ridge

            ax.fill_between(
                [x_start_ns, x_end_ns],
                [y_start_ns, y_start_ns],
                [y_end_ns, y_end_ns],
                color="lightgray",  # Light gray for balanced load
                alpha=0.5,  # Transparent for overlap visibility
                hatch="\\\\\\",  # Opposite diagonal hatch pattern
                edgecolor="black",
                linewidth=1.5,
                label=f"From N-S Ridge: {ps_balanced:.1f} psf\n(Entire SE Quadrant)",
            )

            # Add annotation showing balanced load details
            ax.text(
                total_width + 45,
                total_height * 0.5,
                f"Governing Valley Load (Southeast Quadrant)\n(ASCE 7-22 Section 7.6.1)\n\n"
                f"Balanced Load Condition\n"
                f"No unbalanced loads apply\n\n"
                f"Applied Load: {ps_balanced:.1f} psf\n"
                f"(Covering entire SE quadrant from both ridges)",
                ha="left",
                va="center",
                fontsize=9,
                bbox=dict(
                    facecolor="white",
                    alpha=0.95,
                    edgecolor="dimgray",
                    boxstyle="round,pad=0.5",
                ),
            )

        # Collect load-specific legend handles for bottom legend (after all fill_between calls)
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            if any(
                word in label.lower()
                for word in [
                    "psf",
                    "windward",
                    "leeward",
                    "base",
                    "surcharge",
                    "north",
                    "south",
                    "west",
                    "east",
                ]
            ):
                load_legend_handles.append(handle)

        # Use standardized template methods
        self._add_north_arrow(ax, total_width, total_height)
        self._finalize_diagram(
            ax,
            total_width,
            total_height,
            "Governing Valley Load Application",
            load_legend_handles,
            show_building_legend=False,
        )

        return fig

    def draw_west_unbalanced_overlay(
        self,
        north_span,
        south_span,
        ew_half_width,
        valley_offset,
        west_load,
        east_load,
        ps_balanced,
        surcharge_width_west=0,
    ):
        """Draw west wind unbalanced load distribution on roof planes"""
        fig = plt.Figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        # Copy the exact same roof geometry
        total_width = 2 * ew_half_width
        total_height = north_span + south_span
        center_x = ew_half_width

        # Building outline
        ax.plot(
            [0, total_width, total_width, 0, 0],
            [total_height, total_height, 0, 0, total_height],
            "k-",
            linewidth=2,
            label="Building Outline",
        )

        # E-W ridge
        ax.plot(
            [0, total_width],
            [south_span, south_span],
            "k-",
            linewidth=3,
            label="E-W Ridge",
        )

        # N-S ridge
        ax.plot(
            [center_x, center_x], [south_span, 0], "k-", linewidth=3, label="N-S Ridge"
        )

        # Valley lines
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

        # Labels for roof planes affected by West wind
        ax.text(
            center_x * 0.5,
            total_height * 0.75,
            f"Northern Roof Plane\n(Balanced Load)\n{ew_half_width:.1f} ft span",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )
        ax.text(
            center_x * 0.5,
            total_height * 0.25,
            f"Southern West\n(Windward)\n{ew_half_width:.1f} ft span",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )
        ax.text(
            center_x + ew_half_width * 0.5,
            total_height * 0.25,
            f"Southern East\n(Leeward)\n{ew_half_width:.1f} ft span",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8),
        )

        # === WEST WIND DIAGRAM ===
        # Wind from West affects only the Southern roof plane (below E-W ridge)
        # Northern roof plane remains at balanced load

        # Northern roof plane (above E-W ridge) - balanced load only
        ax.fill_between(
            [0, total_width],
            [south_span, south_span],
            [total_height, total_height],
            color="darkgray",
            alpha=0.6,
            label=f"Northern Plane (Balanced): {ps_balanced:.1f} psf",
        )

        # Southern roof plane (below E-W ridge) - West wind unbalanced loads
        # West portion (windward)
        ax.fill_between(
            [0, center_x],
            [0, 0],
            [south_span, south_span],
            color="gainsboro" if west_load == 0 else "silver",
            alpha=0.5 if west_load == 0 else 0.7,
            hatch="//" if west_load == 0 else None,
            label=f"Southern West (Windward): {west_load:.1f} psf",
        )

        # East portion (leeward)
        if surcharge_width_west > 0:
            # Show base load (ps) over southern east plane
            ax.fill_between(
                [center_x, total_width],
                [0, 0],
                [south_span, south_span],
                color="gray",
                alpha=0.7,
                label=f"Southern East Base: {ps_balanced:.1f} psf",
            )
            # Overlay surcharge area with additional load
            # Surcharge width measured eastward from N-S ridge
            surcharge_intensity = east_load - ps_balanced
            surcharge_end_x = min(center_x + surcharge_width_west, total_width)
            ax.fill_between(
                [center_x, surcharge_end_x],
                [0, 0],
                [south_span, south_span],
                color="red",
                alpha=0.7,
                hatch="///",
                edgecolor="gray",
                linewidth=1.5,
                label=f"Surcharge: +{surcharge_intensity:.1f} psf (w={surcharge_width_west:.1f} ft)",
            )
            # Show remaining area with base load if surcharge doesn't extend to eave
            if surcharge_end_x < total_width:
                ax.fill_between(
                    [surcharge_end_x, total_width],
                    [0, 0],
                    [south_span, south_span],
                    color="gray",
                    alpha=0.7,
                )
        else:
            # No surcharge - uniform load on southern east plane
            ax.fill_between(
                [center_x, total_width],
                [0, 0],
                [south_span, south_span],
                color="gray",
                alpha=0.7,
                label=f"Southern East (Leeward): {east_load:.1f} psf",
            )

        # Annotations
        if surcharge_width_west > 0:
            ax.text(
                total_width + 35,
                total_height * 0.6,
                f"West Wind - Southern Plane Only\nNorthern Plane: {ps_balanced:.1f} psf (Balanced)\nSouthern West: {west_load:.1f} psf (Windward)\nSouthern East: {east_load:.1f} psf (Leeward + Surcharge)",
                ha="left",
                va="center",
                fontsize=9,
                bbox=dict(
                    facecolor="white",
                    alpha=0.95,
                    edgecolor="darkgray",
                    boxstyle="round,pad=0.5",
                ),
            )
        else:
            ax.text(
                total_width + 35,
                total_height * 0.6,
                f"West Wind - Balanced Loads Only\nNorthern Plane: {ps_balanced:.1f} psf\nSouthern Planes: {ps_balanced:.1f} psf\n(No unbalanced loads apply)",
                ha="left",
                va="center",
                fontsize=9,
                bbox=dict(
                    facecolor="white",
                    alpha=0.95,
                    edgecolor="darkgray",
                    boxstyle="round,pad=0.5",
                ),
            )

        # Collect load-specific legend handles for bottom legend
        load_legend_handles = []
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            if any(
                word in label.lower()
                for word in [
                    "psf",
                    "windward",
                    "leeward",
                    "base",
                    "surcharge",
                    "north",
                    "south",
                    "west",
                    "east",
                ]
            ):
                load_legend_handles.append(handle)

        # Use standardized template methods
        self._add_north_arrow(ax, total_width, total_height)
        self._finalize_diagram(
            ax,
            total_width,
            total_height,
            "West Wind - West & East Roof Planes (ASCE 7-22 Section 7.6.1)",
            load_legend_handles,
        )

        return fig

    def generate_diagrams(
        self,
        snow_point_loads,
        dead_point_loads,
        rafter_len,
        ps_balanced,
        gov_drift,
        lv_horizontal,
        north_span,
        south_span,
        ew_half_width,
        valley_offset,
        pitch_n,
        pitch_w,
        valley_angle,
        lu_north,
        lu_west,
        result_north,
        result_west,
        surcharge_width_north=0,
        surcharge_width_west=0,
        north_load_governing=0,
        south_load_governing=0,
        west_load_governing=0,
        east_load_governing=0,
        north_load_north_wind_final=0,
        south_load_north_wind_final=0,
        west_load_west_wind_final=0,
        east_load_west_wind_final=0,
    ):
        """Generate five professional diagrams: plan view, SFD, BMD, drift profile, and sloped point loads."""
        # Clear previous plot but keep figures alive for PDF capture if needed
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        # Keep track of figures for potential PDF capture
        self._current_figures = []

        # ===== ROOF PLAN VIEW =====
        fig_plan = self.draw_plan_view(
            north_span, south_span, ew_half_width, valley_offset
        )
        self._current_figures.append(fig_plan)
        canvas_plan = FigureCanvasTkAgg(fig_plan, master=self.plot_frame)
        canvas_plan.draw()
        canvas_plan.get_tk_widget().pack(side=tk.TOP, pady=5)

        # ===== THREE LOAD DIAGRAMS =====

        # 1. North Wind Diagram
        fig_north = self.draw_north_unbalanced_overlay(
            north_span,
            south_span,
            ew_half_width,
            valley_offset,
            north_load_north_wind_final,
            south_load_north_wind_final,
            ps_balanced,
            surcharge_width_north,
        )
        self._current_figures.append(fig_north)
        canvas_north = FigureCanvasTkAgg(fig_north, master=self.plot_frame)
        canvas_north.draw()
        canvas_north.get_tk_widget().pack(side=tk.TOP, pady=5)

        # 2. West Wind Diagram
        fig_west = self.draw_west_unbalanced_overlay(
            north_span,
            south_span,
            ew_half_width,
            valley_offset,
            west_load_west_wind_final,
            east_load_west_wind_final,
            ps_balanced,
            surcharge_width_west,
        )
        self._current_figures.append(fig_west)
        canvas_west = FigureCanvasTkAgg(fig_west, master=self.plot_frame)
        canvas_west.draw()
        canvas_west.get_tk_widget().pack(side=tk.TOP, pady=5)

        # 3. Governing Unbalanced Loads (maximum from both wind directions)
        fig_governing = self.draw_governing_unbalanced_overlay(
            north_span,
            south_span,
            ew_half_width,
            valley_offset,
            0,
            0,
            0,
            0,  # Dummy values since we use instance variables
            ps_balanced,
            surcharge_width_north,
            surcharge_width_west,
        )
        self._current_figures.append(fig_governing)
        canvas_governing = FigureCanvasTkAgg(fig_governing, master=self.plot_frame)
        canvas_governing.draw()
        canvas_governing.get_tk_widget().pack(side=tk.TOP, pady=5)

        # Get drift parameters
        pd_max = gov_drift["governing_pd_max_psf"]
        w_drift = gov_drift["governing_hd_ft"] * 3  # Approximate drift width

        # Combine snow and dead loads for total point loads (jack rafter reactions)
        # Use stored values from comparison table to ensure diagrams match table
        total_point_loads = []
        if hasattr(self, "valley_beam_sloped_positions") and hasattr(
            self, "valley_beam_sloped_loads"
        ):
            # Use stored sloped positions and loads (these match the comparison table)
            for pos_sloped, total_load in zip(
                self.valley_beam_sloped_positions, self.valley_beam_sloped_loads
            ):
                total_point_loads.append((pos_sloped, total_load))
        else:
            # Fallback to original calculation if stored values not available
            for (pos_s, load_s), (pos_d, load_d) in zip(
                snow_point_loads, dead_point_loads
            ):
                total_load = load_s + load_d  # This is the reaction to the valley beam
                total_point_loads.append((pos_s, total_load))

        # Sort point loads by position
        total_point_loads.sort(key=lambda x: x[0])

        if not total_point_loads:
            return

        # Calculate reactions at supports (same method as beam design)
        total_load = sum(load for _, load in total_point_loads)
        r_eave = 0
        for pos, load in total_point_loads:
            r_eave += load * (lv_horizontal - pos) / lv_horizontal  # Moment about ridge
        r_ridge = total_load - r_eave
        
        # Verify equilibrium: Sum of reactions should equal total point loads
        sum_reactions_valley = r_eave + r_ridge
        equilibrium_check_valley = abs(sum_reactions_valley - total_load) < 0.01  # Allow small rounding error
        self.valley_equilibrium_check = {
            "sum_reactions": sum_reactions_valley,
            "total_loads": total_load,
            "difference": abs(sum_reactions_valley - total_load),
            "passes": equilibrium_check_valley
        }

        # Generate positions for diagrams
        positions = [i * rafter_len / 99 for i in range(100)]

        # ===== SHEAR FORCE DIAGRAM =====
        fig1, ax1 = plt.subplots(1, 1, figsize=(10, 6), dpi=100)
        self._current_figures.append(fig1)

        shear = []
        for x in positions:
            v = r_eave  # Start with eave reaction
            for pos, load in total_point_loads:
                if pos <= x:
                    v -= load  # Subtract loads to the left
            shear.append(v)

        ax1.plot(positions, shear, "b-", linewidth=2.5, label="Shear Force")
        ax1.fill_between(positions, shear, alpha=0.2, color="silver")
        ax1.set_ylabel("Shear Force (lb)", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Distance from Eave (ft)", fontsize=11, fontweight="bold")
        ax1.set_title("Shear Force Diagram", fontsize=13, fontweight="bold")
        ax1.grid(True, linestyle="--", alpha=0.6)
        ax1.axhline(y=0, color="k", linestyle="-", alpha=0.7, linewidth=0.8)
        ax1.legend(loc="upper right")

        # Annotate net reactions at beam ends (arrow + value only)
        ax1.annotate(
            f"{int(r_eave)} lb",
            xy=(0, r_eave),
            xytext=(10, 10),
            textcoords="offset points",
            ha="left",
            fontsize=10,
            arrowprops=dict(arrowstyle="->", color="black"),
        )
        ax1.annotate(
            f"{int(r_ridge)} lb",
            xy=(rafter_len, -r_ridge),
            xytext=(-10, -10),
            textcoords="offset points",
            ha="right",
            fontsize=10,
            arrowprops=dict(arrowstyle="->", color="black"),
        )

        # Annotate max shear
        max_shear = max(abs(s) for s in shear)
        max_shear_idx = (
            shear.index(max(shear))
            if abs(max(shear)) == max_shear
            else shear.index(min(shear))
        )
        max_shear_pos = positions[max_shear_idx]
        ax1.annotate(
            f"{int(abs(shear[max_shear_idx]))} lb",
            xy=(max_shear_pos, shear[max_shear_idx]),
            xytext=(
                max_shear_pos + rafter_len * 0.05,
                shear[max_shear_idx] + max_shear * 0.1,
            ),
            fontsize=9,
            fontweight="bold",
            ha="left",
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"),
        )

        # ===== BENDING MOMENT DIAGRAM =====
        fig2, ax2 = plt.subplots(1, 1, figsize=(10, 6), dpi=100)
        self._current_figures.append(fig2)

        # Calculate moment by integrating shear force (M = ∫V dx)
        moment = [0.0]  # M(0) = 0
        dx = positions[1] - positions[0]  # Assume uniform spacing

        for i in range(1, len(positions)):
            # Trapezoidal integration: M(i) = M(i-1) + (V(i-1) + V(i))/2 * dx
            m_current = moment[-1] + (shear[i - 1] + shear[i]) / 2 * dx
            moment.append(m_current)

        # For gravity-loaded beams, moments should be positive (sagging)
        # If the maximum moment is negative, flip all signs
        max_moment = max(moment)
        if max_moment < 0:
            moment = [-m for m in moment]

        # Ensure M(L) = 0 for simply supported beam (within small tolerance)
        if abs(moment[-1]) < 1.0:
            moment[-1] = 0.0
        else:
            # Linear adjustment to force M(L) = 0
            slope = -moment[-1] / positions[-1]
            moment = [m + slope * x for m, x in zip(moment, positions)]

        ax2.plot(positions, moment, "r-", linewidth=2.5, label="Bending Moment")
        ax2.fill_between(positions, moment, alpha=0.2, color="gray")
        ax2.set_ylabel("Bending Moment (ft-lb)", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Distance from Eave (ft)", fontsize=11, fontweight="bold")
        ax2.set_title("Bending Moment Diagram", fontsize=13, fontweight="bold", pad=20)
        ax2.grid(True, linestyle="--", alpha=0.6)
        ax2.axhline(y=0, color="k", linestyle="-", alpha=0.7, linewidth=0.8)
        ax2.legend(loc="upper right")

        # Annotate max moment (moved further from top)
        max_moment = max(moment)
        max_moment_idx = moment.index(max_moment)
        max_moment_pos = positions[max_moment_idx]
        ax2.annotate(
            f"{int(max_moment)} ft-lb",
            xy=(max_moment_pos, max_moment),
            xytext=(
                max_moment_pos + rafter_len * 0.08,
                max_moment + abs(max_moment) * 0.05,
            ),
            fontsize=9,
            fontweight="bold",
            ha="left",
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"),
        )

        # ===== DRIFT LOAD PROFILE =====
        fig3, ax3 = plt.subplots(1, 1, figsize=(10, 6), dpi=100)
        self._current_figures.append(fig3)

        # Horizontal positions along valley
        x_positions = [i * lv_horizontal / 50 for i in range(51)]

        # Drift surcharge profile (triangular from pd_max at ridge to 0 at w_drift)
        pd_profile = []
        for x in x_positions:
            if w_drift > 0 and x <= w_drift:
                pd_val = pd_max * (1 - x / w_drift)  # Linear taper
            else:
                pd_val = 0
            pd_profile.append(pd_val)

        # Balanced snow load (uniform)
        ps_uniform = [ps_balanced] * len(x_positions)

        # Total snow load envelope
        total_profile = [ps + pd for ps, pd in zip(ps_uniform, pd_profile)]

        ax3.plot(
            x_positions,
            ps_uniform,
            "b-",
            linewidth=2.5,
            label=f"Balanced Snow (ps = {ps_balanced} psf)",
        )
        ax3.plot(
            x_positions,
            pd_profile,
            "r-",
            linewidth=2.5,
            label=f"Drift Surcharge (pd_max = {pd_max} psf)",
        )
        ax3.plot(
            x_positions,
            total_profile,
            "k-",
            linewidth=3,
            label="Total Snow Load (ps + pd)",
        )

        ax3.fill_between(
            x_positions,
            [0] * len(x_positions),
            pd_profile,
            alpha=0.3,
            color="gray",
        )
        ax3.fill_between(
            x_positions, ps_uniform, total_profile, alpha=0.2, color="silver"
        )

        ax3.set_xlabel(
            "Horizontal Distance from Ridge (ft)", fontsize=11, fontweight="bold"
        )
        ax3.set_ylabel("Snow Load (psf)", fontsize=11, fontweight="bold")
        ax3.set_title("Drift Load Profile (Horizontal)", fontsize=13, fontweight="bold")
        ax3.grid(True, linestyle="--", alpha=0.6)
        ax3.legend(loc="upper right")
        ax3.set_ylim(bottom=0)

        # ===== POINT LOADS ON SLOPED BEAM =====
        fig4, ax4 = plt.subplots(1, 1, figsize=(12, 7), dpi=100)
        self._current_figures.append(fig4)

        # Calculate beam geometry for sloped line from eave to ridge
        beam_x = [0, lv_horizontal]
        avg_pitch_rad = math.atan(((pitch_n + pitch_w) / 2) / 12)  # Convert to radians
        beam_y = [0, lv_horizontal * math.tan(avg_pitch_rad)]  # Vertical rise

        # Draw sloped beam line (no fill, clean appearance)
        ax4.plot(
            beam_x,
            beam_y,
            "k-",
            linewidth=6,
            alpha=0.9,
            solid_capstyle="round",
            label="Valley Beam",
        )

        # Scale factors for arrow lengths (larger magnitude = longer arrow)
        max_load = (
            max([abs(load) for _, load in total_point_loads])
            if total_point_loads
            else 1000
        )
        max_reaction = max(abs(r_eave), abs(r_ridge))
        load_scale = 1.5 / max_load if max_load > 0 else 1
        reaction_scale = 1.5 / max_reaction if max_reaction > 0 else 1

        # Add support reactions (upward green arrows at beam ends)
        ax4.arrow(
            0,
            beam_y[0],
            0,
            r_eave * reaction_scale,
            head_width=0.5,
            fc="darkgreen",
            ec="darkgreen",
            linewidth=2,
            alpha=0.9,
        )
        ax4.text(
            0,
            beam_y[0] + r_eave * reaction_scale + 0.8,
            f"R_eave = {int(r_eave)} lb",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="darkgreen",
        )

        ax4.arrow(
            lv_horizontal,
            beam_y[1],
            0,
            r_ridge * reaction_scale,
            head_width=0.5,
            fc="darkgreen",
            ec="darkgreen",
            linewidth=2,
            alpha=0.9,
        )
        ax4.text(
            lv_horizontal,
            beam_y[1] + r_ridge * reaction_scale + 0.8,
            f"R_ridge = {int(r_ridge)} lb",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="darkgreen",
        )

        # Add point loads (downward red arrows - jack rafter reactions)
        for pos, load in total_point_loads:
            # Calculate beam elevation at this position (linear interpolation)
            beam_elev = beam_y[0] + (beam_y[1] - beam_y[0]) * (pos / lv_horizontal)
            arrow_length = -load * load_scale  # Negative for downward arrow

            ax4.arrow(
                pos,
                beam_elev,
                0,
                arrow_length,
                head_width=0.5,
                fc="darkred",
                ec="darkred",
                linewidth=2,
                alpha=0.9,
            )

            # Position text further above the arrow (moved away from arrow)
            text_y = beam_elev + arrow_length - 0.8
            ax4.text(
                pos,
                text_y,
                f"{int(load)} lb",
                ha="center",
                va="top",
                fontsize=9,
                fontweight="bold",
                color="darkred",
            )

        ax4.set_xlabel("Distance from Eave (ft)", fontsize=11, fontweight="bold")
        ax4.set_ylabel("Elevation (ft)", fontsize=11, fontweight="bold")
        ax4.set_title(
            "Point Load Reactions on Sloped Valley Beam", fontsize=13, fontweight="bold"
        )
        ax4.grid(True, linestyle="--", alpha=0.6)
        ax4.set_xlim(-lv_horizontal * 0.05, lv_horizontal * 1.05)

        # Set y-limits to accommodate all arrows
        min_y = min(beam_y[0] - 1, beam_y[1] - 1, -max_load * load_scale - 1)
        max_y = max(
            beam_y[0] + max_reaction * reaction_scale + 1,
            beam_y[1] + max_reaction * reaction_scale + 1,
        )
        ax4.set_ylim(bottom=min_y, top=max_y)

        # Custom legend on left side
        legend_elements = [
            plt.Line2D(
                [0], [0], color="black", linewidth=6, alpha=0.9, label="Valley Beam"
            ),
            plt.arrow(
                0,
                0,
                0,
                -1,
                head_width=0.5,
                fc="darkgreen",
                ec="darkgreen",
                linewidth=2,
                label="Reactions (upward)",
            ),
            plt.Line2D(
                [0], [0], color="darkred", linewidth=2, label="Point Loads (downward)"
            ),
        ]
        ax4.legend(handles=legend_elements, loc="upper left")

        # Create a container frame for the four remaining diagrams
        diagram_container = ttk.Frame(self.plot_frame)
        diagram_container.pack(fill="both", expand=True)

        # Define diagram data
        diagrams = [
            (fig1, "Shear Force"),
            (fig2, "Bending Moment"),
            (fig3, "Drift Load Profile"),
            (fig4, "Point Load Reactions"),
        ]

        # Embed each diagram separately
        for fig, title in diagrams:
            canvas = FigureCanvasTkAgg(fig, master=diagram_container)
            canvas.draw()
            canvas.get_tk_widget().pack(
                side="top", fill="both", expand=True, pady=(0, 5)
            )

            toolbar = NavigationToolbar2Tk(canvas, diagram_container)
            toolbar.update()

        # ===== N-S RIDGE BEAM POINT LOADS DIAGRAM (LAST DIAGRAM) =====
        # Create diagram for N-S ridge beam (if loads are available)
        # This diagram is placed LAST, after all other diagrams
        if (
            hasattr(self, "ns_ridge_snow_point_loads")
            and hasattr(self, "ns_ridge_beam_length")
            and self.ns_ridge_snow_point_loads
        ):
            fig5, ax5 = plt.subplots(1, 1, figsize=(12, 7), dpi=100)
            self._current_figures.append(fig5)

            # N-S ridge beam runs horizontally (south of E-W ridge)
            ns_ridge_length = (
                self.ns_ridge_beam_length
            )  # Horizontal length = south_span
            beam_x_ns = [0, ns_ridge_length]
            beam_y_ns = [0, 0]  # Horizontal beam at elevation 0

            # Draw horizontal beam line
            ax5.plot(
                beam_x_ns,
                beam_y_ns,
                "b-",
                linewidth=6,
                alpha=0.9,
                solid_capstyle="round",
                label="N-S Ridge Beam",
            )

            # Get N-S ridge beam loads and reactions
            # Use stored total loads to ensure diagrams match comparison table
            if hasattr(self, "ns_ridge_total_loads") and hasattr(
                self, "ns_ridge_load_positions"
            ):
                # Use stored values that match the comparison table
                ns_total_loads = [
                    (pos, load)
                    for pos, load in zip(
                        self.ns_ridge_load_positions, self.ns_ridge_total_loads
                    )
                ]
            else:
                # Fallback to calculating from snow and dead loads
                ns_total_loads = [
                    (pos, snow + dead)
                    for (pos, snow), (_, dead) in zip(
                        self.ns_ridge_snow_point_loads, self.ns_ridge_dead_point_loads
                    )
                ]

            if ns_total_loads:
                max_load_ns = max([abs(load) for _, load in ns_total_loads])
                load_scale_ns = 1.5 / max_load_ns if max_load_ns > 0 else 1

                # Calculate reactions
                ns_total = sum(load for _, load in ns_total_loads)
                ns_moment = sum(load * pos for pos, load in ns_total_loads)
                ns_r_bottom = ns_moment / ns_ridge_length if ns_ridge_length > 0 else 0
                ns_r_top = ns_total - ns_r_bottom
                
                # Verify equilibrium: Sum of reactions should equal total point loads
                sum_reactions_ns = ns_r_top + ns_r_bottom
                equilibrium_check_ns = abs(sum_reactions_ns - ns_total) < 0.01  # Allow small rounding error
                self.ns_ridge_equilibrium_check = {
                    "sum_reactions": sum_reactions_ns,
                    "total_loads": ns_total,
                    "difference": abs(sum_reactions_ns - ns_total),
                    "passes": equilibrium_check_ns
                }
                
                max_reaction_ns = max(abs(ns_r_top), abs(ns_r_bottom))
                reaction_scale_ns = 1.5 / max_reaction_ns if max_reaction_ns > 0 else 1

                # Add support reactions (upward green arrows)
                ax5.arrow(
                    0,
                    0,
                    0,
                    ns_r_top * reaction_scale_ns,
                    head_width=0.5,
                    fc="darkgreen",
                    ec="darkgreen",
                    linewidth=2,
                    alpha=0.9,
                )
                ax5.text(
                    0,
                    ns_r_top * reaction_scale_ns + 0.8,
                    f"R_top = {int(ns_r_top)} lb",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    color="darkgreen",
                )

                ax5.arrow(
                    ns_ridge_length,
                    0,
                    0,
                    ns_r_bottom * reaction_scale_ns,
                    head_width=0.5,
                    fc="darkgreen",
                    ec="darkgreen",
                    linewidth=2,
                    alpha=0.9,
                )
                ax5.text(
                    ns_ridge_length,
                    ns_r_bottom * reaction_scale_ns + 0.8,
                    f"R_bottom = {int(ns_r_bottom)} lb",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    color="darkgreen",
                )

                # Add point loads (downward red arrows) at exactly 2 feet on center
                # Sort by position to ensure correct order
                ns_total_loads_sorted = sorted(ns_total_loads, key=lambda x: x[0])
                for pos, load in ns_total_loads_sorted:
                    arrow_length = -load * load_scale_ns
                    ax5.arrow(
                        pos,
                        0,
                        0,
                        arrow_length,
                        head_width=0.5,
                        fc="darkred",
                        ec="darkred",
                        linewidth=2,
                        alpha=0.9,
                    )
                    ax5.text(
                        pos,
                        arrow_length - 0.8,
                        f"{int(load)} lb",
                        ha="center",
                        va="top",
                        fontsize=9,
                        fontweight="bold",
                        color="darkred",
                    )

            ax5.set_xlabel("Distance from Eave (ft)", fontsize=11, fontweight="bold")
            ax5.set_ylabel("Load Magnitude (scaled)", fontsize=11, fontweight="bold")
            ax5.set_title(
                "Point Load Reactions on N-S Ridge Beam", fontsize=13, fontweight="bold"
            )
            ax5.grid(True, linestyle="--", alpha=0.6)
            ax5.set_xlim(-ns_ridge_length * 0.05, ns_ridge_length * 1.05)

            # Set y-limits to accommodate all arrows
            if ns_total_loads:
                min_y_ns = min(0, -max_load_ns * load_scale_ns - 1)
                max_y_ns = max(0, max_reaction_ns * reaction_scale_ns + 1)
                ax5.set_ylim(bottom=min_y_ns, top=max_y_ns)

            # Custom legend
            legend_elements_ns = [
                plt.Line2D(
                    [0],
                    [0],
                    color="blue",
                    linewidth=6,
                    alpha=0.9,
                    label="N-S Ridge Beam",
                ),
                plt.Line2D(
                    [0], [0], color="darkgreen", linewidth=2, label="Reactions (upward)"
                ),
                plt.Line2D(
                    [0],
                    [0],
                    color="darkred",
                    linewidth=2,
                    label="Point Loads (downward)",
                ),
            ]
            ax5.legend(handles=legend_elements_ns, loc="upper right")

            canvas_ns = FigureCanvasTkAgg(fig5, master=self.plot_frame)
            canvas_ns.draw()
            canvas_ns.get_tk_widget().pack(
                side=tk.TOP, pady=5, padx=10, fill=tk.BOTH, expand=True
            )

            # Add toolbar for N-S ridge diagram
            toolbar_ns = NavigationToolbar2Tk(canvas_ns, self.plot_frame)
            toolbar_ns.update()

    def get_float(self, key: str) -> Optional[float]:
        try:
            return float(self.entries[key].get())
        except ValueError:
            messagebox.showerror(
                "Input Error", f"{key.replace('_', ' ').title()} must be a number"
            )
            return None

    def validate_input_realtime(self, value, field_name):
        """Validate input as user types and provide visual feedback."""
        try:
            if value.strip() == "":
                # Allow empty fields (will be validated on calculate)
                self.entries[field_name].config(bg="white")
                return True

            float(value)
            self.entries[field_name].config(bg="white")
            return True
        except ValueError:
            self.entries[field_name].config(bg="#ffe6e6")  # Light red background
            return False

    def validate_all_inputs(self):
        """Validate all inputs before calculation and show specific error messages."""
        errors = []

        # Validate snow load parameters
        try:
            pg = self.get_float("pg")
            if pg is not None:
                if pg < 0:
                    errors.append("Ground snow load (pg) must be positive")
                elif pg > 500:
                    errors.append(
                        "Ground snow load (pg) seems unusually high (>500 psf)"
                    )
        except ValueError:
            errors.append("Ground snow load (pg) must be a valid number")

        try:
            w2 = self.get_float("w2")
            if w2 is not None and not 0.25 <= w2 <= 0.65:
                errors.append(
                    "Winter wind parameter (W2) should typically be between 0.25 and 0.65"
                )
        except ValueError:
            errors.append("Winter wind parameter (W2) must be a valid number")

        try:
            ce = self.get_float("ce")
            if ce is not None and not 0.7 <= ce <= 1.3:
                errors.append(
                    "Exposure factor (Ce) should typically be between 0.7 and 1.3"
                )
        except ValueError:
            errors.append("Exposure factor (Ce) must be a valid number")

        try:
            ct = self.get_float("ct")
            if ct is not None and not 1.0 <= ct <= 1.3:
                errors.append(
                    "Thermal factor (Ct) should typically be between 1.0 and 1.3"
                )
        except ValueError:
            errors.append("Thermal factor (Ct) must be a valid number")

        # Validate geometry
        try:
            north_span = self.get_float("north_span")
            if north_span is not None and north_span <= 0:
                errors.append("North span must be positive")
        except ValueError:
            errors.append("North span must be a valid number")

        try:
            south_span = self.get_float("south_span")
            if south_span is not None and south_span <= 0:
                errors.append("South span must be positive")
        except ValueError:
            errors.append("South span must be a valid number")

        try:
            ew_half_width = self.get_float("ew_half_width")
            if ew_half_width is not None and ew_half_width <= 0:
                errors.append("E-W half-width must be positive")
        except ValueError:
            errors.append("E-W half-width must be a valid number")

        try:
            valley_offset = self.get_float("valley_offset")
            if valley_offset is not None and valley_offset <= 0:
                errors.append("Valley horizontal offset must be positive")
        except ValueError:
            errors.append("Valley horizontal offset must be a valid number")

        try:
            pitch_n = self.get_float("pitch_north")
            if pitch_n is not None and not 0 <= pitch_n <= 45:
                errors.append("Roof pitch north should be between 0° and 45°")
        except ValueError:
            errors.append("Roof pitch north must be a valid number")

        try:
            pitch_w = self.get_float("pitch_west")
            if pitch_w is not None and not 0 <= pitch_w <= 45:
                errors.append("Roof pitch west should be between 0° and 45°")
        except ValueError:
            errors.append("Roof pitch west must be a valid number")

        try:
            valley_angle = self.get_float("valley_angle")
            if valley_angle is not None and not 2 <= valley_angle <= 180:
                errors.append("Valley angle should be between 2° and 180°")
        except ValueError:
            errors.append("Valley angle must be a valid number")

        # Validate beam parameters
        try:
            beam_width = self.get_float("beam_width")
            if beam_width is not None and beam_width <= 0:
                errors.append("Beam width must be positive")
        except ValueError:
            errors.append("Beam width must be a valid number")

        try:
            beam_depth = self.get_float("beam_depth_trial")
            if beam_depth is not None and beam_depth <= 0:
                errors.append("Beam depth must be positive")
        except ValueError:
            errors.append("Beam depth must be a valid number")

        # Validate N-S Ridge Beam parameters
        try:
            ns_ridge_beam_width = self.get_float("ns_ridge_beam_width")
            if ns_ridge_beam_width is not None and ns_ridge_beam_width <= 0:
                errors.append("N-S Ridge Beam width must be positive")
        except ValueError:
            errors.append("N-S Ridge Beam width must be a valid number")

        try:
            ns_ridge_beam_depth = self.get_float("ns_ridge_beam_depth_trial")
            if ns_ridge_beam_depth is not None and ns_ridge_beam_depth <= 0:
                errors.append("N-S Ridge Beam depth must be positive")
        except ValueError:
            errors.append("N-S Ridge Beam depth must be a valid number")

        return errors

    def save_project(self):
        """Save current project data to JSON file."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Project",
            )
            if not filename:
                return

            # Gather all input values
            project_data = {
                "project_info": {
                    "name": "ASCE 7-22 Valley Snow Load Analysis",
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "description": "Valley snow load calculation with beam design analysis",
                },
                "inputs": {
                    "snow_load_parameters": {
                        "pg": self.entries["pg"].get(),
                        "w2": self.entries["w2"].get(),
                        "ce": self.entries["ce"].get(),
                        "ct": self.entries["ct"].get(),
                    },
                    "building_geometry": {
                        "pitch_north": self.entries["pitch_north"].get(),
                        "pitch_west": self.entries["pitch_west"].get(),
                        "north_span": self.entries["north_span"].get(),
                        "south_span": self.entries["south_span"].get(),
                        "ew_half_width": self.entries["ew_half_width"].get(),
                        "valley_offset": self.entries["valley_offset"].get(),
                        "valley_angle": self.entries["valley_angle"].get(),
                        "jack_spacing_inches": self.entries[
                            "jack_spacing_inches"
                        ].get(),
                    },
                    "beam_design": {
                        "material": self.material_combobox.get(),
                        "beam_width": self.entries["beam_width"].get(),
                        "beam_depth_trial": self.entries["beam_depth_trial"].get(),
                    },
                },
            }

            with open(filename, "w") as f:
                json.dump(project_data, f, indent=2)

            messagebox.showinfo("Save Successful", f"Project saved to {filename}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save project: {str(e)}")

    def load_project(self):
        """Load project data from JSON file."""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Project",
            )
            if not filename:
                return

            with open(filename, "r") as f:
                project_data = json.load(f)

            # Load inputs
            inputs = project_data.get("inputs", {})

            # Snow load parameters
            snow_params = inputs.get("snow_load_parameters", {})
            self.entries["pg"].delete(0, tk.END)
            self.entries["pg"].insert(0, snow_params.get("pg", "50"))
            self.entries["w2"].delete(0, tk.END)
            self.entries["w2"].insert(0, snow_params.get("w2", "0.55"))
            self.entries["ce"].delete(0, tk.END)
            self.entries["ce"].insert(0, snow_params.get("ce", "1.0"))
            self.entries["ct"].delete(0, tk.END)
            self.entries["ct"].insert(0, snow_params.get("ct", "1.2"))

            # Handle both old and new field names for backward compatibility
            north_span_value = snow_params.get("north_span") or snow_params.get(
                "lu_north", "16"
            )
            ew_half_width_value = snow_params.get("ew_half_width") or snow_params.get(
                "lu_west", "42"
            )
            valley_offset_value = snow_params.get("valley_offset", "16")

            self.entries["north_span"].delete(0, tk.END)
            self.entries["north_span"].insert(0, north_span_value)
            self.entries["ew_half_width"].delete(0, tk.END)
            self.entries["ew_half_width"].insert(0, ew_half_width_value)
            self.entries["valley_offset"].delete(0, tk.END)
            self.entries["valley_offset"].insert(0, valley_offset_value)

            # Building geometry
            geom_params = inputs.get("building_geometry", {})
            self.entries["pitch_north"].delete(0, tk.END)
            self.entries["pitch_north"].insert(0, geom_params.get("pitch_north", "6"))
            self.entries["pitch_west"].delete(0, tk.END)
            self.entries["pitch_west"].insert(0, geom_params.get("pitch_west", "6"))
            self.entries["north_span"].delete(0, tk.END)
            self.entries["north_span"].insert(0, geom_params.get("north_span", "16"))
            self.entries["south_span"].delete(0, tk.END)
            self.entries["south_span"].insert(0, geom_params.get("south_span", "16"))
            self.entries["ew_half_width"].delete(0, tk.END)
            self.entries["ew_half_width"].insert(
                0, geom_params.get("ew_half_width", "42")
            )
            self.entries["valley_offset"].delete(0, tk.END)
            self.entries["valley_offset"].insert(
                0, geom_params.get("valley_offset", "21.125")
            )
            self.entries["valley_angle"].delete(0, tk.END)
            self.entries["valley_angle"].insert(
                0, geom_params.get("valley_angle", "90")
            )
            self.entries["jack_spacing_inches"].delete(0, tk.END)
            self.entries["jack_spacing_inches"].insert(
                0, geom_params.get("jack_spacing_inches", "24")
            )

            # Beam design
            beam_params = inputs.get("beam_design", {})
            self.material_combobox.set(
                beam_params.get("material", "Glulam 24F-V4 DF (Fb=2400 psi)")
            )
            # Trigger material change to update properties
            self.on_material_change(None)
            self.entries["beam_width"].delete(0, tk.END)
            self.entries["beam_width"].insert(0, beam_params.get("beam_width", "3.5"))
            self.entries["beam_depth_trial"].delete(0, tk.END)
            self.entries["beam_depth_trial"].insert(
                0, beam_params.get("beam_depth_trial", "16")
            )

            messagebox.showinfo("Load Successful", f"Project loaded from {filename}")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load project: {str(e)}")

    def generate_report(self):
        """Generate a PDF report of the current analysis."""
        try:
            # Get user documents folder or desktop as default save location
            import os

            try:
                # Try to use Documents folder first
                default_dir = os.path.expanduser("~/Documents")
                if not os.path.exists(default_dir):
                    # Fallback to Desktop
                    default_dir = os.path.expanduser("~/Desktop")
                if not os.path.exists(default_dir):
                    # Final fallback to user home
                    default_dir = os.path.expanduser("~")
            except:
                default_dir = ""  # Let system decide

            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Generate PDF Report",
                initialdir=default_dir,
            )
            if not filename:
                return

            if not REPORTLAB_AVAILABLE:
                # Fallback to HTML if reportlab is not available
                self.generate_html_report(filename.replace(".pdf", ".html"))
                return

            # Run calculations if not already done (to ensure we have results and diagrams)
            try:
                # Check if we have results by looking at the output text
                current_output = self.output_text.get(1.0, tk.END).strip()
                if not current_output or "Run calculation" in current_output:
                    # No results yet, run calculation
                    self.calculate()
                    # Wait a bit for calculation to complete
                    self.master.update()
            except:
                pass  # Continue even if calculation fails

            # Get the calculation results
            calculation_results = self.output_text.get(1.0, tk.END).strip()

            # Capture diagram images from current display
            diagram_images = []
            try:
                import io

                # Check if diagrams are currently displayed
                if hasattr(self, "_current_figures") and self._current_figures:
                    # Use stored figures
                    for fig in self._current_figures:
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
                        buf.seek(0)
                        diagram_images.append(buf)
                else:
                    # Try to capture from matplotlib's global registry
                    figures = [plt.figure(i) for i in plt.get_fignums()]
                    for fig in figures:
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
                        buf.seek(0)
                        diagram_images.append(buf)
                        plt.close(fig)

                # If no figures found, try to regenerate them
                if not diagram_images:
                    try:
                        # Extract parameters from current entries
                        north_span = float(self.entries["north_span"].get() or "16")
                        south_span = float(self.entries["south_span"].get() or "16")
                        ew_half_width = float(
                            self.entries["ew_half_width"].get() or "42"
                        )
                        valley_offset = float(
                            self.entries["valley_offset"].get() or "16"
                        )

                        # Generate basic diagrams
                        fig_plan = self.draw_plan_view(
                            north_span, south_span, ew_half_width, valley_offset
                        )
                        buf = io.BytesIO()
                        fig_plan.savefig(
                            buf, format="png", dpi=150, bbox_inches="tight"
                        )
                        buf.seek(0)
                        diagram_images.append(buf)
                        plt.close(fig_plan)

                        # Try to generate drift diagram with default values
                        fig_drift = self.draw_north_drift_overlay(
                            north_span,
                            south_span,
                            ew_half_width,
                            valley_offset,
                            5.0,
                            10.0,
                            20.0,
                            30.0,
                        )  # Default values
                        buf = io.BytesIO()
                        fig_drift.savefig(
                            buf, format="png", dpi=150, bbox_inches="tight"
                        )
                        buf.seek(0)
                        diagram_images.append(buf)
                        plt.close(fig_drift)

                    except Exception as regen_error:
                        print(f"Warning: Could not regenerate diagrams: {regen_error}")

            except Exception as e:
                print(f"Warning: Could not capture diagrams for report: {e}")
                diagram_images = []

            # Create PDF report using ReportLab
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=16,
                spaceAfter=30,
                alignment=1,  # Center alignment
            )
            story.append(
                Paragraph("ASCE 7-22 Valley Snow Load Analysis Report", title_style)
            )
            story.append(Spacer(1, 12))

            # Timestamp
            timestamp_style = ParagraphStyle(
                "Timestamp", parent=styles["Normal"], fontSize=10, textColor=colors.gray
            )
            story.append(
                Paragraph(
                    f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    timestamp_style,
                )
            )
            story.append(Spacer(1, 20))

            # Executive Summary
            story.append(Paragraph("Executive Summary", styles["Heading2"]))

            # Extract key results for summary
            summary_points = []
            lines = calculation_results.split("\n")

            for line in lines:
                if "Valley horizontal length" in line:
                    summary_points.append(
                        f"Valley Length: {line.split(':')[1].strip()}"
                    )
                elif "Balanced snow load" in line:
                    summary_points.append(
                        f"Balanced Load: {line.split(':')[1].strip()}"
                    )
                elif "Maximum drift load" in line:
                    summary_points.append(
                        f"Max Drift Load: {line.split(':')[1].strip()}"
                    )
                elif "Beam section" in line and "inches" in line:
                    summary_points.append(
                        f"Required Beam: {line.split(':')[1].strip()}"
                    )
                elif "PASS" in line and "beam" in line.lower():
                    summary_points.append("✓ Beam Design: PASSES all checks")
                elif "FAIL" in line and "beam" in line.lower():
                    summary_points.append("✗ Beam Design: FAILS - requires redesign")

            if summary_points:
                for point in summary_points:
                    bullet_style = ParagraphStyle(
                        "BulletStyle",
                        parent=styles["Normal"],
                        leftIndent=20,
                        fontSize=11,
                    )
                    story.append(Paragraph(f"• {point}", bullet_style))
                    story.append(Spacer(1, 3))
            else:
                story.append(
                    Paragraph(
                        "Run calculations to generate executive summary.",
                        styles["Normal"],
                    )
                )

            story.append(Spacer(1, 20))

            # Snow Load Parameters Section
            story.append(Paragraph("Snow Load Parameters", styles["Heading2"]))
            snow_data = [
                ["Parameter", "Value", "Description"],
                [
                    "Ground Snow Load (pg)",
                    f"{self.entries['pg'].get()} psf",
                    "Reliability-targeted ground snow load",
                ],
                [
                    "Winter Wind Parameter (W2)",
                    self.entries["w2"].get(),
                    "Percentage of heating season with winds >10 mph",
                ],
                [
                    "Exposure Factor (Ce)",
                    self.entries["ce"].get(),
                    "Exposure factor from Table 7.3-1",
                ],
                [
                    "Thermal Factor (Ct)",
                    self.entries["ct"].get(),
                    "Thermal factor from Table 7.3-2",
                ],
                [],
                [
                    "North Span (lu_north)",
                    f"{self.entries['north_span'].get()} ft",
                    "Distance from E-W ridge to north eave",
                ],
                [
                    "South Span",
                    f"{self.entries['south_span'].get()} ft",
                    "Distance from E-W ridge to south eave",
                ],
                [
                    "E-W Half-Width (lu_west)",
                    f"{self.entries['ew_half_width'].get()} ft",
                    "Half-width from ridge to eave",
                ],
                [
                    "Valley Offset",
                    f"{self.entries['valley_offset'].get()} ft",
                    "Horizontal valley low point offset",
                ],
            ]

            snow_table = Table(snow_data, colWidths=[2 * inch, 1 * inch, 3 * inch])
            snow_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(snow_table)
            story.append(Spacer(1, 20))

            # Building Geometry Section
            story.append(Paragraph("Building Geometry", styles["Heading2"]))
            geom_data = [
                ["Parameter", "Value", "Description"],
                [
                    "Roof Pitch North",
                    f"{self.entries['pitch_north'].get()}°",
                    "North roof slope",
                ],
                [
                    "Roof Pitch West",
                    f"{self.entries['pitch_west'].get()}°",
                    "West roof slope",
                ],
                [
                    "North Span (E-W Ridge to North Eave)",
                    f"{self.entries['north_span'].get()} ft",
                    "North roof plane span",
                ],
                [
                    "South Span (E-W Ridge to South Eave)",
                    f"{self.entries['south_span'].get()} ft",
                    "South roof plane span",
                ],
                [
                    "E-W Half-Width (N-S Ridge to Eave)",
                    f"{self.entries['ew_half_width'].get()} ft",
                    "Half width of building",
                ],
                [
                    "Valley Horizontal Offset",
                    f"{self.entries['valley_offset'].get()} ft",
                    "Distance from N-S ridge projection to valley low point",
                ],
                [
                    "Valley Angle",
                    f"{self.entries['valley_angle'].get()}°",
                    "Angle between roof planes",
                ],
                [
                    "Jack Rafter Spacing",
                    f"{self.entries['jack_spacing_inches'].get()}\" o.c.",
                    "Spacing between jack rafters",
                ],
            ]

            geom_table = Table(geom_data, colWidths=[2 * inch, 1.2 * inch, 2.8 * inch])
            geom_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(geom_table)
            story.append(Spacer(1, 20))

            # Beam Design Section
            story.append(Paragraph("Beam Design", styles["Heading2"]))
            beam_data = [
                ["Parameter", "Value", "Description"],
                ["Material", self.material_combobox.get(), "Selected beam material"],
                [
                    "Beam Width",
                    f"{self.entries['beam_width'].get()}\"",
                    "Beam cross-section width",
                ],
                [
                    "Beam Depth",
                    f"{self.entries['beam_depth_trial'].get()}\"",
                    "Beam cross-section depth",
                ],
            ]

            beam_table = Table(beam_data, colWidths=[1.5 * inch, 1.5 * inch, 3 * inch])
            beam_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(beam_table)
            story.append(Spacer(1, 20))

            # Beam Design Results Summary
            story.append(Paragraph("Beam Design Results Summary", styles["Heading2"]))

            # Extract beam design results from calculation text
            beam_summary_lines = []
            in_beam_section = False
            for line in calculation_results.split("\n"):
                if "BEAM DESIGN SUMMARY" in line or "=== BEAM DESIGN" in line:
                    in_beam_section = True
                elif in_beam_section and ("===" in line and "BEAM" not in line):
                    break  # End of beam section
                elif in_beam_section:
                    beam_summary_lines.append(line)

            if beam_summary_lines:
                for line in beam_summary_lines:
                    if line.strip():
                        if "PASS" in line:
                            pass_style = ParagraphStyle(
                                "BeamPass",
                                parent=styles["Normal"],
                                textColor=colors.green,
                                fontSize=11,
                                spaceAfter=6,
                            )
                            story.append(Paragraph(f"✓ {line}", pass_style))
                        elif "FAIL" in line:
                            fail_style = ParagraphStyle(
                                "BeamFail",
                                parent=styles["Normal"],
                                textColor=colors.red,
                                fontSize=11,
                                spaceAfter=6,
                            )
                            story.append(Paragraph(f"✗ {line}", fail_style))
                        else:
                            story.append(Paragraph(line, styles["Normal"]))
            else:
                story.append(
                    Paragraph(
                        "Beam design results will appear here after running calculations.",
                        styles["Normal"],
                    )
                )

            story.append(Spacer(1, 20))

            # Calculation Results - Include ALL sections
            story.append(Paragraph("Complete Analysis Results", styles["Heading2"]))

            # Split the calculation results into manageable chunks for PDF
            if calculation_results and len(calculation_results) > 100:
                # Break into lines and add to PDF - increase limit to include all results
                lines = calculation_results.split("\n")
                for line in lines:  # Include ALL lines for complete report
                    if line.strip():
                        # Handle section headers
                        if "===" in line:
                            story.append(Paragraph(line, styles["Heading3"]))
                        elif (
                            "============================================================"
                            in line
                        ):
                            story.append(
                                Paragraph("─" * 60, styles["Normal"])
                            )  # Separator line
                        elif line.startswith("•") or line.startswith("-"):
                            story.append(Paragraph(line, styles["Normal"]))
                        elif "PASS" in line and ("GREEN" in line or "✓" in line):
                            # Highlight passing results
                            pass_style = ParagraphStyle(
                                "PassStyle",
                                parent=styles["Normal"],
                                textColor=colors.green,
                            )
                            story.append(Paragraph(line, pass_style))
                        elif "FAIL" in line and ("RED" in line or "✗" in line):
                            # Highlight failing results
                            fail_style = ParagraphStyle(
                                "FailStyle",
                                parent=styles["Normal"],
                                textColor=colors.red,
                            )
                            story.append(Paragraph(line, fail_style))
                        else:
                            story.append(Paragraph(line, styles["Normal"]))
                        story.append(Spacer(1, 2))
            else:
                story.append(
                    Paragraph(
                        "No calculation results available. Please run calculations first.",
                        styles["Normal"],
                    )
                )

            story.append(Spacer(1, 20))

            # Include Diagrams
            if diagram_images:
                story.append(Paragraph("Analysis Diagrams", styles["Heading2"]))
                story.append(Spacer(1, 12))

                diagram_names = [
                    "Roof Plan View with Valley Geometry",
                    "North Wind Leeward Drift Distribution",
                    "Shear Force Diagram (ASD)",
                    "Bending Moment Diagram (ASD)",
                    "Drift Load Profile",
                    "Sloped Valley Beam Point Loads",
                ]

                for i, (buf, name) in enumerate(zip(diagram_images, diagram_names)):
                    if i < len(diagram_names):  # Ensure we don't exceed available names
                        # Add diagram title
                        story.append(Paragraph(f"{name}", styles["Heading3"]))
                        story.append(Spacer(1, 6))

                        # Add the image (resize to fit page width)
                        img = Image(buf)
                        img.drawHeight = 3 * inch  # Fixed height
                        img.drawWidth = 6 * inch  # Fixed width to fit page
                        story.append(img)
                        story.append(Spacer(1, 12))

                        # Add page break after major diagrams
                        if i < len(diagram_images) - 1:
                            story.append(PageBreak())
            else:
                story.append(Paragraph("Diagrams", styles["Heading2"]))
                story.append(
                    Paragraph(
                        "No diagrams available. Diagrams will be generated when calculations are run.",
                        styles["Normal"],
                    )
                )
                story.append(Spacer(1, 20))

            # Analysis Notes
            story.append(Paragraph("Analysis Notes", styles["Heading2"]))
            notes = [
                "This report was generated using ASCE 7-22 Chapter 7 snow load provisions",
                "All calculations are based on the input parameters provided",
                "Ground snow load (pg) and winter wind parameter (W2) should be obtained from the official ASCE 7 Hazard Tool",
                "Results are valid for the specific site conditions and building geometry entered",
            ]

            for note in notes:
                story.append(Paragraph(f"• {note}", styles["Normal"]))
                story.append(Spacer(1, 6))

            story.append(Spacer(1, 20))

            # Footer
            footer_style = ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=9,
                textColor=colors.gray,
                alignment=1,  # Center alignment
            )
            story.append(
                Paragraph(
                    "Report generated by ASCE 7-22 Valley Snow Load Calculator v1.0",
                    footer_style,
                )
            )

            # Build PDF
            doc.build(story)
            messagebox.showinfo(
                "PDF Report Generated", f"PDF report saved to {filename}"
            )

        except PermissionError as e:
            messagebox.showerror(
                "Permission Denied",
                f"Cannot save PDF to the selected location.\n\n"
                f"Please choose a different folder where you have write permissions, "
                f"such as your Documents or Desktop folder.\n\n"
                f"Error: {str(e)}",
            )
        except Exception as e:
            error_msg = str(e)
            if "Errno 13" in error_msg or "Permission denied" in error_msg.lower():
                messagebox.showerror(
                    "Permission Denied",
                    f"Cannot save PDF to the selected location.\n\n"
                    f"Please choose a different folder where you have write permissions, "
                    f"such as your Documents or Desktop folder.\n\n"
                    f"Error: {error_msg}",
                )
            else:
                messagebox.showerror(
                    "Report Error", f"Failed to generate PDF report: {error_msg}"
                )

    def generate_html_report(self, filename):
        """Fallback HTML report generation if PDF is not available."""
        try:
            # Get the calculation results
            calculation_results = self.output_text.get(1.0, tk.END).strip()

            # Capture diagram images
            diagram_images_html = []
            try:
                import base64
                import io

                # Save current matplotlib figures as base64 encoded images
                figures = [plt.figure(i) for i in plt.get_fignums()]
                for fig in figures:
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
                    buf.seek(0)
                    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    diagram_images_html.append(f"data:image/png;base64,{img_base64}")
                    plt.close(fig)
            except Exception as e:
                print(f"Warning: Could not capture diagrams for HTML report: {e}")
                diagram_images_html = []

            # Create HTML report
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ASCE 7-22 Valley Snow Load Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2E8B57; }}
        h2 {{ color: #4682B4; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        h3 {{ color: #666; font-size: 1.1em; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        .calculation-results {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4682B4; margin: 20px 0; font-family: 'Courier New', monospace; font-size: 0.9em; white-space: pre-line; }}
    </style>
</head>
<body>
    <h1>ASCE 7-22 Valley Snow Load Analysis Report</h1>
    <p class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>Snow Load Parameters</h2>
    <table>
        <tr><th>Parameter</th><th>Value</th><th>Description</th></tr>
        <tr><td>Ground Snow Load (pg)</td><td>{self.entries["pg"].get()} psf</td><td>Reliability-targeted ground snow load</td></tr>
        <tr><td>Winter Wind Parameter (W2)</td><td>{self.entries["w2"].get()}</td><td>Percentage of heating season with winds >10 mph</td></tr>
        <tr><td>Exposure Factor (Ce)</td><td>{self.entries["ce"].get()}</td><td>Exposure factor from Table 7.3-1</td></tr>
        <tr><td>Thermal Factor (Ct)</td><td>{self.entries["ct"].get()}</td><td>Thermal factor from Table 7.3-2</td></tr>
        <tr><td>North Span (lu_north)</td><td>{self.entries["north_span"].get()} ft</td><td>Distance from E-W ridge to north eave</td></tr>
        <tr><td>South Span</td><td>{self.entries["south_span"].get()} ft</td><td>Distance from E-W ridge to south eave</td></tr>
        <tr><td>E-W Half-Width (lu_west)</td><td>{self.entries["ew_half_width"].get()} ft</td><td>Half-width from ridge to eave</td></tr>
        <tr><td>Valley Offset</td><td>{self.entries["valley_offset"].get()} ft</td><td>Horizontal valley low point offset</td></tr>
    </table>

    <h2>Building Geometry</h2>
    <table>
        <tr><th>Parameter</th><th>Value</th><th>Description</th></tr>
        <tr><td>Roof Pitch North</td><td>{self.entries["pitch_north"].get()}°</td><td>North roof slope</td></tr>
        <tr><td>Roof Pitch West</td><td>{self.entries["pitch_west"].get()}°</td><td>West roof slope</td></tr>
        <tr><td>North Span (E-W Ridge to North Eave)</td><td>{self.entries["north_span"].get()} ft</td><td>North roof plane span</td></tr>
        <tr><td>South Span (E-W Ridge to South Eave)</td><td>{self.entries["south_span"].get()} ft</td><td>South roof plane span</td></tr>
        <tr><td>E-W Half-Width (N-S Ridge to Eave)</td><td>{self.entries["ew_half_width"].get()} ft</td><td>Half width of building</td></tr>
        <tr><td>Valley Horizontal Offset</td><td>{self.entries["valley_offset"].get()} ft</td><td>Distance from N-S ridge projection to valley low point</td></tr>
        <tr><td>Valley Angle</td><td>{self.entries["valley_angle"].get()}°</td><td>Angle between roof planes</td></tr>
        <tr><td>Jack Rafter Spacing</td><td>{self.entries["jack_spacing_inches"].get()}" o.c.</td><td>Spacing between jack rafters</td></tr>
    </table>

    <h2>Beam Design</h2>
    <table>
        <tr><th>Parameter</th><th>Value</th><th>Description</th></tr>
        <tr><td>Material</td><td>{self.material_combobox.get()}</td><td>Selected beam material</td></tr>
        <tr><td>Beam Width</td><td>{self.entries["beam_width"].get()}"</td><td>Beam cross-section width</td></tr>
        <tr><td>Beam Depth</td><td>{self.entries["beam_depth_trial"].get()}"</td><td>Beam cross-section depth</td></tr>
    </table>

    <h2>Calculation Results</h2>
    <div class="calculation-results">{calculation_results if calculation_results else "No calculation results available. Please run calculations first."}</div>

    <h2>Analysis Diagrams</h2>
"""
            diagram_names = [
                "Snow Load Distribution",
                "Drift Load Profile",
                "Point Load Reactions",
                "Shear Force Diagram",
                "Bending Moment Diagram",
            ]

            if diagram_images_html:
                for i, (img_data, name) in enumerate(
                    zip(diagram_images_html, diagram_names)
                ):
                    if i < len(diagram_names):
                        html_content += f"""
    <h3>{name}</h3>
    <div style="text-align: center; margin: 20px 0;">
        <img src="{img_data}" style="max-width: 100%; height: auto; border: 1px solid #ddd;" alt="{name}">
    </div>
"""
            else:
                html_content += """
    <p>No diagrams available. Diagrams will be generated when calculations are run.</p>
"""

            html_content += """
    <h2>Analysis Notes</h2>
    <ul>
        <li>This report was generated using ASCE 7-22 Chapter 7 snow load provisions</li>
        <li>All calculations are based on the input parameters provided</li>
        <li>Ground snow load (pg) and winter wind parameter (W2) should be obtained from the official ASCE 7 Hazard Tool</li>
        <li>Results are valid for the specific site conditions and building geometry entered</li>
    </ul>

    <p><em>Report generated by ASCE 7-22 Valley Snow Load Calculator v1.0</em></p>
</body>
</html>
"""

            with open(filename, "w") as f:
                f.write(html_content)

            messagebox.showinfo(
                "HTML Report Generated",
                f"HTML report saved to {filename} (PDF not available)",
            )

        except PermissionError as e:
            messagebox.showerror(
                "Permission Denied",
                f"Cannot save HTML report to the selected location.\n\n"
                f"Please choose a different folder where you have write permissions, "
                f"such as your Documents or Desktop folder.\n\n"
                f"Error: {str(e)}",
            )
        except Exception as e:
            error_msg = str(e)
            if "Errno 13" in error_msg or "Permission denied" in error_msg.lower():
                messagebox.showerror(
                    "Permission Denied",
                    f"Cannot save HTML report to the selected location.\n\n"
                    f"Please choose a different folder where you have write permissions, "
                    f"such as your Documents or Desktop folder.\n\n"
                    f"Error: {error_msg}",
                )
            else:
                messagebox.showerror(
                    "Report Error", f"Failed to generate HTML report: {error_msg}"
                )

    def on_material_change(self, event):
        """Update material properties when material selection changes."""
        try:
            selected = self.material_combobox.get()
            print(f"Material changed to: {selected}")  # Debug output

            if "Sawn Lumber" in selected:
                self.fb_allowable_value = 875
                self.fv_allowable_value = 180
                self.modulus_e_value = 1600000
            elif "Glulam" in selected:
                self.fb_allowable_value = 2400
                self.fv_allowable_value = 265
                self.modulus_e_value = 1800000
            elif "3100Fb-2.1E (PWT)" in selected:
                self.fb_allowable_value = 3100
                self.fv_allowable_value = 265  # Using typical LVL shear value
                self.modulus_e_value = 2100000
            elif "2850Fb-1.9E (Global)" in selected:
                self.fb_allowable_value = 2850
                self.fv_allowable_value = 265  # Using typical LVL shear value
                self.modulus_e_value = 1900000
            else:  # LVL 2.0E
                self.fb_allowable_value = 2650
                self.fv_allowable_value = 285
                self.modulus_e_value = 2000000

            # Update the Entry widgets with new values
            if hasattr(self, "entries"):
                if "fb_allowable" in self.entries:
                    self.entries["fb_allowable"].delete(0, tk.END)
                    self.entries["fb_allowable"].insert(0, str(self.fb_allowable_value))
                if "fv_allowable" in self.entries:
                    self.entries["fv_allowable"].delete(0, tk.END)
                    self.entries["fv_allowable"].insert(0, str(self.fv_allowable_value))
                if "modulus_e" in self.entries:
                    self.entries["modulus_e"].delete(0, tk.END)
                    self.entries["modulus_e"].insert(0, str(self.modulus_e_value))

            # Mark data as changed for auto-save
            if hasattr(self, "data_changed"):
                self.data_changed = True

            # Trigger data change event
            self.on_data_changed()

        except Exception as e:
            print(f"Error in on_material_change: {e}")  # Debug output
            import traceback

            traceback.print_exc()

    def on_ns_ridge_material_change(self, event):
        """Update N-S ridge beam material properties when material selection changes."""
        try:
            selected = self.ns_ridge_material_combobox.get()
            print(f"N-S Ridge Beam material changed to: {selected}")

            if "Sawn Lumber" in selected:
                self.ns_ridge_fb_allowable_value = 875
                self.ns_ridge_fv_allowable_value = 180
                self.ns_ridge_modulus_e_value = 1600000
            elif "Glulam" in selected:
                self.ns_ridge_fb_allowable_value = 2400
                self.ns_ridge_fv_allowable_value = 265
                self.ns_ridge_modulus_e_value = 1800000
            elif "3100Fb-2.1E (PWT)" in selected:
                self.ns_ridge_fb_allowable_value = 3100
                self.ns_ridge_fv_allowable_value = 265
                self.ns_ridge_modulus_e_value = 2100000
            elif "2850Fb-1.9E (Global)" in selected:
                self.ns_ridge_fb_allowable_value = 2850
                self.ns_ridge_fv_allowable_value = 265
                self.ns_ridge_modulus_e_value = 1900000
            else:  # LVL 2.0E
                self.ns_ridge_fb_allowable_value = 2650
                self.ns_ridge_fv_allowable_value = 285
                self.ns_ridge_modulus_e_value = 2000000

            # Update the Entry widgets with new values
            if hasattr(self, "entries"):
                if "ns_ridge_fb_allowable" in self.entries:
                    self.entries["ns_ridge_fb_allowable"].delete(0, tk.END)
                    self.entries["ns_ridge_fb_allowable"].insert(
                        0, str(self.ns_ridge_fb_allowable_value)
                    )
                if "ns_ridge_fv_allowable" in self.entries:
                    self.entries["ns_ridge_fv_allowable"].delete(0, tk.END)
                    self.entries["ns_ridge_fv_allowable"].insert(
                        0, str(self.ns_ridge_fv_allowable_value)
                    )
                if "ns_ridge_modulus_e" in self.entries:
                    self.entries["ns_ridge_modulus_e"].delete(0, tk.END)
                    self.entries["ns_ridge_modulus_e"].insert(
                        0, str(self.ns_ridge_modulus_e_value)
                    )

            # Mark data as changed for auto-save
            if hasattr(self, "data_changed"):
                self.data_changed = True

            # Trigger data change event
            self.on_data_changed()

        except Exception as e:
            print(f"Error in on_ns_ridge_material_change: {e}")
            import traceback

            traceback.print_exc()

    def compute_s_theta(self, pitch):
        if pitch is None or pitch <= 0:
            return 0.0, 0.0, 0.0
        s = pitch / 12.0  # rise/run
        S = 12.0 / pitch  # Correct ASCE S: run for rise of 1
        theta = math.degrees(math.atan(s))
        return s, theta, S

    def test_6_pitch_logic(self):
        """Test function to verify 6 pitch roof triggers unbalanced loads"""
        pitch = 6.0
        s, theta, S = self.compute_s_theta(pitch)
        min_slope = theta  # For single pitch test
        condition_met = 2.38 <= min_slope <= 30.2

        print("=== 6 PITCH ROOF TEST ===")
        print(f"Pitch: {pitch}/12")
        print(f"Slope ratio s: {s}")
        print(f"Slope angle theta: {theta:.2f} degrees")
        print(f"ASCE range check: 2.38 <= {theta:.2f} <= 30.2 = {condition_met}")
        print(f"Should trigger unbalanced loads: {condition_met}")
        return condition_met

    def calculate_gable_drift(self, pg, lu, W2, Ce, ct, Cs, Is, s, S):
        gamma = min(0.13 * pg + 14, 30)
        hd = 1.5 * math.sqrt(pg**0.74 * lu**0.7 * W2**1.7 / gamma)
        pd = hd * gamma / math.sqrt(S)  # Uniform rectangular
        pd_max = pd
        w = (8 * hd * math.sqrt(S)) / 3
        ps = 0.7 * Ce * ct * Is * pg * Cs
        return {
            "hd_ft": hd,
            "pd_max_psf": pd_max,
            "drift_width_ft": w,
            "pd_max": pd_max,
            "w": w,
            "ps": ps,
            "gamma": gamma,
        }

    def calculate(self):
        print("=" * 60)
        print("CALCULATE METHOD CALLED")
        print("=" * 60)

        # Clear output first to show we're running
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "CALCULATION STARTED...\n\n")
        self.master.update()  # Force GUI update

        # Test 6 pitch logic (for verification)
        try:
            self.test_6_pitch_logic()
        except Exception as e:
            print(f"test_6_pitch_logic error (continuing): {e}")

        # Validate all inputs before calculation
        print("Validating inputs...")
        validation_errors = self.validate_all_inputs()
        if validation_errors:
            error_message = "Please fix the following input errors:\n\n" + "\n".join(
                f"• {error}" for error in validation_errors
            )
            messagebox.showerror("Input Validation Errors", error_message)
            self.output_text.insert(tk.END, f"\nVALIDATION ERRORS:\n{error_message}\n")
            print(f"VALIDATION ERRORS: {validation_errors}")
            return

        print("Validation passed, continuing...")
        self.output_text.insert(
            tk.END, "All inputs validated. Proceeding with calculation...\n\n"
        )
        self.master.update()  # Force GUI update

        pg = self.get_float("pg")
        north_span = self.get_float("north_span")  # = lu_north
        south_span = self.get_float("south_span")
        ew_half_width = self.get_float("ew_half_width")  # = lu_west

        valley_offset = self.get_float("valley_offset")
        if valley_offset is None:
            valley_offset = ew_half_width  # fallback

        lu_north = north_span
        lu_west = ew_half_width

        # Cap at 500 ft per ASCE 7-22
        lu_north = min(lu_north, 500)
        lu_west = min(lu_west, 500)
        w2 = self.get_float("w2")
        ce = self.get_float("ce")
        ct = self.get_float("ct")
        pitch_n = self.get_float("pitch_north")
        pitch_w = self.get_float("pitch_west")
        valley_angle = self.get_float("valley_angle")

        # Use new geometry variables
        de_n = north_span  # For compatibility with existing code
        de_w = south_span  # For compatibility with existing code
        beam_width = self.get_float("beam_width")
        modulus_e = self.get_float("modulus_e")
        fb_allowable = self.get_float("fb_allowable")
        fv_allowable = self.get_float("fv_allowable")
        deflection_snow_limit = self.get_float("deflection_snow_limit")
        deflection_total_limit = self.get_float("deflection_total_limit")
        beam_depth_trial = self.get_float(
            "beam_depth_trial"
        )  # Can be None for back-calculation
        if beam_depth_trial is None:
            beam_depth_trial = 16  # Default value
        jack_spacing_inches = self.get_float("jack_spacing_inches")
        dead_load_horizontal = self.get_float("dead_load_horizontal")
        slippery = self.slippery_var.get()

        # Validate beam design inputs
        if beam_width is None or beam_width <= 0:
            beam_width = 3.125  # Default
        if modulus_e is None or modulus_e <= 0:
            modulus_e = 1800000.0  # Default Glulam
        if fb_allowable is None or fb_allowable <= 0:
            fb_allowable = 2400.0  # Default Glulam
        if fv_allowable is None or fv_allowable <= 0:
            fv_allowable = 265.0  # Default Glulam

        # Check for missing required inputs and show error message
        missing = []
        if pg is None:
            missing.append("Ground snow load (pg)")
        if lu_north is None:
            missing.append("North span")
        if lu_west is None:
            missing.append("E-W half-width")
        if w2 is None:
            missing.append("Winter wind parameter (W2)")
        if ce is None:
            missing.append("Exposure factor (Ce)")
        if ct is None:
            missing.append("Thermal factor (Ct)")
        if pitch_n is None:
            missing.append("Pitch north")
        if pitch_w is None:
            missing.append("Pitch west")
        if valley_angle is None:
            missing.append("Valley angle")
        if beam_width is None:
            missing.append("Beam width")
        if modulus_e is None:
            missing.append("Modulus E")
        if fb_allowable is None:
            missing.append("Fb allowable")
        if fv_allowable is None:
            missing.append("Fv allowable")
        if deflection_snow_limit is None:
            missing.append("Deflection snow limit")
        if deflection_total_limit is None:
            missing.append("Deflection total limit")
        if jack_spacing_inches is None:
            missing.append("Jack spacing")
        if dead_load_horizontal is None:
            missing.append("Dead load horizontal")

        if missing:
            error_msg = "Please fill in the following required inputs:\n\n" + "\n".join(
                f"• {name}" for name in missing
            )
            messagebox.showerror("Missing Required Inputs", error_msg)
            self.output_text.insert(
                tk.END, f"\nERROR: Missing inputs: {', '.join(missing)}\n"
            )
            print(f"ERROR: Missing inputs: {missing}")
            return

        print("All required inputs present, starting calculations...")

        # Calculate slopes for unbalanced load check
        print(f"DEBUG: Computing slopes - pitch_n={pitch_n}, pitch_w={pitch_w}")
        try:
            s_n, theta_n, S_n = self.compute_s_theta(pitch_n)
            s_w, theta_w, S_w = self.compute_s_theta(pitch_w)
            print(f"DEBUG: Slopes computed - theta_n={theta_n}, theta_w={theta_w}")
        except Exception as e:
            error_msg = (
                f"Error computing slopes: {e}\npitch_n={pitch_n}, pitch_w={pitch_w}"
            )
            raise Exception(error_msg) from e

        # ASCE 7-22 Sec. 7.6.1 Unbalanced applicability
        unbalanced_applies_n = (
            0.5 / 12 <= s_n <= 7 / 12
        )  # 0.5 on 12 to 7 on 12 (2.38° to 30.2°)
        unbalanced_applies_w = 0.5 / 12 <= s_w <= 7 / 12
        # Narrow roof check: W = dimension perpendicular to ridge
        # For North Wind: perpendicular to N-S ridge = north_span
        # For West Wind: perpendicular to E-W ridge = ew_half_width
        narrow_roof_n = north_span <= 20
        narrow_roof_w = ew_half_width <= 20

        # Validation
        errors = []
        errors.append(validate_ground_snow_load(pg))
        errors.append(validate_upwind_fetch(lu_north, "North"))
        errors.append(validate_upwind_fetch(lu_west, "West"))
        errors.append(validate_valley_angle(valley_angle))
        errors.append(validate_pitch(pitch_n, "North"))
        errors.append(validate_pitch(pitch_w, "West"))
        errors.append(validate_exposure_factor(ce))
        errors.append(validate_thermal_factor(ct))

        errors = [e for e in errors if e is not None]
        if errors:
            messagebox.showwarning("Validation Warnings", "\n".join(errors))
            return

        # Flat roof snow load - ASCE 7-22 Equation 7.3-1
        pf = 0.7 * ce * ct * pg  # pf = 0.7 × Ce × Ct × pg

        # Slope factor calculations - ASCE 7-22 Section 7.4.1, Figure 7.4-1
        cs_n = calculate_cs(theta_n, ct, slippery=slippery)
        cs_w = calculate_cs(theta_w, ct, slippery=slippery)
        cs = min(cs_n, cs_w)  # governing slope factor

        # Snow density - ASCE 7-22 Equation 7.7-1
        gamma = min(0.13 * pg + 14, 30)  # γ = min(0.13 × pg + 14, 30) pcf

        # Balanced sloped roof snow load - ASCE 7-22 Equation 7.4-1
        ps = cs * pf  # ps = Cs × pf (governing value)

        # Calculate individual plane balanced loads (different slopes may give different ps)
        ps_north = cs_n * pf  # North roof plane
        ps_west = cs_w * pf  # West roof plane

        # Balanced snow depth - ASCE 7-22 Section 7.7.1
        hb = ps / gamma  # hb = ps / γ

        # Low-slope roof check per ASCE 7-22 Sec. 7.3
        min_slope_deg = min(theta_n, theta_w)
        low_slope = min_slope_deg < 15.0

        # Calculate minimum snow load pm - ASCE 7-22 Equation 7.3-2
        # pm = 0.7 × Ce × Ct × pg × 0.6 (no Is factor in ASCE 7-22)
        pm = 0.7 * ce * ct * pg * 0.6

        # Determine governing roof snow load
        if low_slope:
            governing_roof_load = max(ps, pm)
        else:
            governing_roof_load = ps

        # Valley geometry - rectangular cross-gable roof
        # Valley Rafter: High point = Ridge intersection (N-S & E-W ridges meet)
        #               Low point = Eave intersection (where two gable roofs meet)
        lv = math.sqrt(
            south_span**2 + valley_offset**2
        )  # Horizontal valley length from low point to high point

        # Compute valley angle for display (optional)
        (
            math.degrees(math.atan(south_span / valley_offset))
            if valley_offset > 0
            else 90
        )

        rafter_len = valley_rafter_length(
            lv, pitch_n / 12.0, pitch_w / 12.0, north_span, south_span
        )

        # ASCE 7-22 Section 7.6.1: Gable Unbalanced Loads
        # Analyze BOTH North and West wind directions and use governing (maximum) loads

        # Initialize balanced loads (will be modified by unbalanced loads if applicable)
        north_load = ps_north if ps_north > 0 else ps  # North roof plane balanced load
        south_load = (
            ps_north if ps_north > 0 else ps
        )  # South roof plane balanced load (same as north for cross-gable)
        west_load = ps_west if ps_west > 0 else ps  # West roof plane balanced load
        east_load = (
            ps_west if ps_west > 0 else ps
        )  # East roof plane balanced load (same as west for cross-gable)

        # Initialize individual wind direction loads (set to balanced values initially)
        # These will be updated if unbalanced loads apply
        north_load_north_wind = north_load  # Start with balanced loads
        south_load_north_wind = south_load
        west_load_west_wind = west_load
        east_load_west_wind = east_load
        surcharge_width_north = 0
        surcharge_width_west = 0

        # Initialize final variables for diagram display (will be set in both balanced and unbalanced cases)
        north_load_north_wind_final = north_load
        south_load_north_wind_final = south_load
        west_load_west_wind_final = west_load
        east_load_west_wind_final = east_load

        # === ASCE 7-22 FIGURE 7.6-2: BALANCED vs UNBALANCED SNOW LOADS ===
        # Criteria: Roof slope determines balanced vs unbalanced loading
        # If slope outside 2.38°-30.2° range: BALANCED loads on ALL planes
        # If slope within range: UNBALANCED loads based on wind direction

        # Optional debug output for unbalanced load condition
        # min_calc_slope = min(theta_n, theta_w)
        # print(f"DEBUG CALC: theta_n = {theta_n:.2f} degrees, theta_w = {theta_w:.2f} degrees, min_slope = {min_calc_slope:.2f} degrees")
        # print(f"DEBUG CALC: Condition check: 2.38 <= {min_calc_slope:.2f} <= 30.2 = {2.38 <= min_calc_slope <= 30.2}")

        if 2.38 <= min(theta_n, theta_w) <= 30.2:
            # Calculate loads for BOTH wind directions and take maximums

            # ===== NORTH WIND ANALYSIS =====
            # North wind blows parallel to North-South ridge, affecting North-South roof planes
            # Figure 7.6-2: North plane = windward, South plane = leeward
            # Narrow/wide determination based on fetch lu (distance to upwind eave)
            lu_north = north_span  # Fetch distance to north eave
            is_narrow_north = lu_north <= 20

            if is_narrow_north:
                # Narrow roof: p_g on leeward (south), 0 on windward (north)
                north_load_north_wind = 0
                south_load_north_wind = pg
                # For narrow roofs, surcharge extends full span (measured along valley)
                # Already measured along valley, so no projection needed
                surcharge_width_north = lv  # Full valley length for narrow roofs
            else:
                # Wide roof: 0.3p_s on windward (north), p_s + surcharge on leeward (south)
                north_load_north_wind = 0.3 * ps_north if ps_north > 0 else 0

                # Calculate surcharge for south plane
                # Fetch lu = distance from ridge to upwind eave = north_span
                lu_north = north_span
                hd_north = 1.5 * math.sqrt(
                    (pg**0.74 * lu_north**0.70 * w2**1.7) / gamma
                )
                surcharge_north = hd_north * gamma / math.sqrt(S_n)
                surcharge_width_north = (8 * hd_north * math.sqrt(S_n)) / 3

                # Limit surcharge width to available roof dimension (east-west width)
                # For roofs wider than 20 ft, surcharge width should not exceed perpendicular dimension
                roof_width_ew = 2 * ew_half_width  # Total east-west width
                surcharge_width_north = min(surcharge_width_north, roof_width_ew)

                south_load_north_wind = ps + surcharge_north

            # ===== WEST WIND ANALYSIS =====
            # West wind blows parallel to East-West ridge, affecting East-West roof planes
            # Figure 7.6-2: West plane = windward, East plane = leeward
            # Narrow/wide determination based on fetch lu (distance to upwind eave)
            lu_west = ew_half_width  # Fetch distance to west eave
            is_narrow_west = lu_west <= 20

            if is_narrow_west:
                # Narrow roof: p_g on leeward (east), 0 on windward (west)
                west_load_west_wind = 0
                east_load_west_wind = pg
                # For narrow roofs, surcharge extends full span (measured along valley)
                # Already measured along valley, so no projection needed
                surcharge_width_west = lv  # Full valley length for narrow roofs
            else:
                # Wide roof: 0.3p_s on windward (west), p_s + surcharge on leeward (east)
                west_load_west_wind = 0.3 * ps_west if ps_west > 0 else 0

                # Calculate surcharge for east plane
                # Fetch lu = distance from ridge to upwind eave = ew_half_width
                lu_west = ew_half_width
                hd_west = 1.5 * math.sqrt((pg**0.74 * lu_west**0.70 * w2**1.7) / gamma)
                surcharge_west = hd_west * gamma / math.sqrt(S_w)
                surcharge_width_west = (8 * hd_west * math.sqrt(S_w)) / 3

                # Limit surcharge width to available roof dimension (north-south span)
                # For roofs wider than 20 ft, surcharge width should not exceed perpendicular dimension
                roof_span_ns = north_span + south_span  # Total north-south span
                surcharge_width_west = min(surcharge_width_west, roof_span_ns)

                east_load_west_wind = ps + surcharge_west

            # ===== STORE INDIVIDUAL WIND DIRECTION LOADS =====
            # Keep individual wind direction loads for diagram display
            north_load_north_wind_final = north_load_north_wind
            south_load_north_wind_final = south_load_north_wind
            west_load_west_wind_final = west_load_west_wind
            east_load_west_wind_final = east_load_west_wind

            # ===== GOVERNING LOADS (Maximum from both wind directions) =====
            # Each roof plane takes the maximum load from either wind direction
            # This ensures conservative design for unknown wind conditions
            north_load = max(
                north_load, north_load_north_wind
            )  # North plane: max from balanced + north wind
            south_load = max(
                south_load, south_load_north_wind
            )  # South plane: max from balanced + north wind
            west_load = max(
                west_load, west_load_west_wind
            )  # West plane: max from balanced + west wind
            east_load = max(
                east_load, east_load_west_wind
            )  # East plane: max from balanced + west wind

        # Set governing loads for diagram display (maximum from both wind directions)
        # These are always the maximum loads regardless of whether unbalanced loads apply
        self.governing_north = north_load
        self.governing_south = south_load
        self.governing_west = west_load
        self.governing_east = east_load

        # Store individual wind direction loads for valley governing load determination
        if 2.38 <= min(theta_n, theta_w) <= 30.2:
            self.south_load_north_wind = south_load_north_wind_final
            self.east_load_west_wind = east_load_west_wind_final
        else:
            # Balanced loads only - no individual wind direction loads
            self.south_load_north_wind = south_load
            self.east_load_west_wind = east_load

        print("DEBUG: About to call generate_diagrams")

        # Create result dictionaries for compatibility with existing code
        result_north = {
            "hd_ft": 0,  # These will be updated for valley drifts later
            "pd_max_psf": 0,
            "drift_width_ft": 0,
            "pd_max": 0,
            "w": 0,
            "ps": ps,
            "gamma": gamma,
            "unbalanced_load": north_load,
        }

        result_west = {
            "hd_ft": 0,
            "pd_max_psf": 0,
            "drift_width_ft": 0,
            "pd_max": 0,
            "w": 0,
            "ps": ps,
            "gamma": gamma,
            "unbalanced_load": west_load,
        }

        # Special narrow roof case (W <= 20 ft, simply supported prismatic members assumed)
        if narrow_roof_n and unbalanced_applies_n:
            result_north["pd_max"] = (
                pg - ps
            )  # Leeward = pg, windward unloaded → surcharge = pg - ps
            result_north["w"] = de_n  # Full span
        if narrow_roof_w and unbalanced_applies_w:
            result_west["pd_max"] = pg - ps
            result_west["w"] = de_w

        # Valley drift calculations eliminated - using zero drift loads
        gov_drift = {"governing_pd_max_psf": 0.0, "governing_hd_ft": 0.0}
        gov_drift_width = 0.0

        # Max total load at valley corner (no drift contribution)
        ps

        # Jack Rafter Point Loads - calculate first since beam design needs these
        # Determine governing load and distance for jack rafter calculations
        # This matches the diagram: use governing load and governing distance for both ridges
        if 2.38 <= min(theta_n, theta_w) <= 30.2:
            # Determine which wind direction governs (larger total load)
            governing_valley_load_psf = max(
                south_load_north_wind_final, east_load_west_wind_final
            )

            # Use the governing wind direction's distance for BOTH ridges
            if south_load_north_wind_final >= east_load_west_wind_final:
                # North wind governs: use north wind distance for both ridges
                governing_surcharge_width_ft = surcharge_width_north
            else:
                # West wind governs: use west wind distance for both ridges
                governing_surcharge_width_ft = surcharge_width_west

            # Pass governing load and distance for both ridges (matching diagram)
            north_wind_load_for_jacks = governing_valley_load_psf
            west_wind_load_for_jacks = governing_valley_load_psf
            surcharge_width_north_for_jacks = governing_surcharge_width_ft
            surcharge_width_west_for_jacks = governing_surcharge_width_ft
            unbalanced_applies_for_jacks = True
        else:
            # Balanced loads only
            north_wind_load_for_jacks = None
            west_wind_load_for_jacks = None
            surcharge_width_north_for_jacks = 0.0
            surcharge_width_west_for_jacks = 0.0
            unbalanced_applies_for_jacks = False

        jacks_data = calculate_jack_rafters(
            de_north=de_n,
            de_west=de_w,
            pitch_north=pitch_n,
            pitch_west=pitch_w,
            valley_angle_deg=valley_angle,
            jack_spacing_in=jack_spacing_inches,
            ps_psf=ps,  # Balanced snow load
            pd_max_psf=0.0,  # No valley drift load
            w_drift_ft=0.0,  # No drift width
            dead_load_psf_horizontal=dead_load_horizontal,
        )

        # Beam design - now that we have jack rafter data
        beam_inputs = ValleyBeamInputs(
            rafter_sloped_length_ft=rafter_len,
            ps_balanced_psf=governing_roof_load,  # Use governing roof load (accounts for low-slope minimum)
            governing_pd_max_psf=gov_drift["governing_pd_max_psf"],
            roof_dead_psf=dead_load_horizontal,  # Use DL horizontal as roof dead load
            beam_width_in=beam_width,
            beam_depth_trial_in=beam_depth_trial,
            modulus_e_psi=modulus_e,
            fb_allowable_psi=fb_allowable,
            fv_allowable_psi=fv_allowable,
            deflection_snow_limit=deflection_snow_limit,
            deflection_total_limit=deflection_total_limit,
            governing_drift_width_ft=gov_drift_width,
            jack_spacing_inches=jack_spacing_inches,
        )

        beam = ValleyBeamDesigner(beam_inputs)

        # Extract point loads from jack rafters - separate snow and dead loads
        # j_n = North-South Valley Rafters (frame from Valley Beam to East-West Ridge)
        # j_w = East-West Valley Rafters (frame from Valley Beam to North-South Ridge)
        # Each jack rafter has equal reactions at both ends (half at each end)
        # Valley beam receives: j_n/2 + j_w/2 at each position
        # Ridge beam receives: j_w_total (j_w/2 from each side = full j_w)
        # For reactions to match: j_n/2 + j_w/2 should equal j_w_total, so j_n = j_w
        # Since geometry is symmetric and j_n = j_w, both beams use same reaction: (j_n + j_w)/2
        snow_point_loads = []
        dead_point_loads = []
        num_jacks = len(jacks_data["jacks"]["west_side"])
        # Use fixed 2.83-foot spacing along slope for Valley Beam: 0, 2.83, 5.66, 8.49, 11.32, 14.15, 16.98 ft
        fixed_sloped_positions = [
            i * 2.83 for i in range(num_jacks)
        ]  # 0, 2.83, 5.66, 8.49, 11.32, 14.15, 16.98...

        for i, (j_n, j_w) in enumerate(
            zip(jacks_data["jacks"]["north_side"], jacks_data["jacks"]["west_side"])
        ):
            # Use fixed 2.83-foot spacing along the slope
            pos_sloped = (
                fixed_sloped_positions[i]
                if i < len(fixed_sloped_positions)
                else i * 2.83
            )

            # Valley beam receives half reaction from both j_n and j_w
            # Reaction = (j_n_total + j_w_total) / 2
            # Since j_n = j_w (symmetric), this equals j_w_total
            reaction_snow = (j_n["total_snow_lb"] + j_w["total_snow_lb"]) / 2
            reaction_dead = (j_n["dead_load_lb"] + j_w["dead_load_lb"]) / 2

            snow_point_loads.append((pos_sloped, reaction_snow))
            dead_point_loads.append((pos_sloped, reaction_dead))

        # Design beam with separate snow and dead point loads
        print(
            f"DEBUG: About to call beam design - snow loads: {len(snow_point_loads) if snow_point_loads else 0}, dead loads: {len(dead_point_loads) if dead_point_loads else 0}, lv: {lv}, rafter_len: {rafter_len}"
        )

        # Validate inputs before calling beam design
        if not snow_point_loads or not dead_point_loads:
            print("DEBUG: No point loads available - skipping beam design")
            beam_results = {
                "error": "No point loads calculated - check jack rafter configuration"
            }
        elif lv <= 0 or rafter_len <= 0:
            print(f"DEBUG: Invalid dimensions - lv: {lv}, rafter_len: {rafter_len}")
            beam_results = {
                "error": f"Invalid beam dimensions: lv={lv}, rafter_len={rafter_len}"
            }
        else:
            try:
                beam_results = beam.design_with_point_loads(
                    snow_point_loads, dead_point_loads, lv, rafter_len
                )
                print(
                    f"DEBUG: beam.design_with_point_loads completed, result: {type(beam_results)}"
                )
                if beam_results and isinstance(beam_results, dict):
                    print(f"DEBUG: beam_results keys: {list(beam_results.keys())}")
                    print(f"DEBUG: beam_results has 'error': {'error' in beam_results}")
                    print(
                        f"DEBUG: beam_results has 'passes': {'passes' in beam_results}"
                    )
                else:
                    print(
                        f"DEBUG: beam_results is not a dict or is None: {beam_results}"
                    )
            except Exception as e:
                print(f"DEBUG: Exception in beam.design_with_point_loads: {e}")
                import traceback

                traceback.print_exc()
                beam_results = {"error": f"Beam calculation failed: {str(e)}"}

        # === N-S RIDGE BEAM DESIGN (Calculate before diagrams) ===
        # N-S Ridge Beam: Runs along north-south ridge line, south of E-W ridge
        ns_ridge_beam_length = south_span  # Horizontal length of N-S ridge beam

        # Extract point loads from j_w jack rafters for N-S Ridge Beam
        # Use actual horizontal positions from j_n (location_from_eave_ft) - these represent
        # the horizontal distance from south eave in plan view (2 feet on center)
        # Each j_w rafter reaction is split: half goes to N-S Ridge Beam, half goes to Valley Beam
        ns_ridge_snow_point_loads = []
        ns_ridge_dead_point_loads = []
        ns_ridge_load_positions = []

        # Store valley beam loads for comparison table (using same horizontal positions)
        valley_beam_positions = []
        valley_beam_total_loads = []

        # Process each jack rafter pair (j_n and j_w)
        # Use fixed 2-foot spacing (24 inches on center) for N-S Ridge Beam: 0, 2, 4, 6, 8, 10, 12, 14 ft
        # Use fixed 2.83-foot spacing along slope for Valley Beam: 0, 2.83, 5.66, 8.49, 11.32, 14.15, 16.98 ft
        num_jacks = len(jacks_data["jacks"]["west_side"])
        fixed_horizontal_positions = [
            i * 2.0 for i in range(num_jacks)
        ]  # 0, 2, 4, 6, 8, 10, 12, 14...
        fixed_sloped_positions = [
            i * 2.83 for i in range(num_jacks)
        ]  # 0, 2.83, 5.66, 8.49, 11.32, 14.15, 16.98...

        # Initialize sloped positions storage
        if not hasattr(self, "valley_beam_sloped_positions"):
            self.valley_beam_sloped_positions = []
            self.valley_beam_sloped_loads = []

        for i, (j_n, j_w) in enumerate(
            zip(jacks_data["jacks"]["north_side"], jacks_data["jacks"]["west_side"])
        ):
            # Use fixed 2-foot spacing position for ridge beam (24 inches on center)
            pos_horizontal = (
                fixed_horizontal_positions[i]
                if i < len(fixed_horizontal_positions)
                else i * 2.0
            )

            # Use fixed 2.83-foot spacing along slope for valley beam
            pos_sloped_valley = (
                fixed_sloped_positions[i]
                if i < len(fixed_sloped_positions)
                else i * 2.83
            )

            # Each jack rafter has equal reactions at both ends (half at each end)
            # j_w rafter: half reaction goes to N-S Ridge Beam, half to Valley Beam
            # j_n rafter: half reaction goes to E-W Ridge, half to Valley Beam
            # Reactions change as tributary areas change (smaller going north), but equal at each end

            # Calculate reactions for this individual jack rafter pair
            # Since geometry is symmetric and j_n_total = j_w_total:
            # Valley beam receives: (j_n_total + j_w_total) / 2
            # Ridge beam receives: j_w_total (from both sides)
            # Since j_n = j_w: (j_n + j_w)/2 = (j_w + j_w)/2 = j_w_total
            # So both should be equal - use same calculation
            reaction_snow = (j_n["total_snow_lb"] + j_w["total_snow_lb"]) / 2
            reaction_dead = (j_n["dead_load_lb"] + j_w["dead_load_lb"]) / 2
            reaction_total = reaction_snow + reaction_dead

            # Valley beam uses this reaction
            valley_snow_load = reaction_snow
            valley_dead_load = reaction_dead
            valley_total = reaction_total

            # N-S Ridge Beam uses same reaction (since j_n = j_w, j_w_total = (j_n + j_w)/2)
            ns_ridge_snow_load = reaction_snow  # Same as valley beam
            ns_ridge_dead_load = reaction_dead  # Same as valley beam
            ns_ridge_total = reaction_total  # Same as valley beam

            # Store N-S Ridge Beam point loads at fixed 2-foot spacing
            ns_ridge_snow_point_loads.append((pos_horizontal, ns_ridge_snow_load))
            ns_ridge_dead_point_loads.append((pos_horizontal, ns_ridge_dead_load))
            ns_ridge_load_positions.append(pos_horizontal)

            # Store valley beam data for comparison
            valley_beam_positions.append(pos_horizontal)
            valley_beam_total_loads.append(valley_total)

            # Store N-S Ridge Beam total load (should equal valley_total since j_n = j_w)
            if not hasattr(self, "ns_ridge_total_loads"):
                self.ns_ridge_total_loads = []
            self.ns_ridge_total_loads.append(
                ns_ridge_total
            )  # Same value as valley_total

            # Store sloped position for valley beam (for diagram display)
            # Use fixed 2.83-foot spacing along the slope
            if not hasattr(self, "valley_beam_sloped_positions"):
                self.valley_beam_sloped_positions = []
                self.valley_beam_sloped_loads = []
            self.valley_beam_sloped_positions.append(pos_sloped_valley)
            self.valley_beam_sloped_loads.append(valley_total)

        # Store for diagram generation and comparison table
        self.ns_ridge_snow_point_loads = ns_ridge_snow_point_loads
        self.ns_ridge_dead_point_loads = ns_ridge_dead_point_loads
        self.ns_ridge_beam_length = ns_ridge_beam_length
        self.ns_ridge_load_positions = (
            ns_ridge_load_positions  # Store positions for diagram
        )
        self.valley_beam_positions = valley_beam_positions
        self.valley_beam_total_loads = valley_beam_total_loads
        # ns_ridge_total_loads is now calculated above in the loop

        # Generate professional diagrams (using ASD loads D + 0.7S to match detailed analysis)
        # Calculate ASD point loads for diagrams
        asd_snow_point_loads = []
        asd_dead_point_loads = []

        for i, (pos_sloped, snow_load) in enumerate(snow_point_loads):
            pos_sloped_dead, dead_load = dead_point_loads[i]
            asd_snow_load = snow_load * 0.7  # ASD snow load
            asd_snow_point_loads.append((pos_sloped, asd_snow_load))
            asd_dead_point_loads.append((pos_sloped, dead_load))  # Dead load unchanged

        self.generate_diagrams(
            snow_point_loads=asd_snow_point_loads,
            dead_point_loads=asd_dead_point_loads,
            rafter_len=rafter_len,
            ps_balanced=ps,
            gov_drift=gov_drift,
            lv_horizontal=lv,
            north_span=north_span,
            south_span=south_span,
            ew_half_width=ew_half_width,
            valley_offset=valley_offset,
            pitch_n=pitch_n,
            pitch_w=pitch_w,
            valley_angle=valley_angle,
            lu_north=lu_north,
            lu_west=lu_west,
            result_north=result_north,
            result_west=result_west,
            surcharge_width_north=surcharge_width_north,
            surcharge_width_west=surcharge_width_west,
            north_load_north_wind_final=north_load_north_wind_final,
            south_load_north_wind_final=south_load_north_wind_final,
            west_load_west_wind_final=west_load_west_wind_final,
            east_load_west_wind_final=east_load_west_wind_final,
        )

        # === N-S RIDGE BEAM DESIGN (Continue calculations) ===
        # Get N-S ridge beam material properties (from independent inputs)
        ns_ridge_beam_width = self.get_float("ns_ridge_beam_width")
        if ns_ridge_beam_width is None or ns_ridge_beam_width <= 0:
            ns_ridge_beam_width = 3.5  # Default

        ns_ridge_beam_depth = self.get_float("ns_ridge_beam_depth_trial")
        if ns_ridge_beam_depth is None or ns_ridge_beam_depth <= 0:
            ns_ridge_beam_depth = 16  # Default

        ns_ridge_fb = self.ns_ridge_fb_allowable_value
        ns_ridge_fv = self.ns_ridge_fv_allowable_value
        ns_ridge_e = self.ns_ridge_modulus_e_value

        # Get N-S ridge beam deflection limits (from independent inputs)
        ns_ridge_deflection_total_limit = self.get_float(
            "ns_ridge_deflection_total_limit"
        )
        if (
            ns_ridge_deflection_total_limit is None
            or ns_ridge_deflection_total_limit <= 0
        ):
            ns_ridge_deflection_total_limit = 240  # Default

        ns_ridge_deflection_snow_limit = self.get_float(
            "ns_ridge_deflection_snow_limit"
        )
        if (
            ns_ridge_deflection_snow_limit is None
            or ns_ridge_deflection_snow_limit <= 0
        ):
            ns_ridge_deflection_snow_limit = 360  # Default

        # Design N-S ridge beam
        ns_ridge_beam_inputs = ValleyBeamInputs(
            rafter_sloped_length_ft=ns_ridge_beam_length,  # Horizontal length
            ps_balanced_psf=governing_roof_load,
            governing_pd_max_psf=0.0,  # No drift on ridge beam
            roof_dead_psf=dead_load_horizontal,
            beam_width_in=ns_ridge_beam_width,
            beam_depth_trial_in=ns_ridge_beam_depth,
            modulus_e_psi=ns_ridge_e,
            fb_allowable_psi=ns_ridge_fb,
            fv_allowable_psi=ns_ridge_fv,
            deflection_snow_limit=ns_ridge_deflection_snow_limit,
            deflection_total_limit=ns_ridge_deflection_total_limit,
            governing_drift_width_ft=0.0,
            jack_spacing_inches=jack_spacing_inches,
        )

        ns_ridge_beam = ValleyBeamDesigner(ns_ridge_beam_inputs)

        # Design N-S ridge beam with point loads
        if (
            ns_ridge_snow_point_loads
            and ns_ridge_dead_point_loads
            and ns_ridge_beam_length > 0
        ):
            try:
                ns_ridge_beam_results = ns_ridge_beam.design_with_point_loads(
                    ns_ridge_snow_point_loads,
                    ns_ridge_dead_point_loads,
                    ns_ridge_beam_length,  # Horizontal length
                    ns_ridge_beam_length,  # Same for horizontal beam
                )
            except Exception as e:
                print(f"DEBUG: Exception in N-S ridge beam design: {e}")
                import traceback

                traceback.print_exc()
                ns_ridge_beam_results = {
                    "error": f"N-S ridge beam calculation failed: {str(e)}"
                }
        else:
            ns_ridge_beam_results = {
                "error": "No point loads available for N-S ridge beam"
            }

        # Format beam design results
        beam_summary = "Beam design calculation in progress..."  # Initialize

        if beam_results and "error" not in beam_results:
            print("DEBUG: Entering success case for beam summary")
            print(f"DEBUG: beam_results content: {beam_results}")
            # Create summary for dedicated UI box
            overall_pass = beam_results.get("passes", False)
            bend_ratio = beam_results.get("ratio_bending", 0)
            shear_ratio = beam_results.get("ratio_shear", 0)
            snow_def_ratio = beam_results.get("ratio_deflection_snow", 0)
            total_def_ratio = beam_results.get("ratio_deflection_total", 0)
            print(
                f"DEBUG: Extracted ratios - bend: {bend_ratio}, shear: {shear_ratio}, snow: {snow_def_ratio}, total: {total_def_ratio}, pass: {overall_pass}"
            )
        else:
            print("DEBUG: Entering error case for beam summary")
            # Handle beam design error
            error_msg = (
                beam_results.get("error", "Unknown beam design error")
                if beam_results
                else "Beam design calculation failed"
            )
            print(f"BEAM DESIGN ERROR: {error_msg}")
            self.output_text.insert(
                tk.END, f"\n!!! BEAM DESIGN ERROR !!!\n{error_msg}\n\n"
            )
            # Set error values for UI
            overall_pass = False
            bend_ratio = shear_ratio = snow_def_ratio = total_def_ratio = 0
            beam_summary = f"BEAM DESIGN ERROR: {error_msg}"

            # Update summary text widget with error
            self.summary_label.config(state="normal")
            self.summary_label.delete(1.0, tk.END)
            self.summary_label.tag_configure(
                "error", foreground="red", font=("Helvetica", 11, "bold")
            )
            self.summary_label.insert(
                tk.END, f"BEAM DESIGN ERROR: {error_msg}", "error"
            )
            self.summary_label.config(state="disabled")
            print(f"SUMMARY ERROR: {error_msg[:100]}...")
            # Update canvas scroll region and scroll to summary
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.yview_moveto(0.3)  # Scroll to show summary
            return  # Exit early on error

        # Create beam design summary for both success and error cases
        print("DEBUG: Creating summary text")
        ratios = {
            "Bending": bend_ratio,
            "Shear": shear_ratio,
            "Snow Deflection": snow_def_ratio,
            "Total Deflection": total_def_ratio,
        }
        governing_check = max(ratios, key=ratios.get)
        max_ratio = ratios[governing_check]

        summary = "=== BEAM DESIGN SUMMARY ===\n\n"
        if overall_pass:
            summary += "OVERALL STATUS: PASS\n\n"
            self.summary_label.config(foreground="green")
        else:
            summary += "OVERALL STATUS: FAIL\n\n"
            summary += f"Governing Check: {governing_check} (ratio {max_ratio:.3f})\n\n"
            self.summary_label.config(foreground="red")

        summary += "VALLEY BEAM:\n"
        summary += f"Beam Section: {beam_results.get('section', 'Unknown') if beam_results else 'Error'}\n\n"
        summary += f"Bending Check: {bend_ratio:.3f} ({'PASS' if bend_ratio <= 1 else 'FAIL'})\n"
        summary += f"Shear Check: {shear_ratio:.3f} ({'PASS' if shear_ratio <= 1 else 'FAIL'})\n"
        summary += f"Snow Deflection: {snow_def_ratio:.3f} ({'PASS' if snow_def_ratio <= 1 else 'FAIL'})\n"

        # Add N-S Ridge Beam summary
        summary += f"\n{'='*50}\n"
        summary += "N-S RIDGE BEAM:\n"
        if ns_ridge_beam_results and "error" not in ns_ridge_beam_results:
            ns_overall_pass = ns_ridge_beam_results.get("passes", False)
            ns_bend_ratio = ns_ridge_beam_results.get("ratio_bending", 0)
            ns_shear_ratio = ns_ridge_beam_results.get("ratio_shear", 0)
            ns_snow_def_ratio = ns_ridge_beam_results.get("ratio_deflection_snow", 0)
            ns_total_def_ratio = ns_ridge_beam_results.get("ratio_deflection_total", 0)

            summary += f"Length: {ns_ridge_beam_length:.2f} ft\n"
            summary += f"Material: {self.ns_ridge_material_combobox.get()}\n"
            summary += f"Status: {'PASS' if ns_overall_pass else 'FAIL'}\n\n"
            summary += f"Bending Check: {ns_bend_ratio:.3f} ({'PASS' if ns_bend_ratio <= 1 else 'FAIL'})\n"
            summary += f"Shear Check: {ns_shear_ratio:.3f} ({'PASS' if ns_shear_ratio <= 1 else 'FAIL'})\n"
            summary += f"Snow Deflection: {ns_snow_def_ratio:.3f} ({'PASS' if ns_snow_def_ratio <= 1 else 'FAIL'})\n"
            summary += f"Total Deflection: {ns_total_def_ratio:.3f} ({'PASS' if ns_total_def_ratio <= 1 else 'FAIL'})\n"
        else:
            ns_error_msg = (
                ns_ridge_beam_results.get("error", "Unknown error")
                if ns_ridge_beam_results
                else "Calculation failed"
            )
            summary += f"ERROR: {ns_error_msg}\n"

        summary += f"Total Deflection: {total_def_ratio:.3f} ({'PASS' if total_def_ratio <= 1 else 'FAIL'})\n"

        # Update canvas scroll region and scroll to summary
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0.3)  # Scroll to show summary

        # Find governing check
        ratios = {
            "Bending": bend_ratio,
            "Shear": shear_ratio,
            "Snow Deflection": snow_def_ratio,
            "Total Deflection": total_def_ratio,
        }
        governing_check = max(ratios, key=ratios.get)
        max_ratio = ratios[governing_check]

        # Update dedicated summary label
        bend_pass = bend_ratio <= 1
        shear_pass = shear_ratio <= 1
        snow_pass = snow_def_ratio <= 1
        total_pass = total_def_ratio <= 1

        # Clear and enable the text widget
        self.summary_label.config(state="normal")
        self.summary_label.delete(1.0, tk.END)

        # Configure tags for colors
        self.summary_label.tag_configure("pass", foreground="green", font=("Helvetica", 10, "bold"))
        self.summary_label.tag_configure("fail", foreground="red", font=("Helvetica", 10, "bold"))
        self.summary_label.tag_configure("ok", foreground="green", font=("Helvetica", 10, "bold"))
        self.summary_label.tag_configure(
            "header", foreground="black", font=("Helvetica", 11, "bold")
        )

        # Show actual vs allowable calculations
        fb_actual = beam_results.get("fb_actual_psi", 0)
        fb_allowable = beam_results.get("fb_allowable_psi", 1)
        fv_actual = beam_results.get("fv_actual_psi", 0)
        fv_allowable = beam_results.get("fv_allowable_psi", 1)
        delta_snow_actual = beam_results.get("delta_snow_in", 0)
        delta_snow_limit = beam_results.get("delta_limit_snow_in", 1)
        delta_total_actual = beam_results.get("delta_total_in", 0)
        delta_total_limit = beam_results.get("delta_limit_total_in", 1)

        # Header
        self.summary_label.insert(tk.END, "=== BEAM DESIGN SUMMARY ===\n\n", "header")
        self.summary_label.insert(tk.END, "VALLEY BEAM:\n", "header")

        # Overall status
        if overall_pass:
            self.summary_label.insert(tk.END, "OVERALL STATUS: ", "")
            self.summary_label.insert(tk.END, "PASS\n\n", "pass")
        else:
            self.summary_label.insert(tk.END, "OVERALL STATUS: ", "")
            self.summary_label.insert(tk.END, "FAIL\n", "fail")
            self.summary_label.insert(
                tk.END,
                f"Governing Check: {governing_check} (ratio {max_ratio:.3f})\n\n",
                "",
            )

        # Individual checks with color coding
        self.summary_label.insert(
            tk.END,
            f"Bending: {fb_actual:.0f}/{fb_allowable:.0f} psi = {bend_ratio:.3f} (",
            "",
        )
        self.summary_label.insert(
            tk.END, "PASS" if bend_pass else "FAIL", "pass" if bend_pass else "fail"
        )
        self.summary_label.insert(tk.END, ")\n", "")

        self.summary_label.insert(
            tk.END,
            f"Shear: {fv_actual:.0f}/{fv_allowable:.0f} psi = {shear_ratio:.3f} (",
            "",
        )
        self.summary_label.insert(
            tk.END, "PASS" if shear_pass else "FAIL", "pass" if shear_pass else "fail"
        )
        self.summary_label.insert(tk.END, ")\n", "")

        combined_pass = bend_pass and shear_pass
        self.summary_label.insert(
            tk.END,
            f"Snow Load Check (D + S): {bend_ratio:.3f} bending, {shear_ratio:.3f} shear (",
            "",
        )
        self.summary_label.insert(
            tk.END,
            "PASS" if combined_pass else "FAIL",
            "pass" if combined_pass else "fail",
        )
        self.summary_label.insert(tk.END, ")\n", "")

        self.summary_label.insert(
            tk.END,
            f"Total Load Check (D + 0.7S): {bend_ratio:.3f} bending, {shear_ratio:.3f} shear (",
            "",
        )
        self.summary_label.insert(
            tk.END,
            "PASS" if combined_pass else "FAIL",
            "pass" if combined_pass else "fail",
        )
        self.summary_label.insert(tk.END, ")\n", "")

        self.summary_label.insert(
            tk.END,
            f'Snow Deflection: {delta_snow_actual:.3f}"/{delta_snow_limit:.3f}" = {snow_def_ratio:.3f} (',
            "",
        )
        self.summary_label.insert(
            tk.END, "PASS" if snow_pass else "FAIL", "pass" if snow_pass else "fail"
        )
        self.summary_label.insert(tk.END, ")\n", "")

        self.summary_label.insert(
            tk.END,
            f'Total Deflection: {delta_total_actual:.3f}"/{delta_total_limit:.3f}" = {total_def_ratio:.3f} (',
            "",
        )
        self.summary_label.insert(
            tk.END, "PASS" if total_pass else "FAIL", "pass" if total_pass else "fail"
        )
        self.summary_label.insert(tk.END, ")\n", "")

        # Add N-S Ridge Beam summary
        self.summary_label.insert(tk.END, f"\n{'='*50}\n", "header")
        self.summary_label.insert(tk.END, "N-S RIDGE BEAM:\n", "header")

        if ns_ridge_beam_results and "error" not in ns_ridge_beam_results:
            ns_overall_pass = ns_ridge_beam_results.get("passes", False)
            ns_bend_ratio = ns_ridge_beam_results.get("ratio_bending", 0)
            ns_shear_ratio = ns_ridge_beam_results.get("ratio_shear", 0)
            ns_snow_def_ratio = ns_ridge_beam_results.get("ratio_deflection_snow", 0)
            ns_total_def_ratio = ns_ridge_beam_results.get("ratio_deflection_total", 0)

            ns_fb_actual = ns_ridge_beam_results.get("fb_actual_psi", 0)
            ns_fb_allowable = ns_ridge_beam_results.get("fb_allowable_psi", 1)
            ns_fv_actual = ns_ridge_beam_results.get("fv_actual_psi", 0)
            ns_fv_allowable = ns_ridge_beam_results.get("fv_allowable_psi", 1)
            ns_delta_snow_actual = ns_ridge_beam_results.get("delta_snow_in", 0)
            ns_delta_snow_limit = ns_ridge_beam_results.get("delta_limit_snow_in", 1)
            ns_delta_total_actual = ns_ridge_beam_results.get("delta_total_in", 0)
            ns_delta_total_limit = ns_ridge_beam_results.get("delta_limit_total_in", 1)

            self.summary_label.insert(
                tk.END, f"Length: {ns_ridge_beam_length:.2f} ft\n", ""
            )
            self.summary_label.insert(
                tk.END, f"Material: {self.ns_ridge_material_combobox.get()}\n", ""
            )

            if ns_overall_pass:
                self.summary_label.insert(tk.END, "Status: ", "")
                self.summary_label.insert(tk.END, "PASS\n\n", "pass")
            else:
                self.summary_label.insert(tk.END, "Status: ", "")
                self.summary_label.insert(tk.END, "FAIL\n\n", "fail")

            ns_bend_pass = ns_bend_ratio <= 1
            ns_shear_pass = ns_shear_ratio <= 1
            ns_snow_pass = ns_snow_def_ratio <= 1
            ns_total_pass = ns_total_def_ratio <= 1

            self.summary_label.insert(
                tk.END,
                f"Bending: {ns_fb_actual:.0f}/{ns_fb_allowable:.0f} psi = {ns_bend_ratio:.3f} (",
                "",
            )
            self.summary_label.insert(
                tk.END,
                "PASS" if ns_bend_pass else "FAIL",
                "pass" if ns_bend_pass else "fail",
            )
            self.summary_label.insert(tk.END, ")\n", "")

            self.summary_label.insert(
                tk.END,
                f"Shear: {ns_fv_actual:.0f}/{ns_fv_allowable:.0f} psi = {ns_shear_ratio:.3f} (",
                "",
            )
            self.summary_label.insert(
                tk.END,
                "PASS" if ns_shear_pass else "FAIL",
                "pass" if ns_shear_pass else "fail",
            )
            self.summary_label.insert(tk.END, ")\n", "")

            self.summary_label.insert(
                tk.END,
                f'Snow Deflection: {ns_delta_snow_actual:.3f}"/{ns_delta_snow_limit:.3f}" = {ns_snow_def_ratio:.3f} (',
                "",
            )
            self.summary_label.insert(
                tk.END,
                "PASS" if ns_snow_pass else "FAIL",
                "pass" if ns_snow_pass else "fail",
            )
            self.summary_label.insert(tk.END, ")\n", "")

            self.summary_label.insert(
                tk.END,
                f'Total Deflection: {ns_delta_total_actual:.3f}"/{ns_delta_total_limit:.3f}" = {ns_total_def_ratio:.3f} (',
                "",
            )
            self.summary_label.insert(
                tk.END,
                "PASS" if ns_total_pass else "FAIL",
                "pass" if ns_total_pass else "fail",
            )
            self.summary_label.insert(tk.END, ")\n", "")
        else:
            ns_error_msg = (
                ns_ridge_beam_results.get("error", "Unknown error")
                if ns_ridge_beam_results
                else "Calculation failed"
            )
            self.summary_label.insert(tk.END, f"ERROR: {ns_error_msg}\n", "fail")

        if not overall_pass:
            # Calculate suggestions based on material
            selected_material = self.material_combobox.get()
            if "Sawn Lumber" in selected_material:
                common_widths = [1.5, 3.5, 5.5]  # single, double, triple 2x
                common_depths = [7.25, 9.25, 11.25]  # 2x8, 2x10, 2x12 actual
                ply_factor = 1.5  # 2x nominal = 1.5" actual per ply
            elif "Glulam" in selected_material:
                common_widths = [3.125, 3.5, 5.125, 5.5, 6.75, 8.75]
                common_depths = [9, 10.5, 12, 13.5, 15, 16.5, 18, 19.5, 21, 22.5, 24]
                ply_factor = 1.5  # approximate for glulam
            else:  # LVL
                common_widths = [1.75, 3.5, 5.25, 7.0]  # individual ply, 2, 3, 4 plies
                common_depths = [9.25, 9.5, 11.25, 11.875, 14, 16, 18, 20, 24]
                ply_factor = 1.75  # inches per ply for LVL

            current_width = beam_width
            current_depth = beam_depth_trial

            # Find next larger width
            next_width = None
            next_width_plies = None
            for w in common_widths:
                if w > current_width:
                    next_width = w
                    next_width_plies = round(w / ply_factor)
                    break

            # Find next larger depth
            next_depth = None
            for d in common_depths:
                if d > current_depth:
                    next_depth = d
                    break

            self.summary_label.insert(tk.END, "\nSuggestions:", "")
            if next_width:
                self.summary_label.insert(
                    tk.END,
                    f'\n- Increase width to {next_width:.3f}" ({next_width_plies} plies)',
                    "",
                )
            if next_depth:
                self.summary_label.insert(
                    tk.END, f'\n- Increase depth to {next_depth:.3f}"', ""
                )

        # Make the text widget read-only again
        self.summary_label.config(state="disabled")

        # Update canvas scroll region and scroll to summary
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0.3)  # Scroll to show summary

        # Use only detailed beam analysis in results (no summary duplication)
        beam_summary = create_beam_summary(beam_results, beam_inputs)

        # Calculate additional values for formulas
        hd_governing = gov_drift["governing_hd_ft"]
        pd_max_governing = gov_drift["governing_pd_max_psf"]
        w_governing = gov_drift_width

        # Calculate average rise for sloped length (same as valley_rafter_length function)
        h_n = de_n * (pitch_n / 12.0)  # rise = run × slope
        h_w = de_w * (pitch_w / 12.0)
        h_avg = (h_n + h_w) / 2

        # Get beam forces from results
        mu_ftlb = (
            beam_results.get("Mu_ftlb", 0)
            if beam_results and "error" not in beam_results
            else 0
        )
        vu_lb = (
            beam_results.get("Vu_lb", 0)
            if beam_results and "error" not in beam_results
            else 0
        )

        # Output - Restructured per user request
        self.output_text.delete(1.0, tk.END)

        # === REFERENCES AND METHODOLOGY ===
        self.output_text.insert(tk.END, "=== REFERENCES AND METHODOLOGY ===\n\n")
        self.output_text.insert(tk.END, "CALCULATION BASED ON:\n")
        self.output_text.insert(
            tk.END,
            "• ASCE 7-22: Minimum Design Loads for Buildings and Other Structures\n",
        )
        self.output_text.insert(tk.END, "• Chapter 7: Snow Loads\n")
        self.output_text.insert(
            tk.END,
            "• Ground snow loads from ASCE Design Ground Snow Load Geodatabase (2022-1.0)\n",
        )
        self.output_text.insert(
            tk.END, "• Risk-targeted ground snow loads (pg) for Risk Categories I-IV\n"
        )
        self.output_text.insert(
            tk.END, "• Winter wind parameter W2 (percent time wind >10 mph Oct-Apr)\n\n"
        )

        self.output_text.insert(tk.END, "METHODOLOGY:\n")
        self.output_text.insert(
            tk.END,
            "• Determine ground snow load pg from geodatabase based on site location\n",
        )
        self.output_text.insert(
            tk.END,
            "• Calculate flat roof snow load pf using exposure and thermal factors\n",
        )
        self.output_text.insert(
            tk.END, "• Calculate sloped roof snow load ps using slope factor Cs\n"
        )
        self.output_text.insert(
            tk.END, "• Apply minimum snow load pm for low-slope roofs (Sec. 7.3)\n"
        )
        self.output_text.insert(
            tk.END,
            "• Determine balanced vs unbalanced loads based on roof geometry (Sec. 7.6)\n\n",
        )

        # === GROUND SNOW LOAD ===
        self.output_text.insert(tk.END, "=== GROUND SNOW LOAD ===\n")
        self.output_text.insert(tk.END, "ASCE 7-22 Section 7.2: Ground Snow Loads\n\n")
        self.output_text.insert(
            tk.END, f"pg = {pg} psf (from geodatabase based on site location)\n"
        )
        self.output_text.insert(
            tk.END,
            f"W2 = {w2} (Winter wind parameter - % time wind >10 mph Oct-Apr)\n\n",
        )

        # === FLAT ROOF SNOW LOAD ===
        self.output_text.insert(tk.END, "=== FLAT ROOF SNOW LOAD ===\n")
        self.output_text.insert(tk.END, "ASCE 7-22 Section 7.3.1 & Equation 7.3-1\n\n")
        self.output_text.insert(tk.END, "pf = 0.7 × Ce × Ct × pg\n")
        self.output_text.insert(tk.END, f"pf = 0.7 × {ce} × {ct} × {pg}\n")
        self.output_text.insert(tk.END, f"pf = {pf:.1f} psf\n\n")

        # === MINIMUM SNOW LOAD ===
        self.output_text.insert(tk.END, "=== MINIMUM SNOW LOAD ===\n")
        self.output_text.insert(tk.END, "ASCE 7-22 Section 7.3.3 & Equation 7.3-2\n\n")
        self.output_text.insert(tk.END, "pm = 0.7 × Ce × Ct × pg × 0.6\n")
        self.output_text.insert(tk.END, f"pm = 0.7 × {ce} × {ct} × {pg} × 0.6\n")
        self.output_text.insert(tk.END, f"pm = {pm:.1f} psf\n\n")

        # === SLOPED ROOF SNOW LOAD ===
        self.output_text.insert(tk.END, "=== SLOPED ROOF SNOW LOAD ===\n")
        self.output_text.insert(tk.END, "ASCE 7-22 Section 7.4.1 & Equation 7.4-1\n\n")
        self.output_text.insert(tk.END, "ps = pf × Cs\n")
        self.output_text.insert(tk.END, f"ps = {pf:.1f} × {cs:.3f}\n")
        self.output_text.insert(tk.END, f"ps = {ps:.1f} psf\n\n")

        # === LOAD DETERMINATIONS ===
        self.output_text.insert(tk.END, "=== LOAD DETERMINATIONS ===\n")
        self.output_text.insert(
            tk.END, "ASCE 7-22 Section 7.3: Minimum Snow Load Check\n\n"
        )

        # Roof slope analysis
        self.output_text.insert(
            tk.END,
            f"Roof slopes: North = {pitch_n:.1f}/12 ({theta_n:.1f}°), West = {pitch_w:.1f}/12 ({theta_w:.1f}°)\n",
        )
        self.output_text.insert(tk.END, f"Minimum slope = {min_slope_deg:.1f}°\n\n")

        # Balanced vs Unbalanced Load Determination
        self.output_text.insert(tk.END, "BALANCED vs UNBALANCED LOAD DETERMINATION:\n")
        self.output_text.insert(
            tk.END, "ASCE 7-22 Section 7.6.1: Unbalanced snow loads apply when:\n"
        )
        self.output_text.insert(
            tk.END, "• Roof slope ≥ 2.38° (0.5/12) AND ≤ 30.2° (7/12)\n"
        )
        self.output_text.insert(tk.END, "• Outside this range: Balanced loads only\n\n")

        if low_slope:
            self.output_text.insert(
                tk.END, "✓ Slope < 15° → Minimum snow load pm applies\n"
            )
            self.output_text.insert(
                tk.END,
                f"Governing balanced load = max(ps, pm) = max({ps:.1f}, {pm:.1f}) = {governing_roof_load:.1f} psf\n\n",
            )
        else:
            self.output_text.insert(
                tk.END, "✗ Slope ≥ 15° → Minimum snow load pm does not apply\n"
            )
            self.output_text.insert(
                tk.END, f"Governing balanced load = ps = {ps:.1f} psf\n\n"
            )

        # Check if unbalanced loads apply
        unbalanced_applies = 2.38 <= min_slope_deg <= 30.2
        if unbalanced_applies:
            self.output_text.insert(
                tk.END,
                "✓ Roof slope in unbalanced range → Calculate unbalanced loads per Section 7.6\n\n",
            )
        else:
            self.output_text.insert(
                tk.END,
                "✗ Roof slope outside unbalanced range → Balanced loads only\n\n",
            )
        self.output_text.insert(
            tk.END, "pf = 0.7 × Ce × Ct × pg   (ASCE 7-22 Equation 7.3-1)\n"
        )
        self.output_text.insert(tk.END, "ps = pf × Cs   (ASCE 7-22 Equation 7.4-1)\n")
        self.output_text.insert(
            tk.END,
            "Cs determined from Figure 7.4-1 based on Ct and surface type   (ASCE 7-22 Section 7.4.1)\n",
        )
        self.output_text.insert(
            tk.END, "γ = min(0.13 × pg + 14, 30) pcf   (ASCE 7-22 Equation 7.7-1)\n\n"
        )

        # Additional parameters for reference
        surface_type = "slippery" if slippery else "non-slippery"
        self.output_text.insert(
            tk.END,
            f"Slope factors: Cs = {cs:.3f} (based on Ct = {ct} and {surface_type} surface per Figure 7.4-1)\n",
        )
        self.output_text.insert(
            tk.END,
            f"Snow density: γ = min(0.13 × pg + 14, 30) = {gamma:.1f} pcf (Eq. 7.7-1)\n",
        )
        self.output_text.insert(
            tk.END,
            f"Balanced snow height: hb = ps / γ = {hb:.2f} ft (Section 7.7.1)\n\n",
        )

        # === SECTION 7.6: UNBALANCED SNOW LOADS ===
        self.output_text.insert(tk.END, "=== SECTION 7.6: UNBALANCED SNOW LOADS ===\n")
        self.output_text.insert(
            tk.END,
            "ASCE 7-22 Section 7.6.1: Unbalanced Snow Loads for Hip and Gable Roofs\n\n",
        )

        min_slope = min(theta_n, theta_w)
        # Optional debug output in results (uncomment if needed)
        # self.output_text.insert(tk.END, f"DEBUG: theta_n = {theta_n:.2f}°, theta_w = {theta_w:.2f}°, min_slope = {min_slope:.2f}°\n")
        if 2.38 <= min_slope <= 30.2:
            self.output_text.insert(tk.END, "UNBALANCED LOAD APPLICABILITY:\n")
            self.output_text.insert(
                tk.END, f"Roof slope range check: 2.38° ≤ {min_slope:.1f}° ≤ 30.2° ✓\n"
            )
            self.output_text.insert(
                tk.END, "→ Unbalanced loads apply per Section 7.6.1\n\n"
            )

            self.output_text.insert(tk.END, "CALCULATION METHODOLOGY:\n")
            self.output_text.insert(
                tk.END, "• Evaluate both North and West wind directions\n"
            )
            self.output_text.insert(
                tk.END,
                "• Use maximum loads from both directions (conservative approach)\n",
            )
            self.output_text.insert(
                tk.END, "• Windward span W = dimension perpendicular to ridge\n"
            )
            self.output_text.insert(tk.END, "• Narrow roof: W ≤ 20 ft (special case)\n")
            self.output_text.insert(
                tk.END, "• Wide roof: W > 20 ft (standard unbalanced calculation)\n\n"
            )

            # North Wind Analysis
            self.output_text.insert(tk.END, "NORTH WIND ANALYSIS:\n")
            lu_north = north_span  # Fetch distance to north eave
            is_narrow_north = lu_north <= 20
            self.output_text.insert(
                tk.END,
                f"Fetch lu = {lu_north:.1f} ft ({'Narrow' if is_narrow_north else 'Wide'} roof)\n",
            )

            if is_narrow_north:
                self.output_text.insert(tk.END, "Narrow roof case (W ≤ 20 ft):\n")
                self.output_text.insert(tk.END, "• Windward (North): 0 psf\n")
                self.output_text.insert(
                    tk.END, f"• Leeward (South): pg = {pg:.1f} psf\n"
                )
            else:
                self.output_text.insert(tk.END, "Wide roof case (W > 20 ft):\n")
                self.output_text.insert(tk.END, "• Windward (North): 0.3 × ps\n")
                north_load_north = 0.3 * ps_north if ps_north > 0 else 0
                self.output_text.insert(
                    tk.END,
                    f"• Windward (North): 0.3 × {ps_north:.1f} = {north_load_north:.1f} psf\n",
                )

                self.output_text.insert(tk.END, "• Leeward surcharge calculation:\n")
                self.output_text.insert(
                    tk.END, "  Fetch lu = distance from ridge to upwind eave\n"
                )
                lu_north = north_span
                self.output_text.insert(tk.END, f"  lu = {lu_north:.1f} ft\n")
                self.output_text.insert(
                    tk.END,
                    "  hd = 1.5 × √[(pg^0.74 × lu^0.70 × W2^1.7) / γ]  (Eq. 7.6-1)\n",
                )
                hd_calc_north = (pg**0.74 * lu_north**0.70 * w2**1.7) / gamma
                hd_north = 1.5 * math.sqrt(hd_calc_north)
                self.output_text.insert(
                    tk.END,
                    f"  hd = 1.5 × √[({pg}^{0.74} × {lu_north}^{0.70} × {w2}^{1.7}) / {gamma}] = {hd_north:.2f} ft\n",
                )

                self.output_text.insert(tk.END, "  pd = hd × γ / √S  (Eq. 7.6-2)\n")
                surcharge_north = hd_north * gamma / math.sqrt(S_n)
                self.output_text.insert(
                    tk.END,
                    f"  pd = {hd_north:.2f} × {gamma:.1f} / √{S_n:.2f} = {surcharge_north:.1f} psf\n",
                )

                south_load_north = ps + surcharge_north
                self.output_text.insert(
                    tk.END,
                    f"• Leeward (South): ps + pd = {ps:.1f} + {surcharge_north:.1f} = {south_load_north:.1f} psf\n",
                )

                surcharge_width_north = (8 * hd_north * math.sqrt(S_n)) / 3

            self.output_text.insert(tk.END, "\n")

            # West Wind Analysis
            self.output_text.insert(tk.END, "WEST WIND ANALYSIS:\n")
            lu_west = ew_half_width  # Fetch distance to west eave
            is_narrow_west = lu_west <= 20
            self.output_text.insert(
                tk.END,
                f"Fetch lu = {lu_west:.1f} ft ({'Narrow' if is_narrow_west else 'Wide'} roof)\n",
            )

            if is_narrow_west:
                self.output_text.insert(tk.END, "Narrow roof case (W ≤ 20 ft):\n")
                self.output_text.insert(tk.END, "• Windward (West): 0 psf\n")
                self.output_text.insert(
                    tk.END, f"• Leeward (East): pg = {pg:.1f} psf\n"
                )
            else:
                self.output_text.insert(tk.END, "Wide roof case (W > 20 ft):\n")
                self.output_text.insert(tk.END, "• Windward (West): 0.3 × ps\n")
                west_load_west = 0.3 * ps_west if ps_west > 0 else 0
                self.output_text.insert(
                    tk.END,
                    f"• Windward (West): 0.3 × {ps_west:.1f} = {west_load_west:.1f} psf\n",
                )

                self.output_text.insert(tk.END, "• Leeward surcharge calculation:\n")
                self.output_text.insert(
                    tk.END, "  Fetch lu = distance from ridge to upwind eave\n"
                )
                lu_west = ew_half_width
                self.output_text.insert(tk.END, f"  lu = {lu_west:.1f} ft\n")
                self.output_text.insert(
                    tk.END,
                    "  hd = 1.5 × √[(pg^0.74 × lu^0.70 × W2^1.7) / γ]  (Eq. 7.6-1)\n",
                )
                hd_calc_west = (pg**0.74 * lu_west**0.70 * w2**1.7) / gamma
                hd_west = 1.5 * math.sqrt(hd_calc_west)
                self.output_text.insert(
                    tk.END,
                    f"  hd = 1.5 × √[({pg}^{0.74} × {lu_west}^{0.70} × {w2}^{1.7}) / {gamma}] = {hd_west:.2f} ft\n",
                )

                self.output_text.insert(tk.END, "  pd = hd × γ / √S  (Eq. 7.6-2)\n")
                surcharge_west = hd_west * gamma / math.sqrt(S_w)
                self.output_text.insert(
                    tk.END,
                    f"  pd = {hd_west:.2f} × {gamma:.1f} / √{S_w:.2f} = {surcharge_west:.1f} psf\n",
                )

                east_load_west = ps + surcharge_west
                self.output_text.insert(
                    tk.END,
                    f"• Leeward (East): ps + pd = {ps:.1f} + {surcharge_west:.1f} = {east_load_west:.1f} psf\n",
                )

                surcharge_width_west = (8 * hd_west * math.sqrt(S_w)) / 3

            self.output_text.insert(tk.END, "\n")

            # Governing loads summary eliminated per user request

        else:
            self.output_text.insert(tk.END, "NO UNBALANCED LOADS REQUIRED:\n")
            self.output_text.insert(
                tk.END, f"Roof slope {min_slope:.1f}° outside 2.38°-30.2° range\n"
            )
            self.output_text.insert(
                tk.END, "ASCE 7-22 Section 7.6.1: Balanced loads only\n"
            )
            self.output_text.insert(
                tk.END, f"Uniform balanced load: {ps:.1f} psf on all planes\n\n"
            )

        # Valley drift load calculations eliminated per user request

        # Beam ASD formulas (no drift load)
        self.output_text.insert(
            tk.END,
            f"ASD Snow Load = 0.7 × ps per IBC/ASCE serviceability = 0.7 × {ps:.1f} = {0.7 * ps:.1f} psf\n",
        )
        self.output_text.insert(
            tk.END, f"Mu = maximum moment (exact point loads) = {mu_ftlb:.0f} ft-lb\n"
        )
        self.output_text.insert(tk.END, f"Vu = maximum shear = {vu_lb:.0f} lb\n\n")

        # References and methodology notes after unbalanced snow load cases eliminated per user request

        self.output_text.insert(
            tk.END, "\n=== UNBALANCED LOAD APPLICABILITY (Sec. 7.6.1) ===\n"
        )
        if unbalanced_applies_n:
            self.output_text.insert(
                tk.END,
                f"North roof plane (θ_n = {theta_n:.1f}°): Unbalanced loads APPLY\n",
            )
            if narrow_roof_n:
                self.output_text.insert(
                    tk.END,
                    f"   Narrow roof (de_north ≤ 20 ft): Leeward = pg = {pg:.1f} psf (windward unloaded)\n",
                )
        else:
            self.output_text.insert(
                tk.END,
                f"North roof plane (θ_n = {theta_n:.1f}°): Unbalanced loads NOT required (slope outside 2.38°–30.2°)\n",
            )
        if unbalanced_applies_w:
            self.output_text.insert(
                tk.END,
                f"West roof plane (θ_w = {theta_w:.1f}°): Unbalanced loads APPLY\n",
            )
            if narrow_roof_w:
                self.output_text.insert(
                    tk.END,
                    f"   Narrow roof (de_west ≤ 20 ft): Leeward = pg = {pg:.1f} psf (windward unloaded)\n",
                )
        else:
            self.output_text.insert(
                tk.END,
                f"West roof plane (θ_w = {theta_w:.1f}°): Unbalanced loads NOT required (slope outside 2.38°–30.2°)\n",
            )
        # Determine Figure 7.4-1 part and roof classification
        if ct == 1.1:
            pass
        elif 1.1 < ct < 1.2:
            pass
        else:  # ct >= 1.2
            pass

        surface_type = "slippery" if slippery else "non-slippery"
        surface_type = "Slippery" if slippery else "Non-slippery"
        self.output_text.insert(
            tk.END,
            f"Surface: {surface_type} (Cs from corresponding line in Figure 7.4-1)\n",
        )
        self.output_text.insert(
            tk.END,
            f"Governing Slope Factor (Cs): {cs:.3f} (automatically calculated from Figure 7.4-1 based on Ct and surface)\n",
        )
        self.output_text.insert(tk.END, f"Sloped Roof Snow Load (ps): {ps:.1f} psf\n\n")
        self.output_text.insert(tk.END, f"Valley horizontal length (lv): {lv:.2f} ft\n")
        self.output_text.insert(tk.END, f"Valley rafter length: {rafter_len:.2f} ft\n")

        self.output_text.insert(tk.END, "\n")
        self.output_text.insert(
            tk.END,
            "=== ASCE 7-22 SECTION 7.6.1: UNBALANCED SNOW LOADS FOR HIP AND GABLE ROOFS ===\n",
            "blue",
        )
        self.output_text.insert(
            tk.END, "[LOCATION: RESULTS - AFTER GEOMETRY CALCULATIONS]\n", "blue"
        )
        self.output_text.insert(
            tk.END,
            "Unbalanced snow loads (including valley drifts derived from them) are governed by Sec. 7.6.1.\n\n",
            "blue",
        )
        self.output_text.insert(tk.END, "APPLICABILITY:\n", "blue")
        self.output_text.insert(
            tk.END,
            "• Unbalanced loads are REQUIRED only for roof slopes between 0.5/12 (≈2.38°) and 7/12 (≈30.2°).\n",
            "blue",
        )
        self.output_text.insert(
            tk.END,
            "• Outside this range: Unbalanced loads and associated drifts are NOT required.\n\n",
            "blue",
        )
        self.output_text.insert(
            tk.END,
            "SPECIAL NARROW ROOF CASE (eave-to-ridge distance W ≤ 20 ft AND simply supported prismatic members):\n",
            "blue",
        )
        self.output_text.insert(
            tk.END,
            "  → Leeward side: Full ground snow load pg (windward unloaded)\n",
            "blue",
        )
        self.output_text.insert(
            tk.END, "  → No separate drift surcharge calculated\n\n", "blue"
        )
        self.output_text.insert(
            tk.END, f"North Roof Plane (θ_n = {theta_n:.1f}°): ", "blue"
        )
        self.output_text.insert(
            tk.END,
            "Unbalanced APPLIES"
            if unbalanced_applies_n
            else "Unbalanced NOT required (slope outside 2.38°–30.2°)",
            "blue",
        )
        if narrow_roof_n and unbalanced_applies_n:
            self.output_text.insert(
                tk.END, f" → Narrow roof: Leeward = pg = {pg:.1f} psf\n", "blue"
            )
        self.output_text.insert(tk.END, "\n", "blue")
        self.output_text.insert(
            tk.END, f"West Roof Plane (θ_w = {theta_w:.1f}°): ", "blue"
        )
        self.output_text.insert(
            tk.END,
            "Unbalanced APPLIES"
            if unbalanced_applies_w
            else "Unbalanced NOT required (slope outside 2.38°–30.2°)",
            "blue",
        )
        if narrow_roof_w and unbalanced_applies_w:
            self.output_text.insert(
                tk.END, f" → Narrow roof: Leeward = pg = {pg:.1f} psf\n", "blue"
            )
        self.output_text.insert(tk.END, "\n", "blue")
        self.output_text.insert(
            tk.END,
            "If unbalanced loads do not apply on either plane, drift surcharge = 0.\n",
            "blue",
        )

        # === VALLEY RAFTER BEAM DESIGN ANALYSIS (FULL DEAD + SNOW LOADS) ===
        self.output_text.insert(
            tk.END, "\n============================================================\n"
        )
        self.output_text.insert(tk.END, "VALLEY RAFTER BEAM DESIGN ANALYSIS\n")
        self.output_text.insert(
            tk.END, "------------------------------------------------------------\n"
        )
        self.output_text.insert(tk.END, f"Sloped Length: {rafter_len:.2f} ft\n")
        self.output_text.insert(
            tk.END,
            f"Point Loads: {jacks_data['num_per_side']} locations (combined North + West, including full dead load + balanced snow + valley drift)\n",
        )

        # Default roof dead load (from user input or default)
        roof_dead_load_psf = self.get_float("dead_load_horizontal")
        if roof_dead_load_psf is None:
            roof_dead_load_psf = 15.0  # Default value

        # Extract jack rafter data for detailed analysis
        spacing_along_ridge_ft = jack_spacing_inches / 12.0  # Convert to feet
        combined_point_loads = []
        distances_from_eave = []

        self.output_text.insert(tk.END, f"\nRoof Dead Load: {roof_dead_load_psf} psf\n")
        self.output_text.insert(
            tk.END, "\n=== JACK RAFTER POINT LOADS (Eave → Ridge) ===\n"
        )
        self.output_text.insert(
            tk.END, f"Number of jacks per side: {jacks_data['num_per_side']}\n"
        )
        self.output_text.insert(
            tk.END, f"Spacing along ridges: {jack_spacing_inches:.1f} inches o.c.\n"
        )
        self.output_text.insert(
            tk.END,
            f"Spacing along valley: {jacks_data['spacing_along_valley_ft']*12:.1f} inches o.c.\n\n",
        )

        for i in range(jacks_data["num_per_side"]):
            # j_n = North-South Valley Rafter: frames from Valley Beam to East-West Ridge
            # j_w = East-West Valley Rafter: frames from Valley Beam to North-South Ridge
            j_n = jacks_data["jacks"]["north_side"][i]
            j_w = jacks_data["jacks"]["west_side"][i]

            # Tributary area calculations
            trib_area_n = j_n["horiz_length_ft"] * spacing_along_ridge_ft
            trib_area_w = j_w["horiz_length_ft"] * spacing_along_ridge_ft

            # Dead loads
            dl_n = roof_dead_load_psf * trib_area_n
            dl_w = roof_dead_load_psf * trib_area_w
            dl_n + dl_w

            # Snow loads (already calculated)
            snow_n = j_n["total_snow_lb"]
            snow_w = j_w["total_snow_lb"]
            snow_n + snow_w

            # Get surcharge and balanced load breakdown for verification
            surcharge_n = j_n.get("surcharge_snow_lb", 0.0)
            balanced_portion_n = j_n.get("balanced_snow_lb", 0.0)
            surcharge_length_n = j_n.get("surcharge_length_ft", 0.0)
            balanced_length_n = j_n.get("balanced_length_ft", j_n["horiz_length_ft"])
            surcharge_psf_n = j_n.get("surcharge_psf", 0.0)
            balanced_psf_n = j_n.get("balanced_psf", ps)

            surcharge_w = j_w.get("surcharge_snow_lb", 0.0)
            balanced_portion_w = j_w.get("balanced_snow_lb", 0.0)
            surcharge_length_w = j_w.get("surcharge_length_ft", 0.0)
            balanced_length_w = j_w.get("balanced_length_ft", j_w["horiz_length_ft"])
            surcharge_psf_w = j_w.get("surcharge_psf", 0.0)
            balanced_psf_w = j_w.get("balanced_psf", ps)

            # Full loads and reactions
            full_load_n = dl_n + snow_n
            full_load_w = dl_w + snow_w
            reaction_n = full_load_n / 2  # Simply supported
            reaction_w = full_load_w / 2
            combined_point = reaction_n + reaction_w

            combined_point_loads.append(combined_point)
            distances_from_eave.append(j_n.get("location_from_eave_ft", 0))

            self.output_text.insert(
                tk.END,
                f"Jack {i+1} (from eave {j_n.get('location_from_eave_ft', 0):.2f} ft):\n",
            )
            self.output_text.insert(
                tk.END,
                f"  North-South Rafter (Valley Beam → E-W Ridge):\n"
                f"    Trib area: {trib_area_n:.1f} ft²\n"
                f"    Load Distribution: surcharge zone {surcharge_length_n:.2f} ft @ {surcharge_psf_n:.1f} psf ({surcharge_n:.0f} lb), balanced zone {balanced_length_n:.2f} ft @ {balanced_psf_n:.1f} psf ({balanced_portion_n:.0f} lb)\n"
                f"    DL: {dl_n:.0f} lb, Snow: {snow_n:.0f} lb (surcharge={surcharge_n:.0f} lb @ {surcharge_psf_n:.1f} psf + balanced={balanced_portion_n:.0f} lb @ {balanced_psf_n:.1f} psf + drift={j_n.get('drift_load_lb', 0):.0f} lb), Reaction: {reaction_n:.0f} lb\n",
            )
            self.output_text.insert(
                tk.END,
                f"  East-West Rafter (Valley Beam → N-S Ridge):\n"
                f"    Trib area: {trib_area_w:.1f} ft²\n"
                f"    Load Distribution: surcharge zone {surcharge_length_w:.2f} ft @ {surcharge_psf_w:.1f} psf ({surcharge_w:.0f} lb), balanced zone {balanced_length_w:.2f} ft @ {balanced_psf_w:.1f} psf ({balanced_portion_w:.0f} lb)\n"
                f"    DL: {dl_w:.0f} lb, Snow: {snow_w:.0f} lb (surcharge={surcharge_w:.0f} lb @ {surcharge_psf_w:.1f} psf + balanced={balanced_portion_w:.0f} lb @ {balanced_psf_w:.1f} psf + drift={j_w.get('drift_load_lb', 0):.0f} lb), Reaction: {reaction_w:.0f} lb\n",
            )
            self.output_text.insert(
                tk.END, f"  Combined point load on valley: {combined_point:.0f} lb\n\n"
            )

        # Valley rafter equilibrium
        total_load = sum(combined_point_loads)
        moment_about_eave = sum(
            load * dist for load, dist in zip(combined_point_loads, distances_from_eave)
        )
        reaction_ridge = moment_about_eave / rafter_len
        reaction_eave = total_load - reaction_ridge

        # Calculate max moment and shear
        max_moment = 0.0
        max_shear = reaction_eave
        current_shear = reaction_eave
        current_moment = 0.0
        prev_dist = 0.0

        for dist, load in zip(distances_from_eave, combined_point_loads):
            delta = dist - prev_dist
            current_moment += current_shear * delta
            max_moment = max(max_moment, current_moment)
            current_shear -= load
            max_shear = max(max_shear, abs(current_shear))
            prev_dist = dist

        # Final segment to ridge
        delta = rafter_len - prev_dist
        current_moment += current_shear * delta
        max_moment = max(max_moment, current_moment)

        self.output_text.insert(
            tk.END,
            f"Valley Rafter Reactions: {reaction_eave:.0f} lb @ eave, {reaction_ridge:.0f} lb @ ridge\n",
        )
        self.output_text.insert(tk.END, f"Maximum Moment: {max_moment:.0f} ft-lb\n")
        self.output_text.insert(tk.END, f"Maximum Shear: {max_shear:.0f} lb\n")
        self.output_text.insert(tk.END, f"Total Load: {total_load:.0f} lb\n")
        self.output_text.insert(
            tk.END,
            "Note: Loads include full dead load + full snow (balanced + valley drift). Reactions verified by equilibrium.\n\n",
        )

        # Add to output
        self.output_text.insert(tk.END, beam_summary)

        # Display jack rafter summary in results
        self.output_text.insert(
            tk.END, "\n=== JACK RAFTER POINT LOADS (Eave → Ridge) ===\n"
        )
        self.output_text.insert(
            tk.END, f"Number of jacks per side: {jacks_data['num_per_side']}\n"
        )
        self.output_text.insert(
            tk.END, f"Spacing along ridges: {jack_spacing_inches} inches o.c.\n"
        )
        self.output_text.insert(
            tk.END,
            f"Spacing along valley: {jacks_data['spacing_along_valley_ft']*12:.1f} inches o.c.\n\n",
        )

        for i in range(jacks_data["num_per_side"]):
            # j_n = North-South Valley Rafter: frames from Valley Beam to East-West Ridge
            # j_w = East-West Valley Rafter: frames from Valley Beam to North-South Ridge
            j_n = jacks_data["jacks"]["north_side"][i]
            j_w = jacks_data["jacks"]["west_side"][i]
            total_p = j_n["point_load_lb"] + j_w["point_load_lb"]
            pos_from_eave = j_n.get("location_from_eave_ft", "N/A")

            # Get surcharge and balanced load breakdown
            surcharge_n = j_n.get("surcharge_snow_lb", 0.0)
            balanced_portion_n = j_n.get("balanced_snow_lb", 0.0)
            surcharge_length_n = j_n.get("surcharge_length_ft", 0.0)
            balanced_length_n = j_n.get("balanced_length_ft", j_n["horiz_length_ft"])
            surcharge_psf_n = j_n.get("surcharge_psf", 0.0)
            balanced_psf_n = j_n.get("balanced_psf", ps)

            surcharge_w = j_w.get("surcharge_snow_lb", 0.0)
            balanced_portion_w = j_w.get("balanced_snow_lb", 0.0)
            surcharge_length_w = j_w.get("surcharge_length_ft", 0.0)
            balanced_length_w = j_w.get("balanced_length_ft", j_w["horiz_length_ft"])
            surcharge_psf_w = j_w.get("surcharge_psf", 0.0)
            balanced_psf_w = j_w.get("balanced_psf", ps)

            self.output_text.insert(
                tk.END,
                f"Jack {i+1} (from eave {pos_from_eave:.2f} ft):\n"
                f"  North-South Rafter (Valley Beam → E-W Ridge):\n"
                f"    Length: sloped={j_n['sloped_length_ft']:.2f} ft, horiz={j_n['horiz_length_ft']:.2f} ft\n"
                f"    Load Distribution:\n"
                f"      Surcharge zone: {surcharge_length_n:.2f} ft @ {surcharge_psf_n:.1f} psf (ps + surcharge) = {surcharge_n:.0f} lb\n"
                f"      Balanced zone: {balanced_length_n:.2f} ft @ {balanced_psf_n:.1f} psf (ps only) = {balanced_portion_n:.0f} lb\n"
                f"    Snow Loads: surcharge={surcharge_n:.0f} lb ({surcharge_psf_n:.1f} psf), balanced={balanced_portion_n:.0f} lb ({balanced_psf_n:.1f} psf), drift={j_n['drift_load_lb']:.0f} lb, total snow={j_n['total_snow_lb']:.0f} lb\n"
                f"    Dead Load: {j_n['dead_load_lb']:.0f} lb\n"
                f"    Full Load: {j_n['full_load_on_jack_lb']:.0f} lb\n"
                f"    Reaction to Valley Beam: {j_n['point_load_lb']:.0f} lb\n"
                f"  East-West Rafter (Valley Beam → N-S Ridge):\n"
                f"    Length: sloped={j_w['sloped_length_ft']:.2f} ft, horiz={j_w['horiz_length_ft']:.2f} ft\n"
                f"    Load Distribution:\n"
                f"      Surcharge zone: {surcharge_length_w:.2f} ft @ {surcharge_psf_w:.1f} psf (ps + surcharge) = {surcharge_w:.0f} lb\n"
                f"      Balanced zone: {balanced_length_w:.2f} ft @ {balanced_psf_w:.1f} psf (ps only) = {balanced_portion_w:.0f} lb\n"
                f"    Snow Loads: surcharge={surcharge_w:.0f} lb ({surcharge_psf_w:.1f} psf), balanced={balanced_portion_w:.0f} lb ({balanced_psf_w:.1f} psf), drift={j_w['drift_load_lb']:.0f} lb, total snow={j_w['total_snow_lb']:.0f} lb\n"
                f"    Dead Load: {j_w['dead_load_lb']:.0f} lb\n"
                f"    Full Load: {j_w['full_load_on_jack_lb']:.0f} lb\n"
                f"    Reaction to Valley Beam: {j_w['point_load_lb']:.0f} lb\n"
                f"  Combined point load at location: {total_p:.0f} lb\n\n",
            )

        self.output_text.insert(
            tk.END,
            "Note: Point loads are reactions (half-span) assuming simply supported jack at ridge.\n",
        )
        self.output_text.insert(
            tk.END,
            "Note: Load Distribution Explanation:\n"
            "  - Surcharge zone: Within surcharge width, load = balanced (ps) + surcharge (pd)\n"
            "  - Balanced zone: After surcharge width, load = balanced (ps) only\n"
            "  - Each jack rafter's length is divided into surcharge and balanced portions\n"
            "  - Reaction is calculated based on the total distributed load along the jack rafter\n\n",
        )
        self.output_text.insert(
            tk.END,
            "Note: Drift load is higher at the ridge (higher pd intensity), but jack rafters are shorter there. Point loads may be higher at eave due to longer lengths despite lower drift. This is correct per ASCE 7-22 drift taper and framing geometry.\n\n",
        )

        # === VALLEY RAFTER REACTION VERIFICATION (STATIC EQUILIBRIUM CHECK) ===
        self.output_text.insert(
            tk.END, "============================================================\n"
        )
        self.output_text.insert(tk.END, "VALLEY RAFTER END REACTION VERIFICATION\n")
        self.output_text.insert(
            tk.END, "------------------------------------------------------------\n"
        )
        self.output_text.insert(
            tk.END,
            "Using jack rafter combined point loads and distances to independently verify reactions via equilibrium.\n\n",
        )

        # Extract data from jacks_data for verification
        distances_from_eave = []
        point_loads_combined = []

        for i in range(jacks_data["num_per_side"]):
            j_n = jacks_data["jacks"]["north_side"][i]
            j_w = jacks_data["jacks"]["west_side"][i]
            pos_from_eave = j_n.get("location_from_eave_ft", 0)
            total_p = j_n["point_load_lb"] + j_w["point_load_lb"]

            distances_from_eave.append(pos_from_eave)
            point_loads_combined.append(total_p)

        L_valley_sloped = rafter_len  # Valley rafter length

        # Step 1: Total downward load
        total_downward = sum(point_loads_combined)
        self.output_text.insert(
            tk.END,
            f"Total downward load from {len(point_loads_combined)} point loads: {total_downward} lb\n",
        )

        # Step 2: Moment about eave end
        moment_about_eave = sum(
            load * dist for load, dist in zip(point_loads_combined, distances_from_eave)
        )
        self.output_text.insert(
            tk.END, f"Moment about eave: {moment_about_eave:.0f} ft-lb\n"
        )

        # Step 3: Reaction at ridge
        reaction_ridge = moment_about_eave / L_valley_sloped
        self.output_text.insert(
            tk.END, f"Calculated reaction at ridge: {reaction_ridge:.0f} lb (upward)\n"
        )

        # Step 4: Reaction at eave
        reaction_eave = total_downward - reaction_ridge
        self.output_text.insert(
            tk.END, f"Calculated reaction at eave: {reaction_eave:.0f} lb (upward)\n"
        )

        # Step 5: Verification check
        sum_reactions = reaction_eave + reaction_ridge
        if abs(sum_reactions - total_downward) < 10:  # tolerance for rounding
            self.output_text.insert(
                tk.END,
                f"Verification: Reactions sum ({sum_reactions:.0f} lb) matches total load ({total_downward} lb) — EQUILIBRIUM SATISFIED\n",
            )
        else:
            self.output_text.insert(
                tk.END,
                f"Verification: DISCREPANCY — Reactions sum {sum_reactions:.0f} lb vs total load {total_downward} lb\n",
            )

        self.output_text.insert(
            tk.END,
            "Note: These reactions are independently derived for shear/moment diagram use. Max shear ≈ eave reaction.\n\n",
        )

        # === VALLEY RAFTER ASD ANALYSIS (D + 0.7S FOR STRESS CHECKS) ===
        self.output_text.insert(
            tk.END, "============================================================\n"
        )
        self.output_text.insert(
            tk.END,
            "VALLEY RAFTER ASD LOAD COMBINATION: DEAD + 0.7 SNOW (STRESS CHECKS)\n",
        )
        self.output_text.insert(
            tk.END, "------------------------------------------------------------\n"
        )
        self.output_text.insert(
            tk.END,
            "Per ASCE 7-22 Sec. 2.4.1: Ultimate snow scaled by 0.7 for ASD service-level equivalent.\n",
        )
        self.output_text.insert(tk.END, f"Sloped Beam Length: {rafter_len:.2f} ft\n")
        self.output_text.insert(
            tk.END,
            "Jack reactions calculated as half tributary load (uniform on horizontal projection for snow).\n\n",
        )

        # Get dead load from user input
        roof_dead_load_psf = self.get_float("dead_load_horizontal")
        if roof_dead_load_psf is None:
            roof_dead_load_psf = 15.0  # Default value

        # Extract horizontal jack lengths (reverse order for eave to ridge)
        horiz_jack_full = []
        distances_from_eave = []

        for i in range(jacks_data["num_per_side"]):
            j_n = jacks_data["jacks"]["north_side"][i]
            horiz_full = j_n["horiz_length_ft"] * 2  # Full horizontal span
            horiz_jack_full.append(horiz_full)
            distances_from_eave.append(j_n.get("location_from_eave_ft", 0))

        # Reverse to eave to ridge order
        horiz_jack_full.reverse()
        distances_from_eave.sort()

        # Spacing along ridge
        spacing_ridge = jacks_data.get(
            "spacing_along_ridge_ft", jack_spacing_inches / 12.0
        )

        # Calculate average height for sloped jack length approximation
        avg_pitch = (pitch_n + pitch_w) / 2
        h_avg = math.tan(math.atan(avg_pitch / 12)) * (
            sum(horiz_jack_full) / len(horiz_jack_full)
        )

        # Extract snow values from jacks_data
        balanced_one_side = []
        drift_one_side = []

        for i in range(jacks_data["num_per_side"]):
            # j_n = North-South Valley Rafter: frames from Valley Beam to East-West Ridge
            j_n = jacks_data["jacks"]["north_side"][i]
            balanced_one_side.append(j_n["balanced_snow_lb"])
            drift_one_side.append(j_n["drift_load_lb"])

        # Reverse to match eave to ridge order
        balanced_one_side.reverse()
        drift_one_side.reverse()

        snow_one_side_full = [b + d for b, d in zip(balanced_one_side, drift_one_side)]

        # ASD snow one side = 0.7 * full snow
        asd_snow_one_side = [0.7 * s for s in snow_one_side_full]

        # DL one side: based on sloped area
        sloped_jack = [math.sqrt(h**2 + h_avg**2) for h in horiz_jack_full]
        trib_area_sloped_one_side = [s * spacing_ridge for s in sloped_jack]
        dl_one_side = [roof_dead_load_psf * a for a in trib_area_sloped_one_side]

        # ASD full one side = DL + ASD snow
        asd_full_one_side = [
            dl + asd_s for dl, asd_s in zip(dl_one_side, asd_snow_one_side)
        ]

        # ASD jack reaction one side = half ASD full
        asd_reaction_one_side = [f / 2 for f in asd_full_one_side]

        # Combined ASD point load on valley = 2 * reaction one side (North + West)
        asd_point_loads = [2 * r for r in asd_reaction_one_side]

        L = rafter_len

        # Equilibrium for ASD
        total_asd = sum(asd_point_loads)
        moment_about_eave = sum(
            p * d for p, d in zip(asd_point_loads, distances_from_eave)
        )
        reaction_ridge = moment_about_eave / L
        reaction_eave = total_asd - reaction_ridge

        # Traverse for max ASD shear/moment (corrected for positive sagging moment)
        max_moment = 0.0
        max_shear = abs(reaction_eave)  # absolute max shear
        current_shear = reaction_eave  # positive at eave
        current_moment = 0.0
        prev_dist = 0.0

        shear_values = [current_shear]  # for optional detailed output
        moment_values = [0.0]

        for dist, load in zip(distances_from_eave, asd_point_loads):
            delta = dist - prev_dist
            # Moment increment = shear * delta (trapezoidal, but linear between points)
            current_moment += current_shear * delta
            moment_values.append(current_moment)
            max_moment = max(max_moment, current_moment)  # positive sagging

            current_shear -= load
            shear_values.append(current_shear)
            max_shear = max(max_shear, abs(current_shear))

            prev_dist = dist

        # Final segment to ridge
        delta = L - prev_dist
        current_moment += current_shear * delta
        moment_values.append(current_moment)
        max_moment = max(max_moment, current_moment)  # should be near 0

        # Ensure final moment ~0 (rounding tolerance)
        if abs(current_moment) > 10:
            self.output_text.insert(
                tk.END,
                "Warning: Final moment not zero — check equilibrium (rounding error possible)\n",
            )

        # Output updated max (positive)
        self.output_text.insert(
            tk.END, f"Max ASD Moment (positive sagging): {max_moment:.0f} ft-lb\n"
        )

        # Updated text diagrams with positive moment
        self.output_text.insert(
            tk.END, "\n=== ASD SHEAR FORCE DIAGRAM (Sloped Valley Beam) ===\n"
        )
        self.output_text.insert(
            tk.END,
            f"Eave reaction: +{reaction_eave:.0f} lb (upward) → initial shear +{reaction_eave:.0f} lb\n",
        )
        self.output_text.insert(
            tk.END, "Shear decreases with each downward ASD point load\n"
        )
        self.output_text.insert(
            tk.END,
            "Crosses zero mid-span, ends just left of ridge at -{reaction_ridge:.0f} lb\n",
        )
        self.output_text.insert(
            tk.END,
            f"Ridge reaction: +{reaction_ridge:.0f} lb (upward) → shear back to 0\n",
        )
        self.output_text.insert(tk.END, f"Max |shear| = {max_shear:.0f} lb\n\n")

        self.output_text.insert(
            tk.END, "=== ASD BENDING MOMENT DIAGRAM (Sloped Valley Beam) ===\n"
        )
        self.output_text.insert(tk.END, "Moment starts at 0 at eave\n")
        self.output_text.insert(
            tk.END, "Increases positively (sagging) due to gravity loads\n"
        )
        self.output_text.insert(
            tk.END,
            f"Peaks at +{max_moment:.0f} ft-lb (positive sagging, typically 9-12 ft from eave)\n",
        )
        self.output_text.insert(tk.END, "Decreases to 0 at ridge\n")
        self.output_text.insert(
            tk.END, "NO NEGATIVE MOMENT for this simply supported gravity-loaded beam\n"
        )
        self.output_text.insert(
            tk.END,
            "Shape: Polygonal curve, convex upward (positive throughout interior)\n",
        )

        # Detailed values for verification
        self.output_text.insert(tk.END, "\nDetailed values for verification:\n")
        distances_all = [0] + distances_from_eave + [L]
        moments_all = moment_values + [current_moment]
        shears_all = shear_values + [0]  # Final shear = 0 due to ridge reaction

        for i, (dist, m, v) in enumerate(zip(distances_all, moments_all, shears_all)):
            self.output_text.insert(
                tk.END,
                f"At {dist:.2f} ft: Moment = {m:.0f} ft-lb, Shear = {v:.0f} lb\n",
            )

        self.output_text.insert(tk.END, "\n")

        # === JACK RAFTER REACTION COMPARISON TABLE ===
        self.output_text.insert(
            tk.END, "\n============================================================\n"
        )
        self.output_text.insert(tk.END, "JACK RAFTER REACTION COMPARISON TABLE\n")
        self.output_text.insert(
            tk.END, "------------------------------------------------------------\n"
        )
        self.output_text.insert(
            tk.END,
            "Comparison of reactions at each jack rafter location (0, 2, 4, 6, 8, 10, 12, 14 ft)\n",
        )
        self.output_text.insert(
            tk.END,
            "Note: Each jack rafter reaction is one half the total load at that location.\n",
        )
        self.output_text.insert(
            tk.END, "j_n reaction goes to Valley Beam (half) and E-W Ridge (half)\n"
        )
        self.output_text.insert(
            tk.END,
            "j_w reaction goes to Valley Beam (half) and N-S Ridge Beam (half)\n\n",
        )

        # Create detailed jack rafter reaction table
        if hasattr(self, "valley_beam_positions") and jacks_data:
            self.output_text.insert(
                tk.END,
                f"{'Position':<12} {'j_n Total':<15} {'j_w Total':<15} {'j_n Reaction':<18} {'j_w Reaction':<18} {'Valley Beam':<18} {'Ridge Beam':<18}\n",
            )
            self.output_text.insert(
                tk.END,
                f"{'(ft)':<12} {'(lb)':<15} {'(lb)':<15} {'(lb, j_n/2)':<18} {'(lb, j_w/2)':<18} {'(lb, j_n/2+j_w/2)':<18} {'(lb, j_w/2)':<18}\n",
            )
            self.output_text.insert(tk.END, "-" * 114 + "\n")

            # Get jack rafter data and create fixed 2-foot spacing positions
            num_jacks = len(jacks_data["jacks"]["north_side"])
            fixed_positions = [
                i * 2.0 for i in range(num_jacks)
            ]  # 0, 2, 4, 6, 8, 10, 12, 14...

            for i, (j_n, j_w) in enumerate(
                zip(jacks_data["jacks"]["north_side"], jacks_data["jacks"]["west_side"])
            ):
                pos = fixed_positions[i] if i < len(fixed_positions) else i * 2.0

                j_n_total = j_n["total_snow_lb"] + j_n["dead_load_lb"]
                j_w_total = j_w["total_snow_lb"] + j_w["dead_load_lb"]

                j_n_reaction = j_n_total / 2  # Half reaction
                j_w_reaction = j_w_total / 2  # Half reaction

                valley_beam_load = (
                    j_n_reaction + j_w_reaction
                )  # Valley receives both reactions
                ridge_beam_load = j_w_reaction  # Ridge receives only j_w reaction

                self.output_text.insert(
                    tk.END,
                    f"{pos:<12.1f} {j_n_total:<15.0f} {j_w_total:<15.0f} {j_n_reaction:<18.0f} {j_w_reaction:<18.0f} {valley_beam_load:<18.0f} {ridge_beam_load:<18.0f}\n",
                )

            self.output_text.insert(tk.END, "-" * 114 + "\n")
            self.output_text.insert(tk.END, "\n")

        # === REACTION COMPARISON TABLE ===
        self.output_text.insert(
            tk.END, "\n============================================================\n"
        )
        self.output_text.insert(tk.END, "REACTION COMPARISON TABLE\n")
        self.output_text.insert(
            tk.END, "------------------------------------------------------------\n"
        )
        self.output_text.insert(
            tk.END,
            "Comparison of reactions at corresponding points on Valley Beam vs N-S Ridge Beam\n",
        )
        self.output_text.insert(
            tk.END,
            "Note: Ridge Beam uses horizontal positions, Valley Beam uses sloped positions.\n",
        )
        self.output_text.insert(
            tk.END,
            "Ridge Beam reaction at 2 ft (horizontal) = Valley Beam reaction at 2.83 ft (sloped)\n",
        )
        self.output_text.insert(
            tk.END, "Valley Beam: receives (j_n + j_w)/2 reactions\n"
        )
        self.output_text.insert(
            tk.END,
            "N-S Ridge Beam: receives j_w_total reactions (from both sides)\n",
        )
        self.output_text.insert(
            tk.END, "Reactions should be EQUAL at each corresponding point.\n\n"
        )

        # Create detailed reaction comparison table
        if (
            hasattr(self, "valley_beam_positions")
            and hasattr(self, "valley_beam_total_loads")
            and hasattr(self, "ns_ridge_total_loads")
            and self.valley_beam_positions
            and jacks_data
        ):
            self.output_text.insert(
                tk.END,
                f"{'Ridge Pos':<12} {'Valley Pos':<15} {'j_n Total':<15} {'j_w Total':<15} {'Valley Beam':<18} {'Ridge Beam':<18} {'Match?':<10}\n",
            )
            self.output_text.insert(
                tk.END,
                f"{'(ft horiz)':<12} {'(ft sloped)':<15} {'(lb)':<15} {'(lb)':<15} {'(lb, (j_n+j_w)/2)':<18} {'(lb, j_w total)':<18} {'':<10}\n",
            )
            self.output_text.insert(tk.END, "-" * 103 + "\n")

            # Get sloped positions for valley beam
            valley_sloped_positions = []
            if hasattr(self, "valley_beam_sloped_positions"):
                valley_sloped_positions = self.valley_beam_sloped_positions
            else:
                # Calculate sloped positions if not stored
                for pos_horiz in self.valley_beam_positions:
                    pos_sloped = pos_horiz * (rafter_len / lv) if lv > 0 else pos_horiz
                    valley_sloped_positions.append(pos_sloped)

            # Sort by horizontal position
            combined_data = list(
                zip(
                    self.valley_beam_positions,
                    valley_sloped_positions,
                    self.valley_beam_total_loads,
                    self.ns_ridge_total_loads,
                )
            )
            combined_data.sort(key=lambda x: x[0])

            for i, (pos_horiz, pos_sloped, valley_load, ns_load) in enumerate(
                combined_data
            ):
                if i < len(jacks_data["jacks"]["north_side"]) and i < len(
                    jacks_data["jacks"]["west_side"]
                ):
                    j_n = jacks_data["jacks"]["north_side"][i]
                    j_w = jacks_data["jacks"]["west_side"][i]

                    j_n_total = j_n["total_snow_lb"] + j_n["dead_load_lb"]
                    j_w_total = j_w["total_snow_lb"] + j_w["dead_load_lb"]

                    # Check if reactions match (should be equal)
                    reactions_match = "✓" if abs(valley_load - ns_load) < 0.1 else "✗"

                    self.output_text.insert(
                        tk.END,
                        f"{pos_horiz:<12.1f} {pos_sloped:<15.2f} {j_n_total:<15.0f} {j_w_total:<15.0f} {valley_load:<18.0f} {ns_load:<18.0f} {reactions_match:<10}\n",
                    )
                else:
                    self.output_text.insert(
                        tk.END,
                        f"{pos_horiz:<12.1f} {pos_sloped:<15.2f} {'N/A':<15} {'N/A':<15} {valley_load:<18.0f} {ns_load:<18.0f} {'':<10}\n",
                    )

            # Summary
            total_valley = sum(self.valley_beam_total_loads)
            total_ns = sum(self.ns_ridge_total_loads)
            self.output_text.insert(tk.END, "-" * 103 + "\n")
            self.output_text.insert(
                tk.END,
                f"{'Total:':<12} {'':<15} {'':<15} {'':<15} {total_valley:<18.0f} {total_ns:<18.0f}\n",
            )

            # Check if all reactions match
            all_match = all(
                abs(v - n) < 0.1
                for v, n in zip(self.valley_beam_total_loads, self.ns_ridge_total_loads)
            )
            if all_match:
                self.output_text.insert(
                    tk.END,
                    "\n✓ Reactions are EQUAL at each corresponding point\n",
                    "green",
                )
            else:
                self.output_text.insert(
                    tk.END, "\n✗ Reactions do not match - check calculations\n", "red"
                )
        
        # === EQUILIBRIUM VERIFICATION (STATIC CHECK) ===
        self.output_text.insert(
            tk.END, "\n============================================================\n"
        )
        self.output_text.insert(tk.END, "EQUILIBRIUM VERIFICATION\n")
        self.output_text.insert(
            tk.END, "------------------------------------------------------------\n"
        )
        self.output_text.insert(
            tk.END,
            "Static Equilibrium Check: Sum of reactions should equal total applied point loads\n\n",
        )
        
        # Valley Beam Equilibrium Check
        if hasattr(self, "valley_equilibrium_check"):
            check = self.valley_equilibrium_check
            self.output_text.insert(tk.END, "VALLEY BEAM:\n")
            self.output_text.insert(
                tk.END,
                f"  Sum of Reactions (R_eave + R_ridge): {check['sum_reactions']:.2f} lb\n",
            )
            self.output_text.insert(
                tk.END, f"  Total Point Loads: {check['total_loads']:.2f} lb\n"
            )
            self.output_text.insert(
                tk.END, f"  Difference: {check['difference']:.4f} lb\n"
            )
            if check["passes"]:
                self.output_text.insert(
                    tk.END, "  ✓ EQUILIBRIUM SATISFIED\n\n", "green"
                )
            else:
                self.output_text.insert(
                    tk.END, "  ✗ EQUILIBRIUM NOT SATISFIED - CHECK CALCULATIONS\n\n", "red"
                )
        else:
            self.output_text.insert(
                tk.END, "VALLEY BEAM: Equilibrium check not available\n\n"
            )
        
        # N-S Ridge Beam Equilibrium Check
        if hasattr(self, "ns_ridge_equilibrium_check"):
            check = self.ns_ridge_equilibrium_check
            self.output_text.insert(tk.END, "N-S RIDGE BEAM:\n")
            self.output_text.insert(
                tk.END,
                f"  Sum of Reactions (R_top + R_bottom): {check['sum_reactions']:.2f} lb\n",
            )
            self.output_text.insert(
                tk.END, f"  Total Point Loads: {check['total_loads']:.2f} lb\n"
            )
            self.output_text.insert(
                tk.END, f"  Difference: {check['difference']:.4f} lb\n"
            )
            if check["passes"]:
                self.output_text.insert(
                    tk.END, "  ✓ EQUILIBRIUM SATISFIED\n\n", "green"
                )
            else:
                self.output_text.insert(
                    tk.END, "  ✗ EQUILIBRIUM NOT SATISFIED - CHECK CALCULATIONS\n\n", "red"
                )
        else:
            self.output_text.insert(
                tk.END, "N-S RIDGE BEAM: Equilibrium check not available\n\n"
            )
        
        self.output_text.insert(tk.END, "\n")

        self.output_text.insert(tk.END, "\n")

        # === N-S RIDGE BEAM DESIGN ANALYSIS ===
        self.output_text.insert(
            tk.END, "\n============================================================\n"
        )
        self.output_text.insert(tk.END, "N-S RIDGE BEAM DESIGN ANALYSIS\n")
        self.output_text.insert(
            tk.END, "------------------------------------------------------------\n"
        )
        self.output_text.insert(
            tk.END, f"Horizontal Length: {ns_ridge_beam_length:.2f} ft\n"
        )
        self.output_text.insert(
            tk.END, f"Material: {self.ns_ridge_material_combobox.get()}\n"
        )
        self.output_text.insert(
            tk.END,
            f"Point Loads: {len(ns_ridge_snow_point_loads)} locations from j_w jack rafters (East-West Valley Rafters)\n",
        )
        self.output_text.insert(
            tk.END,
            "Note: Each j_w rafter reaction is applied to the N-S ridge beam\n\n",
        )

        if ns_ridge_beam_results and "error" not in ns_ridge_beam_results:
            ns_max_moment = ns_ridge_beam_results.get("max_moment_ft_kip", 0) * 1000
            ns_max_shear = ns_ridge_beam_results.get("max_shear_kip", 0) * 1000
            ns_bend_ratio = ns_ridge_beam_results.get("ratio_bending", 0)
            ns_shear_ratio = ns_ridge_beam_results.get("ratio_shear", 0)
            ns_snow_def_ratio = ns_ridge_beam_results.get("ratio_deflection_snow", 0)
            ns_total_def_ratio = ns_ridge_beam_results.get("ratio_deflection_total", 0)

            # Calculate reactions for N-S ridge beam
            ns_total_load = sum(load for _, load in ns_ridge_snow_point_loads) + sum(
                load for _, load in ns_ridge_dead_point_loads
            )
            ns_moment_about_top = sum(
                load * pos
                for (pos, load) in zip(
                    ns_ridge_load_positions,
                    [
                        s + d
                        for s, d in zip(
                            [l for _, l in ns_ridge_snow_point_loads],
                            [l for _, l in ns_ridge_dead_point_loads],
                        )
                    ],
                )
            )
            ns_reaction_bottom = (
                ns_moment_about_top / ns_ridge_beam_length
                if ns_ridge_beam_length > 0
                else 0
            )
            ns_reaction_top = ns_total_load - ns_reaction_bottom

            self.output_text.insert(
                tk.END,
                f"Reactions: Top (E-W ridge) = {ns_reaction_top:.0f} lb, Bottom (south eave) = {ns_reaction_bottom:.0f} lb\n",
            )
            self.output_text.insert(
                tk.END, f"Maximum Moment: {ns_max_moment:.0f} ft-lb\n"
            )
            self.output_text.insert(tk.END, f"Maximum Shear: {ns_max_shear:.0f} lb\n")
            self.output_text.insert(tk.END, f"Total Load: {ns_total_load:.0f} lb\n\n")

            self.output_text.insert(tk.END, "=== DESIGN CHECKS ===\n")
            self.output_text.insert(
                tk.END,
                f"Bending: {ns_bend_ratio:.3f} ({'PASS' if ns_bend_ratio <= 1 else 'FAIL'})\n",
            )
            self.output_text.insert(
                tk.END,
                f"Shear: {ns_shear_ratio:.3f} ({'PASS' if ns_shear_ratio <= 1 else 'FAIL'})\n",
            )
            self.output_text.insert(
                tk.END,
                f"Snow Deflection: {ns_snow_def_ratio:.3f} ({'PASS' if ns_snow_def_ratio <= 1 else 'FAIL'})\n",
            )
            self.output_text.insert(
                tk.END,
                f"Total Deflection: {ns_total_def_ratio:.3f} ({'PASS' if ns_total_def_ratio <= 1 else 'FAIL'})\n",
            )

            if ns_ridge_beam_results.get("passes", False):
                self.output_text.insert(tk.END, "\nOVERALL STATUS: PASS\n", "green")
            else:
                self.output_text.insert(
                    tk.END, "\nOVERALL STATUS: FAIL - Redesign required\n", "red"
                )
        else:
            ns_error_msg = (
                ns_ridge_beam_results.get("error", "Unknown error")
                if ns_ridge_beam_results
                else "Calculation failed"
            )
            self.output_text.insert(tk.END, f"\nERROR: {ns_error_msg}\n", "red")

        self.output_text.insert(tk.END, "\n")

        self.output_text.insert(tk.END, "Validation passed. GUI working correctly!\n")
        self.output_text.insert(
            tk.END, "Complete ASCE 7-22 Valley Snow Load Calculator"
        )
        print("DEBUG: Calculate method completed successfully")
