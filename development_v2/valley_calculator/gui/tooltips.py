# tooltips.py - Enhanced tooltip system for Valley Calculator V2.0

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Union


class TooltipManager:
    """
    Advanced tooltip system for the Valley Snow Load Calculator.

    Features:
    - Rich text tooltips with formatting
    - Delayed appearance and disappearance
    - Context-aware help information
    - Keyboard navigation support
    - Accessible design
    """

    def __init__(self, root: tk.Tk):
        """Initialize tooltip manager."""
        self.root = root
        self.tooltips: Dict[str, Dict] = {}
        self.active_tooltip: Optional[tk.Toplevel] = None
        self.active_widget: Optional[tk.Widget] = None

        # Configuration
        self.delay_show = 500  # ms
        self.delay_hide = 3000  # ms
        self.max_width = 400  # pixels

        # Create tooltip window
        self._create_tooltip_window()

        # Tooltip content database
        self._load_tooltip_content()

    def _create_tooltip_window(self):
        """Create the tooltip window."""
        self.tooltip_window = tk.Toplevel(self.root)
        self.tooltip_window.withdraw()  # Hide initially
        self.tooltip_window.overrideredirect(True)  # Remove window decorations
        self.tooltip_window.attributes('-topmost', True)  # Stay on top

        # Configure tooltip appearance
        self.tooltip_window.configure(bg='#ffffe0', relief='solid', borderwidth=1)

        # Create text widget for rich content
        self.tooltip_text = tk.Text(self.tooltip_window,
                                  wrap=tk.WORD,
                                  font=('Arial', 9),
                                  bg='#ffffe0',
                                  fg='#000000',
                                  relief='flat',
                                  padx=8,
                                  pady=6,
                                  height=1,
                                  width=50)
        self.tooltip_text.pack(expand=True, fill=tk.BOTH)

        # Make text read-only
        self.tooltip_text.config(state='disabled')

    def _load_tooltip_content(self):
        """Load tooltip content for all UI elements."""
        self.tooltip_content = {
            # Project Information
            "project_name": {
                "title": "Project Name",
                "content": "Enter a descriptive name for your snow load analysis project.\n\nExamples: 'Valley Residence', 'Commercial Building A', 'Roof Analysis 2024'\n\nThis name will be used in saved files and reports."
            },

            "location": {
                "title": "Project Location",
                "content": "Specify the geographic location for code compliance.\n\nUsed for:\n• Ground snow load determination\n• Local code requirements\n• Report documentation\n\nExamples: 'Denver, CO', 'Site Address'"
            },

            # Snow Load Parameters
            "pg": {
                "title": "Ground Snow Load (pg)",
                "content": "The minimum ground snow load per ASCE 7-22 Figure 7.2-1.\n\n• Based on statistical data (50-year return period)\n• Local building code requirements\n• Typically 20-100 psf depending on location\n\nUnits: pounds per square foot (psf)"
            },

            "w2": {
                "title": "Winter Wind Parameter (W2)",
                "content": "Wind speed parameter for winter conditions per ASCE 7-22 Figure 7.2-2.\n\n• Affects drift calculations\n• Typically 0.25-0.65\n• Lower values = more severe winter winds\n• Higher values = less severe conditions\n\nDimensionless parameter"
            },

            "ce": {
                "title": "Exposure Factor (Ce)",
                "content": "Terrain exposure factor per ASCE 7-22 Table 7.3-1.\n\nValues:\n• 0.9: Terrain with windbreaks\n• 1.0: Open terrain (typical)\n• 1.2: Exposed ridge lines\n\nAdjusts for local wind exposure conditions"
            },

            "ct": {
                "title": "Thermal Factor (Ct)",
                "content": "Thermal factor per ASCE 7-22 Table 7.3-2.\n\nValues:\n• 1.0: All structures except as indicated below\n• 1.1: Structures kept just above freezing\n• 1.2: Continuously heated greenhouses\n\nAccounts for building thermal conditions"
            },

            "is_factor": {
                "title": "Importance Factor (Is)",
                "content": "Importance factor per ASCE 7-22 Table 1.5-2.\n\nRisk Categories:\n• I: Low hazard (1.0)\n• II: Typical buildings (1.0)\n• III: Substantial hazard (1.1)\n• IV: Essential facilities (1.2)\n\nIncreases design loads for critical structures"
            },

            # Geometry
            "north_span": {
                "title": "North Roof Span",
                "content": "Distance from E-W ridge to north eave (ft).\n\n• Defines the north roof plane length\n• Used for tributary area calculations\n• Affects drift windward fetch\n\nTypically 10-50 ft for residential structures"
            },

            "south_span": {
                "title": "South Roof Span",
                "content": "Distance from E-W ridge to south eave (ft).\n\n• Defines the south roof plane length\n• Critical for valley geometry\n• Affects leeward drift extent\n\nTypically 10-50 ft for residential structures"
            },

            "ew_half_width": {
                "title": "E-W Half Width",
                "content": "Half-width from N-S ridge to eave (ft).\n\n• Symmetric about N-S ridge\n• Defines building width\n• Affects tributary areas\n\nTotal building width = 2 × (E-W half width)"
            },

            "valley_offset": {
                "title": "Valley Horizontal Offset",
                "content": "Horizontal distance from N-S ridge projection to valley low point (ft).\n\n• Defines valley geometry\n• Affects drift patterns\n• Symmetric on both sides\n\nTypically 4-20 ft for standard valleys"
            },

            "pitch_north": {
                "title": "North Roof Pitch",
                "content": "North roof slope (rise/12).\n\n• Rise in inches per 12 inches horizontal\n• Affects snow retention per ASCE 7-22 Figure 7.4-1\n• Influences unbalanced load requirements\n\nTypical: 4/12 to 12/12"
            },

            "pitch_west": {
                "title": "West Roof Pitch",
                "content": "West roof slope (rise/12).\n\n• Rise in inches per 12 inches horizontal\n• Affects snow retention per ASCE 7-22 Figure 7.4-1\n• Influences unbalanced load requirements\n\nTypical: 4/12 to 12/12"
            },

            # Material Properties
            "dead_load": {
                "title": "Roof Dead Load",
                "content": "Weight of roof system (psf).\n\nIncludes:\n• Roofing materials\n• Insulation\n• Structural deck\n• Mechanical equipment\n\nTypical Values:\n• 10-15 psf: Lightweight construction\n• 15-25 psf: Standard construction\n• 25+ psf: Heavy roof systems"
            },

            "beam_width": {
                "title": "Valley Beam Width",
                "content": "Width of the valley support beam (inches).\n\n• Dimension perpendicular to span\n• Affects moment of inertia (I = bh³/12)\n• Influences bending capacity\n\nCommon sizes: 3.5\", 5.5\", 7.25\" (nominal)"
            },

            "beam_depth": {
                "title": "Valley Beam Depth",
                "content": "Depth of the valley support beam (inches).\n\n• Dimension parallel to span\n• Critical for bending strength\n• Affects deflection\n• Larger depth = greater capacity\n\nTypical: 9.5\" to 16\"+ for valley beams"
            },

            # Buttons and Actions
            "calculate_button": {
                "title": "Calculate Snow Loads",
                "content": "Perform complete ASCE 7-22 snow load analysis.\n\nCalculations include:\n• Balanced snow loads\n• Unbalanced snow loads\n• Drift surcharge analysis\n• Valley beam design\n• Professional report generation\n\nResults appear in tabs to the right."
            },

            # Menu items
            "file_new": {
                "title": "New Project",
                "content": "Start a new snow load analysis project.\n\n• Clears all current data\n• Resets to default values\n• Prompts to save current work\n\nShortcut: Ctrl+N"
            },

            "file_open": {
                "title": "Open Project",
                "content": "Load a previously saved project file.\n\n• Supports .json project files\n• Loads all input parameters\n• Recalculates results automatically\n\nShortcut: Ctrl+O"
            },

            "file_save": {
                "title": "Save Project",
                "content": "Save current project to file.\n\n• Saves all inputs and results\n• JSON format for compatibility\n• Includes metadata and timestamp\n\nShortcut: Ctrl+S"
            }
        }

    def add_tooltip(self, widget: tk.Widget, tooltip_id: str, custom_content: Optional[Dict] = None):
        """Add tooltip to a widget."""
        if custom_content:
            self.tooltip_content[tooltip_id] = custom_content

        # Bind events
        widget.bind('<Enter>', lambda e: self._schedule_show_tooltip(widget, tooltip_id))
        widget.bind('<Leave>', lambda e: self._schedule_hide_tooltip())
        widget.bind('<Motion>', lambda e: self._update_tooltip_position())

        # Store tooltip info
        if not hasattr(widget, '_tooltip_id'):
            widget._tooltip_id = tooltip_id

    def remove_tooltip(self, widget: tk.Widget):
        """Remove tooltip from a widget."""
        widget.unbind('<Enter>')
        widget.unbind('<Leave>')
        widget.unbind('<Motion>')
        if hasattr(widget, '_tooltip_id'):
            delattr(widget, '_tooltip_id')

    def _schedule_show_tooltip(self, widget: tk.Widget, tooltip_id: str):
        """Schedule tooltip to appear after delay."""
        self._cancel_scheduled_hide()

        if tooltip_id in self.tooltip_content:
            self.active_widget = widget
            self.root.after(self.delay_show, lambda: self._show_tooltip(tooltip_id))

    def _schedule_hide_tooltip(self):
        """Schedule tooltip to hide after delay."""
        if self.active_tooltip and self.active_tooltip.winfo_exists():
            self.root.after(self.delay_hide, self._hide_tooltip)

    def _cancel_scheduled_hide(self):
        """Cancel any scheduled tooltip hiding."""
        # This would need a more sophisticated implementation with job tracking
        pass

    def _show_tooltip(self, tooltip_id: str):
        """Display the tooltip."""
        if not self.active_widget or tooltip_id not in self.tooltip_content:
            return

        content = self.tooltip_content[tooltip_id]

        # Update tooltip content
        self.tooltip_text.config(state='normal')
        self.tooltip_text.delete(1.0, tk.END)

        # Add title in bold
        if 'title' in content:
            self.tooltip_text.insert(tk.END, content['title'] + '\n', 'title')
            self.tooltip_text.insert(tk.END, '\n')

        # Add main content
        if 'content' in content:
            self.tooltip_text.insert(tk.END, content['content'])

        self.tooltip_text.config(state='disabled')

        # Configure title tag
        self.tooltip_text.tag_configure('title', font=('Arial', 9, 'bold'))

        # Position tooltip near mouse cursor
        x, y = self.root.winfo_pointerxy()
        self.tooltip_window.geometry(f"+{x+15}+{y+10}")

        # Show tooltip
        self.tooltip_window.deiconify()
        self.active_tooltip = self.tooltip_window

    def _hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window and self.tooltip_window.winfo_exists():
            self.tooltip_window.withdraw()
        self.active_tooltip = None
        self.active_widget = None

    def _update_tooltip_position(self):
        """Update tooltip position to follow mouse."""
        if self.active_tooltip and self.active_tooltip.winfo_exists():
            x, y = self.root.winfo_pointerxy()
            self.tooltip_window.geometry(f"+{x+15}+{y+10}")

    def show_help_tooltip(self, widget: tk.Widget, help_text: str):
        """Show a temporary help tooltip."""
        # Create temporary tooltip content
        temp_id = f"temp_{id(widget)}"
        self.tooltip_content[temp_id] = {
            "title": "Help",
            "content": help_text
        }

        # Show immediately without delay
        self.active_widget = widget
        self._show_tooltip(temp_id)

        # Auto-hide after longer delay
        self.root.after(5000, lambda: self._hide_tooltip())

    def get_tooltip_content(self, tooltip_id: str) -> Optional[Dict]:
        """Get tooltip content for a given ID."""
        return self.tooltip_content.get(tooltip_id)


# Global tooltip manager instance
_tooltip_manager = None


def get_tooltip_manager(root: tk.Tk = None) -> TooltipManager:
    """Get or create the global tooltip manager instance."""
    global _tooltip_manager
    if _tooltip_manager is None and root is not None:
        _tooltip_manager = TooltipManager(root)
    return _tooltip_manager


def add_tooltip(widget: tk.Widget, tooltip_id: str, custom_content: Optional[Dict] = None):
    """Add tooltip to widget globally."""
    if _tooltip_manager:
        _tooltip_manager.add_tooltip(widget, tooltip_id, custom_content)


def show_help_tooltip(widget: tk.Widget, help_text: str):
    """Show temporary help tooltip globally."""
    if _tooltip_manager:
        _tooltip_manager.show_help_tooltip(widget, help_text)


