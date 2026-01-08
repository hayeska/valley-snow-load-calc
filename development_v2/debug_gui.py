#!/usr/bin/env python3
"""Debug GUI to see what the interface actually looks like"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the valley_calculator package to Python path
sys.path.insert(0, os.path.dirname(__file__))


def debug_gui():
    """Create a debug version of the GUI to see what it looks like"""
    print("Creating debug GUI...")

    root = tk.Tk()
    root.title("Valley Snow Load Calculator V2.0 - DEBUG MODE")
    root.geometry("1200x800")

    # Create main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Create paned window for resizable panels
    paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True)

    # Left panel - Input (simplified for debug)
    left_frame = ttk.Frame(paned)
    paned.add(left_frame, weight=1)

    # Simple input panel for testing
    input_frame = ttk.LabelFrame(left_frame, text="Input Panel", padding=10)
    input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    ttk.Label(input_frame, text="Ground Snow Load (psf):").grid(
        row=0, column=0, sticky="w", pady=2
    )
    pg_var = tk.DoubleVar(value=25.0)
    ttk.Entry(input_frame, textvariable=pg_var).grid(
        row=0, column=1, sticky="ew", pady=2
    )

    ttk.Label(input_frame, text="North Roof Pitch (rise/12):").grid(
        row=1, column=0, sticky="w", pady=2
    )
    pitch_var = tk.DoubleVar(value=8.0)
    ttk.Entry(input_frame, textvariable=pitch_var).grid(
        row=1, column=1, sticky="ew", pady=2
    )

    ttk.Button(
        input_frame,
        text="Test Input Values",
        command=lambda: print(f"PG: {pg_var.get()}, Pitch: {pitch_var.get()}"),
    ).grid(row=2, column=0, columnspan=2, pady=10)

    input_frame.columnconfigure(1, weight=1)

    # Right panel - Results (simplified for debug)
    right_frame = ttk.Frame(paned)
    paned.add(right_frame, weight=2)

    # Simple results panel for testing
    results_frame = ttk.LabelFrame(right_frame, text="Results Panel", padding=10)
    results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Create notebook for tabbed results
    notebook = ttk.Notebook(results_frame)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Summary tab
    summary_frame = ttk.Frame(notebook)
    notebook.add(summary_frame, text="Summary")

    summary_text = tk.Text(summary_frame, wrap=tk.WORD, height=20)
    summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    summary_text.insert(tk.END, "=== Valley Snow Load Calculator V2.0 ===\n\n")
    summary_text.insert(tk.END, "This is the DEBUG version to test the GUI layout.\n\n")
    summary_text.insert(
        tk.END, "If you can see this text, the basic GUI framework is working.\n\n"
    )
    summary_text.insert(tk.END, "Expected features:\n")
    summary_text.insert(tk.END, "• Input panel on the left with form fields\n")
    summary_text.insert(tk.END, "• Results panel on the right with tabs\n")
    summary_text.insert(tk.END, "• Professional engineering interface\n")
    summary_text.insert(tk.END, "• Modern Tkinter styling\n\n")
    summary_text.insert(tk.END, "If this looks different from what you expected,\n")
    summary_text.insert(
        tk.END, "please describe what you're seeing vs. what you expected."
    )

    # Diagrams tab
    diagrams_frame = ttk.Frame(notebook)
    notebook.add(diagrams_frame, text="Diagrams")

    ttk.Label(diagrams_frame, text="Diagrams would appear here").pack(pady=20)

    # Detailed tab
    detailed_frame = ttk.Frame(notebook)
    notebook.add(detailed_frame, text="Detailed")

    ttk.Label(detailed_frame, text="Detailed calculations would appear here").pack(
        pady=20
    )

    # Report tab
    report_frame = ttk.Frame(notebook)
    notebook.add(report_frame, text="Report")

    ttk.Label(report_frame, text="PDF report generation would happen here").pack(
        pady=20
    )

    # Calculate button
    calc_frame = ttk.Frame(main_frame)
    calc_frame.pack(fill=tk.X, pady=5)

    ttk.Button(
        calc_frame,
        text="Run Test Calculation",
        command=lambda: run_test_calculation(summary_text),
    ).pack(pady=5)

    # Status bar
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill=tk.X, pady=(0, 5))

    status_label = ttk.Label(status_frame, text="Ready - Debug mode active")
    status_label.pack(side=tk.LEFT)

    ttk.Label(status_frame, text="Valley Snow Load Calculator V2.0").pack(side=tk.RIGHT)

    print("GUI created successfully. Check your desktop for the application window.")
    print("Close the window when done testing.")
    root.mainloop()


def run_test_calculation(text_widget):
    """Run a test calculation and display results"""
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, "=== Test Calculation Results ===\n\n")
    text_widget.insert(tk.END, "Ground Snow Load: 25.0 psf\n")
    text_widget.insert(tk.END, "North Roof Pitch: 8/12\n")
    text_widget.insert(tk.END, "Calculated Flat Roof Load: 17.5 psf\n")
    text_widget.insert(tk.END, "Calculated Balanced Load: 14.0 psf\n\n")
    text_widget.insert(tk.END, "✅ Calculation completed successfully!\n\n")
    text_widget.insert(tk.END, "This confirms the GUI framework is working.\n")
    text_widget.insert(
        tk.END, "If the full application looks different, there may be\n"
    )
    text_widget.insert(tk.END, "an issue with component loading or initialization.")


if __name__ == "__main__":
    debug_gui()
