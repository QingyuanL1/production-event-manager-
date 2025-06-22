import tkinter as tk
from data_loader import DataLoader

if __name__ == "__main__":
    root = tk.Tk()
    app = DataLoader(root)
    root.mainloop() 