"""
LCA产能损失处理模块
LCA Capacity Loss Processing Module

专门处理LCA产能损失事件的业务逻辑模块
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging


class LCACapacityLossProcessor:
    """
    LCA产能损失处理器
    
    负责处理LCA产能损失事件的具体业务逻辑
    包括产能损失计算、影响分析、补偿方案生成等
    """
    
    def __init__(self, data_loader, logger=None):
        """
        初始化LCA产能损失处理器
        
        Args:
            data_loader: 数据加载器实例
            logger: 日志记录器
        """
        self.data_loader = data_loader
        self.logger = logger or logging.getLogger(__name__)
        
    def process_lca_capacity_loss(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理LCA产能损失事件的主要入口函数
        
        Args:
            event_data: 事件数据字典
            
        Returns:
            处理结果字典
        """
        self.logger.info("开始处理LCA产能损失事件")
        
        try:
            # 第一步：检查是否有LCA产量损失报告
            has_report = self._check_lca_report_exists(event_data)
            if not has_report:
                self.logger.info("没有LCA产量损失报告，结束处理")
                return {
                    "status": "ended",
                    "message": "没有LCA产量损失报告，流程结束",
                    "step": "检查LCA报告",
                    "result": "END"
                }
            
            self.logger.info("检测到LCA产量损失报告，继续处理")
            
            # 提取事件基本信息
            event_info = self._extract_event_info(event_data)
            
            # 获取相关数据
            production_data = self._get_production_data()
            
            # 计算产能损失影响
            impact_analysis = self._analyze_capacity_impact(event_info, production_data)
            
            # 生成补偿方案
            compensation_plan = self._generate_compensation_plan(event_info, impact_analysis)
            
            # 生成最终结果
            result = self._generate_result(event_info, impact_analysis, compensation_plan)
            
            self.logger.info("LCA产能损失事件处理完成")
            return result
            
        except Exception as e:
            error_msg = f"处理LCA产能损失事件失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "event_data": event_data
            }
    
    def _check_lca_report_exists(self, event_data: Dict[str, Any]) -> bool:
        """
        检查是否有LCA产量损失报告
        
        Args:
            event_data: 事件数据字典
            
        Returns:
            bool: True表示有报告，False表示没有报告
        """
        self.logger.info("检查是否有LCA产量损失报告...")
        
        try:
            # 基本检查：事件数据是否包含必要字段
            required_fields = ['选择影响日期', '选择影响班次', '选择产线', '输入XX小时']
            for field in required_fields:
                if field not in event_data or not event_data[field]:
                    self.logger.warning(f"缺少必要字段: {field}")
                    return False
            
            # 检查损失小时数是否大于0
            loss_hours = event_data.get('输入XX小时', 0)
            if loss_hours <= 0:
                self.logger.warning("损失小时数无效或为0")
                return False
            
            # 验证Daily Plan中是否存在对应的生产计划数据
            date = event_data.get('选择影响日期')
            line = event_data.get('选择产线')
            
            # 获取Daily Plan数据
            daily_plan = self.data_loader.get_data('HSA Daily Plan')
            if daily_plan is None or daily_plan.empty:
                # 尝试加载Daily Plan数据
                success, message, daily_plan = self.data_loader.load_data('HSA Daily Plan')
                if not success or daily_plan is None or daily_plan.empty:
                    self.logger.warning("无法获取Daily Plan数据")
                    return False
            
            # 检查指定日期是否在Daily Plan中
            if date not in daily_plan.columns:
                self.logger.warning(f"Daily Plan中不存在指定日期: {date}")
                return False
            
            # 检查指定产线是否在Daily Plan中
            if daily_plan.empty or line not in daily_plan.iloc[:, 0].values:
                self.logger.warning(f"Daily Plan中不存在指定产线: {line}")
                return False
            
            # 检查该日期该产线是否有生产计划
            line_data = daily_plan[daily_plan.iloc[:, 0] == line]
            if line_data.empty or line_data[date].isna().all():
                self.logger.warning(f"指定日期和产线没有生产计划: {date}, {line}")
                return False
            
            # 如果指定了产品PN，验证是否存在
            product_pn = event_data.get('确认产品PN')
            if product_pn:
                if product_pn not in line_data.iloc[:, 2].values:
                    self.logger.warning(f"指定产线不生产该产品: {line}, {product_pn}")
                    return False
            
            self.logger.info("LCA产量损失报告检查通过")
            return True
            
        except Exception as e:
            self.logger.error(f"检查LCA产量损失报告时发生错误: {str(e)}")
            return False
    
    def _extract_event_info(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取事件基本信息
        
        Args:
            event_data: 原始事件数据
            
        Returns:
            整理后的事件信息
        """
        return {
            "affect_date": event_data.get('选择影响日期'),
            "affect_shift": event_data.get('选择影响班次'),
            "production_line": event_data.get('选择产线'),
            "loss_hours": event_data.get('输入XX小时', 0),
            "event_type": "LCA产能损失"
        }
    
    def _get_production_data(self) -> Dict[str, Any]:
        """
        获取生产相关数据
        
        Returns:
            生产数据字典
        """
        return {
            "daily_plan": self.data_loader.get_data('daily_plan'),
            "capacity_data": self.data_loader.get_data('capacity'),
            "fg_eoh": self.data_loader.get_data('fg_eoh'),
            "learning_curve": self.data_loader.get_data('learning_curve')
        }
    
    def _analyze_capacity_impact(self, event_info: Dict[str, Any], production_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析产能损失影响
        
        Args:
            event_info: 事件信息
            production_data: 生产数据
            
        Returns:
            影响分析结果
        """
        # TODO: 实现具体的产能损失影响分析逻辑
        self.logger.info("分析产能损失影响...")
        
        return {
            "affected_products": [],
            "capacity_loss": event_info["loss_hours"],
            "impact_level": "medium",
            "affected_shifts": [],
            "downstream_effects": []
        }
    
    def _generate_compensation_plan(self, event_info: Dict[str, Any], impact_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成补偿方案
        
        Args:
            event_info: 事件信息
            impact_analysis: 影响分析结果
            
        Returns:
            补偿方案
        """
        # TODO: 实现具体的补偿方案生成逻辑
        self.logger.info("生成补偿方案...")
        
        return {
            "compensation_type": "overtime_scheduling",
            "additional_shifts": [],
            "alternative_lines": [],
            "resource_adjustments": [],
            "timeline": []
        }
    
    def _generate_result(self, event_info: Dict[str, Any], impact_analysis: Dict[str, Any], compensation_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终处理结果
        
        Args:
            event_info: 事件信息
            impact_analysis: 影响分析结果
            compensation_plan: 补偿方案
            
        Returns:
            最终处理结果
        """
        return {
            "status": "success",
            "event_type": "LCA产能损失",
            "event_info": event_info,
            "impact_analysis": impact_analysis,
            "compensation_plan": compensation_plan,
            "timestamp": datetime.now().isoformat(),
            "message": f"LCA产能损失处理完成 - 产线{event_info['production_line']}，损失{event_info['loss_hours']}小时"
        }