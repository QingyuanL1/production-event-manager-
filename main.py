import tkinter as tk
from data_loader import ProductionSchedulingApp

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductionSchedulingApp(root)
    root.mainloop() 