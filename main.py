# main.py
# Entry point for ASCE 7-22 Valley Snow Load Calculator – GUI Version
# Fixed for direct execution in Cursor

import tkinter as tk
from gui_interface import ValleySnowCalculator

if __name__ == "__main__":
    root = tk.Tk()
    app = ValleySnowCalculator(root)
    root.mainloop()
