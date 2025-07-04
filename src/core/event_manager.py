import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import re
from .database_manager import DatabaseManager

class EventManager:
    """
    事件管理类，负责处理生产事件的录入、验证和管理
    实现多级级联表单功能，支持五大事件类型的完整录入流程
    """
    
    def __init__(self, data_loader, log_callback=None):
        """
        初始化事件管理器
        
        Args:
            data_loader: 数据加载器实例，用于获取相关生产数据
            log_callback: 日志回调函数
        """
        self.data_loader = data_loader
        self.log_callback = log_callback
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager("data/events.db", self._create_logger())
        
        # 当前事件录入状态
        self.current_event = {}
        self.current_level = 0
        self.current_event_type = None
        
        # 事件类型定义
        self.event_types = {
            "LCA产量损失": {
                "levels": [
                    {"name": "选择影响日期", "type": "date", "source": "daily_plan_dates"},
                    {"name": "选择产线", "type": "dropdown", "source": "production_lines"},
                    {"name": "确认产品PN", "type": "dropdown", "source": "product_pn"},
                    {"name": "已经损失的产量", "type": "number", "validation": "positive_number"},
                    {"name": "剩余修理时间", "type": "number", "validation": "positive_number"},
                ],
                "description": "LCA产线产量损失事件登记"
            },
            "物料情况": {
                "levels": [
                    {"name": "选择影响日期", "type": "date", "source": "daily_plan_dates"},
                    {"name": "选择影响班次", "type": "dropdown", "source": "shifts"},
                    {"name": "选择产线", "type": "dropdown", "source": "production_lines"},
                    {"name": "确认产品PN", "type": "dropdown", "source": "product_pn"},
                    {"name": "填入影响数量", "type": "number", "validation": "positive_number"}
                ],
                "description": "物料供应问题事件登记"
            },
            "SBR信息": {
                "levels": [
                    {"name": "选择影响日期", "type": "date", "source": "daily_plan_dates"},
                    {"name": "选择影响班次", "type": "dropdown", "source": "shifts"},
                    {"name": "选择产线", "type": "dropdown", "source": "production_lines"},
                    {"name": "操作类型", "type": "dropdown", "source": "sbr_operations", "branches": True}
                ],
                "branches": {
                    "全部取消": [],
                    "延期": [
                        {"name": "选择延期时间", "type": "dropdown", "source": "delay_options"},
                    ],
                    "部分取消": [
                        {"name": "输入取消数量", "type": "number", "validation": "positive_number"},
                    ],
                    "提前": [
                        {"name": "选择提前时间", "type": "dropdown", "source": "advance_options"},
                    ]
                },
                "description": "SBR生产信息变更事件登记"
            },
            "PM状态": {
                "levels": [
                    {"name": "选择影响日期", "type": "date", "source": "daily_plan_dates"},
                    {"name": "选择影响班次", "type": "dropdown", "source": "shifts"},
                    {"name": "选择产线", "type": "dropdown", "source": "production_lines"},
                    {"name": "提前还是延期", "type": "dropdown", "source": "pm_operations", "branches": True}
                ],
                "branches": {
                    "提前": [
                        {"name": "选择提前时间", "type": "dropdown", "source": "advance_options"}
                    ],
                    "延期": [
                        {"name": "选择延期时间", "type": "dropdown", "source": "delay_options"}
                    ]
                },
                "description": "设备维护状态变更事件登记"
            },
            "Drive loading计划": {
                "levels": [
                    {"name": "选择影响日期", "type": "date", "source": "daily_plan_dates"},
                    {"name": "选择影响班次", "type": "dropdown", "source": "shifts"},
                    {"name": "选择产线", "type": "dropdown", "source": "production_lines"},
                    {"name": "确认问题类型", "type": "dropdown", "source": "drive_operations", "branches": True}
                ],
                "branches": {
                    "日期提前": [
                        {"name": "选择提前时间", "type": "dropdown", "source": "advance_options"}
                    ],
                    "日期延期": [
                        {"name": "选择延期时间", "type": "dropdown", "source": "delay_options"}
                    ],
                    "数量减少": [
                        {"name": "输入减少数量", "type": "number", "validation": "positive_number"}
                    ],
                    "数量增加": [
                        {"name": "输入增加数量", "type": "number", "validation": "positive_number"}
                    ],
                    "换PN": [
                        {"name": "选择需要操作的PN", "type": "dropdown", "source": "product_pn"},
                        {"name": "选择需要转换的PN", "type": "dropdown", "source": "product_pn"}
                    ]
                },
                "description": "Drive loading计划调整事件登记"
            }
        }
        
        # 数据源选项定义
        self.data_sources = {
            "shifts": ["T1", "T2", "T3", "T4", "Day", "Night"],
            "shift_count": ["一个班", "两个班", "三个班", "全部班次"],
            "sbr_operations": ["全部取消", "延期", "部分取消", "提前"],
            "pm_operations": ["提前", "延期"],
            "drive_operations": ["日期提前", "日期延期", "数量减少", "数量增加", "换PN"],
            "delay_options": ["一个班", "两个班", "三个班"],
            "advance_options": ["一个班", "两个班", "三个班"],
            "schedule_change_reasons": ["客户需求变更", "供应链调整", "产能优化", "设备维护", "紧急订单", "其他"],
            "quantity_change_reasons": ["市场需求变化", "物料供应问题", "产能调整", "客户取消订单", "库存调整", "其他"],
            "pn_change_scope": ["仅当前批次", "当日全部", "本周全部", "后续全部", "需要确认范围"]
        }
        
    def log_message(self, level: str, message: str):
        """记录日志消息"""
        if self.log_callback:
            self.log_callback(level, message)
        else:
            print(f"[{level}] {message}")
    
    def _create_logger(self):
        """创建日志记录器"""
        import logging
        
        class EventManagerLoggerAdapter:
            """日志适配器，将数据库日志转发到EventManager的日志系统"""
            def __init__(self, event_manager):
                self.event_manager = event_manager
            
            def info(self, message):
                self.event_manager.log_message("INFO", message)
            
            def error(self, message):
                self.event_manager.log_message("ERROR", message)
            
            def warning(self, message):
                self.event_manager.log_message("WARNING", message)
            
            def debug(self, message):
                self.event_manager.log_message("DEBUG", message)
        
        return EventManagerLoggerAdapter(self)
    
    def get_data_source_options(self, source: str, context: Dict = None) -> List[str]:
        """
        根据数据源类型获取选项列表
        
        Args:
            source: 数据源类型
            context: 上下文信息，包含之前选择的值
            
        Returns:
            选项列表
        """
        if context is None:
            context = self.current_event
            
        if source == "daily_plan_dates":
            return self._get_daily_plan_dates()
        elif source == "production_lines":
            return self._get_production_lines(context.get("选择影响日期"))
        elif source == "product_pn":
            return self._get_product_pn(context.get("选择影响日期"), context.get("选择产线"))
        elif source in self.data_sources:
            return self.data_sources[source]
        else:
            self.log_message("WARNING", f"未知数据源: {source}")
            return []
    
    def _get_daily_plan_dates(self) -> List[str]:
        """获取Daily Plan中的可用日期"""
        try:
            data = self.data_loader.get_data("HSA Daily Plan")
            if data is None or data.empty:
                return []
            
            # 从列名中提取日期
            date_columns = []
            for col in data.columns:
                if isinstance(col, str) and re.match(r'\d{4}-\d{2}-\d{2}', col):
                    date_columns.append(col)
            
            return sorted(date_columns)
        except Exception as e:
            self.log_message("ERROR", f"获取日期列表时出错: {str(e)}")
            return []
    
    def _get_production_lines(self, date: str = None) -> List[str]:
        """获取可用的生产线列表"""
        try:
            data = self.data_loader.get_data("HSA Daily Plan")
            if data is None or data.empty:
                return []
            
            # 从第一列（Line列）获取生产线
            lines = data.iloc[:, 0].dropna().unique().tolist()
            # 过滤掉空值和非字符串值
            lines = [str(line) for line in lines if pd.notna(line) and str(line).strip()]
            
            return sorted(lines)
        except Exception as e:
            self.log_message("ERROR", f"获取生产线列表时出错: {str(e)}")
            return []
    
    def _get_product_pn(self, date: str = None, line: str = None) -> List[str]:
        """根据日期和生产线获取产品PN列表"""
        try:
            data = self.data_loader.get_data("HSA Daily Plan")
            if data is None or data.empty:
                return []
            
            # 如果指定了生产线，过滤对应的行
            if line:
                line_data = data[data.iloc[:, 0] == line]
                if not line_data.empty:
                    # 从第三列（Part Number列）获取产品PN
                    pns = line_data.iloc[:, 2].dropna().unique().tolist()
                    pns = [str(pn) for pn in pns if pd.notna(pn) and str(pn).strip()]
                    return sorted(pns)
            
            # 如果没有指定生产线，返回所有产品PN
            pns = data.iloc[:, 2].dropna().unique().tolist()
            pns = [str(pn) for pn in pns if pd.notna(pn) and str(pn).strip()]
            
            return sorted(pns)
        except Exception as e:
            self.log_message("ERROR", f"获取产品PN列表时出错: {str(e)}")
            return []
    
    def validate_input(self, validation_type: str, value: Any) -> Tuple[bool, str]:
        """
        验证用户输入
        
        Args:
            validation_type: 验证类型
            value: 输入值
            
        Returns:
            (是否有效, 错误消息)
        """
        if validation_type == "positive_number":
            try:
                num = float(value)
                if num <= 0:
                    return False, "数值必须大于0"
                return True, ""
            except ValueError:
                return False, "请输入有效的数字"
        
        return True, ""
    
    def validate_event_logic(self, event_data: Dict) -> Tuple[bool, str]:
        """
        验证事件逻辑的合理性
        
        Args:
            event_data: 事件数据
            
        Returns:
            (是否有效, 错误消息)
        """
        event_type = event_data.get("事件类型")
        
        # 基础验证：检查必要字段
        if not event_type:
            return False, "事件类型不能为空"
        
        # 根据事件类型进行特定验证
        if event_type == "LCA产量损失":
            return self._validate_lca_loss_event(event_data)
        elif event_type == "物料情况":
            return self._validate_material_event(event_data)
        elif event_type == "SBR信息":
            return self._validate_sbr_event(event_data)
        elif event_type == "PM状态":
            return self._validate_pm_event(event_data)
        elif event_type == "Drive loading计划":
            return self._validate_drive_loading_event(event_data)
        
        return True, ""
    
    def _validate_lca_loss_event(self, event_data: Dict) -> Tuple[bool, str]:
        """验证LCA产量损失事件"""
        # 检查损失产量是否超过计划产量
        date = event_data.get("选择影响日期")
        line = event_data.get("选择产线")
        pn = event_data.get("确认产品PN")
        loss_qty = event_data.get("填入已经损失的产量")
        
        if all([date, line, pn, loss_qty]):
            planned_qty = self._get_planned_quantity(date, line, pn)
            if planned_qty and float(loss_qty) > planned_qty:
                return False, f"损失产量({loss_qty})超过计划产量({planned_qty})"
        
        return True, ""
    
    def _validate_material_event(self, event_data: Dict) -> Tuple[bool, str]:
        """验证物料情况事件"""
        # 可以添加物料相关的验证逻辑
        return True, ""
    
    def _validate_sbr_event(self, event_data: Dict) -> Tuple[bool, str]:
        """验证SBR信息事件"""
        operation = event_data.get("操作类型")
        if operation == "部分取消":
            cancel_qty = event_data.get("输入取消数量")
            if cancel_qty:
                # 检查取消数量是否合理
                date = event_data.get("选择影响日期")
                line = event_data.get("选择产线")
                if date and line:
                    planned_qty = self._get_total_planned_quantity(date, line)
                    if planned_qty and float(cancel_qty) > planned_qty:
                        return False, f"取消数量({cancel_qty})超过总计划产量({planned_qty})"
        
        return True, ""
    
    def _validate_pm_event(self, event_data: Dict) -> Tuple[bool, str]:
        """验证PM状态事件"""
        # PM相关验证逻辑
        return True, ""
    
    def _validate_drive_loading_event(self, event_data: Dict) -> Tuple[bool, str]:
        """验证Drive loading计划事件"""
        problem_type = event_data.get("确认问题类型")
        if problem_type == "换PN":
            from_pn = event_data.get("选择需要操作的PN")
            to_pn = event_data.get("选择需要转换的PN")
            if from_pn == to_pn:
                return False, "源PN和目标PN不能相同"
        
        return True, ""
    
    def _get_planned_quantity(self, date: str, line: str, pn: str) -> Optional[float]:
        """获取指定日期、生产线和产品的计划产量"""
        try:
            data = self.data_loader.get_data("HSA Daily Plan")
            if data is None or data.empty:
                return None
            
            # 过滤指定生产线和产品的数据
            filtered_data = data[(data.iloc[:, 0] == line) & (data.iloc[:, 2] == pn)]
            
            if not filtered_data.empty and date in filtered_data.columns:
                qty = filtered_data[date].iloc[0]
                if pd.notna(qty):
                    return float(qty)
            
            return None
        except Exception as e:
            self.log_message("ERROR", f"获取计划产量时出错: {str(e)}")
            return None
    
    def _get_total_planned_quantity(self, date: str, line: str) -> Optional[float]:
        """获取指定日期和生产线的总计划产量"""
        try:
            data = self.data_loader.get_data("HSA Daily Plan")
            if data is None or data.empty:
                return None
            
            # 过滤指定生产线的数据
            filtered_data = data[data.iloc[:, 0] == line]
            
            if not filtered_data.empty and date in filtered_data.columns:
                total_qty = filtered_data[date].sum()
                if pd.notna(total_qty):
                    return float(total_qty)
            
            return None
        except Exception as e:
            self.log_message("ERROR", f"获取总计划产量时出错: {str(e)}")
            return None
    
    def create_event(self, event_data: Dict) -> Tuple[bool, str]:
        """
        创建新事件
        
        Args:
            event_data: 事件数据字典
            
        Returns:
            (是否成功, 消息)
        """
        # 验证事件数据
        is_valid, error_msg = self.validate_event_logic(event_data)
        if not is_valid:
            return False, error_msg
        
        # 如果是LCA产能损失事件，从Daily Plan获取实际数据
        if event_data.get("事件类型") == "LCA产能损失":
            self._enhance_lca_event_data(event_data)
        
        # 使用数据库管理器创建事件
        success, message = self.db_manager.create_event(event_data)
        
        if success:
            self.log_message("SUCCESS", f"事件创建成功: {event_data.get('事件ID', 'Unknown')} - {event_data.get('事件类型', 'Unknown')}")
            
            # 如果是LCA产能损失事件，自动执行处理逻辑
            if event_data.get("事件类型") == "LCA产能损失":
                self._execute_lca_processing(event_data)
        
        return success, message
    
    def get_events(self) -> List[Dict]:
        """获取所有事件列表"""
        return self.db_manager.get_all_events()
    
    def delete_event(self, event_id: str) -> bool:
        """删除指定事件"""
        success = self.db_manager.delete_event(event_id)
        if success:
            self.log_message("INFO", f"事件已删除: {event_id}")
        return success
    
    def export_events_to_excel(self, file_path: str) -> bool:
        """导出事件到Excel文件"""
        success = self.db_manager.export_to_excel(file_path)
        if success:
            self.log_message("SUCCESS", f"事件已导出到: {file_path}")
        else:
            self.log_message("ERROR", "导出事件失败")
        return success
    
    def _enhance_lca_event_data(self, event_data: Dict) -> None:
        """
        增强LCA事件数据，从Daily Plan获取实际数据
        
        Args:
            event_data: 事件数据字典（会被修改）
        """
        try:
            date = event_data.get("选择影响日期")
            line = event_data.get("选择产线")
            product_pn = event_data.get("确认产品PN")
            
            if date and line and product_pn:
                # 从Daily Plan获取计划产量
                planned_qty = self._get_planned_quantity(date, line, product_pn)
                if planned_qty is not None:
                    event_data["_daily_plan_quantity"] = planned_qty
                    self.log_message("INFO", f"从Daily Plan获取计划产量: {planned_qty}")
                else:
                    self.log_message("WARNING", f"无法从Daily Plan获取产量数据: {date}, {line}, {product_pn}")
            
            # 验证损失产量是否合理
            lost_qty = event_data.get("已经损失的产量")
            if lost_qty and event_data.get("_daily_plan_quantity"):
                if float(lost_qty) > float(event_data["_daily_plan_quantity"]):
                    self.log_message("WARNING", f"损失产量({lost_qty})超过计划产量({event_data['_daily_plan_quantity']})")
            
        except Exception as e:
            self.log_message("ERROR", f"增强LCA事件数据时出错: {str(e)}")
    
    def _execute_lca_processing(self, event_data: Dict) -> None:
        """
        执行LCA产能损失处理逻辑
        
        Args:
            event_data: 事件数据字典
        """
        try:
            self.log_message("INFO", "开始执行LCA产能损失处理逻辑...")
            
            # 创建LCA处理器并执行处理
            from .lca_capacity_loss import LCACapacityLossProcessor
            
            # 创建LCA处理器，使用适配器传递日志
            lca_processor = LCACapacityLossProcessor(self.data_loader, self._create_logger())
            
            # 执行LCA处理逻辑
            result = lca_processor.process_lca_capacity_loss(event_data)
            
            # 输出处理结果
            if result["status"] == "add_line_required":
                self.log_message("WARNING", f"🏭 {result['message']}")
                self.log_message("INFO", f"📊 累计损失: {result.get('check_result', {}).get('total_loss', 0):.0f}")
            elif result["status"] == "normal_process":
                self.log_message("INFO", f"ℹ️  {result['message']}")
            elif result["status"] == "error":
                self.log_message("ERROR", f"❌ LCA处理失败: {result['message']}")
            
            # 保存处理结果到数据库（移除不可序列化的对象）
            result_copy = result.copy()
            if 'check_result' in result_copy and 'previous_shifts' in result_copy['check_result']:
                # 移除datetime对象，只保留日期字符串
                for shift in result_copy['check_result']['previous_shifts']:
                    if 'datetime' in shift:
                        del shift['datetime']
            
            self.db_manager.save_processing_result(
                event_data.get("事件ID", ""),
                "LCA产能损失检查",
                result_copy,
                result["status"]
            )
            
        except Exception as e:
            error_msg = f"执行LCA处理逻辑时发生错误: {str(e)}"
            self.log_message("ERROR", error_msg)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        return self.db_manager.get_database_stats()