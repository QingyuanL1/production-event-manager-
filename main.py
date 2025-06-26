#!/usr/bin/env python3
"""
生产排班系统主入口文件
Production Scheduling System Main Entry Point
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tkinter as tk
from src.ui.main_ui import ProductionSchedulingSystem

def main():
    """主函数"""
    root = tk.Tk()
    app = ProductionSchedulingSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()