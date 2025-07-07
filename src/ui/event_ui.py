import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional, Callable
import pandas as pd
from datetime import datetime

class EventFormUI:
    """
    多级级联事件表单UI组件
    支持动态生成最多7级的级联下拉框和输入框
    """
    
    def __init__(self, parent_frame, event_manager, log_callback=None):
        """
        初始化事件表单UI
        
        Args:
            parent_frame: 父窗口框架
            event_manager: 事件管理器实例
            log_callback: 日志回调函数
        """
        self.parent_frame = parent_frame
        self.event_manager = event_manager
        self.log_callback = log_callback
        
        # 当前表单状态
        self.current_event_type = None
        self.current_level = 0
        self.current_event_data = {}
        self.current_branch = None
        
        # UI组件存储
        self.level_frames = []
        self.level_widgets = []
        self.level_variables = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="生产事件登记系统", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 事件类型选择区域
        type_frame = ttk.LabelFrame(main_frame, text="选择事件类型")
        type_frame.pack(fill=tk.X, pady=10)
        
        self.event_type_var = tk.StringVar()
        self.event_type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.event_type_var,
            values=list(self.event_manager.event_types.keys()),
            state="readonly",
            width=30
        )
        self.event_type_combo.pack(side=tk.LEFT, padx=10, pady=10)
        self.event_type_combo.bind("<<ComboboxSelected>>", self.on_event_type_selected)
        
        # 重置按钮
        reset_btn = ttk.Button(type_frame, text="重置表单", command=self.reset_form)
        reset_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # 动态表单区域 - 直接使用Frame，不要滚动条
        self.form_frame = ttk.LabelFrame(main_frame, text="事件详细信息")
        self.form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.preview_btn = ttk.Button(button_frame, text="预览事件", command=self.preview_event, state=tk.DISABLED)
        self.preview_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(button_frame, text="提交事件", command=self.save_event, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # 事件列表区域
        list_frame = ttk.LabelFrame(main_frame, text="已创建事件列表")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 事件列表
        columns = ("事件ID", "事件类型", "创建时间", "状态")
        self.event_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        
        for col in columns:
            self.event_tree.heading(col, text=col)
            self.event_tree.column(col, width=120)
        
        # 滚动条
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.event_tree.yview)
        self.event_tree.configure(yscrollcommand=list_scrollbar.set)
        
        self.event_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 事件操作按钮
        event_btn_frame = ttk.Frame(list_frame)
        event_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        execute_btn = ttk.Button(event_btn_frame, text="执行选中事件", command=self.execute_selected_event)
        execute_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = ttk.Button(event_btn_frame, text="删除选中事件", command=self.delete_selected_event)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(event_btn_frame, text="导出事件列表", command=self.export_events)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(event_btn_frame, text="刷新列表", command=self.refresh_event_list)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # 初始化事件列表
        self.refresh_event_list()
    
    def log_message(self, level: str, message: str):
        """记录日志消息"""
        if self.log_callback:
            self.log_callback(level, message)
        else:
            print(f"[{level}] {message}")
    
    def on_event_type_selected(self, event=None):
        """当事件类型被选择时的回调"""
        event_type = self.event_type_var.get()
        if event_type:
            self.current_event_type = event_type
            self.current_level = 0
            self.current_event_data = {"事件类型": event_type}
            self.current_branch = None
            
            self.log_message("INFO", f"选择事件类型: {event_type}")
            self.build_dynamic_form()
    
    def build_dynamic_form(self):
        """构建静态表单，一次性显示所有字段"""
        # 清除现有表单
        self.clear_form()
        
        if not self.current_event_type:
            return
        
        event_config = self.event_manager.event_types[self.current_event_type]
        
        # 直接构建表单，不需要描述标签，因为在build_static_form中已经添加了
        
        # 创建网格布局的表单
        self.build_static_form(event_config)
    
    def build_static_form(self, event_config: Dict):
        """构建简洁的静态表单"""
        # 存储所有输入组件
        self.form_widgets = {}
        self.form_variables = {}
        
        # 添加事件描述
        desc_frame = ttk.Frame(self.form_frame)
        desc_frame.pack(fill=tk.X, padx=15, pady=10)
        
        desc_label = ttk.Label(
            desc_frame, 
            text=f"📝 {event_config['description']}", 
            font=("Arial", 11, "bold"),
            foreground="blue"
        )
        desc_label.pack(anchor=tk.W)
        
        # 基础字段区域
        basic_frame = ttk.Frame(self.form_frame)
        basic_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 构建基础字段
        self.build_basic_fields(basic_frame, event_config)
        
        # 如果有分支逻辑，构建分支选择区域
        if event_config.get("branches"):
            self.build_branch_section(self.form_frame, event_config)
        
        # 启用预览和保存按钮
        self.preview_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
    
    def build_basic_fields(self, parent_frame: ttk.Frame, event_config: Dict):
        """构建基础字段 - 使用简洁的网格布局"""
        levels = event_config["levels"]
        
        # 使用网格布局，3列：标签、输入框、提示
        row = 0
        
        for i, level_config in enumerate(levels):
            field_name = level_config["name"]
            field_type = level_config["type"]
            
            # 跳过有分支的字段，在后面单独处理
            if level_config.get("branches"):
                continue
            
            # 创建标签
            label = ttk.Label(parent_frame, text=f"{field_name}:", font=("Arial", 10))
            label.grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=8)
            
            # 创建输入组件
            if field_type == "dropdown" or field_type == "date":
                var = tk.StringVar()
                self.form_variables[field_name] = var
                
                # 获取选项
                options = self.event_manager.get_data_source_options(
                    level_config["source"], 
                    {}  # 初始为空，后续根据其他字段更新
                )
                
                combo = ttk.Combobox(
                    parent_frame,
                    textvariable=var,
                    values=options,
                    state="readonly",
                    width=30,
                    font=("Arial", 10)
                )
                combo.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 15), pady=8)
                self.form_widgets[field_name] = combo
                
                # 绑定变更事件，用于更新关联字段
                combo.bind("<<ComboboxSelected>>", self.on_field_changed)
                
                # 空的提示列
                ttk.Label(parent_frame, text="").grid(row=row, column=2, sticky=tk.W)
                
            elif field_type == "number":
                var = tk.StringVar()
                self.form_variables[field_name] = var
                
                entry = ttk.Entry(parent_frame, textvariable=var, width=30, font=("Arial", 10))
                entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=(0, 15), pady=8)
                self.form_widgets[field_name] = entry
                
                # 添加验证提示
                if "validation" in level_config:
                    hint_label = ttk.Label(parent_frame, text="请输入正数", 
                                         font=("Arial", 9), foreground="gray")
                    hint_label.grid(row=row, column=2, sticky=tk.W)
                else:
                    ttk.Label(parent_frame, text="").grid(row=row, column=2, sticky=tk.W)
            
            row += 1
        
        # 配置列权重，让输入框可以拉伸
        parent_frame.columnconfigure(1, weight=1)
    
    def build_branch_section(self, parent_frame: ttk.Frame, event_config: Dict):
        """构建分支选择区域"""
        # 找到有分支的字段
        branch_field = None
        for level_config in event_config["levels"]:
            if level_config.get("branches"):
                branch_field = level_config
                break
        
        if not branch_field:
            return
        
        # 分支选择区域
        branch_frame = ttk.Frame(parent_frame)
        branch_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # 分支标题
        title_label = ttk.Label(branch_frame, text="▶ 操作类型选择", 
                               font=("Arial", 11, "bold"), foreground="green")
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 分支选择框架
        branch_input_frame = ttk.Frame(branch_frame)
        branch_input_frame.pack(fill=tk.X)
        
        # 分支选择标签和下拉框
        branch_label = ttk.Label(branch_input_frame, text=f"{branch_field['name']}:", 
                                font=("Arial", 10))
        branch_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 15), pady=8)
        
        branch_var = tk.StringVar()
        self.form_variables[branch_field["name"]] = branch_var
        
        branch_options = self.event_manager.get_data_source_options(branch_field["source"], {})
        branch_combo = ttk.Combobox(
            branch_input_frame,
            textvariable=branch_var,
            values=branch_options,
            state="readonly",
            width=30,
            font=("Arial", 10)
        )
        branch_combo.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, 15), pady=8)
        self.form_widgets[branch_field["name"]] = branch_combo
        
        # 配置列权重
        branch_input_frame.columnconfigure(1, weight=1)
        
        # 分支字段容器
        self.branch_fields_frame = ttk.Frame(branch_frame)
        self.branch_fields_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 绑定分支选择事件
        branch_combo.bind("<<ComboboxSelected>>", self.on_branch_selected)
    
    def on_branch_selected(self, event=None):
        """处理分支选择"""
        # 清除现有分支字段
        for widget in self.branch_fields_frame.winfo_children():
            widget.destroy()
        
        # 获取选择的分支
        branch_field = None
        for level_config in self.event_manager.event_types[self.current_event_type]["levels"]:
            if level_config.get("branches"):
                branch_field = level_config
                break
        
        if not branch_field:
            return
        
        selected_branch = self.form_variables[branch_field["name"]].get()
        if not selected_branch:
            return
        
        # 获取分支配置
        event_config = self.event_manager.event_types[self.current_event_type]
        branch_configs = event_config["branches"].get(selected_branch, [])
        
        self.log_message("INFO", f"选择分支操作: {selected_branch}")
        
        # 构建分支字段
        if branch_configs:
            title_label = ttk.Label(self.branch_fields_frame, text=f"📋 {selected_branch} - 详细设置", 
                                  font=("Arial", 10, "bold"), foreground="purple")
            title_label.pack(anchor=tk.W, pady=(0, 10))
            
            # 分支字段使用pack布局（避免与之前的pack冲突）
            for i, branch_config in enumerate(branch_configs):
                field_name = branch_config["name"]
                field_type = branch_config["type"]
                
                # 创建字段框架
                field_frame = ttk.Frame(self.branch_fields_frame)
                field_frame.pack(fill=tk.X, pady=5)
                
                # 标签
                label = ttk.Label(field_frame, text=f"{field_name}:", font=("Arial", 10))
                label.pack(side=tk.LEFT, padx=(0, 15))
                
                # 输入组件
                if field_type == "dropdown":
                    var = tk.StringVar()
                    self.form_variables[field_name] = var
                    
                    options = self.event_manager.get_data_source_options(branch_config["source"], {})
                    combo = ttk.Combobox(
                        field_frame,
                        textvariable=var,
                        values=options,
                        state="readonly",
                        width=30,
                        font=("Arial", 10)
                    )
                    combo.pack(side=tk.LEFT, padx=(0, 15))
                    self.form_widgets[field_name] = combo
                    
                elif field_type == "number":
                    var = tk.StringVar()
                    self.form_variables[field_name] = var
                    
                    entry = ttk.Entry(field_frame, textvariable=var, width=30, font=("Arial", 10))
                    entry.pack(side=tk.LEFT, padx=(0, 15))
                    self.form_widgets[field_name] = entry
                    
                    # 验证提示
                    if "validation" in branch_config:
                        hint_label = ttk.Label(field_frame, text="请输入正数", 
                                             font=("Arial", 9), foreground="gray")
                        hint_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def on_field_changed(self, event=None):
        """当字段值改变时，更新相关联的字段选项"""
        # 获取触发事件的组件
        triggered_widget = event.widget if event else None
        triggered_field = None
        
        # 找到触发字段的名称
        for field_name, widget in self.form_widgets.items():
            if widget == triggered_widget:
                triggered_field = field_name
                break
        
        # 构建当前表单上下文
        context = {}
        for field_name, var in self.form_variables.items():
            if var.get():
                context[field_name] = var.get()
        
        self.log_message("INFO", f"字段变更: {triggered_field} = {context.get(triggered_field, '')}")
        
        # 1. 当日期改变时，更新班次选项
        if triggered_field == "选择影响日期" and "选择影响班次" in self.form_widgets:
            date_value = context.get("选择影响日期")
            if date_value:
                shifts = self.event_manager.get_data_source_options("shifts", context)
                self.form_widgets["选择影响班次"]["values"] = shifts
                
                # 检查当前班次是否还有效，如果无效则清空
                current_shift = self.form_variables["选择影响班次"].get()
                if current_shift and current_shift not in shifts:
                    self.form_variables["选择影响班次"].set("")
                    # 清空依赖班次的字段
                    if "选择产线" in self.form_variables:
                        self.form_variables["选择产线"].set("")
                        self.form_widgets["选择产线"]["values"] = []
                    if "确认产品PN" in self.form_variables:
                        self.form_variables["确认产品PN"].set("")
                        self.form_widgets["确认产品PN"]["values"] = []
                
                self.log_message("INFO", f"日期 {date_value} 的班次选项已更新: {shifts}")
        
        # 2. 当日期或班次改变时，更新产线选项
        if (triggered_field in ["选择影响日期", "选择影响班次"] and 
            "选择影响日期" in context and "选择影响班次" in context and 
            "选择产线" in self.form_widgets):
            
            lines = self.event_manager.get_data_source_options("production_lines", context)
            self.form_widgets["选择产线"]["values"] = lines
            
            # 检查当前产线是否还有效，如果无效则清空
            current_line = self.form_variables["选择产线"].get()
            if current_line and current_line not in lines:
                self.form_variables["选择产线"].set("")
                # 清空依赖产线的字段
                if "确认产品PN" in self.form_variables:
                    self.form_variables["确认产品PN"].set("")
                    self.form_widgets["确认产品PN"]["values"] = []
            
            self.log_message("INFO", f"产线选项已更新，共 {len(lines)} 个")
        
        # 3. 当产线改变时，更新产品PN选项
        if (triggered_field in ["选择影响日期", "选择影响班次", "选择产线"] and 
            "选择影响日期" in context and "选择产线" in context and 
            "确认产品PN" in self.form_widgets):
            
            pns = self.event_manager.get_data_source_options("product_pn", context)
            self.form_widgets["确认产品PN"]["values"] = pns
            
            # 检查当前PN是否还有效，如果无效则清空
            current_pn = self.form_variables["确认产品PN"].get()
            if current_pn and current_pn not in pns:
                self.form_variables["确认产品PN"].set("")
            
            self.log_message("INFO", f"产品PN选项已更新，共 {len(pns)} 个")
    
    def build_level(self, level: int, level_configs: List[Dict], branch_name: str = None):
        """
        构建指定级别的表单组件
        
        Args:
            level: 当前级别
            level_configs: 级别配置列表
            branch_name: 分支名称（用于分支逻辑）
        """
        if level >= len(level_configs):
            # 所有级别完成，启用保存按钮
            self.save_btn.config(state=tk.NORMAL)
            self.preview_btn.config(state=tk.NORMAL)
            return
        
        level_config = level_configs[level]
        
        # 创建级别框架
        level_frame = ttk.LabelFrame(
            self.scrollable_frame, 
            text=f"第{level + 1}级: {level_config['name']}"
        )
        level_frame.pack(fill=tk.X, pady=5)
        self.level_frames.append(level_frame)
        
        # 创建输入组件
        if level_config["type"] == "dropdown":
            var = tk.StringVar()
            self.level_variables.append(var)
            
            # 获取选项
            options = self.event_manager.get_data_source_options(
                level_config["source"], 
                self.current_event_data
            )
            
            combo = ttk.Combobox(
                level_frame,
                textvariable=var,
                values=options,
                state="readonly",
                width=40
            )
            combo.pack(padx=10, pady=10)
            self.level_widgets.append(combo)
            
            # 绑定选择事件
            combo.bind("<<ComboboxSelected>>", 
                      lambda e, l=level, lc=level_configs, bn=branch_name: self.on_level_selected(e, l, lc, bn))
        
        elif level_config["type"] == "number":
            var = tk.StringVar()
            self.level_variables.append(var)
            
            entry = ttk.Entry(level_frame, textvariable=var, width=40)
            entry.pack(padx=10, pady=10)
            self.level_widgets.append(entry)
            
            # 添加验证提示
            if "validation" in level_config:
                hint_label = ttk.Label(level_frame, text="请输入正数", font=("Arial", 9))
                hint_label.pack(pady=(0, 5))
            
            # 绑定输入完成事件
            entry.bind("<KeyRelease>", 
                      lambda e, l=level, lc=level_configs, bn=branch_name: self.on_number_input(e, l, lc, bn))
        
        elif level_config["type"] == "date":
            var = tk.StringVar()
            self.level_variables.append(var)
            
            # 获取日期选项
            date_options = self.event_manager.get_data_source_options(
                level_config["source"], 
                self.current_event_data
            )
            
            combo = ttk.Combobox(
                level_frame,
                textvariable=var,
                values=date_options,
                state="readonly",
                width=40
            )
            combo.pack(padx=10, pady=10)
            self.level_widgets.append(combo)
            
            # 绑定选择事件
            combo.bind("<<ComboboxSelected>>", 
                      lambda e, l=level, lc=level_configs, bn=branch_name: self.on_level_selected(e, l, lc, bn))
    
    def on_level_selected(self, event, level: int, level_configs: List[Dict], branch_name: str = None):
        """当某级别被选择时的回调"""
        if level < len(self.level_variables):
            selected_value = self.level_variables[level].get()
            level_config = level_configs[level]
            field_name = level_config["name"]
            
            # 更新事件数据
            self.current_event_data[field_name] = selected_value
            
            self.log_message("INFO", f"第{level + 1}级选择: {field_name} = {selected_value}")
            
            # 清除后续级别
            self.clear_levels_after(level)
            
            # 检查是否有分支逻辑
            if level_config.get("branches") and selected_value:
                self.handle_branch_logic(level, level_configs, selected_value)
            else:
                # 构建下一级
                self.build_level(level + 1, level_configs, branch_name)
    
    def on_number_input(self, event, level: int, level_configs: List[Dict], branch_name: str = None):
        """当数字输入框内容改变时的回调"""
        if level < len(self.level_variables):
            input_value = self.level_variables[level].get()
            level_config = level_configs[level]
            field_name = level_config["name"]
            
            # 验证输入
            if input_value:
                if "validation" in level_config:
                    is_valid, error_msg = self.event_manager.validate_input(
                        level_config["validation"], 
                        input_value
                    )
                    if not is_valid:
                        # 显示错误提示
                        messagebox.showwarning("输入错误", error_msg)
                        return
                
                # 更新事件数据
                self.current_event_data[field_name] = input_value
                
                # 清除后续级别
                self.clear_levels_after(level)
                
                # 构建下一级
                self.build_level(level + 1, level_configs, branch_name)
    
    def handle_branch_logic(self, level: int, level_configs: List[Dict], selected_value: str):
        """处理分支逻辑"""
        event_config = self.event_manager.event_types[self.current_event_type]
        
        if "branches" in event_config and selected_value in event_config["branches"]:
            branch_configs = event_config["branches"][selected_value]
            self.current_branch = selected_value
            
            self.log_message("INFO", f"进入分支: {selected_value}")
            
            # 构建分支的第一级
            if branch_configs:
                self.build_level(0, branch_configs, selected_value)
            else:
                # 分支无后续级别，启用保存按钮
                self.save_btn.config(state=tk.NORMAL)
                self.preview_btn.config(state=tk.NORMAL)
    
    def clear_levels_after(self, level: int):
        """清除指定级别之后的所有级别"""
        # 清除级别框架
        for i in range(level + 1, len(self.level_frames)):
            self.level_frames[i].destroy()
        
        # 清除变量和组件
        self.level_frames = self.level_frames[:level + 1]
        self.level_variables = self.level_variables[:level + 1]
        self.level_widgets = self.level_widgets[:level + 1]
        
        # 禁用保存按钮
        self.save_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.DISABLED)
    
    def clear_form(self):
        """清除整个表单"""
        # 清除旧的动态表单组件
        if hasattr(self, 'level_frames'):
            for frame in self.level_frames:
                frame.destroy()
            self.level_frames = []
            self.level_variables = []
            self.level_widgets = []
        
        # 清除新的静态表单组件
        if hasattr(self, 'form_widgets'):
            self.form_widgets = {}
        if hasattr(self, 'form_variables'):
            self.form_variables = {}
        
        # 清除表单区域的所有子组件
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        
        self.save_btn.config(state=tk.DISABLED)
        self.preview_btn.config(state=tk.DISABLED)
    
    def reset_form(self):
        """重置表单"""
        self.event_type_var.set("")
        self.current_event_type = None
        self.current_event_data = {}
        self.current_branch = None
        self.clear_form()
        self.log_message("INFO", "表单已重置")
    
    def preview_event(self):
        """预览事件数据"""
        # 收集当前表单数据
        event_data = self.collect_form_data()
        
        if not event_data or len(event_data) <= 1:  # 只有事件类型
            messagebox.showwarning("预览失败", "请先填写事件信息")
            return
        
        # 创建预览窗口
        preview_window = tk.Toplevel(self.parent_frame)
        preview_window.title("事件预览")
        preview_window.geometry("600x500")
        preview_window.resizable(True, True)
        
        # 预览内容框架
        main_frame = ttk.Frame(preview_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 标题
        title_label = ttk.Label(main_frame, text="📋 事件信息预览", 
                               font=("Arial", 14, "bold"), foreground="blue")
        title_label.pack(pady=(0, 15))
        
        # 使用Treeview显示数据
        columns = ("字段", "值")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        
        # 设置列
        tree.heading("字段", text="字段名称")
        tree.heading("值", text="填写内容")
        tree.column("字段", width=200, anchor=tk.W)
        tree.column("值", width=300, anchor=tk.W)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 填充数据
        for key, value in event_data.items():
            if value:  # 只显示有值的字段
                tree.insert("", "end", values=(key, value))
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(preview_window)
        button_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 关闭和保存按钮
        close_btn = ttk.Button(button_frame, text="关闭", command=preview_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        save_btn = ttk.Button(button_frame, text="确认保存", 
                             command=lambda: [preview_window.destroy(), self.save_event()])
        save_btn.pack(side=tk.RIGHT)
    
    def collect_form_data(self) -> Dict[str, Any]:
        """收集当前表单的所有数据"""
        if not self.current_event_type:
            return {}
        
        event_data = {"事件类型": self.current_event_type}
        
        # 收集所有表单变量的值
        if hasattr(self, 'form_variables'):
            for field_name, var in self.form_variables.items():
                value = var.get().strip()
                if value:
                    event_data[field_name] = value
        
        return event_data
    
    def save_event(self):
        """提交并处理事件"""
        # 收集表单数据
        event_data = self.collect_form_data()
        
        if not event_data or len(event_data) <= 1:  # 只有事件类型
            messagebox.showwarning("提交失败", "请先填写事件信息")
            return
        
        # 验证必填字段
        validation_result = self.validate_required_fields(event_data)
        if not validation_result[0]:
            messagebox.showwarning("验证失败", validation_result[1])
            return
        
        # 创建事件
        success, message = self.event_manager.create_event(event_data)
        
        if success:
            messagebox.showinfo("提交成功", message)
            self.log_message("SUCCESS", f"事件提交成功: {message}")
            
            # 刷新事件列表
            self.refresh_event_list()
            
            # 重置表单
            self.reset_form()
        else:
            messagebox.showerror("提交失败", message)
            self.log_message("ERROR", f"事件提交失败: {message}")
    
    def validate_required_fields(self, event_data: Dict[str, Any]) -> tuple:
        """验证必填字段"""
        event_type = event_data.get("事件类型")
        if not event_type:
            return False, "事件类型不能为空"
        
        # 基础必填字段
        required_fields = ["选择影响日期"]
        
        # 根据事件类型添加特定必填字段
        if event_type in ["LCA产量损失", "物料情况"]:
            required_fields.extend(["选择影响班次", "选择产线", "确认产品PN"])
        elif event_type in ["SBR信息", "PM状态", "Drive loading计划"]:
            required_fields.extend(["选择影响班次", "选择产线"])
        
        # 检查必填字段
        for field in required_fields:
            if field not in event_data or not event_data[field]:
                return False, f"必填字段 '{field}' 不能为空"
        
        return True, ""
    
    def refresh_event_list(self):
        """刷新事件列表"""
        # 清除现有项目
        for item in self.event_tree.get_children():
            self.event_tree.delete(item)
        
        # 添加事件
        events = self.event_manager.get_events()
        for event in events:
            self.event_tree.insert("", "end", values=(
                event.get("事件ID", ""),
                event.get("事件类型", ""),
                event.get("创建时间", ""),
                "已创建"
            ))
    
    def execute_selected_event(self):
        """执行选中的事件"""
        selected_items = self.event_tree.selection()
        if not selected_items:
            messagebox.showwarning("执行失败", "请先选择要执行的事件")
            return
        
        if len(selected_items) > 1:
            messagebox.showwarning("执行失败", "请只选择一个事件进行执行")
            return
        
        # 获取选中的事件ID
        item = selected_items[0]
        event_id = self.event_tree.item(item)["values"][0]
        event_type = self.event_tree.item(item)["values"][1]
        
        # 确认执行
        if messagebox.askyesno("确认执行", f"确定要执行事件 {event_id} ({event_type}) 吗？\n\n这将重新运行事件的处理逻辑并显示详细流程。"):
            self.log_message("INFO", f"开始执行事件: {event_id}")
            
            # 从数据库获取事件数据
            event_data = self.get_event_data_by_id(event_id)
            if event_data:
                self.log_message("INFO", f"📋 事件详情: {event_type}")
                for key, value in event_data.items():
                    if key not in ["事件ID", "创建时间"] and value:  # 跳过ID和时间戳
                        self.log_message("INFO", f"   {key}: {value}")
                
                # 根据事件类型执行相应的处理逻辑
                self.execute_event_logic(event_data)
            else:
                messagebox.showerror("执行失败", f"无法获取事件 {event_id} 的数据")
                self.log_message("ERROR", f"无法获取事件数据: {event_id}")
    
    def get_event_data_by_id(self, event_id):
        """根据事件ID获取事件数据"""
        try:
            events = self.event_manager.get_events()
            for event in events:
                if event.get("事件ID") == event_id:
                    return event
            return None
        except Exception as e:
            self.log_message("ERROR", f"获取事件数据失败: {str(e)}")
            return None
    
    def execute_event_logic(self, event_data):
        """执行事件的业务逻辑"""
        event_type = event_data.get("事件类型")
        
        try:
            if event_type == "LCA产量损失":
                self.log_message("INFO", "🚀 开始执行LCA产量损失处理逻辑...")
                self.execute_lca_logic(event_data)
            elif event_type == "物料情况":
                self.log_message("INFO", "🚀 开始执行物料情况处理逻辑...")
                self.log_message("INFO", "物料情况事件处理逻辑暂未实现")
            elif event_type == "SBR信息":
                self.log_message("INFO", "🚀 开始执行SBR信息处理逻辑...")
                self.log_message("INFO", "SBR信息事件处理逻辑暂未实现")
            elif event_type == "PM状态":
                self.log_message("INFO", "🚀 开始执行PM状态处理逻辑...")
                self.log_message("INFO", "PM状态事件处理逻辑暂未实现")
            elif event_type == "Drive loading计划":
                self.log_message("INFO", "🚀 开始执行Drive loading计划处理逻辑...")
                self.log_message("INFO", "Drive loading计划事件处理逻辑暂未实现")
            else:
                self.log_message("WARNING", f"未知的事件类型: {event_type}")
                
        except Exception as e:
            self.log_message("ERROR", f"执行事件逻辑时发生错误: {str(e)}")
    
    def execute_lca_logic(self, event_data):
        """执行LCA产量损失处理逻辑"""
        try:
            # 创建LCA处理器并执行处理
            from src.core.lca_capacity_loss import LCACapacityLossProcessor
            
            # 创建LCA处理器，使用GUI的日志回调
            class GUILoggerAdapter:
                def __init__(self, log_callback):
                    self.log_callback = log_callback
                
                def info(self, message):
                    self.log_callback("INFO", message)
                
                def error(self, message):
                    self.log_callback("ERROR", message)
                
                def warning(self, message):
                    self.log_callback("WARNING", message)
                
                def debug(self, message):
                    self.log_callback("DEBUG", message)
            
            # 获取data_loader实例
            data_loader = self.event_manager.data_loader
            logger = GUILoggerAdapter(self.log_message)
            
            lca_processor = LCACapacityLossProcessor(data_loader, logger)
            
            # 执行LCA处理逻辑
            result = lca_processor.process_lca_capacity_loss(event_data)
            
            # 显示处理结果
            self.display_lca_result(result)
            
        except Exception as e:
            self.log_message("ERROR", f"执行LCA处理逻辑时发生错误: {str(e)}")
    
    def display_lca_result(self, result):
        """显示LCA处理结果"""
        self.log_message("INFO", "=" * 50)
        self.log_message("INFO", "📊 LCA处理结果总结:")
        
        status = result.get("status", "unknown")
        message = result.get("message", "无消息")
        
        if status == "add_line_required":
            self.log_message("WARNING", f"🏭 {message}")
            check_result = result.get("check_result", {})
            total_loss = check_result.get("total_loss", 0)
            self.log_message("INFO", f"📈 累计损失: {total_loss:.0f}")
            self.log_message("INFO", "🔧 建议操作: 考虑增加生产线")
        elif status == "normal_process":
            self.log_message("INFO", f"ℹ️  {message}")
            
            # 显示DOS计算结果
            dos_result = result.get("dos_result", {})
            if dos_result.get("success"):
                self.display_dos_result(dos_result)
            else:
                self.log_message("WARNING", f"DOS计算失败: {dos_result.get('error', '未知错误')}")
            
            recommendation = result.get("recommendation", "按标准流程处理")
            self.log_message("INFO", f"✅ 最终建议: {recommendation}")
        elif status == "error":
            self.log_message("ERROR", f"❌ {message}")
        
        self.log_message("INFO", "=" * 50)
    
    def display_dos_result(self, dos_result):
        """显示DOS计算结果详情"""
        self.log_message("INFO", "")
        self.log_message("INFO", "🔮 DOS计算结果详情:")
        
        # 显示计算过程
        previous_eoh = dos_result.get("previous_eoh", 0)
        planned_production = dos_result.get("planned_production", 0)
        actual_production = dos_result.get("actual_production", 0)
        current_shipment = dos_result.get("current_shipment", 0)
        predicted_eoh = dos_result.get("predicted_eoh", 0)
        new_dos = dos_result.get("new_dos", 0)
        
        self.log_message("INFO", f"📦 上一班次EOH: {previous_eoh}")
        self.log_message("INFO", f"🏭 损失后实际产量: {actual_production} (计划: {planned_production})")
        self.log_message("INFO", f"🚛 本班出货计划: {current_shipment}")
        self.log_message("INFO", f"📈 预计EOH: {predicted_eoh}")
        
        # 显示DOS分析
        analysis = dos_result.get("analysis", {})
        dos_level = analysis.get("level", "未知")
        dos_status = analysis.get("status", "unknown")
        dos_message = analysis.get("message", "")
        
        if dos_status == "critical":
            self.log_message("ERROR", f"🚨 {dos_message}")
        elif dos_status == "warning":
            self.log_message("WARNING", f"⚠️  {dos_message}")
        elif dos_status == "caution":
            self.log_message("INFO", f"⚠️  {dos_message}")
        else:
            self.log_message("INFO", f"✅ {dos_message}")
        
        if new_dos != float('inf'):
            self.log_message("INFO", f"📊 新DOS值: {new_dos:.2f} 天 (状态: {dos_level})")
    
    def delete_selected_event(self):
        """删除选中的事件"""
        selected_items = self.event_tree.selection()
        if not selected_items:
            messagebox.showwarning("删除失败", "请先选择要删除的事件")
            return
        
        # 确认删除
        if messagebox.askyesno("确认删除", "确定要删除选中的事件吗？"):
            for item in selected_items:
                event_id = self.event_tree.item(item)["values"][0]
                if self.event_manager.delete_event(event_id):
                    self.event_tree.delete(item)
                    self.log_message("INFO", f"事件已删除: {event_id}")
    
    def export_events(self):
        """导出事件列表"""
        from tkinter import filedialog
        
        events = self.event_manager.get_events()
        if not events:
            messagebox.showwarning("导出失败", "没有可导出的事件")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            success = self.event_manager.export_events_to_excel(file_path)
            if success:
                messagebox.showinfo("导出成功", f"事件列表已导出到: {file_path}")
            else:
                messagebox.showerror("导出失败", "导出过程中发生错误")