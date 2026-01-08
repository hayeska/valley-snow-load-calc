#!/usr/bin/env python3
"""
Simple GUI test to verify Tkinter is working and can display windows.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class SimpleValleyCalculator:
    """Minimal GUI test for Valley Snow Load Calculator"""

    def __init__(self, master):
        self.master = master
        master.title("ASCE 7-22 Valley Snow Load Calculator - TEST VERSION")
        master.geometry("800x600")

        # Create menu bar
        menubar = tk.Menu(master)
        master.configure(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=master.quit)

        # Create main layout
        main_frame = ttk.Frame(master, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Valley Snow Load Calculator", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)

        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding=10)
        input_frame.pack(fill=tk.X, pady=10)

        # Snow load input
        ttk.Label(input_frame, text="Ground Snow Load pg (psf):").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.pg_var = tk.DoubleVar(value=25.0)
        ttk.Entry(input_frame, textvariable=self.pg_var).grid(row=0, column=1, pady=2)

        # Roof geometry
        ttk.Label(input_frame, text="North Roof Pitch (rise/12):").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.pitch_var = tk.DoubleVar(value=8.0)
        ttk.Entry(input_frame, textvariable=self.pitch_var).grid(
            row=1, column=1, pady=2
        )

        # Calculate button
        calc_button = ttk.Button(
            main_frame, text="Calculate Snow Loads", command=self.calculate
        )
        calc_button.pack(pady=10)

        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.results_text = tk.Text(results_frame, height=15, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.results_text.yview
        )
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status message
        self.status_label = ttk.Label(
            main_frame, text="Ready - Test GUI loaded successfully"
        )
        self.status_label.pack(pady=5)

        # Initial message
        self.results_text.insert(tk.END, "=== Valley Snow Load Calculator Test ===\n\n")
        self.results_text.insert(tk.END, "✅ GUI loaded successfully!\n")
        self.results_text.insert(tk.END, "✅ Tkinter is working properly\n")
        self.results_text.insert(tk.END, "✅ Application window is visible\n\n")
        self.results_text.insert(
            tk.END, "This is a simplified test version to verify the GUI framework.\n"
        )
        self.results_text.insert(
            tk.END, "Enter values above and click 'Calculate' to test functionality.\n"
        )

    def calculate(self):
        """Simple calculation test"""
        try:
            pg = self.pg_var.get()
            pitch = self.pitch_var.get()

            # Simple calculation
            flat_load = pg * 0.7  # Simplified
            sloped_load = flat_load * (1 - pitch * 0.02)  # Simplified

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "=== Calculation Results ===\n\n")
            self.results_text.insert(tk.END, f"Ground Snow Load: {pg} psf\n")
            self.results_text.insert(tk.END, f"Roof Pitch: {pitch}/12\n\n")
            self.results_text.insert(tk.END, f"Flat Roof Load: {flat_load:.1f} psf\n")
            self.results_text.insert(
                tk.END, f"Sloped Roof Load: {sloped_load:.1f} psf\n\n"
            )
            self.results_text.insert(tk.END, "✅ Calculation completed successfully!\n")
            self.results_text.insert(tk.END, "✅ GUI interaction working properly\n")

            self.status_label.config(text="Calculation completed successfully")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error: {str(e)}")
            self.status_label.config(text="Error during calculation")


def main():
    root = tk.Tk()
    app = SimpleValleyCalculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
