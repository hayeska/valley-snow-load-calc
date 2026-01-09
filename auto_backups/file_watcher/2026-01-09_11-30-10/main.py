# main.py
# Entry point for ASCE 7-22 Valley Snow Load Calculator – GUI Version
# Fixed for direct execution in Cursor

import tkinter as tk
from gui_interface import ValleySnowCalculator
import sys

# Start file watcher for automatic backups and auto-commit
try:
    from file_watcher import start_file_watcher_in_background

    print("Starting file watcher for automatic backups and auto-commit...")
    start_file_watcher_in_background(auto_commit=True)
    print("File watcher started successfully.")
except ImportError:
    print(
        "Warning: file_watcher module not available. Install watchdog: pip install watchdog"
    )
except Exception as e:
    print(f"Warning: Could not start file watcher: {e}")
    print("Application will continue without automatic file backups.")

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
