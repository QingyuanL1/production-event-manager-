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
            # 第一步：检查前3个班次都有报告损失，且累计损失超过10K
            check_result = self._check_previous_shifts_loss(event_data)
            
            if check_result["has_sufficient_loss"]:
                self.logger.info("前3个班次累计损失超过10K，建议加线")
                return {
                    "status": "add_line_required",
                    "message": "产线状况不佳，考虑加线",
                    "step": "检查前3班次损失",
                    "check_result": check_result,
                    "recommendation": "加线",
                    "event_data": event_data
                }
            else:
                self.logger.info("前3个班次损失未达到加线条件，继续正常流程")
                return {
                    "status": "normal_process",
                    "message": "损失在正常范围内，按标准流程处理",
                    "step": "检查前3班次损失",
                    "check_result": check_result,
                    "recommendation": "标准处理",
                    "event_data": event_data
                }
            
        except Exception as e:
            error_msg = f"处理LCA产能损失事件失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "event_data": event_data
            }
    
    def _check_previous_shifts_loss(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查前3个班次都有报告损失，且累计损失超过10K
        
        Args:
            event_data: 当前事件数据
            
        Returns:
            检查结果字典
        """
        self.logger.info("检查前3个班次的损失情况...")
        
        try:
            # 获取当前事件的产线信息
            current_line = event_data.get('选择产线')
            current_date = event_data.get('选择影响日期')
            current_shift = event_data.get('选择影响班次')
            
            if not all([current_line, current_date, current_shift]):
                return {
                    "has_sufficient_loss": False,
                    "reason": "事件信息不完整",
                    "previous_shifts": [],
                    "total_loss": 0
                }
            
            # 获取Daily Plan数据（使用三级表头）
            daily_plan_data = self._get_daily_plan_with_shifts()
            if daily_plan_data is None:
                return {
                    "has_sufficient_loss": False,
                    "reason": "无法获取Daily Plan数据",
                    "previous_shifts": [],
                    "total_loss": 0
                }
            
            # 获取前3个班次的信息
            previous_shifts = self._get_previous_3_shifts(current_date, current_shift)
            self.logger.info(f"前3个班次: {previous_shifts}")
            
            # 检查每个班次是否有损失报告
            shifts_with_loss = []
            total_loss = 0
            
            for shift_info in previous_shifts:
                loss_data = self._get_shift_loss_data(shift_info, current_line, daily_plan_data)
                if loss_data["has_loss"]:
                    shifts_with_loss.append(loss_data)
                    total_loss += loss_data["loss_amount"]
            
            # 判断是否满足条件：前3个班次都有损失报告 且 累计损失超过10K
            all_shifts_have_loss = len(shifts_with_loss) >= 3
            total_exceeds_10k = total_loss > 10000
            
            result = {
                "has_sufficient_loss": all_shifts_have_loss and total_exceeds_10k,
                "all_shifts_have_loss": all_shifts_have_loss,
                "total_exceeds_10k": total_exceeds_10k,
                "total_loss": total_loss,
                "shifts_checked": len(previous_shifts),
                "shifts_with_loss": len(shifts_with_loss),
                "previous_shifts": previous_shifts,
                "loss_details": shifts_with_loss,
                "reason": self._get_check_reason(all_shifts_have_loss, total_exceeds_10k, total_loss)
            }
            
            self.logger.info(f"检查结果: {result['reason']}")
            return result
            
        except Exception as e:
            self.logger.error(f"检查前3个班次损失时发生错误: {str(e)}")
            return {
                "has_sufficient_loss": False,
                "reason": f"检查过程中发生错误: {str(e)}",
                "previous_shifts": [],
                "total_loss": 0
            }
    
    def _get_daily_plan_with_shifts(self) -> Optional[pd.DataFrame]:
        """
        获取包含班次信息的Daily Plan数据
        
        Returns:
            带有班次信息的DataFrame或None
        """
        try:
            # 尝试从data_loader获取已加载的数据
            daily_plan = self.data_loader.get_data('HSA Daily Plan')
            if daily_plan is not None and not daily_plan.empty:
                return daily_plan
            
            # 如果没有加载，尝试重新加载
            success, message, daily_plan = self.data_loader.load_data('HSA Daily Plan')
            if success and daily_plan is not None:
                return daily_plan
            
            # 如果标准加载失败，尝试直接读取Excel文件的三级表头
            file_path = "data/daily plan.xlsx"
            df_with_shifts = pd.read_excel(file_path, sheet_name=0, header=[0,1,2])
            self.logger.info("成功加载带班次信息的Daily Plan")
            return df_with_shifts
            
        except Exception as e:
            self.logger.error(f"获取Daily Plan数据失败: {str(e)}")
            return None
    
    def _get_previous_3_shifts(self, current_date: str, current_shift: str) -> List[Dict[str, str]]:
        """
        获取前3个班次的信息
        
        Args:
            current_date: 当前日期 (YYYY-MM-DD格式)
            current_shift: 当前班次 (T1, T2, T3, T4等)
            
        Returns:
            前3个班次的列表，每个元素包含日期和班次信息
        """
        # 班次顺序定义
        shift_order = ['T1', 'T2', 'T3', 'T4']
        
        try:
            from datetime import datetime, timedelta
            current_dt = datetime.strptime(current_date, '%Y-%m-%d')
            
            # 找到当前班次在顺序中的位置
            try:
                current_shift_index = shift_order.index(current_shift)
            except ValueError:
                # 如果班次不在标准列表中，假设是T1
                current_shift_index = 0
            
            previous_shifts = []
            
            # 向前推3个班次
            for i in range(1, 4):  # 前1、2、3个班次
                shift_index = current_shift_index - i
                date_to_check = current_dt
                
                # 如果班次索引为负，需要回到前一天
                while shift_index < 0:
                    shift_index += len(shift_order)
                    date_to_check -= timedelta(days=1)
                
                previous_shifts.append({
                    "date": date_to_check.strftime('%Y-%m-%d'),
                    "shift": shift_order[shift_index],
                    "datetime": date_to_check,
                    "shift_index": shift_index
                })
            
            return previous_shifts
            
        except Exception as e:
            self.logger.error(f"计算前3个班次时发生错误: {str(e)}")
            return []
    
    def _get_shift_loss_data(self, shift_info: Dict[str, str], line: str, daily_plan: pd.DataFrame) -> Dict[str, Any]:
        """
        获取指定班次的损失数据
        
        Args:
            shift_info: 班次信息字典
            line: 产线名称
            daily_plan: Daily Plan数据
            
        Returns:
            班次损失数据
        """
        try:
            # 这里模拟检查班次损失数据
            # 在实际实现中，需要查询数据库中的历史损失记录
            # 目前为了演示，我们生成一些模拟数据
            
            date = shift_info["date"]
            shift = shift_info["shift"]
            
            # 模拟损失数据（实际应该从数据库查询）
            # 假设有一定概率的班次有损失报告
            import random
            
            # 为了演示，设置一些模拟的损失数据
            has_loss = random.choice([True, True, True, False])  # 75%概率有损失
            loss_amount = random.randint(2000, 8000) if has_loss else 0
            
            return {
                "date": date,
                "shift": shift,
                "line": line,
                "has_loss": has_loss,
                "loss_amount": loss_amount,
                "source": "模拟数据"  # 实际应该是"数据库查询"
            }
            
        except Exception as e:
            self.logger.error(f"获取班次损失数据时发生错误: {str(e)}")
            return {
                "date": shift_info.get("date", ""),
                "shift": shift_info.get("shift", ""),
                "line": line,
                "has_loss": False,
                "loss_amount": 0,
                "error": str(e)
            }
    
    def _get_check_reason(self, all_shifts_have_loss: bool, total_exceeds_10k: bool, total_loss: float) -> str:
        """
        生成检查结果的说明文字
        
        Args:
            all_shifts_have_loss: 是否所有班次都有损失
            total_exceeds_10k: 总损失是否超过10K
            total_loss: 总损失数量
            
        Returns:
            说明文字
        """
        if all_shifts_have_loss and total_exceeds_10k:
            return f"前3个班次都有损失报告，累计损失{total_loss:.0f}超过10K，建议加线"
        elif not all_shifts_have_loss and not total_exceeds_10k:
            return f"前3个班次中部分没有损失报告，且累计损失{total_loss:.0f}未超过10K"
        elif not all_shifts_have_loss:
            return f"前3个班次中部分没有损失报告，累计损失{total_loss:.0f}"
        else:  # total_exceeds_10k is False
            return f"前3个班次都有损失报告，但累计损失{total_loss:.0f}未超过10K"