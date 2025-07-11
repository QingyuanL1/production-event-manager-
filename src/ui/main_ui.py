import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import threading
import time
import datetime
from src.core.data_loader import DataLoader
from src.core.event_manager import EventManager
from src.ui.event_ui import EventFormUI

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
        
        # Currently selected data type
        self.current_data_type = tk.StringVar()
        
        # Currently displayed data
        self.current_data = None
        
        # Currently selected sheet
        self.current_sheet = tk.StringVar()
        
        # Build the UI first
        self.setup_ui()
        
        # Initialize Event manager after UI is set up
        self.event_manager = EventManager(self.data_loader, self.log_message)
        
        # Create the actual event management UI now that event_manager is ready
        self.setup_event_management_ui()
        
        # Initialize system log
        self.log_message("INFO", "系统初始化完成")
        self.log_message("INFO", f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_message("INFO", "使用默认配置")
        
        # Auto-load all data tables
        self.auto_load_all_data()
        
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
        
        # System log text area (调大高度以便查看更多日志)
        self.log_text = tk.Text(log_frame, height=20, bg="#f0f0f0", state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for formatting
        self.log_text.tag_configure("bold", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("normal", font=("Consolas", 9, "normal"))
        
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
        
        dos_config_btn = ttk.Button(
            left_panel, 
            text="DOS配置", 
            command=self.open_dos_config,
            **button_style
        )
        dos_config_btn.pack(pady=5, anchor=tk.W)
        
        settings_btn = ttk.Button(
            left_panel, 
            text="系统设置/DOS配置", 
            command=self.open_dos_config,
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
        # 暂时创建一个占位符，实际的事件管理UI会在event_manager初始化后创建
        ttk.Label(
            self.event_management_tab, 
            text="事件管理界面初始化中...", 
            font=("Arial", 14)
        ).pack(pady=50)
    
    def setup_event_management_ui(self):
        """
        Create the actual event management UI after event_manager is initialized.
        """
        # Clear the placeholder
        for widget in self.event_management_tab.winfo_children():
            widget.destroy()
        
        # Create the real event management UI
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
    
    def auto_load_all_data(self):
        """
        自动加载所有必需的数据表
        """
        self.log_message("INFO", "开始自动加载所有数据表...")
        
        # 定义需要加载的数据表
        data_tables = [
            "HSA Daily Plan",
            "HSA FG EOH", 
            "HSA Capacity",
            "Learning Curve"
        ]
        
        # 用于跟踪加载进度
        self.auto_load_progress = {
            "total": len(data_tables),
            "completed": 0,
            "success": 0,
            "failed": 0
        }
        
        # 依次加载每个表
        for data_type in data_tables:
            self.auto_load_single_data(data_type)
    
    def auto_load_single_data(self, data_type):
        """
        自动加载单个数据表
        
        Args:
            data_type: 要加载的数据类型
        """
        self.log_message("INFO", f"正在加载 {data_type}...")
        
        def load_thread():
            success, message, data = self.data_loader.load_data(data_type)
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self.on_auto_data_loaded(success, message, data_type))
            
        threading.Thread(target=load_thread).start()
    
    def on_auto_data_loaded(self, success, message, data_type):
        """
        自动加载数据完成的回调
        
        Args:
            success: 是否加载成功
            message: 结果消息
            data_type: 数据类型
        """
        self.auto_load_progress["completed"] += 1
        
        if success:
            self.auto_load_progress["success"] += 1
            self.log_message("SUCCESS", message)
        else:
            self.auto_load_progress["failed"] += 1
            self.log_message("ERROR", message)
        
        # 检查是否所有数据都已加载完成
        if self.auto_load_progress["completed"] == self.auto_load_progress["total"]:
            self.on_auto_load_complete()
    
    def on_auto_load_complete(self):
        """
        所有数据自动加载完成的回调
        """
        success_count = self.auto_load_progress["success"]
        failed_count = self.auto_load_progress["failed"]
        total_count = self.auto_load_progress["total"]
        
        if failed_count == 0:
            self.log_message("SUCCESS", f"✅ 所有数据表加载完成！({success_count}/{total_count})")
        else:
            self.log_message("WARNING", f"⚠️  数据加载完成，但有失败项：成功 {success_count}，失败 {failed_count}")
        
        # 设置默认显示的数据类型
        if success_count > 0:
            # 优先显示 HSA Daily Plan
            if self.data_loader.get_data("HSA Daily Plan") is not None:
                self.current_data_type.set("HSA Daily Plan")
            else:
                # 如果没有，显示第一个成功加载的
                for data_type in ["HSA FG EOH", "HSA Capacity", "Learning Curve"]:
                    if self.data_loader.get_data(data_type) is not None:
                        self.current_data_type.set(data_type)
                        break
            
            # 更新UI组件
            self.update_ui_after_auto_load()
    
    def update_ui_after_auto_load(self):
        """
        自动加载完成后更新UI组件
        """
        # 更新数据类型下拉框
        current_type = self.current_data_type.get()
        if current_type:
            # 更新工作表下拉列表
            sheet_names = self.data_loader.get_sheet_names(current_type)
            if hasattr(self, 'sheet_combobox'):
                self.sheet_combobox['values'] = sheet_names
                
                # 选择默认工作表
                if sheet_names:
                    self.current_sheet.set(sheet_names[0])
                    
                # 刷新数据预览
                self.refresh_data_preview()
        
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
        
        # Check if message contains bold formatting
        if "**" in message:
            # Parse bold text
            parts = message.split("**")
            log_prefix = f"[{timestamp}] {level}: "
            self.log_text.insert(tk.END, log_prefix, "normal")
            
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Odd indices are bold
                    self.log_text.insert(tk.END, part, "bold")
                else:  # Even indices are normal
                    self.log_text.insert(tk.END, part, "normal")
            
            self.log_text.insert(tk.END, "\n", "normal")
        else:
            # Normal message without formatting
            log_entry = f"[{timestamp}] {level}: {message}\n"
            self.log_text.insert(tk.END, log_entry, "normal")
        
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
    
    def open_dos_config(self):
        """
        Open DOS configuration dialog.
        """
        try:
            # 获取当前配置
            current_threshold = self.event_manager.db_manager.get_dos_threshold()
            current_shift_count = self.event_manager.db_manager.get_shift_check_count()
            
            # 创建配置对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("LCA处理配置")
            dialog.geometry("400x280")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (dialog.winfo_screenheight() // 2) - (280 // 2)
            dialog.geometry(f"400x280+{x}+{y}")
            
            # 主框架
            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # 标题
            ttk.Label(main_frame, text="LCA处理配置", font=("Arial", 14, "bold")).pack(pady=(0, 15))
            
            # DOS阈值配置
            dos_frame = ttk.LabelFrame(main_frame, text="DOS阈值设置")
            dos_frame.pack(fill=tk.X, pady=(0, 15))
            
            # 当前DOS值显示
            ttk.Label(dos_frame, text=f"当前阈值: {current_threshold:.1f} 天").pack(pady=5)
            
            # DOS输入框
            dos_input_frame = ttk.Frame(dos_frame)
            dos_input_frame.pack(pady=5)
            
            ttk.Label(dos_input_frame, text="新阈值:").pack(side=tk.LEFT)
            threshold_var = tk.StringVar(value=f"{current_threshold:.1f}")
            threshold_entry = ttk.Entry(dos_input_frame, textvariable=threshold_var, width=8)
            threshold_entry.pack(side=tk.LEFT, padx=(5, 5))
            ttk.Label(dos_input_frame, text="天").pack(side=tk.LEFT)
            
            # 班次检查数量配置
            shift_frame = ttk.LabelFrame(main_frame, text="班次检查设置")
            shift_frame.pack(fill=tk.X, pady=(0, 15))
            
            # 当前班次检查数量显示
            ttk.Label(shift_frame, text=f"当前检查班次数: {current_shift_count} 个").pack(pady=5)
            
            # 班次检查数量输入框
            shift_input_frame = ttk.Frame(shift_frame)
            shift_input_frame.pack(pady=5)
            
            ttk.Label(shift_input_frame, text="检查班次数:").pack(side=tk.LEFT)
            shift_count_var = tk.StringVar(value=str(current_shift_count))
            shift_count_entry = ttk.Entry(shift_input_frame, textvariable=shift_count_var, width=8)
            shift_count_entry.pack(side=tk.LEFT, padx=(5, 5))
            ttk.Label(shift_input_frame, text="个").pack(side=tk.LEFT)
            
            # 按钮框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X)
            
            def save_and_close():
                try:
                    new_threshold = float(threshold_var.get())
                    new_shift_count = int(shift_count_var.get())
                    
                    # 验证输入范围
                    if not (0.1 <= new_threshold <= 5.0):
                        messagebox.showerror("错误", "DOS阈值必须在0.1到5.0之间")
                        return
                    
                    if not (1 <= new_shift_count <= 10):
                        messagebox.showerror("错误", "检查班次数必须在1到10之间")
                        return
                    
                    # 保存配置
                    dos_success = self.event_manager.db_manager.set_dos_threshold(
                        new_threshold, 
                        description="GUI设置"
                    )
                    shift_success = self.event_manager.db_manager.set_shift_check_count(
                        new_shift_count,
                        description="GUI设置"
                    )
                    
                    if dos_success and shift_success:
                        messagebox.showinfo("成功", 
                            f"配置已保存:\n"
                            f"DOS阈值: {new_threshold:.1f} 天\n"
                            f"检查班次数: {new_shift_count} 个")
                        self.log_message("INFO", 
                            f"LCA配置已更新: DOS阈值={new_threshold:.1f}天, 检查班次数={new_shift_count}个")
                        dialog.destroy()
                    else:
                        messagebox.showerror("错误", "保存失败")
                        
                except ValueError:
                    messagebox.showerror("错误", "请输入有效数字")
            
            def reset_and_close():
                if messagebox.askyesno("确认", "重置为默认配置？\nDOS阈值: 0.5天\n检查班次数: 2个"):
                    self.event_manager.db_manager.set_dos_threshold(0.5)
                    self.event_manager.db_manager.set_shift_check_count(2)
                    messagebox.showinfo("成功", "已重置为默认配置")
                    self.log_message("INFO", "LCA配置已重置为默认值")
                    dialog.destroy()
            
            # 按钮
            ttk.Button(button_frame, text="确认保存", command=save_and_close).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="重置默认", command=reset_and_close).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)
            
            # 焦点到DOS输入框
            threshold_entry.focus()
            threshold_entry.select_range(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("错误", f"打开DOS配置失败: {str(e)}")
            self.log_message("ERROR", f"打开DOS配置失败: {str(e)}")


class SimpleDOSConfigDialog:
    """
    简化的DOS配置对话框
    """
    
    def __init__(self, parent, db_manager, log_callback):
        """
        初始化DOS配置对话框
        
        Args:
            parent: 父窗口
            db_manager: 数据库管理器
            log_callback: 日志回调函数
        """
        self.parent = parent
        self.db_manager = db_manager
        self.log_callback = log_callback
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("DOS阈值配置")
        self.dialog.geometry("450x300")
        self.dialog.resizable(True, True)
        
        # 使对话框模态
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"450x300+{x}+{y}")
        
        self.setup_ui()
        self.load_current_config()
        
    def setup_ui(self):
        """设置对话框界面"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="DOS阈值配置", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 当前配置显示
        current_frame = ttk.LabelFrame(main_frame, text="当前配置")
        current_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.current_label = ttk.Label(current_frame, text="加载中...", font=("Arial", 12))
        self.current_label.pack(padx=15, pady=15)
        
        # 阈值设置
        config_frame = ttk.LabelFrame(main_frame, text="设置新阈值")
        config_frame.pack(fill=tk.X, pady=(0, 20))
        
        threshold_frame = ttk.Frame(config_frame)
        threshold_frame.pack(padx=15, pady=15)
        
        ttk.Label(threshold_frame, text="最小DOS阈值:", font=("Arial", 11)).pack(side=tk.LEFT)
        
        self.threshold_var = tk.StringVar()
        threshold_spinbox = ttk.Spinbox(
            threshold_frame, 
            from_=0.1, 
            to=5.0, 
            increment=0.1, 
            textvariable=self.threshold_var,
            width=10,
            format="%.1f",
            font=("Arial", 11)
        )
        threshold_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(threshold_frame, text="天", font=("Arial", 11)).pack(side=tk.LEFT)
        
        # 说明文本
        desc_text = "当计算DOS值低于此阈值时，系统会发出警告提示"
        desc_label = ttk.Label(config_frame, text=desc_text, font=("Arial", 9), foreground="gray")
        desc_label.pack(padx=15, pady=(0, 10))
        
        # 按钮框架 - 固定在底部
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(30, 0))
        
        # 分隔线
        separator = ttk.Separator(button_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 15))
        
        # 按钮容器
        btn_container = ttk.Frame(button_frame)
        btn_container.pack()
        
        # 确认按钮 - 大号，醒目
        confirm_btn = ttk.Button(btn_container, text="✓ 确认保存", command=self.save_config)
        confirm_btn.pack(side=tk.LEFT, padx=(0, 15))
        confirm_btn.configure(width=12)
        
        # 重置按钮
        reset_btn = ttk.Button(btn_container, text="🔄 重置", command=self.reset_config)
        reset_btn.pack(side=tk.LEFT, padx=(0, 15))
        reset_btn.configure(width=10)
        
        # 取消按钮
        cancel_btn = ttk.Button(btn_container, text="✗ 取消", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.LEFT)
        cancel_btn.configure(width=10)
        
        # 绑定回车键到确认按钮
        self.dialog.bind('<Return>', lambda e: self.save_config())
        
    def load_current_config(self):
        """加载当前配置"""
        try:
            current_threshold = self.db_manager.get_dos_threshold()
            self.current_label.config(text=f"当前DOS阈值: {current_threshold:.1f} 天")
            self.threshold_var.set(f"{current_threshold:.1f}")
        except Exception as e:
            self.current_label.config(text=f"加载配置失败: {e}")
            
    def save_config(self):
        """保存配置"""
        try:
            threshold_str = self.threshold_var.get().strip()
            if not threshold_str:
                messagebox.showerror("错误", "请输入阈值")
                return
                
            new_threshold = float(threshold_str)
            
            if new_threshold < 0.1 or new_threshold > 5.0:
                messagebox.showerror("错误", "阈值必须在0.1到5.0之间")
                return
            
            success = self.db_manager.set_dos_threshold(
                new_threshold, 
                description=f"GUI配置更新于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            if success:
                messagebox.showinfo("成功", f"DOS阈值已设置为 {new_threshold:.1f} 天")
                self.log_callback("INFO", f"DOS阈值已更新为 {new_threshold:.1f} 天")
                self.load_current_config()
            else:
                messagebox.showerror("错误", "保存配置失败")
                
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
            
    def reset_config(self):
        """重置配置"""
        if messagebox.askyesno("确认", "重置为默认配置0.5天？"):
            success = self.db_manager.set_dos_threshold(0.5, description="重置为默认")
            if success:
                messagebox.showinfo("成功", "已重置为默认配置")
                self.log_callback("INFO", "DOS阈值已重置为默认值 0.5 天")
                self.load_current_config()
            else:
                messagebox.showerror("错误", "重置失败")


class DOSConfigDialogOld:
    """
    DOS配置对话框
    """
    
    def __init__(self, parent, db_manager, log_callback):
        """
        初始化DOS配置对话框
        
        Args:
            parent: 父窗口
            db_manager: 数据库管理器
            log_callback: 日志回调函数
        """
        self.parent = parent
        self.db_manager = db_manager
        self.log_callback = log_callback
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("DOS阈值配置")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        
        # 使对话框模态
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        self.setup_ui()
        self.load_current_config()
        
    def setup_ui(self):
        """设置对话框界面"""
        # 创建主画布和滚动条
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 主框架
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="DOS阈值配置", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 配置框架
        config_frame = ttk.LabelFrame(main_frame, text="当前配置")
        config_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 最小阈值设置
        threshold_frame = ttk.Frame(config_frame)
        threshold_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(threshold_frame, text="最小DOS阈值:").pack(side=tk.LEFT)
        
        self.threshold_var = tk.StringVar()
        self.threshold_spinbox = ttk.Spinbox(
            threshold_frame, 
            from_=0.1, 
            to=5.0, 
            increment=0.1, 
            textvariable=self.threshold_var,
            width=10,
            format="%.1f"
        )
        self.threshold_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(threshold_frame, text="天").pack(side=tk.LEFT)
        
        # 说明文本
        desc_frame = ttk.Frame(config_frame)
        desc_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        desc_text = """说明：
• 当计算得到的DOS值低于此阈值时，系统会发出警告
• 默认最小阈值为0.5天
• 建议根据实际生产情况调整此值"""
        
        desc_label = ttk.Label(desc_frame, text=desc_text, justify=tk.LEFT)
        desc_label.pack(anchor=tk.W)
        
        # 当前配置显示
        current_frame = ttk.LabelFrame(main_frame, text="当前系统配置")
        current_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_config_text = tk.Text(current_frame, height=6, state=tk.DISABLED, wrap=tk.WORD)
        self.current_config_text.pack(fill=tk.X, padx=10, pady=10)
        
        # 按钮框架 - 使用分隔线突出显示
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(15, 15))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 20))
        
        # 确认/保存按钮 - 加大尺寸，使用醒目颜色
        confirm_btn = ttk.Button(button_frame, text="✓ 确认保存", command=self.save_config)
        confirm_btn.pack(side=tk.LEFT, padx=(0, 15))
        confirm_btn.configure(width=15)
        
        # 重置按钮
        reset_btn = ttk.Button(button_frame, text="🔄 重置默认", command=self.reset_config)
        reset_btn.pack(side=tk.LEFT, padx=(0, 15))
        reset_btn.configure(width=15)
        
        # 取消按钮
        cancel_btn = ttk.Button(button_frame, text="✗ 取消", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
        cancel_btn.configure(width=10)
        
    def load_current_config(self):
        """加载当前配置"""
        try:
            # 获取当前阈值
            current_threshold = self.db_manager.get_dos_threshold()
            self.threshold_var.set(f"{current_threshold:.1f}")
            
            # 获取所有配置
            configs = self.db_manager.get_all_dos_configs()
            
            # 显示配置信息
            self.current_config_text.config(state=tk.NORMAL)
            self.current_config_text.delete(1.0, tk.END)
            
            config_info = f"当前活动配置:\n"
            config_info += f"• 最小DOS阈值: {current_threshold:.1f} 天\n\n"
            config_info += f"所有配置记录:\n"
            
            for config in configs:
                status = "✓ 激活" if config['is_active'] else "  停用"
                config_info += f"{status} {config['config_name']}: {config['min_dos_threshold']:.1f} 天\n"
                config_info += f"   创建时间: {config['created_time'][:19]}\n"
                if config['description']:
                    config_info += f"   说明: {config['description']}\n"
                config_info += "\n"
            
            self.current_config_text.insert(tk.END, config_info)
            self.current_config_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
            
    def save_config(self):
        """保存配置"""
        try:
            # 获取新的阈值
            threshold_str = self.threshold_var.get().strip()
            print(f"Debug: 获取到的阈值字符串: '{threshold_str}'")  # 调试信息
            
            if not threshold_str:
                messagebox.showerror("错误", "请输入阈值")
                return
                
            new_threshold = float(threshold_str)
            print(f"Debug: 转换后的阈值: {new_threshold}")  # 调试信息
            
            # 验证阈值范围
            if new_threshold < 0.1 or new_threshold > 5.0:
                messagebox.showerror("错误", "阈值必须在0.1到5.0之间")
                return
            
            print(f"Debug: 准备保存到数据库: {new_threshold}")  # 调试信息
            
            # 保存到数据库
            try:
                success = self.db_manager.set_dos_threshold(
                    new_threshold, 
                    description=f"用户配置于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                print(f"Debug: 数据库保存结果: {success}")  # 调试信息
                
                if success:
                    messagebox.showinfo("成功", f"DOS阈值已设置为 {new_threshold:.1f} 天")
                    self.log_callback("INFO", f"DOS阈值已更新为 {new_threshold:.1f} 天")
                    self.load_current_config()
                else:
                    messagebox.showerror("错误", "保存配置失败，请检查数据库连接")
                    
            except Exception as db_error:
                messagebox.showerror("错误", f"数据库操作失败: {str(db_error)}")
                print(f"Database error: {db_error}")  # 调试信息
                import traceback
                traceback.print_exc()
                
        except ValueError as ve:
            messagebox.showerror("错误", f"请输入有效的数字: {str(ve)}")
            print(f"ValueError: {ve}")  # 调试信息
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            print(f"Save config error: {e}")  # 调试信息
            import traceback
            traceback.print_exc()
            
    def reset_config(self):
        """重置为默认配置"""
        try:
            # 确认重置
            if messagebox.askyesno("确认", "确定要重置为默认配置(0.5天)吗？"):
                try:
                    success = self.db_manager.set_dos_threshold(
                        0.5, 
                        description=f"重置为默认配置于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    
                    if success:
                        self.threshold_var.set("0.5")
                        messagebox.showinfo("成功", "已重置为默认配置")
                        self.log_callback("INFO", "DOS阈值已重置为默认值 0.5 天")
                        self.load_current_config()
                    else:
                        messagebox.showerror("错误", "重置失败，请检查数据库连接")
                        
                except Exception as db_error:
                    messagebox.showerror("错误", f"数据库操作失败: {str(db_error)}")
                    print(f"Database reset error: {db_error}")  # 调试信息
                    
        except Exception as e:
            messagebox.showerror("错误", f"重置配置失败: {str(e)}")
            print(f"Reset config error: {e}")  # 调试信息


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductionSchedulingSystem(root)
    root.mainloop() 