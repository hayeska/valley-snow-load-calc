# themes.py - Theme management for Valley Calculator V2.0

import tkinter as tk
from tkinter import ttk
from typing import Dict


class ThemeManager:
    """
    Manages light and dark themes for the Valley Snow Load Calculator.

    Provides consistent styling across all UI components with support for:
    - Light and dark color schemes
    - Professional engineering software appearance
    - High contrast options
    - Customizable color palettes
    """

    def __init__(self, root: tk.Tk):
        """Initialize theme manager with root window."""
        self.root = root
        self.current_theme = "light"
        self.style = ttk.Style()

        # Define color palettes
        self.themes = {
            "light": {
                "name": "Light",
                "colors": {
                    "bg_primary": "#f8f9fa",
                    "bg_secondary": "#ffffff",
                    "bg_tertiary": "#e9ecef",
                    "fg_primary": "#212529",
                    "fg_secondary": "#495057",
                    "fg_tertiary": "#6c757d",
                    "accent_primary": "#007bff",
                    "accent_secondary": "#0056b3",
                    "success": "#28a745",
                    "warning": "#ffc107",
                    "error": "#dc3545",
                    "border": "#dee2e6",
                    "border_hover": "#adb5bd",
                    "input_bg": "#ffffff",
                    "input_border": "#ced4da",
                    "input_focus": "#007bff",
                    "button_bg": "#007bff",
                    "button_fg": "#ffffff",
                    "button_hover": "#0056b3",
                    "menu_bg": "#ffffff",
                    "menu_fg": "#212529",
                    "status_bg": "#e9ecef",
                    "status_fg": "#495057",
                },
            },
            "dark": {
                "name": "Dark",
                "colors": {
                    "bg_primary": "#1a1a1a",
                    "bg_secondary": "#2d2d2d",
                    "bg_tertiary": "#404040",
                    "fg_primary": "#ffffff",
                    "fg_secondary": "#cccccc",
                    "fg_tertiary": "#999999",
                    "accent_primary": "#4dabf7",
                    "accent_secondary": "#339af0",
                    "success": "#51cf66",
                    "warning": "#ffd43b",
                    "error": "#ff6b6b",
                    "border": "#555555",
                    "border_hover": "#777777",
                    "input_bg": "#404040",
                    "input_border": "#666666",
                    "input_focus": "#4dabf7",
                    "button_bg": "#4dabf7",
                    "button_fg": "#ffffff",
                    "button_hover": "#339af0",
                    "menu_bg": "#2d2d2d",
                    "menu_fg": "#ffffff",
                    "status_bg": "#404040",
                    "status_fg": "#cccccc",
                },
            },
            "high_contrast": {
                "name": "High Contrast",
                "colors": {
                    "bg_primary": "#000000",
                    "bg_secondary": "#1a1a1a",
                    "bg_tertiary": "#333333",
                    "fg_primary": "#ffffff",
                    "fg_secondary": "#ffff00",
                    "fg_tertiary": "#cccccc",
                    "accent_primary": "#00ffff",
                    "accent_secondary": "#00cccc",
                    "success": "#00ff00",
                    "warning": "#ffff00",
                    "error": "#ff0000",
                    "border": "#ffffff",
                    "border_hover": "#ffff00",
                    "input_bg": "#000000",
                    "input_border": "#ffffff",
                    "input_focus": "#00ffff",
                    "button_bg": "#ffffff",
                    "button_fg": "#000000",
                    "button_hover": "#cccccc",
                    "menu_bg": "#000000",
                    "menu_fg": "#ffffff",
                    "status_bg": "#333333",
                    "status_fg": "#ffffff",
                },
            },
        }

        # Initialize with light theme
        self.apply_theme("light")

    def get_available_themes(self) -> list:
        """Get list of available theme names."""
        return list(self.themes.keys())

    def get_theme_name(self, theme_key: str) -> str:
        """Get display name for a theme."""
        return self.themes.get(theme_key, {}).get("name", theme_key)

    def get_current_theme_colors(self) -> Dict[str, str]:
        """Get colors for current theme."""
        return self.themes.get(self.current_theme, {}).get("colors", {})

    def apply_theme(self, theme_name: str):
        """Apply a theme to the application."""
        if theme_name not in self.themes:
            print(f"Warning: Theme '{theme_name}' not found, using light theme")
            theme_name = "light"

        self.current_theme = theme_name
        colors = self.themes[theme_name]["colors"]

        # Configure root window colors
        self.root.configure(bg=colors["bg_primary"])

        # Configure ttk styles
        self._configure_ttk_styles(colors)

        # Configure custom styles
        self._configure_custom_styles(colors)

        # Update existing widgets if needed
        self._update_existing_widgets(colors)

    def _configure_ttk_styles(self, colors: Dict[str, str]):
        """Configure ttk widget styles."""
        # Frame styles
        self.style.configure(
            "Card.TFrame",
            background=colors["bg_secondary"],
            borderwidth=1,
            relief="solid",
        )

        # Label styles
        self.style.configure(
            "TLabel", background=colors["bg_primary"], foreground=colors["fg_primary"]
        )

        self.style.configure(
            "Header.TLabel",
            background=colors["bg_primary"],
            foreground=colors["fg_primary"],
            font=("Arial", 12, "bold"),
        )

        self.style.configure(
            "Accent.TLabel",
            background=colors["bg_primary"],
            foreground=colors["accent_primary"],
            font=("Arial", 10, "bold"),
        )

        # Button styles
        self.style.configure(
            "TButton",
            background=colors["button_bg"],
            foreground=colors["button_fg"],
            borderwidth=1,
            relief="raised",
            font=("Arial", 10),
        )

        self.style.map(
            "TButton",
            background=[("active", colors["button_hover"])],
            foreground=[("active", colors["button_fg"])],
        )

        # Accent button (for calculate button)
        self.style.configure(
            "Accent.TButton",
            background=colors["accent_primary"],
            foreground=colors["button_fg"],
            borderwidth=2,
            relief="raised",
            font=("Arial", 12, "bold"),
        )

        self.style.map(
            "Accent.TButton",
            background=[("active", colors["accent_secondary"])],
            foreground=[("active", colors["button_fg"])],
        )

        # Entry styles
        self.style.configure(
            "TEntry", fieldbackground=colors["input_bg"], borderwidth=1, relief="solid"
        )

        # Combobox styles
        self.style.configure(
            "TCombobox",
            fieldbackground=colors["input_bg"],
            background=colors["button_bg"],
            foreground=colors["button_fg"],
        )

        # Notebook styles
        self.style.configure(
            "TNotebook", background=colors["bg_primary"], tabmargins=[2, 5, 2, 0]
        )

        self.style.configure(
            "TNotebook.Tab",
            background=colors["bg_tertiary"],
            foreground=colors["fg_primary"],
            padding=[10, 5],
        )

        self.style.map(
            "TNotebook.Tab",
            background=[("selected", colors["bg_secondary"])],
            foreground=[("selected", colors["fg_primary"])],
        )

        # Progressbar styles
        self.style.configure(
            "TProgressbar",
            background=colors["accent_primary"],
            troughcolor=colors["bg_tertiary"],
            borderwidth=1,
            lightcolor=colors["accent_secondary"],
            darkcolor=colors["accent_primary"],
        )

    def _configure_custom_styles(self, colors: Dict[str, str]):
        """Configure custom widget styles."""
        # Status bar style
        self.style.configure(
            "Status.TLabel",
            background=colors["status_bg"],
            foreground=colors["status_fg"],
            font=("Arial", 9),
        )

        # Error/Success message styles
        self.style.configure(
            "Error.TLabel",
            background=colors["bg_primary"],
            foreground=colors["error"],
            font=("Arial", 9, "italic"),
        )

        self.style.configure(
            "Success.TLabel",
            background=colors["bg_primary"],
            foreground=colors["success"],
            font=("Arial", 9, "italic"),
        )

        self.style.configure(
            "Warning.TLabel",
            background=colors["bg_primary"],
            foreground=colors["warning"],
            font=("Arial", 9, "italic"),
        )

    def _update_existing_widgets(self, colors: Dict[str, str]):
        """Update colors for existing custom widgets."""
        # Update the main window background
        if hasattr(self, "root") and self.root:
            self.root.configure(bg=colors["bg_primary"])

        # Update V1 interface widgets (canvas, frames, etc.)
        self._update_v1_interface(colors)

    def _update_v1_interface(self, colors: Dict[str, str]):
        """Update V1 interface widgets for theme changes."""
        try:
            # Find V1 widgets by traversing the widget tree
            for child in self.root.winfo_children():
                if isinstance(child, tk.Canvas):
                    # Update canvas background
                    child.configure(bg=colors["bg_primary"])
                elif hasattr(child, "configure") and hasattr(child, "winfo_class"):
                    widget_class = child.winfo_class()
                    if widget_class in ["Frame", "LabelFrame"]:
                        # Update frame backgrounds
                        child.configure(bg=colors["bg_primary"])
                    elif widget_class == "Label":
                        # Update label colors
                        child.configure(
                            bg=colors["bg_primary"], fg=colors["fg_primary"]
                        )
                    elif widget_class == "Button":
                        # Update button colors
                        child.configure(bg=colors["button_bg"], fg=colors["button_fg"])

                # Recursively update children
                if hasattr(child, "winfo_children"):
                    self._update_widget_tree(child, colors)
        except Exception as e:
            print(f"Error updating V1 interface: {e}")

    def _update_widget_tree(self, widget, colors: Dict[str, str]):
        """Recursively update widget tree colors."""
        try:
            for child in widget.winfo_children():
                if hasattr(child, "configure") and hasattr(child, "winfo_class"):
                    widget_class = child.winfo_class()
                    if widget_class in ["Frame", "LabelFrame"]:
                        child.configure(bg=colors["bg_primary"])
                    elif widget_class == "Label":
                        child.configure(
                            bg=colors["bg_primary"], fg=colors["fg_primary"]
                        )
                    elif widget_class == "Entry":
                        child.configure(
                            bg=colors["input_bg"],
                            fg=colors["fg_primary"],
                            insertbackground=colors["fg_primary"],
                        )
                    elif widget_class == "Text":
                        child.configure(bg=colors["input_bg"], fg=colors["fg_primary"])

                # Continue recursion
                if hasattr(child, "winfo_children"):
                    self._update_widget_tree(child, colors)
        except Exception:
            # Silently ignore errors in widget updates
            pass

    def get_color(self, color_key: str) -> str:
        """Get a specific color from current theme."""
        colors = self.get_current_theme_colors()
        return colors.get(color_key, "#000000")

    def create_colored_button(
        self, parent, text: str, color_key: str = "accent_primary", command=None
    ) -> tk.Button:
        """Create a custom colored button."""
        colors = self.get_current_theme_colors()
        button_color = colors.get(color_key, colors["accent_primary"])

        button = tk.Button(
            parent,
            text=text,
            bg=button_color,
            fg=colors["button_fg"],
            activebackground=colors["accent_secondary"],
            activeforeground=colors["button_fg"],
            relief="raised",
            borderwidth=2,
            font=("Arial", 10, "bold"),
            command=command,
        )
        return button

    def create_highlight_frame(self, parent, highlight_color: str = None) -> tk.Frame:
        """Create a frame with highlight border."""
        colors = self.get_current_theme_colors()
        if highlight_color is None:
            highlight_color = colors["accent_primary"]

        frame = tk.Frame(
            parent,
            bg=colors["bg_secondary"],
            highlightbackground=highlight_color,
            highlightcolor=highlight_color,
            highlightthickness=2,
        )
        return frame


# Global theme manager instance
_theme_manager = None


def get_theme_manager(root: tk.Tk = None) -> ThemeManager:
    """Get or create the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None and root is not None:
        _theme_manager = ThemeManager(root)
    return _theme_manager


def apply_theme(theme_name: str):
    """Apply a theme globally."""
    if _theme_manager:
        _theme_manager.apply_theme(theme_name)


def get_current_theme_colors() -> Dict[str, str]:
    """Get colors for current theme."""
    if _theme_manager:
        return _theme_manager.get_current_theme_colors()
    return {}
