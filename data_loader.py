import pandas as pd
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext
import numpy as np
import datetime

class ProductionSchedulingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能生产排班系统")
        self.root.geometry("1200x800")
        self.setup_styles()
        self.data_files = {}
        self.setup_ui()
        self.load_data_files()

    def setup_ui(self):
        # Main container for top (controls+tabs) and bottom (log)
        main_paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True)

        # Top container for left (controls) and right (tabs)
        top_pane = ttk.PanedWindow(main_paned_window, orient=tk.HORIZONTAL)
        main_paned_window.add(top_pane, weight=4)  # Give more space to top part

        # Left control panel
        self.left_panel = ttk.LabelFrame(top_pane, text="控制面板", width=200)
        top_pane.add(self.left_panel, weight=1)

        # Right panel for tabs
        self.right_panel = ttk.Frame(top_pane)
        top_pane.add(self.right_panel, weight=4)

        # Bottom log panel
        self.log_panel = ttk.LabelFrame(main_paned_window, text="系统日志", height=150)
        main_paned_window.add(self.log_panel, weight=1)

        self.create_control_panel(self.left_panel)
        self.create_main_tabs(self.right_panel)
        self.create_log_panel(self.log_panel)

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Calibri', 12, 'bold'))
        style.configure("Treeview", rowheight=25)
        style.map("Treeview", background=[("selected", "lightblue")])
        
        # Add gridlines
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) # Remove borders
        style.configure("Treeview",
                        background="#D3D3D3",
                        fieldbackground="#D3D3D3")
        
    def create_control_panel(self, parent):
        parent.pack_propagate(False)  # Prevent resizing
        
        # Use grid layout for easier management
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=0)
        parent.grid_rowconfigure(2, weight=0)
        parent.grid_rowconfigure(3, weight=1)  # Spacer
        parent.grid_columnconfigure(0, weight=1)

        run_button = ttk.Button(parent, text="执行排班", command=self.not_implemented)
        run_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        save_button = ttk.Button(parent, text="保存排班结果", command=self.not_implemented)
        save_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        load_button = ttk.Button(parent, text="加载排班结果", command=self.not_implemented)
        load_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def create_log_panel(self, parent):
        parent.pack_propagate(False)
        log_text = scrolledtext.ScrolledText(parent, state='disabled', wrap=tk.WORD, font=('Courier New', 9))
        log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text = log_text
        self.log_message("系统初始化完成。")

    def log_message(self, message):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{now}] {message}\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def create_main_tabs(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.data_preview_tab = ttk.Frame(notebook)
        event_management_tab = ttk.Frame(notebook)
        results_tab = ttk.Frame(notebook)

        notebook.add(self.data_preview_tab, text="数据预览")
        notebook.add(event_management_tab, text="事件管理")
        notebook.add(results_tab, text="结果分析")
        
        self.create_data_preview_tab(self.data_preview_tab)
        self.create_event_management_tab(event_management_tab)

    def create_data_preview_tab(self, parent):
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="选择数据表:").pack(side=tk.LEFT, padx=5)
        self.file_var = tk.StringVar()
        
        self.file_map = {
            "HSA Daily Plan": "daily plan.xlsx",
            "FG EOH": "FG EOH.xlsx",
            "Learning Curve": "Learning Curve.xlsx",
            "Capacity": "capacity .xlsx"
        }
        
        self.file_combo = ttk.Combobox(top_frame, textvariable=self.file_var, state="readonly", width=30,
                                       values=list(self.file_map.keys()))
        self.file_combo.pack(side=tk.LEFT, padx=5)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)

        self.info_label = ttk.Label(top_frame, text="")
        self.info_label.pack(side=tk.LEFT, padx=10)
        
        self.data_view_frame = ttk.Frame(parent)
        self.data_view_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_event_management_tab(self, parent):
        input_frame = ttk.LabelFrame(parent, text="事件输入")
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        labels = ["事件类型:", "产线:", "产品PN:", "数量:", "日期:", "备注:"]
        self.event_entries = {}

        for i, label_text in enumerate(labels):
            ttk.Label(input_frame, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky='w')
            if label_text == "事件类型:":
                event_type_combo = ttk.Combobox(input_frame, state="readonly", values=["产量调整", "产品转换", "产线停机", "紧急插单", "取消订单"])
                event_type_combo.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
                self.event_entries[label_text] = event_type_combo
            elif label_text == "备注:":
                entry = ttk.Entry(input_frame)
                entry.grid(row=i, column=1, columnspan=3, padx=5, pady=5, sticky='ew')
                self.event_entries[label_text] = entry
            else:
                entry = ttk.Entry(input_frame)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
                self.event_entries[label_text] = entry

        ttk.Button(input_frame, text="添加事件", command=self.not_implemented).grid(row=len(labels), column=1, pady=10)
        input_frame.grid_columnconfigure(1, weight=1)

        list_frame = ttk.LabelFrame(parent, text="事件列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        cols = ["类型", "产线", "产品PN", "数量", "日期", "状态", "备注"]
        event_tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        for col in cols:
            event_tree.heading(col, text=col)
        event_tree.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="删除选中事件", command=self.not_implemented).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="清空所有事件", command=self.not_implemented).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="导入事件表", command=self.not_implemented).pack(side=tk.RIGHT, padx=5)

    def on_file_selected(self, event):
        selected_friendly_name = self.file_var.get()
        file_name = self.file_map.get(selected_friendly_name)
        if not file_name:
            return

        if file_name in self.data_files:
            self.log_message(f"选择查看文件: {selected_friendly_name} ({file_name})")
            workbook = self.data_files[file_name]
            sheet_name = workbook.sheet_names[0] # Always select the first sheet
            self.display_sheet(workbook, sheet_name)
            
    def load_data_files(self):
        data_path = "数据表"
        if not os.path.exists(data_path):
            messagebox.showerror("错误", "数据表目录不存在！")
            self.log_message("错误: 数据表目录不存在！")
            return

        for file_name in os.listdir(data_path):
            if file_name.endswith(('.xlsx', '.xls')):
                try:
                    file_path = os.path.join(data_path, file_name)
                    workbook = pd.ExcelFile(file_path)
                    self.data_files[file_name] = workbook
                    self.log_message(f"成功加载文件: {file_name}")
                except Exception as e:
                    messagebox.showerror("加载错误", f"加载文件 {file_name} 失败: {e}")
                    self.log_message(f"加载文件 {file_name} 失败: {e}")
        
        if self.data_files:
            self.file_combo.set(list(self.file_map.keys())[0])
            self.on_file_selected(None)
            self.log_message("所有数据文件加载完毕。")
            
    def display_sheet(self, workbook, sheet_name):
        try:
            df = pd.read_excel(workbook, sheet_name=sheet_name, header=None)
            
            # Forward fill for merged cells
            for col in df.columns:
                df[col] = df[col].ffill()
            
            # Special header handling for 'daily plan.xlsx'
            if workbook.io.endswith('daily plan.xlsx'):
                header_rows = pd.read_excel(workbook, sheet_name=sheet_name, nrows=4, header=None)
                
                # Forward fill for merged headers
                header_rows = header_rows.ffill(axis=1)
                
                new_header = []
                for col_idx in range(header_rows.shape[1]):
                    col_values = [str(v) if pd.notna(v) else '' for v in header_rows.iloc[:, col_idx]]
                    # Join and remove duplicates while preserving order
                    unique_values = list(dict.fromkeys(filter(None, col_values)))
                    new_header.append('\n'.join(unique_values))
                
                df = pd.read_excel(workbook, sheet_name=sheet_name, header=4)
                df.columns = new_header[:len(df.columns)]
            else:
                df = pd.read_excel(workbook, sheet_name=sheet_name, header=0)

            self.display_dataframe(df)
            self.info_label.config(text=f"行数: {df.shape[0]}, 列数: {df.shape[1]}")
            self.log_message(f"成功显示工作表: {sheet_name}")
        except Exception as e:
            messagebox.showerror("加载错误", f"加载工作表时出错: {e}")
            self.log_message(f"错误: 加载工作表 {sheet_name} 时出错: {e}")

    def display_dataframe(self, df):
        for widget in self.data_view_frame.winfo_children():
            widget.destroy()

        if df is None:
            return

        frame = ttk.Frame(self.data_view_frame)
        frame.pack(fill=tk.BOTH, expand=True)
        
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")
        
        tree = ttk.Treeview(frame, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=tk.BOTH, expand=True)

        columns = list(df.columns)
        tree["columns"] = columns
        tree["show"] = "headings"
        
        for col in columns:
            header_text = str(col)
            try:
                # Format date-like column headers
                dt = pd.to_datetime(header_text)
                header_text = dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass  # Not a date, use original header
            tree.heading(col, text=header_text)
            tree.column(col, width=100, minwidth=50)
        
        for i, row in df.iterrows():
            values = ["" if pd.isna(row[col]) else str(row[col]) for col in columns]
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            tree.insert("", "end", values=values, tags=(tag,))
            
        tree.tag_configure('oddrow', background='white')
        tree.tag_configure('evenrow', background='#F0F0F0') # Light grey for zebra effect

    def not_implemented(self):
        messagebox.showinfo("提示", "此功能尚未实现")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductionSchedulingApp(root)
    root.mainloop() 