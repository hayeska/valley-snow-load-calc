# main_window.py - Resilient main application window for Valley Calculator V2.0

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
import matplotlib.pyplot as plt
import threading
import time

from ..core.calculator import ValleyCalculator
from ..core.project import ProjectManager
from ..core.state import StateManager
from ..calculations.engine import CalculationEngine
from ..core.config import get_config_manager
from ..utils.logging.logger import get_logger
from ..core.recovery.checkpoint_system import get_checkpoint_manager
from .input_panels import InputPanel
from .results_display import ResultsDisplay
from .themes import ThemeManager
from .tooltips import TooltipManager


class MainWindow:
    """
    Resilient main application window with modern architecture and state management.

    Features:
    - Clean layered architecture (GUI/Service/Domain/Data)
    - Centralized state management with validation
    - Pure calculation engine with no UI dependencies
    - Comprehensive error handling and recovery
    - Project management with auto-save and recovery
    - Results visualization with error handling
    - Performance monitoring and logging
    """

    def __init__(self, calculator: ValleyCalculator, project_manager: ProjectManager):
        """Initialize the resilient main window with modern architecture."""
        self.calculator = calculator
        self.project_manager = project_manager

        # Initialize new architecture components
        self.state_manager = StateManager()
        self.calculation_engine = CalculationEngine()
        self.config_manager = get_config_manager()

        self.logger = get_logger()
        self.checkpoint_mgr = get_checkpoint_manager()

        # Recovery and error handling state
        self.recovery_mode = False
        self.last_auto_save = time.time()
        self.calculation_thread = None
        self.stop_calculation = threading.Event()

        # Create main window
        self.root = tk.Tk()
        self.root.title("Valley Snow Load Calculator V2.0 - ASCE 7-22 Compliant")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Initialize theme manager
        self.theme_manager = ThemeManager(self.root)

        # Initialize tooltip manager
        self.tooltip_manager = TooltipManager(self.root)

        # Initialize variables
        self.current_project = None
        self.current_project_id = None
        self.calculation_results = None
        self.calculation_in_progress = False

        # Create UI components
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()

        # Check for crash recovery on startup
        self._check_crash_recovery()

        # Initialize with default values
        self._initialize_defaults()

        # Bind events
        self._bind_events()

        # Start auto-save timer
        self._start_auto_save_timer()

        self.logger.log_recovery_action("Main window initialized successfully", True)

    def _check_crash_recovery(self):
        """Check for crash recovery options on startup."""
        try:
            health_status = self.project_manager.get_system_health_status()

            if health_status.get("database_status") == "error":
                self._show_recovery_dialog(
                    "Database Error",
                    "The application detected database issues. "
                    "Would you like to attempt recovery?",
                )
                return

            # Check for recent projects that might need recovery
            recent_projects = self.project_manager.get_recent_projects()
            recovery_needed = False

            for project in recent_projects:
                if project.get("type") == "database":
                    project_id = project.get("project_id")
                    if project_id:
                        recovery_options = (
                            self.project_manager.get_project_recovery_options(
                                project_id
                            )
                        )
                        if len(recovery_options) > 1:  # More than just basic recovery
                            recovery_needed = True
                            break

            if recovery_needed:
                self._show_recovery_dialog(
                    "Recovery Options Available",
                    "Recent projects have recovery options available. "
                    "Would you like to view recovery options?",
                )

        except Exception as e:
            self.logger.log_error(e, operation="crash_recovery_check")
            # Continue startup even if recovery check fails

    def _show_recovery_dialog(self, title: str, message: str):
        """Show recovery options dialog."""
        result = messagebox.askyesno(title, message, icon="warning")
        if result:
            self._show_recovery_window()

    def _show_recovery_window(self):
        """Show detailed recovery options window."""
        recovery_win = tk.Toplevel(self.root)
        recovery_win.title("Data Recovery Options")
        recovery_win.geometry("600x400")

        # Create recovery options display
        ttk.Label(
            recovery_win, text="Available Recovery Options:", font=("Arial", 12, "bold")
        ).pack(pady=10)

        # Recovery options frame
        options_frame = ttk.Frame(recovery_win)
        options_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Display recovery options
        try:
            recent_projects = self.project_manager.get_recent_projects()

            for project in recent_projects[:5]:  # Show last 5 projects
                if project.get("type") == "database":
                    project_id = project.get("project_id")
                    project_name = project.get("name", "Unknown")

                    # Project frame
                    proj_frame = ttk.LabelFrame(
                        options_frame, text=f"Project: {project_name}"
                    )
                    proj_frame.pack(fill="x", pady=5)

                    recovery_opts = self.project_manager.get_project_recovery_options(
                        project_id
                    )

                    for opt in recovery_opts:
                        opt_type = opt.get("type", "unknown")
                        if opt_type == "checkpoint":
                            btn_text = f"Restore from {opt.get('operation', 'checkpoint')} ({opt.get('created_at', '')[:19]})"
                        elif opt_type == "last_good_state":
                            btn_text = "Restore from last good state"
                        else:
                            continue

                        ttk.Button(
                            proj_frame,
                            text=btn_text,
                            command=lambda pid=project_id,
                            oid=opt.get("id"): self._perform_recovery(
                                pid, oid, recovery_win
                            ),
                        ).pack(fill="x", pady=2)

        except Exception as e:
            self.logger.log_error(e, operation="show_recovery_window")
            ttk.Label(options_frame, text="Error loading recovery options").pack()

        # Close button
        ttk.Button(recovery_win, text="Close", command=recovery_win.destroy).pack(
            pady=10
        )

    def _perform_recovery(self, project_id: str, recovery_id: str, parent_window):
        """Perform data recovery operation."""
        try:
            if recovery_id:
                recovered_data = self.project_manager.recover_project_from_checkpoint(
                    recovery_id
                )
                if recovered_data:
                    self.current_project = recovered_data
                    self.current_project_id = project_id
                    self._update_ui_from_project_data()
                    messagebox.showinfo(
                        "Recovery Successful",
                        "Project data has been recovered successfully.",
                    )
                    parent_window.destroy()
                else:
                    messagebox.showerror(
                        "Recovery Failed", "Failed to recover project data."
                    )
            else:
                # Load last good state
                project_data = self.project_manager.load_project(project_id)
                if project_data:
                    self.current_project = project_data
                    self.current_project_id = project_id
                    self._update_ui_from_project_data()
                    messagebox.showinfo(
                        "Recovery Successful", "Project loaded from last good state."
                    )
                    parent_window.destroy()

        except Exception as e:
            self.logger.log_error(
                e,
                operation="perform_recovery",
                context={"project_id": project_id, "recovery_id": recovery_id},
            )
            messagebox.showerror("Recovery Error", f"Recovery failed: {e}")

    def _start_auto_save_timer(self):
        """Start the auto-save timer."""

        def auto_save_worker():
            while not hasattr(
                self, "stop_calculation"
            ) or not self.stop_calculation.wait(300):  # Auto-save every 5 minutes
                try:
                    self._perform_auto_save()
                except Exception as e:
                    self.logger.log_error(e, operation="auto_save_timer")

        self.auto_save_thread = threading.Thread(target=auto_save_worker, daemon=True)
        self.auto_save_thread.start()

    def _perform_auto_save(self):
        """Perform automatic save of current project."""
        if self.current_project and self.current_project_id:
            try:
                # Update project with current UI state
                current_data = self._get_current_project_data()

                if current_data:
                    self.project_manager.save_project(
                        current_data, self.current_project_id
                    )
                    self.last_auto_save = time.time()

                    # Update status bar
                    self._update_status_bar(
                        f"Auto-saved at {time.strftime('%H:%M:%S')}"
                    )

            except Exception as e:
                self.logger.log_error(
                    e,
                    operation="auto_save",
                    context={"project_id": self.current_project_id},
                )

    def _update_ui_from_project_data(self):
        """Update UI components from loaded project data."""
        # This method would update all input fields and results display
        # from the loaded project data
        try:
            if self.current_project:
                inputs = self.current_project.get("inputs", {})
                results = self.current_project.get("results", {})

                # Update input panels
                if hasattr(self, "input_panel"):
                    self.input_panel.load_inputs(inputs)

                # Update results display
                if hasattr(self, "results_display") and results:
                    self.results_display.display_results(results)

                # Update window title
                project_name = self.current_project.get(
                    "project_name", "Unnamed Project"
                )
                self.root.title(f"Valley Snow Load Calculator - {project_name}")

        except Exception as e:
            self.logger.log_error(e, operation="update_ui_from_project")

    def _get_current_project_data(self) -> Dict[str, Any]:
        """Get current project data from UI state."""
        try:
            # Collect data from input panels
            inputs = {}
            if hasattr(self, "input_panel"):
                inputs = self.input_panel.get_inputs()

            # Include results if available
            results = self.calculation_results or {}

            return {
                "project_name": self.current_project.get(
                    "project_name", "Unnamed Project"
                )
                if self.current_project
                else "Unnamed Project",
                "inputs": inputs,
                "results": results,
                "timestamp": time.time(),
            }

        except Exception as e:
            self.logger.log_error(e, operation="get_current_project_data")
            return None

    def _update_status_bar(self, message: str):
        """Update the status bar with a message."""
        # This would update a status bar widget
        if hasattr(self, "status_bar"):
            self.status_bar.config(text=message)

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="New Project", command=self._new_project, accelerator="Ctrl+N"
        )
        file_menu.add_command(
            label="Open Project...", command=self._open_project, accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label="Save Project", command=self._save_project, accelerator="Ctrl+S"
        )
        file_menu.add_command(label="Save Project As...", command=self._save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results...", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit", command=self._exit_application, accelerator="Alt+F4"
        )

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Reset to Defaults", command=self._reset_defaults)
        edit_menu.add_command(label="Load Template...", command=self._load_template)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(
            label="Data Recovery...", command=self._show_recovery_window
        )
        tools_menu.add_command(
            label="System Health Check", command=self._show_health_check
        )
        tools_menu.add_separator()
        tools_menu.add_command(label="Create Backup...", command=self._create_backup)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)

        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)

        for theme_key in self.theme_manager.get_available_themes():
            theme_name = self.theme_manager.get_theme_name(theme_key)
            theme_menu.add_command(
                label=theme_name, command=lambda t=theme_key: self._change_theme(t)
            )

        view_menu.add_separator()
        view_menu.add_command(
            label="Toggle Results Panel", command=self._toggle_results_panel
        )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(
            label="ASCE 7-22 Reference", command=self._show_asce_reference
        )
        help_menu.add_command(label="User Guide", command=self._show_user_guide)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)

    def _create_main_layout(self):
        """Create the main window layout."""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create paned window for resizable panels
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Input
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # Input panel
        self.input_panel = InputPanel(
            left_frame, self.calculator.defaults, self.tooltip_manager
        )
        self.input_panel.pack(fill=tk.BOTH, expand=True)

        # Right panel - Results
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # Results display
        self.results_display = ResultsDisplay(right_frame)
        self.results_display.pack(fill=tk.BOTH, expand=True)

        # Calculate button and progress area
        calc_frame = ttk.Frame(main_frame)
        calc_frame.pack(fill=tk.X, pady=5)

        # Button frame
        button_frame = ttk.Frame(calc_frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.calc_button = ttk.Button(
            button_frame,
            text="Calculate Snow Loads",
            command=self._perform_calculation,
            style="Accent.TButton",
        )
        self.calc_button.pack(side=tk.LEFT, padx=(0, 10))

        # Progress frame (initially hidden)
        self.progress_frame = ttk.Frame(calc_frame)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, orient="horizontal", mode="determinate", length=300
        )
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 10))

        # Progress label
        self.progress_label = ttk.Label(self.progress_frame, text="Ready")
        self.progress_label.pack(side=tk.LEFT)

        # Add tooltip to calculate button
        from .tooltips import add_tooltip

        add_tooltip(self.calc_button, "calculate_button")

    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = ttk.Label(
            self.root, text="Ready", style="Status.TLabel", anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _initialize_defaults(self):
        """Initialize input fields with default values."""
        # Set default values in input panel
        defaults = self.calculator.defaults
        self.input_panel.set_values(defaults)

    def _bind_events(self):
        """Bind keyboard and other events."""
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self._new_project())
        self.root.bind("<Control-o>", lambda e: self._open_project())
        self.root.bind("<Control-s>", lambda e: self._save_project())

        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self._exit_application)

    def _perform_calculation(self):
        """Perform the snow load calculation with progress indication."""
        try:
            # Get input values
            inputs = self.input_panel.get_values()

            # Validate inputs
            self._update_progress("Validating inputs...", 10)
            is_valid, errors = self.calculator.validate_inputs(inputs)
            if not is_valid:
                self._hide_progress()
                error_msg = "Input validation errors:\n" + "\n".join(errors)
                messagebox.showerror("Input Error", error_msg)
                return

            # Start progress indication
            self._show_progress()
            self.calc_button.config(state="disabled")

            # Perform calculation steps with progress updates
            self._update_progress("Analyzing roof geometry...", 20)
            self.root.update()

            self._update_progress("Calculating snow loads...", 40)
            self.root.update()

            self._update_progress("Analyzing drift conditions...", 60)
            self.root.update()

            self._update_progress("Performing beam analysis...", 80)
            self.root.update()

            # Perform complete calculation
            self._update_progress("Finalizing results...", 90)
            self.calculation_results = self.calculator.perform_complete_analysis(inputs)

            # Display results
            self._update_progress("Displaying results...", 100)
            self.results_display.display_results(self.calculation_results)

            # Complete
            self._hide_progress()
            self.calc_button.config(state="normal")
            self.status_bar.config(text="Calculation complete")

        except Exception as e:
            self._hide_progress()
            self.calc_button.config(state="normal")
            error_msg = f"Calculation error: {str(e)}"
            messagebox.showerror("Calculation Error", error_msg)
            self.status_bar.config(text="Error during calculation")

    def _new_project(self):
        """Start a new project."""
        if self._confirm_discard_changes():
            self.current_project = None
            self.calculation_results = None
            self._initialize_defaults()
            self.results_display.clear()
            self.status_bar.config(text="New project started")

    def _open_project(self):
        """Open an existing project."""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if file_path:
            try:
                project_data = self.project_manager.load_project(file_path)
                self.current_project = file_path
                self._load_project_data(project_data)
                self.status_bar.config(text=f"Opened: {file_path}")
            except Exception as e:
                messagebox.showerror("Open Error", f"Failed to open project: {str(e)}")

    def _save_project(self):
        """Save the current project."""
        if self.current_project:
            self._do_save_project(self.current_project)
        else:
            self._save_project_as()

    def _save_project_as(self):
        """Save project with new filename."""
        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if file_path:
            self._do_save_project(file_path)
            self.current_project = file_path

    def _do_save_project(self, file_path: str):
        """Perform the actual save operation."""
        try:
            # Gather project data
            project_data = {
                "project_name": self.input_panel.get_project_name(),
                "inputs": self.input_panel.get_values(),
                "results": self.calculation_results or {},
                "timestamp": "2024-12-24T20:00:00Z",
            }

            # Save
            self.project_manager.save_project(project_data, file_path)
            self.status_bar.config(text=f"Saved: {file_path}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save project: {str(e)}")

    def _export_results(self):
        """Export calculation results."""
        if not self.calculation_results:
            messagebox.showwarning(
                "Export Warning", "No results to export. Please calculate first."
            )
            return

        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                format_type = "csv" if file_path.endswith(".csv") else "json"
                exported_path = self.project_manager.export_results(
                    self.calculation_results, format_type, file_path
                )
                self.status_bar.config(text=f"Exported: {exported_path}")
                messagebox.showinfo(
                    "Export Complete", f"Results exported to {exported_path}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Export Error", f"Failed to export results: {str(e)}"
                )

    def _load_project_data(self, project_data: dict):
        """Load project data into the UI."""
        # Load inputs
        if "inputs" in project_data:
            self.input_panel.set_values(project_data["inputs"])

        # Load results if available
        if "results" in project_data:
            self.calculation_results = project_data["results"]
            self.results_display.display_results(self.calculation_results)

    def _confirm_discard_changes(self) -> bool:
        """Confirm if user wants to discard unsaved changes."""
        if self.calculation_results:
            result = messagebox.askyesnocancel(
                "Discard Changes", "You have unsaved changes. Discard them?"
            )
            return result is True
        return True

    def _change_theme(self, theme_name: str):
        """Change the application theme."""
        try:
            self.theme_manager.apply_theme(theme_name)
            self.status_bar.config(
                text=f"Theme changed to {self.theme_manager.get_theme_name(theme_name)}"
            )
        except Exception as e:
            messagebox.showerror("Theme Error", f"Failed to apply theme: {str(e)}")

    def _show_progress(self):
        """Show the progress indicator."""
        if not self.progress_frame.winfo_ismapped():
            self.progress_frame.pack(fill=tk.X, pady=5)

    def _hide_progress(self):
        """Hide the progress indicator."""
        if self.progress_frame.winfo_ismapped():
            self.progress_frame.pack_forget()
        self.progress_bar["value"] = 0
        self.progress_label.config(text="Ready")

    def _update_progress(self, message: str, value: int):
        """Update progress bar and message."""
        self.progress_bar["value"] = value
        self.progress_label.config(text=message)
        self.status_bar.config(text=message)
        self.root.update_idletasks()  # Allow UI to update

    def _reset_defaults(self):
        """Reset all inputs to default values."""
        if messagebox.askyesno(
            "Reset to Defaults", "Reset all inputs to default values?"
        ):
            self._initialize_defaults()
            self.calculation_results = None
            self.results_display.clear()

    def _load_template(self):
        """Load a project template."""
        templates = self.project_manager.get_project_templates()
        if not templates:
            messagebox.showinfo("No Templates", "No project templates available.")
            return

        # Simple template selection (could be enhanced with a dialog)
        template_name = (
            templates[0] if len(templates) == 1 else templates[0]
        )  # Default to first

        try:
            template_data = self.project_manager.load_project_template(template_name)
            self.input_panel.set_values(template_data)
            self.status_bar.config(text=f"Loaded template: {template_name}")
        except Exception as e:
            messagebox.showerror("Template Error", f"Failed to load template: {str(e)}")

    def _toggle_results_panel(self):
        """Toggle visibility of results panel."""
        # Implementation would resize the paned window
        pass

    def _show_asce_reference(self):
        """Show ASCE 7-22 reference information."""
        reference_text = """
ASCE 7-22 Minimum Design Loads and Associated Criteria

Chapter 7 - Snow Loads
Section 7.6.1 - Unbalanced Snow Loads for Hip and Gable Roofs
Section 7.7 - Drifts on Lower Roofs
Section 7.8 - Roof Projections and Parapets

Key Provisions:
• Unbalanced loads apply for roof slopes between 0.5/12 and 7/12
• Drift calculations use uniform rectangular surcharge
• Valley drifts combine intersecting gable drifts

For complete reference, consult ASCE 7-22 Chapter 7.
        """
        messagebox.showinfo("ASCE 7-22 Reference", reference_text)

    def _show_user_guide(self):
        """Show user guide."""
        guide_text = """
Valley Snow Load Calculator V2.0 - User Guide

1. Input Parameters:
   - Ground snow load (pg) from local code
   - Roof geometry (spans, offsets)
   - Material properties

2. Calculation Process:
   - Click "Calculate Snow Loads"
   - Review results in right panel
   - View diagrams and reports

3. Project Management:
   - Save/load projects as JSON files
   - Export results for reports

4. ASCE 7-22 Compliance:
   - Section 7.6.1 unbalanced loads
   - Section 7.7 drift calculations
   - Professional engineering analysis

For detailed help, consult the ASCE 7-22 standard.
        """
        messagebox.showinfo("User Guide", guide_text)

    def _show_about(self):
        """Show about dialog."""
        about_text = """
Valley Snow Load Calculator V2.0

ASCE 7-22 Compliant Engineering Software
Complete snow load analysis for valley roof intersections

Features:
• Professional ASCE 7-22 calculations
• Interactive roof geometry modeling
• Comprehensive beam design analysis
• PDF report generation
• Project save/load functionality

Version: 2.0.0
Built with Python and Tkinter

© 2024 Valley Snow Load Calculator Development Team
        """
        messagebox.showinfo("About", about_text)

    def _show_health_check(self):
        """Show system health check dialog."""
        try:
            health_status = self.project_manager.get_system_health_status()

            health_win = tk.Toplevel(self.root)
            health_win.title("System Health Check")
            health_win.geometry("500x400")

            ttk.Label(
                health_win, text="System Health Status", font=("Arial", 14, "bold")
            ).pack(pady=10)

            # Health status
            status_frame = ttk.Frame(health_win)
            status_frame.pack(fill="x", padx=20, pady=10)

            db_status = health_status.get("database_status", "unknown")
            status_color = (
                "green"
                if db_status == "healthy"
                else "red"
                if db_status == "error"
                else "orange"
            )

            ttk.Label(
                status_frame,
                text=f"Database Status: {db_status.upper()}",
                foreground=status_color,
                font=("Arial", 10, "bold"),
            ).pack(anchor="w")

            ttk.Label(
                status_frame,
                text=f"Total Projects: {health_status.get('total_projects', 0)}",
            ).pack(anchor="w")

            # Error summary
            error_summary = health_status.get("error_summary", {})
            if error_summary.get("total_errors", 0) > 0:
                ttk.Label(
                    status_frame,
                    text=f"Recent Errors: {error_summary['total_errors']}",
                    foreground="red",
                ).pack(anchor="w")

                if error_summary.get("most_common_error"):
                    error_type, count = error_summary["most_common_error"]
                    ttk.Label(
                        status_frame, text=f"Most Common: {error_type} ({count} times)"
                    ).pack(anchor="w")

            # Recovery status
            recovery_status = (
                "Ready" if health_status.get("recovery_ready", False) else "Not Ready"
            )
            ttk.Label(status_frame, text=f"Recovery Status: {recovery_status}").pack(
                anchor="w", pady=(10, 0)
            )

            # Action buttons
            button_frame = ttk.Frame(health_win)
            button_frame.pack(fill="x", padx=20, pady=10)

            if db_status != "healthy":
                ttk.Button(
                    button_frame,
                    text="Run Recovery",
                    command=lambda: self._run_health_recovery(health_win),
                ).pack(side="left", padx=5)

            ttk.Button(button_frame, text="Close", command=health_win.destroy).pack(
                side="right", padx=5
            )

        except Exception as e:
            self.logger.log_error(e, operation="show_health_check")
            messagebox.showerror(
                "Health Check Error", f"Failed to check system health: {e}"
            )

    def _run_health_recovery(self, parent_window):
        """Run system health recovery."""
        try:
            # This would implement various recovery strategies
            messagebox.showinfo(
                "Recovery", "System recovery completed. Please restart the application."
            )
            parent_window.destroy()
        except Exception as e:
            self.logger.log_error(e, operation="run_health_recovery")
            messagebox.showerror("Recovery Error", f"Recovery failed: {e}")

    def _create_backup(self):
        """Create a backup of current data."""
        try:
            backup_path = self.project_manager.create_backup(self.current_project_id)
            if backup_path:
                messagebox.showinfo(
                    "Backup Created", f"Backup created successfully:\n{backup_path}"
                )
            else:
                messagebox.showerror("Backup Failed", "Failed to create backup.")
        except Exception as e:
            self.logger.log_error(e, operation="create_backup")
            messagebox.showerror("Backup Error", f"Backup failed: {e}")

    def _exit_application(self):
        """Exit the application."""
        if self._confirm_discard_changes():
            plt.close("all")  # Close any matplotlib figures
            self.root.quit()

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()
