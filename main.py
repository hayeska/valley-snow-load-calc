# main.py
# Entry point for ASCE 7-22 Valley Snow Load Calculator – GUI Version
# Fixed for direct execution in Cursor

import tkinter as tk
from gui_interface import ValleySnowCalculator
import sys

if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.lift()
        root.attributes("-topmost", True)
        root.after_idle(root.attributes, "-topmost", False)
        app = ValleySnowCalculator(root)
        root.update()
        root.deiconify()
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
