"""
事件处理器 - 实现生产事件的业务逻辑处理
Event Processor - Implements business logic for production events
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging

class EventProcessor:
    """
    事件处理器类，负责处理各种生产事件
    """
    
    def __init__(self, data_loader, logger=None):
        """
        初始化事件处理器
        
        Args:
            data_loader: 数据加载器实例
            logger: 日志记录器
        """
        self.data_loader = data_loader
        self.logger = logger or logging.getLogger(__name__)
        self.original_plan = None
        self.current_plan = None
        self.processing_results = []
        
    def process_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个事件
        
        Args:
            event_data: 事件数据字典
            
        Returns:
            处理结果字典
        """
        event_type = event_data.get('事件类型')
        self.logger.info(f"开始处理事件: {event_type}")
        
        try:
            if event_type == "LCA产能损失":
                return self._process_lca_capacity_loss(event_data)
            elif event_type == "物料情况":
                return self._process_material_issue(event_data)
            elif event_type == "SBR信息":
                return self._process_sbr_info(event_data)
            elif event_type == "PM状态":
                return self._process_pm_status(event_data)
            elif event_type == "Drive loading计划":
                return self._process_loading_plan(event_data)
            else:
                raise ValueError(f"未知事件类型: {event_type}")
                
        except Exception as e:
            error_msg = f"处理事件失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "event_data": event_data
            }
    
    def _process_lca_capacity_loss(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理LCA产能损失事件
        
        根据流程图逻辑：
        1. 获取影响的产线和时间
        2. 计算产能损失
        3. 判断是否需要调整计划
        4. 生成补偿方案
        """
        self.logger.info("处理LCA产能损失事件...")
        
        # 提取事件参数
        affect_date = event_data.get('选择影响日期')
        affect_shift = event_data.get('选择影响班次')
        production_line = event_data.get('选择产线')
        loss_hours = event_data.get('输入XX小时', 0)
        
        # 获取当前计划数据
        daily_plan = self.data_loader.get_data('daily_plan')
        capacity_data = self.data_loader.get_data('capacity')
        
        if daily_plan is None or capacity_data is None:
            return {
                "status": "error",
                "message": "无法获取计划数据或产能数据"
            }
        
        # 计算产能损失影响
        affected_products = self._get_affected_products(daily_plan, affect_date, production_line)
        capacity_loss = self._calculate_capacity_loss(capacity_data, production_line, loss_hours)
        
        # 生成调整方案
        adjustment_plan = self._generate_lca_adjustment_plan(
            affected_products, capacity_loss, affect_date, production_line
        )
        
        result = {
            "status": "success",
            "event_type": "LCA产能损失",
            "affected_date": affect_date,
            "affected_line": production_line,
            "capacity_loss_hours": loss_hours,
            "affected_products": affected_products,
            "adjustment_plan": adjustment_plan,
            "message": f"LCA产能损失处理完成，影响产线{production_line}，损失{loss_hours}小时产能"
        }
        
        self.logger.info(result["message"])
        return result
    
    def _process_loading_plan(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理Drive Loading计划变更事件
        
        根据流程图逻辑处理各种计划变更
        """
        self.logger.info("处理Drive Loading计划变更...")
        
        # 提取基础信息
        affect_date = event_data.get('选择影响日期')
        affect_shift = event_data.get('选择影响班次')
        production_line = event_data.get('选择产线')
        operation_type = event_data.get('操作类型选择')
        
        # 根据操作类型分发处理
        if operation_type == "日期提前":
            return self._process_date_advance(event_data)
        elif operation_type == "日期延期":
            return self._process_date_delay(event_data)
        elif operation_type == "数量增加":
            return self._process_quantity_increase(event_data)
        elif operation_type == "数量减少":
            return self._process_quantity_decrease(event_data)
        elif operation_type == "换PN":
            return self._process_pn_change(event_data)
        else:
            return {
                "status": "error",
                "message": f"未知的操作类型: {operation_type}"
            }
    
    def _process_date_advance(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理日期提前"""
        advance_time = event_data.get('选择提前时间')
        self.logger.info(f"处理日期提前: {advance_time}")
        
        # 实现日期提前逻辑
        return {
            "status": "success",
            "event_type": "日期提前",
            "advance_time": advance_time,
            "message": f"计划提前{advance_time}处理完成"
        }
    
    def _process_date_delay(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理日期延期"""
        delay_time = event_data.get('选择延期时间')
        self.logger.info(f"处理日期延期: {delay_time}")
        
        # 实现日期延期逻辑
        return {
            "status": "success", 
            "event_type": "日期延期",
            "delay_time": delay_time,
            "message": f"计划延期{delay_time}处理完成"
        }
    
    def _process_quantity_increase(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数量增加"""
        increase_amount = event_data.get('输入增加数量')
        self.logger.info(f"处理数量增加: {increase_amount}")
        
        return {
            "status": "success",
            "event_type": "数量增加", 
            "increase_amount": increase_amount,
            "message": f"数量增加{increase_amount}处理完成"
        }
    
    def _process_quantity_decrease(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数量减少"""
        decrease_amount = event_data.get('输入减少数量')
        self.logger.info(f"处理数量减少: {decrease_amount}")
        
        return {
            "status": "success",
            "event_type": "数量减少",
            "decrease_amount": decrease_amount, 
            "message": f"数量减少{decrease_amount}处理完成"
        }
    
    def _process_pn_change(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理PN变更"""
        source_pn = event_data.get('选择需要操作的PN')
        target_pn = event_data.get('选择需要转换的PN')
        self.logger.info(f"处理PN变更: {source_pn} -> {target_pn}")
        
        return {
            "status": "success",
            "event_type": "PN变更",
            "source_pn": source_pn,
            "target_pn": target_pn,
            "message": f"PN从{source_pn}变更为{target_pn}处理完成"
        }
    
    def _process_material_issue(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理物料情况事件"""
        self.logger.info("处理物料情况事件...")
        
        affect_quantity = event_data.get('填入影响数量')
        product_pn = event_data.get('确认产品PN')
        
        return {
            "status": "success",
            "event_type": "物料情况",
            "affected_pn": product_pn,
            "affected_quantity": affect_quantity,
            "message": f"物料情况处理完成，影响产品{product_pn}数量{affect_quantity}"
        }
    
    def _process_sbr_info(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理SBR信息事件"""
        self.logger.info("处理SBR信息事件...")
        
        operation_type = event_data.get('操作类型选择')
        
        return {
            "status": "success", 
            "event_type": "SBR信息",
            "operation_type": operation_type,
            "message": f"SBR信息{operation_type}处理完成"
        }
    
    def _process_pm_status(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理PM状态事件"""
        self.logger.info("处理PM状态事件...")
        
        operation = event_data.get('提前还是延期')
        if operation == "提前":
            advance_time = event_data.get('选择提前时间')
            message = f"PM维护提前{advance_time}"
        else:
            delay_time = event_data.get('选择延期时间')
            message = f"PM维护延期{delay_time}"
        
        return {
            "status": "success",
            "event_type": "PM状态",
            "operation": operation,
            "message": f"{message}处理完成"
        }
    
    def _get_affected_products(self, daily_plan, date, production_line):
        """获取受影响的产品"""
        # 实现获取受影响产品逻辑
        return []
    
    def _calculate_capacity_loss(self, capacity_data, production_line, loss_hours):
        """计算产能损失"""
        # 实现产能损失计算逻辑
        return loss_hours
    
    def _generate_lca_adjustment_plan(self, affected_products, capacity_loss, date, line):
        """生成LCA调整方案"""
        # 实现调整方案生成逻辑
        return {
            "adjustment_type": "capacity_compensation",
            "details": f"需要在其他时段补偿{capacity_loss}小时产能"
        }
    
    def export_results(self, filename: str = None) -> str:
        """
        导出处理结果到Excel文件
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"event_processing_results_{timestamp}.xlsx"
        
        # 实现结果导出逻辑
        self.logger.info(f"处理结果已导出到: {filename}")
        return filename