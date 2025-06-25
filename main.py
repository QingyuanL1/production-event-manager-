import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import threading
import time
import datetime
from data_loader import DataLoader
from event_manager import EventManager
from event_ui import EventFormUI

class ProductionSchedulingSystem:
    """
    Main class for the Production Scheduling System application.
    """
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("生产排班系统 - Production Scheduling System v1.0")
        self.root.geometry("1200x800")
        
        # Data loader
        self.data_loader = DataLoader()
        
        # Event manager
        self.event_manager = EventManager(self.data_loader, self.log_message)
        
        # Currently selected data type
        self.current_data_type = tk.StringVar()
        
        # Currently displayed data
        self.current_data = None
        
        # Currently selected sheet
        self.current_sheet = tk.StringVar()
        
        # Build the UI
        self.setup_ui()
        
        # Initialize system log
        self.log_message("INFO", "系统初始化完成")
        self.log_message("INFO", f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_message("INFO", "使用默认配置")
        self.log_message("INFO", "自动加载线程已启动")
        self.log_message("SUCCESS", "生产排班系统启动成功")
        
    def setup_ui(self):
        """
        Set up the user interface.
        """
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        
        # Tab frames
        self.control_panel_tab = ttk.Frame(self.notebook)
        self.data_preview_tab = ttk.Frame(self.notebook)
        self.event_management_tab = ttk.Frame(self.notebook)
        self.result_analysis_tab = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.control_panel_tab, text="控制面板")
        self.notebook.add(self.data_preview_tab, text="数据预览")
        self.notebook.add(self.event_management_tab, text="事件管理")
        self.notebook.add(self.result_analysis_tab, text="结果分析")
        
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Set up each tab
        self.setup_control_panel()
        self.setup_data_preview()
        self.setup_event_management()
        self.setup_result_analysis()
        
        # System log frame at the bottom
        log_frame = ttk.LabelFrame(main_frame, text="系统日志")
        log_frame.pack(fill=tk.BOTH, expand=False, pady=10)
        
        # System log text area
        self.log_text = tk.Text(log_frame, height=6, bg="#f0f0f0", state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_control_panel(self):
        """
        Set up the control panel tab.
        """
        # Left panel for buttons
        left_panel = ttk.Frame(self.control_panel_tab, width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # Button styles - removed pady from here as ttk.Button doesn't support it
        button_style = {'width': 20}
        
        # Data loading buttons
        load_daily_plan_btn = ttk.Button(
            left_panel, 
            text="加载HSA Daily Plan", 
            command=lambda: self.load_data("HSA Daily Plan"),
            **button_style
        )
        load_daily_plan_btn.pack(pady=5, anchor=tk.W)
        
        load_fg_eoh_btn = ttk.Button(
            left_panel, 
            text="加载HSA FG EOH", 
            command=lambda: self.load_data("HSA FG EOH"),
            **button_style
        )
        load_fg_eoh_btn.pack(pady=5, anchor=tk.W)
        
        load_capacity_btn = ttk.Button(
            left_panel, 
            text="加载HSA Capacity", 
            command=lambda: self.load_data("HSA Capacity"),
            **button_style
        )
        load_capacity_btn.pack(pady=5, anchor=tk.W)
        
        load_learning_curve_btn = ttk.Button(
            left_panel, 
            text="加载Learning Curve", 
            command=lambda: self.load_data("Learning Curve"),
            **button_style
        )
        load_learning_curve_btn.pack(pady=5, anchor=tk.W)
        
        # Separator
        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # Event management buttons
        create_event_btn = ttk.Button(
            left_panel, 
            text="创建新事件", 
            command=self.switch_to_event_tab,
            **button_style
        )
        create_event_btn.pack(pady=5, anchor=tk.W)
        
        view_events_btn = ttk.Button(
            left_panel, 
            text="查看事件列表", 
            command=self.view_events,
            **button_style
        )
        view_events_btn.pack(pady=5, anchor=tk.W)
        
        export_events_btn = ttk.Button(
            left_panel, 
            text="导出事件", 
            command=self.export_events,
            **button_style
        )
        export_events_btn.pack(pady=5, anchor=tk.W)
        
        # Separator
        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # System buttons
        clear_log_btn = ttk.Button(
            left_panel, 
            text="清空日志", 
            command=self.clear_log,
            **button_style
        )
        clear_log_btn.pack(pady=5, anchor=tk.W)
        
        settings_btn = ttk.Button(
            left_panel, 
            text="系统设置", 
            **button_style
        )
        settings_btn.pack(pady=5, anchor=tk.W)
        
        # Right panel for status and info
        right_panel = ttk.Frame(self.control_panel_tab)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status display
        status_frame = ttk.LabelFrame(right_panel, text="系统状态")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Status information
        self.status_text = tk.Text(status_frame, height=20, bg="#f5f5f5", state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Update status
        self.update_status()
        
    def setup_data_preview(self):
        """
        Set up the data preview tab.
        """
        # Top frame for data selection
        top_frame = ttk.Frame(self.data_preview_tab)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Data selection dropdown
        ttk.Label(top_frame, text="选择数据表:").pack(side=tk.LEFT, padx=5)
        
        data_types = self.data_loader.get_available_data_types()
        self.data_combobox = ttk.Combobox(
            top_frame, 
            textvariable=self.current_data_type,
            values=data_types,
            width=20
        )
        self.data_combobox.pack(side=tk.LEFT, padx=5)
        self.data_combobox.bind("<<ComboboxSelected>>", self.on_data_type_selected)
        
        # Sheet selection dropdown (for files with multiple sheets)
        ttk.Label(top_frame, text="选择工作表:").pack(side=tk.LEFT, padx=5)
        
        self.sheet_combobox = ttk.Combobox(
            top_frame,
            textvariable=self.current_sheet,
            width=25
        )
        self.sheet_combobox.pack(side=tk.LEFT, padx=5)
        self.sheet_combobox.bind("<<ComboboxSelected>>", self.on_sheet_selected)
        
        # Refresh button
        refresh_btn = ttk.Button(
            top_frame, 
            text="刷新", 
            command=self.refresh_data_preview
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Data display frame
        data_frame = ttk.Frame(self.data_preview_tab)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for data display
        self.data_tree = ttk.Treeview(data_frame)
        
        # Configure tag for alternating row colors (zebra stripes) and header style
        self.data_tree.tag_configure('oddrow', background='#f0f0f0')
        self.data_tree.tag_configure('evenrow', background='white')
        self.data_tree.tag_configure('header', font=('Arial', 9, 'bold'))
        
        # Scrollbars for the treeview
        y_scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        x_scrollbar = ttk.Scrollbar(data_frame, orient=tk.HORIZONTAL, command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack scrollbars and treeview
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
    def setup_event_management(self):
        """
        Set up the event management tab.
        """
        # 创建事件管理UI
        self.event_form_ui = EventFormUI(
            self.event_management_tab, 
            self.event_manager, 
            self.log_message
        )
        
    def setup_result_analysis(self):
        """
        Set up the result analysis tab.
        """
        # Placeholder for result analysis tab
        ttk.Label(
            self.result_analysis_tab, 
            text="结果分析功能将在后续实现", 
            font=("Arial", 14)
        ).pack(pady=50)
        
    def load_data(self, data_type):
        """
        Load the specified data type.
        
        Args:
            data_type: Type of data to load
        """
        self.log_message("INFO", f"正在加载 {data_type}...")
        
        # Use a thread to avoid UI freezing during data loading
        def load_thread():
            success, message, data = self.data_loader.load_data(data_type)
            
            # Update UI in the main thread
            self.root.after(0, lambda: self.on_data_loaded(success, message, data_type))
            
        threading.Thread(target=load_thread).start()
        
    def on_data_loaded(self, success, message, data_type):
        """
        Callback when data is loaded.
        
        Args:
            success: Whether the data was loaded successfully
            message: Message describing the result
            data_type: Type of data that was loaded
        """
        if success:
            self.log_message("SUCCESS", message)
            # Update current data type in the combobox
            self.current_data_type.set(data_type)
            
            # 更新工作表下拉列表
            sheet_names = self.data_loader.get_sheet_names(data_type)
            self.sheet_combobox['values'] = sheet_names
            
            # 如果只有一个工作表，直接选择它
            if sheet_names and len(sheet_names) == 1:
                self.current_sheet.set(sheet_names[0])
            elif sheet_names:
                # 否则选择第一个工作表
                self.current_sheet.set(sheet_names[0])
                
            # Switch to data preview tab
            self.notebook.select(self.data_preview_tab)
            # Refresh the data preview
            self.refresh_data_preview()
        else:
            self.log_message("ERROR", message)
            messagebox.showerror("加载错误", message)
        
    def on_data_type_selected(self, event):
        """
        Handle data type selection from the combobox.
        
        Args:
            event: ComboboxSelected event
        """
        data_type = self.current_data_type.get()
        
        # 更新工作表下拉列表
        sheet_names = self.data_loader.get_sheet_names(data_type)
        self.sheet_combobox['values'] = sheet_names
        
        # 选择默认工作表
        if sheet_names:
            self.current_sheet.set(sheet_names[0])
        else:
            self.current_sheet.set("")
            
        self.refresh_data_preview()
        
    def on_sheet_selected(self, event):
        """
        Handle sheet selection from the combobox.
        
        Args:
            event: ComboboxSelected event
        """
        self.refresh_data_preview()
    
    def get_current_data(self):
        """
        根据当前选择的数据类型和工作表获取对应的数据
        
        Returns:
            当前选择的数据
        """
        data_type = self.current_data_type.get()
        sheet = self.current_sheet.get()
        
        # 如果没有选择数据类型或工作表，返回None
        if not data_type:
            return None
        
        # 对于HSA Daily Plan，使用sheet感知的数据获取方法
        if data_type == "HSA Daily Plan":
            return self.data_loader.get_data_for_sheet(data_type, sheet)
            
        # 获取基本数据
        data = self.data_loader.get_data(data_type)
        
        # 处理多工作表的情况
        if data_type == "HSA Capacity":
            if sheet == "Manual":
                data = self.data_loader.get_data(f"{data_type}_Manual")
            elif sheet == "Special HSA PN":
                data = self.data_loader.get_data(f"{data_type}_Special")
            elif sheet == "Minimum packaging":
                data = self.data_loader.get_data(f"{data_type}_MinPkg")
                
        elif data_type == "Learning Curve":
            if sheet == "Learning curve (2)":
                data = self.data_loader.get_data(f"{data_type}_Other")
            elif sheet == "Learning curve for shutdown":
                data = self.data_loader.get_data(f"{data_type}_Shutdown")
        
        return data
    
    def refresh_data_preview(self):
        """
        Refresh the data preview based on the currently selected data type.
        """
        data = self.get_current_data()
        
        if data is None:
            self.log_message("INFO", "未选择数据或数据未加载，请先加载数据")
            return
            
        self.current_data = data
        self.display_data_in_tree(data)
        
    def display_data_in_tree(self, data):
        """
        Display the given DataFrame in the treeview.
        
        Args:
            data: DataFrame to display
        """
        if data is None or data.empty:
            # 如果数据为空，清空树视图
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            return
            
        # Clear existing data
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        data_type = self.current_data_type.get()
        sheet = self.current_sheet.get()
        
        # 处理Daily Plan的特殊情况，其有独立的表头
        headers = None
        if data_type == "HSA Daily Plan":
            headers = self.data_loader.get_headers_for_sheet(data_type, sheet)
            
        # 制作数据的工作副本，避免修改原始数据
        # 不再使用全局前向填充，而是有选择地处理每种数据类型
        working_data = data.copy()
        
        # Configure columns
        self.data_tree['columns'] = list(data.columns)
        self.data_tree['show'] = 'headings'
        
        # Set column headings
        for col in data.columns:
            # Limit column width for better display
            display_text = str(col)
            
            # Handle datetime column names and remove time part if it's 00:00:00
            if isinstance(col, datetime.datetime):
                # 检查是否是标准日期格式（时间部分为00:00:00）
                if col.hour == 0 and col.minute == 0 and col.second == 0:
                    display_text = col.strftime('%Y-%m-%d')
                # 检查是否是类似 2025-03-02 00:00:00.1 格式
                elif str(col).endswith('00:00:00.1') or '.1' in str(col):
                    # 提取日期部分
                    date_part = col.strftime('%Y-%m-%d')
                    # 如果是类似带小数的时间部分，保留特殊标记（如T4）
                    display_text = date_part
                else:
                    display_text = col.strftime('%Y-%m-%d')
                
            col_width = min(150, max(50, len(display_text) * 10))
            self.data_tree.column(col, width=col_width, anchor='w')
            self.data_tree.heading(col, text=display_text)
            
        # 如果是Daily Plan，额外添加表头行
        if headers is not None and not headers.empty:
            # 清除所有行并重新设置表头行
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
                
            # 添加表头行
            for i, row in headers.iterrows():
                values = []
                for val in row.values:
                    if pd.isna(val):
                        values.append("")
                    elif isinstance(val, (float, np.float64)) and val.is_integer():
                        values.append(str(int(val)))
                    else:
                        values.append(str(val))
                
                self.data_tree.insert('', 'end', values=values, tags=('header',))
        
        # Add data rows with alternating colors (zebra stripes)
        count = 0
        for i, row in working_data.iterrows():
            # Convert values to strings, handling NaN values
            values = []
            for val in row.values:
                if pd.isna(val):
                    values.append("")
                elif isinstance(val, (float, np.float64)) and val.is_integer():
                    # Format integer-valued floats as integers
                    values.append(str(int(val)))
                else:
                    values.append(str(val))
            
            # Apply alternating row colors
            tag = 'evenrow' if count % 2 == 0 else 'oddrow'
            self.data_tree.insert('', 'end', values=values, tags=(tag,))
            count += 1
            
    def update_status(self):
        """
        Update the system status display.
        """
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        
        # Add current status information
        status_info = [
            f"系统版本: v1.0",
            f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"数据目录: {self.data_loader.data_dir}",
            f"",
            f"已加载数据:",
        ]
        
        # Add information about loaded data
        for data_type in self.data_loader.get_available_data_types():
            data = self.data_loader.get_data(data_type)
            status = "已加载" if data is not None else "未加载"
            status_info.append(f"  - {data_type}: {status}")
        
        # Add event management information
        status_info.append("")
        status_info.append("事件管理状态:")
        if hasattr(self, 'event_manager'):
            event_count = len(self.event_manager.get_events())
            status_info.append(f"  - 已创建事件数量: {event_count}")
            status_info.append(f"  - 事件管理器: 已初始化")
        else:
            status_info.append("  - 事件管理器: 未初始化")
            
        # Add the status information to the text widget
        self.status_text.insert(tk.END, "\n".join(status_info))
        self.status_text.config(state=tk.DISABLED)
        
        # Schedule the next update
        self.root.after(1000, self.update_status)
        
    def log_message(self, level, message):
        """
        Add a message to the system log.
        
        Args:
            level: Message level (INFO, ERROR, SUCCESS, etc.)
            message: The message to log
        """
        self.log_text.config(state=tk.NORMAL)
        
        # Get current time
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        
        # Format the log message
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # Apply tag based on level for color
        self.log_text.insert(tk.END, log_entry)
        
        # Scroll to the end
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def clear_log(self):
        """
        Clear the system log.
        """
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("INFO", "日志已清空")
    
    def switch_to_event_tab(self):
        """
        Switch to the event management tab.
        """
        self.notebook.select(self.event_management_tab)
        self.log_message("INFO", "切换到事件管理页面")
    
    def view_events(self):
        """
        View events and switch to event management tab.
        """
        self.switch_to_event_tab()
        # 刷新事件列表
        if hasattr(self, 'event_form_ui'):
            self.event_form_ui.refresh_event_list()
        self.log_message("INFO", "查看事件列表")
    
    def export_events(self):
        """
        Export events to Excel file.
        """
        if hasattr(self, 'event_form_ui'):
            self.event_form_ui.export_events()
        else:
            messagebox.showwarning("导出失败", "事件管理功能尚未初始化")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductionSchedulingSystem(root)
    root.mainloop() 