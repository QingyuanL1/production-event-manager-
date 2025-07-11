"""
LCA产能损失处理模块 - 干净版本
LCA Capacity Loss Processing Module - Clean Version

专门处理LCA产能损失事件的业务逻辑模块
只包含前3个班次损失检查逻辑
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging
import os


class LCACapacityLossProcessor:
    """
    LCA产能损失处理器 - 干净版本
    
    负责处理LCA产能损失事件的具体业务逻辑
    当前只实现前3个班次的损失检查
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
        
        # 初始化数据库管理器用于DOS阈值检查
        from .database_manager import DatabaseManager
        self.db_manager = DatabaseManager("data/events.db", self.logger)
        
    def process_lca_capacity_loss(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理LCA产能损失事件的主要入口函数
        
        Args:
            event_data: 事件数据字典
            
        Returns:
            处理结果字典
        """
        self.logger.info("🚀 **LCA产能损失事件处理**")
        self.logger.info(f"事件: {event_data.get('选择影响日期')} {event_data.get('选择影响班次')} {event_data.get('选择产线')}")
        
        try:
            # 步骤0：计算本班预测产量
            forecast_calculation = self._calculate_shift_forecast_i(event_data)
            
            if forecast_calculation["status"] == "success":
                self.logger.info(f"本班预测产量: {forecast_calculation['F']:.2f} (E={forecast_calculation['E']}, C={forecast_calculation['C']}, D={forecast_calculation['D']}h)")
            else:
                self.logger.error(f"本班预测产量计算失败: {forecast_calculation['message']}")
            
            # 步骤1：检查前3班次损失
            check_result = self._check_previous_shifts_loss(event_data)
            
            self.logger.info(f"前3班次检查: {check_result.get('shifts_with_loss', 0)}/{check_result.get('shifts_checked', 0)}班次有损失, 累计{check_result.get('total_loss', 0):.0f}")
            
            # 根据损失检查结果决定后续流程
            if check_result["has_sufficient_loss"]:
                self.logger.info("🔧 建议加线 (前3班次累计损失>10K)")
                
                return {
                    "status": "add_line_required",
                    "message": "产线状况不佳，考虑加线",
                    "step": "检查前3班次损失",
                    "check_result": check_result,
                    "forecast_calculation": forecast_calculation,
                    "recommendation": "加线",
                    "event_data": event_data
                }
            else:
                self.logger.info("➡️ 继续DOS计算")
                
                # 步骤2：计算DOS
                dos_calculation = self._calculate_new_dos(event_data, forecast_calculation)
                
                # 检查是否需要跳出事件
                if dos_calculation.get("status") == "skip_event":
                    self.logger.info(f"⏭️ 跳出事件: {dos_calculation.get('message')}")
                    return {
                        "status": "skip_event",
                        "message": dos_calculation.get('message'),
                        "step": "DOS计算",
                        "check_result": check_result,
                        "dos_calculation": dos_calculation,
                        "forecast_calculation": forecast_calculation,
                        "recommendation": "跳出事件",
                        "event_data": event_data
                    }
                
                # 步骤3：DOS阈值检查和决策
                dos_threshold_check = None
                dos_acceptance_decision = None
                
                if dos_calculation.get("status") == "success":
                    dos_value = dos_calculation.get("dos_value", 0.0)
                    dos_threshold_check = self._check_dos_threshold(dos_value)
                    
                    self.logger.info(f"DOS计算结果: {dos_value:.2f}天 (阈值: {dos_threshold_check['threshold']:.2f}天)")
                    
                    # 步骤4：DOS损失接受性决策
                    dos_acceptance_decision = self._make_dos_acceptance_decision(
                        dos_value, 
                        dos_threshold_check, 
                        dos_calculation,
                        event_data
                    )
                
                return {
                    "status": "normal_process",
                    "message": "损失在正常范围内，已计算DOS",
                    "step": "检查前3班次损失 + DOS计算 + DOS阈值检查 + DOS损失接受性决策",
                    "check_result": check_result,
                    "dos_calculation": dos_calculation,
                    "dos_threshold_check": dos_threshold_check,
                    "dos_acceptance_decision": dos_acceptance_decision,
                    "forecast_calculation": forecast_calculation,
                    "recommendation": self._get_final_recommendation(check_result, dos_calculation, dos_threshold_check),
                    "final_output": dos_acceptance_decision.get("output_message", "") if dos_acceptance_decision else "",
                    "event_data": event_data
                }
            
        except Exception as e:
            error_msg = f"处理LCA产能损失事件失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "event_data": event_data
            }
    
    def _calculate_shift_forecast_i(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算本班预测产量 I
        
        根据公式：F = E - C - D * (E/11)
        其中：
        - E: 本班出货计划（从Daily Plan的forecast获取）
        - C: 已经损失的产量（用户输入）
        - D: 剩余修理时间（用户输入，小时）
        - F: 本班预测产量计算结果 (即 I 值)
        
        Args:
            event_data: 事件数据字典
            
        Returns:
            计算结果字典，包含所有相关数值
        """
        try:
            # 获取事件数据
            date = event_data.get("选择影响日期")
            shift = event_data.get("选择影响班次")
            lost_quantity = event_data.get("已经损失的产量", 0)
            remaining_repair_time = event_data.get("剩余修理时间", 0)
            
            if not date or not shift:
                return {
                    "status": "error",
                    "message": "缺少必要的日期或班次信息",
                    "E": 0, "C": 0, "D": 0, "F": 0
                }
            
            # 获取本班出货计划 E (forecast值)
            line = event_data.get("选择产线", "")
            E = self._get_forecast_value(date, shift, line)
            
            # 转换用户输入为数值
            try:
                C = float(lost_quantity) if lost_quantity else 0.0
                D = float(remaining_repair_time) if remaining_repair_time else 0.0
            except (ValueError, TypeError):
                return {
                    "status": "error", 
                    "message": "用户输入的数值格式不正确",
                    "E": E, "C": 0, "D": 0, "F": 0
                }
            
            # 计算本班预测产量 F = E - C - D * (E/11)
            if E > 0:
                F = E - C - D * (E / 11)
                
                return {
                    "status": "success",
                    "message": f"本班预测产量 I 计算完成: {F:.2f}",
                    "E": E,  # 本班出货计划
                    "C": C,  # 已损失产量
                    "D": D,  # 剩余修理时间
                    "F": F,  # 本班预测产量 (I值)
                    "capacity_loss_per_hour": E / 11,  # 每小时产能损失
                    "total_capacity_loss": D * (E / 11),  # 总产能损失
                    "date": date,
                    "shift": shift
                }
            else:
                return {
                    "status": "error",
                    "message": f"未找到 {date} {shift} 的forecast数据或数据为0",
                    "E": 0, "C": C, "D": D, "F": 0
                }
            
        except Exception as e:
            error_msg = f"计算本班预测产量 I 时出错: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "E": 0, "C": 0, "D": 0, "F": 0
            }
    
    def _get_forecast_value(self, date: str, shift: str, target_line: str = "") -> float:
        """
        从Daily Plan获取指定日期班次的forecast值（本班出货计划 E）
        
        Args:
            date: 日期字符串 (YYYY-MM-DD格式)
            shift: 班次字符串 (T1, T2, T3, T4)
            target_line: 目标产线名称 (如 F17)，用于找到正确的forecast值
            
        Returns:
            forecast值，如果未找到返回0.0
        """
        try:
            # 直接读取Excel文件以获取三级表头信息
            file_path = "data/daily plan.xlsx"
            df_with_shifts = pd.read_excel(file_path, sheet_name=0, header=[0,1,2])
            
            # 找到目标日期和班次对应的列
            target_column = None
            target_col_idx = None
            for i, col in enumerate(df_with_shifts.columns):
                if isinstance(col, tuple) and len(col) >= 3:
                    date_obj = col[0]
                    col_shift = col[2]
                    
                    # 处理日期格式转换
                    formatted_date = None
                    if hasattr(date_obj, 'strftime'):
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                    elif isinstance(date_obj, str) and '-' in date_obj:
                        try:
                            day, month = date_obj.split('-')
                            month_map = {
                                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 
                                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                            }
                            if month in month_map:
                                formatted_date = f"2025-{month_map[month]}-{day.zfill(2)}"
                        except:
                            continue
                    
                    # 找到匹配的日期和班次列
                    if formatted_date == date and col_shift == shift:
                        target_column = col
                        target_col_idx = i
                        break
            
            if target_column is None:
                self.logger.warning(f"未找到 {date} {shift} 对应的数据列")
                return 0.0
            
            # 找到Forecast行 - 修复逻辑：找到与目标产线相关的forecast
            line_column = df_with_shifts.columns[0]
            
            # 区分两种用途：
            # 1. 如果target_line为None或用于本班预测产量计算，使用Forecast行
            # 2. 如果target_line不为None且用于DOS计算的I值，使用产线行
            
            # 通过检查调用栈来判断用途
            import inspect
            frame = inspect.currentframe()
            caller_name = frame.f_back.f_code.co_name if frame.f_back else ""
            
            if target_line and (caller_name == "_get_next_two_shifts_forecast" or caller_name == "_calculate_new_dos"):
                # 这是DOS计算中的I值获取或H值获取，使用产线行数据
                for idx, row in df_with_shifts.iterrows():
                    line_value = row[line_column]
                    if pd.notna(line_value) and target_line in str(line_value):
                        # 直接从该产线行获取目标列的值
                        line_value = row[target_column]
                        if pd.notna(line_value) and line_value != 0:
                            return float(line_value)
                        else:
                            # 如果产线行在该班次没有值，返回0
                            return 0.0
            else:
                # 这是本班预测产量计算的E值获取，使用Forecast行
                if target_line:
                    # 找到目标产线行来确定对应的forecast
                    target_line_row = None
                    for idx, row in df_with_shifts.iterrows():
                        line_value = row[line_column]
                        if pd.notna(line_value) and target_line in str(line_value):
                            target_line_row = idx
                            # 移除重复的日志输出
                            break
                    
                    # 查找最近的forecast行（在目标产线之前）
                    if target_line_row is not None:
                        forecast_rows = []
                        for idx, row in df_with_shifts.iterrows():
                            line_value = row[line_column]
                            if pd.notna(line_value) and "forecast" in str(line_value).lower():
                                forecast_value = row[target_column]
                                if pd.notna(forecast_value) and forecast_value != 0:
                                    forecast_rows.append((idx, forecast_value))
                        
                        # 找到最近的forecast行（在目标产线之前）
                        closest_forecast_value = None
                        min_distance = float('inf')
                        
                        for forecast_idx, forecast_value in forecast_rows:
                            if forecast_idx < target_line_row:
                                distance = target_line_row - forecast_idx
                                if distance < min_distance:
                                    min_distance = distance
                                    closest_forecast_value = forecast_value
                        
                        if closest_forecast_value is not None:
                            return float(closest_forecast_value)
            
            # 如果没有指定产线或没有找到相关forecast，使用原始逻辑（找第一个非零forecast）
            for idx, row in df_with_shifts.iterrows():
                line_value = row[line_column]
                if pd.notna(line_value) and "forecast" in str(line_value).lower():
                    forecast_value = row[target_column]
                    if pd.notna(forecast_value) and forecast_value != 0:
                        return float(forecast_value)
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"获取forecast值时出错: {str(e)}")
            return 0.0
    
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
            # 直接读取Excel文件的三级表头以保留班次信息
            file_path = "data/daily plan.xlsx"
            df_with_shifts = pd.read_excel(file_path, sheet_name=0, header=[0,1,2])
            self.logger.info(f"成功加载带班次信息的Daily Plan: {df_with_shifts.shape}")
            return df_with_shifts
            
        except Exception as e:
            self.logger.error(f"获取Daily Plan数据失败: {str(e)}")
            # 如果直接读取失败，尝试从data_loader获取（虽然没有班次信息）
            try:
                daily_plan = self.data_loader.get_data('HSA Daily Plan')
                if daily_plan is not None and not daily_plan.empty:
                    self.logger.warning("使用扁平化的Daily Plan数据（无班次信息）")
                    return daily_plan
                return None
            except:
                return None
    
    def _get_previous_3_shifts(self, current_date: str, current_shift: str) -> List[Dict[str, str]]:
        """
        获取前3个班次的信息 - 只从Daily Plan中实际存在的班次中查找
        
        Args:
            current_date: 当前日期 (YYYY-MM-DD格式)
            current_shift: 当前班次 (T1, T2, T3, T4等)
            
        Returns:
            前3个班次的列表，每个元素包含日期和班次信息
        """
        try:
            # 获取Daily Plan数据以获取实际的日期和班次组合
            daily_plan = self._get_daily_plan_with_shifts()
            if daily_plan is None:
                self.logger.error("无法获取Daily Plan数据")
                return []
            
            # 提取所有可用的日期-班次组合
            available_shifts = self._extract_available_shifts(daily_plan)
            
            # 找到当前班次在可用班次列表中的位置
            current_position = self._find_current_shift_position(available_shifts, current_date, current_shift)
            if current_position == -1:
                self.logger.warning(f"当前班次 {current_date} {current_shift} 未在Daily Plan中找到")
                return []
            
            # 获取前3个班次（如果存在）
            previous_shifts = []
            for i in range(1, 4):  # 前1、2、3个班次
                pos = current_position - i
                if pos >= 0:  # 确保索引有效
                    shift_info = available_shifts[pos]
                    previous_shifts.append({
                        "date": shift_info["date"],
                        "shift": shift_info["shift"],
                        "datetime": shift_info["datetime"],
                        "position": pos
                    })
            
            return previous_shifts
            
        except Exception as e:
            self.logger.error(f"计算前3个班次时发生错误: {str(e)}")
            return []
    
    def _extract_available_shifts(self, daily_plan: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        从Daily Plan的三级表头中提取所有可用的日期-班次组合
        
        Args:
            daily_plan: Daily Plan DataFrame（三级表头）
            
        Returns:
            按时间顺序排列的日期-班次组合列表
        """
        available_shifts = []
        
        try:
            # 获取列索引（三级表头）
            columns = daily_plan.columns
            
            for col in columns:
                if isinstance(col, tuple) and len(col) >= 3:
                    # 三级表头格式：(日期, 星期, 班次)
                    date_obj = col[0]
                    day_of_week = col[1] 
                    shift = col[2]
                    
                    # 跳过非班次列（如Line, Build Type, Part Number, Total等）
                    if shift in ['T1', 'T2', 'T3', 'T4']:
                        try:
                            # 处理不同类型的日期对象
                            from datetime import datetime
                            
                            if isinstance(date_obj, datetime):
                                # 如果是datetime对象，直接使用
                                date_dt = date_obj
                                formatted_date = date_dt.strftime('%Y-%m-%d')
                            elif isinstance(date_obj, str):
                                # 如果是字符串，尝试解析
                                if '-' in date_obj:
                                    # "1-Mar" 格式
                                    day, month = date_obj.split('-')
                                    month_map = {
                                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 
                                        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                                    }
                                    if month in month_map:
                                        formatted_date = f"2025-{month_map[month]}-{day.zfill(2)}"
                                        date_dt = datetime.strptime(formatted_date, '%Y-%m-%d')
                                    else:
                                        continue
                                else:
                                    continue
                            else:
                                # 其他类型，跳过
                                continue
                            
                            available_shifts.append({
                                "date": formatted_date,
                                "shift": shift,
                                "day_of_week": day_of_week,
                                "datetime": date_dt,
                                "original_column": col
                            })
                            
                        except Exception as e:
                            self.logger.debug(f"跳过列 {col}: {str(e)}")
                            continue
            
            # 按日期和班次顺序排序
            shift_order = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}
            available_shifts.sort(key=lambda x: (x["datetime"], shift_order.get(x["shift"], 5)))
            
            
            return available_shifts
            
        except Exception as e:
            self.logger.error(f"提取可用班次时发生错误: {str(e)}")
            return []
    
    def _find_current_shift_position(self, available_shifts: List[Dict[str, Any]], current_date: str, current_shift: str) -> int:
        """
        在可用班次列表中找到当前班次的位置
        
        Args:
            available_shifts: 可用班次列表
            current_date: 当前日期
            current_shift: 当前班次
            
        Returns:
            当前班次在列表中的索引，未找到返回-1
        """
        for i, shift_info in enumerate(available_shifts):
            if shift_info["date"] == current_date and shift_info["shift"] == current_shift:
                return i
        
        return -1
    
    def _get_shift_loss_data(self, shift_info: Dict[str, str], line: str, daily_plan: pd.DataFrame) -> Dict[str, Any]:
        """
        从事件表获取指定班次的损失数据
        
        Args:
            shift_info: 班次信息字典
            line: 产线名称
            daily_plan: Daily Plan数据
            
        Returns:
            班次损失数据
        """
        try:
            date = shift_info["date"]
            shift = shift_info["shift"]
            
            # 从数据库查询历史LCA损失事件
            from .database_manager import DatabaseManager
            
            # 创建数据库管理器实例
            db_manager = DatabaseManager("data/events.db")
            
            # 查询匹配的LCA事件
            matching_events = db_manager.get_lca_events_by_criteria(
                date=date,
                line=line
            )
            
            # 查找匹配班次的事件
            matched_event = None
            for event in matching_events:
                event_shift = event.get("选择影响班次")
                if event_shift == shift:
                    matched_event = event
                    break
            
            if matched_event:
                # 提取损失数据
                loss_amount = matched_event.get("已经损失的产量", 0)
                if loss_amount is None:
                    loss_amount = 0
                
                # 尝试转换为数字
                try:
                    loss_amount = float(loss_amount)
                except (ValueError, TypeError):
                    loss_amount = 0
                
                return {
                    "date": date,
                    "shift": shift,
                    "line": line,
                    "has_loss": loss_amount > 0,
                    "loss_amount": loss_amount,
                    "event_id": matched_event.get("事件ID", ""),
                    "source": "事件数据库",
                    "event_data": matched_event
                }
            else:
                # 没有找到匹配的事件
                return {
                    "date": date,
                    "shift": shift,
                    "line": line,
                    "has_loss": False,
                    "loss_amount": 0,
                    "source": "事件数据库",
                    "reason": f"未找到{date} {shift}班次的损失事件"
                }
            
        except Exception as e:
            self.logger.error(f"从事件表获取班次损失数据时发生错误: {str(e)}")
            return {
                "date": shift_info.get("date", ""),
                "shift": shift_info.get("shift", ""),
                "line": line,
                "has_loss": False,
                "loss_amount": 0,
                "source": "错误",
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
    
    def _load_fg_eoh_data(self) -> Optional[pd.DataFrame]:
        """
        加载FG EOH数据
        
        Returns:
            FG EOH DataFrame或None
        """
        try:
            file_path = "data/FG EOH.xlsx"
            if not os.path.exists(file_path):
                self.logger.error(f"FG EOH文件不存在: {file_path}")
                return None
            
            df = pd.read_excel(file_path, sheet_name=0)
            
            # 清理列名中的多余空格
            df.columns = df.columns.str.strip()
            
            # 标准化TTL QTY列名
            if 'TTL  QTY' in df.columns:
                df = df.rename(columns={'TTL  QTY': 'TTL QTY'})
            
            self.logger.info(f"成功加载FG EOH数据: {df.shape}")
            self.logger.info(f"列名: {list(df.columns)}")
            return df
            
        except Exception as e:
            self.logger.error(f"加载FG EOH数据失败: {str(e)}")
            return None
    
    def _get_g_value_for_pn(self, part_number: str) -> Tuple[float, Dict[str, Any]]:
        """
        为指定PN获取G值（上一个班的合计EOH库存）
        
        Args:
            part_number: 产品PN号
            
        Returns:
            (G值, 详细信息字典)
        """
        try:
            df = self._load_fg_eoh_data()
            if df is None:
                return 0.0, {"status": "error", "message": "无法加载FG EOH数据"}
            
            # 查找包含指定PN的行（处理数字格式的PN）
            try:
                # 尝试将part_number转换为float进行匹配
                pn_numeric = float(part_number)
                pn_rows = df[df['P/N'] == pn_numeric]
            except (ValueError, TypeError):
                # 如果转换失败，使用字符串匹配
                pn_rows = df[df['P/N'].astype(str) == str(part_number)]
            
            if pn_rows.empty:
                return 0.0, {
                    "status": "error", 
                    "message": f"未找到PN {part_number} 的EOH数据"
                }
            
            # 获取该PN所属的Product和Head_Qty
            pn_row = pn_rows.iloc[0]
            product = pn_row['Product']
            head_qty = pn_row['Head_Qty']
            
            # 找到同一Product和Head_Qty组的所有行
            group_rows = df[(df['Product'] == product) & (df['Head_Qty'] == head_qty)]
            
            # 计算TTL QTY总和作为G值
            g_value = group_rows['TTL QTY'].sum()
            
            details = {
                "status": "success",
                "product": product,
                "head_qty": head_qty,
                "group_size": len(group_rows),
                "g_value": g_value,
                "group_pns": group_rows['P/N'].tolist()
            }
            
            self.logger.info(f"📎 计算PN {part_number} 的G值: {g_value}")
            self.logger.info(f"   🏷️ Product: {product}, Head_Qty: {head_qty}")
            self.logger.info(f"   🔢 组内PN数量: {len(group_rows)}")
            
            return float(g_value), details
            
        except Exception as e:
            error_msg = f"计算PN {part_number} 的G值时出错: {str(e)}"
            self.logger.error(error_msg)
            return 0.0, {"status": "error", "message": error_msg}
    
    def _get_next_two_shifts_forecast(self, current_date: str, current_shift: str, target_line: str) -> Tuple[float, Dict[str, Any]]:
        """
        获取下两个班次的出货计划总和（I值）
        
        Args:
            current_date: 当前日期 (YYYY-MM-DD格式)
            current_shift: 当前班次 (T1, T2, T3, T4)
            target_line: 目标产线
            
        Returns:
            (I值, 详细信息字典)
        """
        try:
            # 获取所有可用班次
            daily_plan = self._get_daily_plan_with_shifts()
            if daily_plan is None:
                return 0.0, {"status": "error", "message": "无法获取Daily Plan数据"}
            
            available_shifts = self._extract_available_shifts(daily_plan)
            
            # 找到当前班次位置
            current_position = self._find_current_shift_position(available_shifts, current_date, current_shift)
            if current_position == -1:
                return 0.0, {"status": "error", "message": f"未找到当前班次 {current_date} {current_shift}"}
            
            # 获取下两个班次
            next_shifts = []
            valid_forecasts = []
            
            for i in range(1, 3):  # 下1、2个班次
                next_pos = current_position + i
                if next_pos < len(available_shifts):
                    shift_info = available_shifts[next_pos]
                    next_date = shift_info["date"]
                    next_shift = shift_info["shift"]
                    
                    # 获取该班次的forecast值
                    forecast_value = self._get_forecast_value(next_date, next_shift, target_line)
                    
                    next_shifts.append({
                        "date": next_date,
                        "shift": next_shift,
                        "forecast": forecast_value
                    })
                    
                    # 只记录非零的forecast值
                    if forecast_value > 0:
                        valid_forecasts.append(forecast_value)
                    
                    self.logger.info(f"   下第{i}个班次 {next_date} {next_shift}: {forecast_value}")
                else:
                    self.logger.warning(f"无法找到下第{i}个班次（超出可用范围）")
            
            # 处理特殊情况
            if len(valid_forecasts) == 0:
                # 两个班次都是0，跳出事件
                details = {
                    "status": "skip_event",
                    "message": "下两个班次出货计划都为0，跳出事件",
                    "current_date": current_date,
                    "current_shift": current_shift,
                    "target_line": target_line,
                    "next_shifts": next_shifts,
                    "i_total": 0.0
                }
                self.logger.info("⚠️ **下两个班次出货计划都为0，跳出事件**")
                return 0.0, details
                
            elif len(valid_forecasts) == 1:
                # 只有一个有效数据，乘以2
                i_total = valid_forecasts[0] * 2
                details = {
                    "status": "single_forecast_doubled",
                    "message": f"只有一个班次有有效出货计划，将其乘以2: {valid_forecasts[0]} * 2 = {i_total}",
                    "current_date": current_date,
                    "current_shift": current_shift,
                    "target_line": target_line,
                    "next_shifts": next_shifts,
                    "i_total": i_total,
                    "single_forecast": valid_forecasts[0]
                }
                self.logger.info(f"🔢 **只有一个班次有有效出货计划，将其乘以2: {valid_forecasts[0]} * 2 = {i_total}**")
                
            else:
                # 两个班次都有数据，正常求和
                i_total = sum(valid_forecasts)
                details = {
                    "status": "success",
                    "message": f"两个班次都有有效出货计划，总和: {i_total}",
                    "current_date": current_date,
                    "current_shift": current_shift,
                    "target_line": target_line,
                    "next_shifts": next_shifts,
                    "i_total": i_total
                }
                self.logger.info(f"➕ **两个班次都有有效出货计划，总和 I: {i_total}**")
            
            return float(i_total), details
            
        except Exception as e:
            error_msg = f"获取下两个班次出货计划时出错: {str(e)}"
            self.logger.error(error_msg)
            return 0.0, {"status": "error", "message": error_msg}
    
    def _calculate_new_dos(self, event_data: Dict[str, Any], forecast_calculation: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算预测损失后新DOS
        
        公式: (G+F-H)/I
        其中:
        - G: 上一个班的合计EOH(库存)
        - F: 本班预计产量 (已计算)
        - H: 本班出货计划 (forecast_calculation中的E值)
        - I: 下两个班次的出货计划
        
        Args:
            event_data: 事件数据
            forecast_calculation: 预测产量计算结果
            
        Returns:
            DOS计算结果字典
        """
        try:
            self.logger.info("🧮 **步骤2: 计算预测损失后新DOS...**")
            
            # 获取必要的参数
            part_number = event_data.get("确认产品PN")
            current_date = event_data.get("选择影响日期")
            current_shift = event_data.get("选择影响班次")
            target_line = event_data.get("选择产线")
            
            if not all([part_number, current_date, current_shift, target_line]):
                return {
                    "status": "error",
                    "message": "缺少DOS计算必要参数",
                    "dos_value": 0.0
                }
            
            # 获取F值（本班预计产量）
            f_value = forecast_calculation.get("F", 0.0)
            
            # 获取H值（本班安排产量 - 产线PN在当前班次的值）
            h_value = self._get_forecast_value(current_date, current_shift, target_line)
            
            self.logger.info(f"DOS计算参数:")
            self.logger.info(f"   PN: {part_number}")
            self.logger.info(f"   产线: {target_line}")
            self.logger.info(f"   当前班次: {current_date} {current_shift}")
            
            # 获取G值（上一个班的合计EOH库存）
            g_value, g_details = self._get_g_value_for_pn(part_number)
            if g_details["status"] != "success":
                return {
                    "status": "error",
                    "message": f"获取G值失败: {g_details['message']}",
                    "dos_value": 0.0
                }
            
            # 获取I值（下两个班次的出货计划）
            i_value, i_details = self._get_next_two_shifts_forecast(current_date, current_shift, target_line)
            
            # 处理跳出事件的情况
            if i_details["status"] == "skip_event":
                return {
                    "status": "skip_event",
                    "message": i_details["message"],
                    "dos_value": 0.0,
                    "i_details": i_details
                }
            
            # 处理其他错误情况
            if i_details["status"] not in ["success", "single_forecast_doubled"]:
                return {
                    "status": "error",
                    "message": f"获取I值失败: {i_details.get('message', '未知错误')}",
                    "dos_value": 0.0
                }
            
            # 防止除零错误
            if i_value <= 0:
                return {
                    "status": "error",
                    "message": "下两个班次出货计划为0，无法计算DOS",
                    "dos_value": 0.0
                }
            
            # 计算新DOS: (G+F-H)/I
            dos_value = (g_value + f_value - h_value) / i_value
            
            # 记录详细计算过程
            self.logger.info("🧮 **DOS计算公式: (G+F-H)/I**")
            self.logger.info(f"   📎 G (上一个班的合计EOH): {g_value}")
            self.logger.info(f"   🎯 F (本班预计产量): {f_value}")
            self.logger.info(f"   📈 H (本班安排产量): {h_value}")
            self.logger.info(f"   📅 I (下两个班次出货计划): {i_value}")
            self.logger.info(f"   📊 计算过程: ({g_value} + {f_value} - {h_value}) / {i_value}")
            self.logger.info(f"   🆕 **预测损失后新DOS: {dos_value:.2f} 天**")
            
            return {
                "status": "success",
                "message": f"DOS计算成功: {dos_value:.2f} 天",
                "dos_value": dos_value,
                "g_value": g_value,
                "f_value": f_value,
                "h_value": h_value,
                "i_value": i_value,
                "g_details": g_details,
                "i_details": i_details,
                "calculation_formula": f"({g_value} + {f_value} - {h_value}) / {i_value} = {dos_value:.2f}"
            }
            
        except Exception as e:
            error_msg = f"计算预测损失后新DOS时出错: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "dos_value": 0.0
            }
    
    def _check_dos_threshold(self, dos_value: float) -> Dict[str, Any]:
        """
        检查DOS值是否符合阈值要求
        
        Args:
            dos_value: 计算得到的DOS值
            
        Returns:
            检查结果字典
        """
        try:
            return self.db_manager.check_dos_threshold(dos_value)
        except Exception as e:
            self.logger.error(f"DOS阈值检查失败: {str(e)}")
            return {
                "dos_value": dos_value,
                "threshold": 0.5,
                "meets_threshold": dos_value >= 0.5,
                "status": "error",
                "message": f"检查过程出错，使用默认阈值0.5: {str(e)}"
            }
    
    def _get_final_recommendation(self, check_result: Dict[str, Any], 
                                 dos_calculation: Dict[str, Any], 
                                 dos_threshold_check: Optional[Dict[str, Any]]) -> str:
        """
        根据所有检查结果生成最终建议
        
        Args:
            check_result: 前3班次损失检查结果
            dos_calculation: DOS计算结果
            dos_threshold_check: DOS阈值检查结果
            
        Returns:
            最终建议字符串
        """
        try:
            # 如果前3班次累计损失超过10K，建议加线
            if check_result.get("has_sufficient_loss", False):
                return "加线处理"
            
            # 如果DOS计算失败或需要跳出事件
            if dos_calculation.get("status") != "success":
                return "跳出事件"
            
            # 如果DOS阈值检查失败
            if not dos_threshold_check or dos_threshold_check.get("status") == "error":
                return "标准处理（阈值检查失败）"
            
            # 根据DOS阈值检查结果给出建议
            if dos_threshold_check.get("meets_threshold", False):
                return "标准处理（DOS值符合要求）"
            else:
                dos_value = dos_threshold_check.get("dos_value", 0.0)
                threshold = dos_threshold_check.get("threshold", 0.5)
                return f"谨慎处理（DOS值{dos_value:.2f}低于阈值{threshold:.2f}）"
                
        except Exception as e:
            self.logger.error(f"生成最终建议失败: {str(e)}")
            return "标准处理（建议生成失败）"
    
    def _make_dos_acceptance_decision(self, dos_value: float, 
                                    dos_threshold_check: Dict[str, Any],
                                    dos_calculation: Dict[str, Any], 
                                    event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据DOS阈值检查结果做出DOS损失接受性决策
        
        根据流程图逻辑：
        - 如果预计损失后DOS > 最低控制DOS：可以接受损失，输出"损失已用DOS覆盖，未进行产量调整"
        - 如果预计损失后DOS ≤ 最低控制DOS：不可接受损失，输出"新DOS预计降为XXXX"
        
        Args:
            dos_value: 计算得到的DOS值
            dos_threshold_check: DOS阈值检查结果
            event_data: 事件数据
            
        Returns:
            决策结果字典
        """
        try:
            self.logger.info("🔍 **步骤4: DOS损失接受性决策**")
            
            threshold = dos_threshold_check.get("threshold", 0.5)
            meets_threshold = dos_threshold_check.get("meets_threshold", False)
            
            self.logger.info(f"   🧮 决策逻辑: 预计损失后DOS({dos_value:.2f}) vs 最低控制DOS({threshold:.2f})")
            
            if meets_threshold:
                # DOS值符合要求，可以接受损失
                output_message = "损失已用DOS覆盖，未进行产量调整"
                decision = "可以接受损失"
                action_required = False
                
                self.logger.info(f"   ✅ **决策结果: {decision}**")
                self.logger.info(f"   📢 **输出信息: {output_message}**")
                self.logger.info("   📋 说明: 预计损失后的DOS值仍高于最低控制阈值，现有库存足以覆盖损失")
                
            else:
                # DOS值低于要求，不可接受损失
                output_message = f"新DOS预计降为{dos_value:.2f}天"
                decision = "不可接受损失"
                action_required = True
                shortage = abs(dos_threshold_check.get("difference", 0))
                
                self.logger.warning(f"❌ {decision}: {output_message}, 短缺{shortage:.2f}天")
                
                # 计算具体的补偿产量
                compensation_calculation = self._calculate_compensation_production(
                    dos_value, threshold, dos_calculation, event_data
                )
                
                # 步骤5：检查后续班次是否可以调整补偿
                subsequent_shifts_check = self._check_subsequent_shifts_for_adjustment(
                    event_data, compensation_calculation
                )
            
            result = {
                "status": "success",
                "decision": decision,
                "output_message": output_message,
                "action_required": action_required,
                "dos_value": dos_value,
                "threshold": threshold,
                "meets_threshold": meets_threshold,
                "shortage_days": abs(dos_threshold_check.get("difference", 0)) if not meets_threshold else 0,
                "decision_time": datetime.now().isoformat()
            }
            
            # 如果需要补偿，添加补偿计算信息
            if not meets_threshold:
                result["compensation_calculation"] = compensation_calculation
                result["subsequent_shifts_check"] = subsequent_shifts_check
                
            return result
            
        except Exception as e:
            error_msg = f"DOS损失接受性决策失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "decision": "决策失败",
                "output_message": f"决策过程出错: {str(e)}",
                "action_required": False,
                "error": error_msg
            }
    
    
    def _calculate_compensation_production(self, current_dos: float, target_dos: float, 
                                         dos_calculation: Dict[str, Any], 
                                         _: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算剩余产量补偿数据
        
        根据公式：
        - 预测损失后DOS: G' = (G+F-H)/I  (已计算得到 = current_dos)
        - 最低控制DOS: J = target_dos
        - 需要达到的补偿后产量: F' = J*I + H - G
        - 实际需要补偿的产量: F' - F
        
        Args:
            current_dos: 当前预测损失后DOS值 (G')
            target_dos: 最低控制DOS值 (J)
            dos_calculation: DOS计算结果，包含G、F、H、I值
            event_data: 事件数据
            
        Returns:
            补偿计算结果字典
        """
        try:
            self.logger.info("🧮 步骤4.1: 计算补偿产量")
            
            # 从DOS计算结果中获取各个参数
            G = dos_calculation.get("g_value", 0)  # 上一个班的合计EOH
            F = dos_calculation.get("f_value", 0)  # 本班预计产量
            H = dos_calculation.get("h_value", 0)  # 本班安排产量
            I = dos_calculation.get("i_value", 0)  # 下两个班次出货计划
            
            
            # 验证参数有效性
            if I <= 0:
                return {
                    "status": "error",
                    "message": "下两班次出货计划为0，无法计算补偿产量",
                    "compensation_needed": 0
                }
            
            # 计算需要达到的补偿后总产量 F'
            # 公式: F' = J*I + H - G
            F_prime = target_dos * I + H - G
            
            # 实际需要补偿的产量
            compensation_needed = F_prime - F
            
            self.logger.info(f"   🧮 **补偿产量计算:**")
            self.logger.info(f"      公式: F' = J*I + H - G")
            self.logger.info(f"      计算: F' = {target_dos:.2f}*{I:.2f} + {H:.2f} - {G:.2f}")
            self.logger.info(f"      补偿后总产量 F': {F_prime:.2f}")
            self.logger.info(f"      当前预计产量 F: {F:.2f}")
            self.logger.info(f"      **需要补偿产量: {compensation_needed:.2f}**")
            
            verification_dos = (G + F_prime - H) / I
            self.logger.info(f"   ✅ **验算:**")
            self.logger.info(f"      用F'计算DOS: ({G:.2f} + {F_prime:.2f} - {H:.2f}) / {I:.2f} = {verification_dos:.2f}")
            self.logger.info(f"      是否达到目标 {target_dos:.2f}: {'✅ 是' if abs(verification_dos - target_dos) < 0.01 else '❌ 否'}")
            
            # 补偿产量分析
            if compensation_needed <= 0:
                compensation_type = "无需补偿"
            elif compensation_needed < 1000:
                compensation_type = "少量补偿"
            elif compensation_needed < 5000:
                compensation_type = "中等补偿"
            else:
                compensation_type = "大量补偿"
            
            return {
                "status": "success",
                "message": f"补偿产量计算完成",
                "current_dos": current_dos,
                "target_dos": target_dos,
                "original_production": F,
                "required_total_production": F_prime,
                "compensation_needed": compensation_needed,
                "compensation_type": compensation_type,
                "verification_dos": verification_dos,
                "parameters": {
                    "G": G, "F": F, "H": H, "I": I,
                    "F_prime": F_prime
                },
                "formula": f"F' = J*I + H - G = {target_dos:.2f}*{I:.2f} + {H:.2f} - {G:.2f} = {F_prime:.2f}",
                "calculation_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"计算补偿产量失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "compensation_needed": 0
            }
    
    def _check_subsequent_shifts_for_adjustment(self, event_data: Dict[str, Any], 
                                              compensation_calculation: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查后续班次是否可以调整来补偿损失
        
        逻辑：从当前事件班次开始，查找后续班次（如3号T3后面的班次），
        检查是否有可用的产能来补偿所需的产量
        
        Args:
            event_data: 当前事件数据
            compensation_calculation: 补偿产量计算结果
            
        Returns:
            后续班次检查结果字典
        """
        try:
            self.logger.info("🔍 步骤5: 检查后续班次调整可能性")
            
            # 获取补偿产量需求
            if compensation_calculation.get("status") != "success":
                return {
                    "status": "skip",
                    "message": "补偿产量计算失败，跳过后续班次检查",
                    "available_shifts": [],
                    "adjustment_possible": False
                }
            
            compensation_needed = compensation_calculation.get("compensation_needed", 0)
            if compensation_needed <= 0:
                return {
                    "status": "no_need",
                    "message": "无需补偿，跳过后续班次检查",
                    "available_shifts": [],
                    "adjustment_possible": False
                }
            
            # 获取当前事件信息
            current_date = event_data.get("选择影响日期")
            current_shift = event_data.get("选择影响班次")
            target_line = event_data.get("选择产线")
            
            if not all([current_date, current_shift, target_line]):
                return {
                    "status": "error",
                    "message": "事件信息不完整",
                    "available_shifts": [],
                    "adjustment_possible": False
                }
            
            self.logger.info(f"需要补偿产量: {compensation_needed:.0f}")
            self.logger.info(f"当前事件: {current_date} {current_shift} {target_line}")
            
            # 获取后续可用班次
            subsequent_shifts = self._get_subsequent_shifts(current_date, current_shift)
            
            if not subsequent_shifts:
                self.logger.info("❌ 无后续班次可调整")
                return {
                    "status": "no_shifts",
                    "message": "无后续班次可用于调整",
                    "available_shifts": [],
                    "adjustment_possible": False
                }
            
            # 检查每个后续班次的调整可能性
            adjustment_options = self._evaluate_shift_adjustment_options(
                subsequent_shifts, target_line, compensation_needed
            )
            
            # 判断是否有可行的调整方案
            has_viable_options = any(option["viable"] for option in adjustment_options)
            
            if has_viable_options:
                self.logger.info("✅ 找到可调整的后续班次")
                
                # 检查前两个可调整班次是否有冲突事件
                conflict_check = self._check_event_conflicts_in_next_shifts(
                    adjustment_options, target_line
                )
                
                return {
                    "status": "adjustable",
                    "message": "找到可调整的后续班次",
                    "available_shifts": subsequent_shifts,
                    "adjustment_options": adjustment_options,
                    "adjustment_possible": True,
                    "compensation_needed": compensation_needed,
                    "conflict_check": conflict_check
                }
            else:
                self.logger.info("❌ 后续班次无法满足补偿需求")
                return {
                    "status": "insufficient",
                    "message": "后续班次无法满足补偿需求",
                    "available_shifts": subsequent_shifts,
                    "adjustment_options": adjustment_options,
                    "adjustment_possible": False,
                    "compensation_needed": compensation_needed
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查后续班次时出错: {str(e)}",
                "available_shifts": [],
                "adjustment_possible": False
            }
    
    def _get_subsequent_shifts(self, current_date: str, current_shift: str) -> List[Dict[str, Any]]:
        """
        获取当前班次之后的后续班次列表
        
        Args:
            current_date: 当前日期 (YYYY-MM-DD格式)
            current_shift: 当前班次 (T1, T2, T3, T4)
            
        Returns:
            后续班次列表，每个元素包含日期和班次信息
        """
        try:
            # 获取Daily Plan数据以获取实际的日期和班次组合
            daily_plan = self._get_daily_plan_with_shifts()
            if daily_plan is None:
                return []
            
            # 提取所有可用的日期-班次组合
            available_shifts = self._extract_available_shifts(daily_plan)
            
            # 找到当前班次在可用班次列表中的位置
            current_position = self._find_current_shift_position(available_shifts, current_date, current_shift)
            if current_position == -1:
                return []
            
            # 获取后续班次（当前班次之后的所有班次）
            subsequent_shifts = []
            total_shifts = len(available_shifts)
            
            # 限制检查后续班次数量（例如最多检查接下来的10个班次）
            max_subsequent_shifts = 10
            
            for i in range(1, min(max_subsequent_shifts + 1, total_shifts - current_position)):
                pos = current_position + i
                if pos < total_shifts:
                    shift_info = available_shifts[pos]
                    subsequent_shifts.append({
                        "date": shift_info["date"],
                        "shift": shift_info["shift"],
                        "datetime": shift_info["datetime"],
                        "position": pos,
                        "sequence": i  # 第几个后续班次
                    })
            
            self.logger.info(f"找到 {len(subsequent_shifts)} 个后续班次")
            
            return subsequent_shifts
            
        except Exception:
            return []
    
    def _evaluate_shift_adjustment_options(self, subsequent_shifts: List[Dict[str, Any]], 
                                         target_line: str, compensation_needed: float) -> List[Dict[str, Any]]:
        """
        评估每个后续班次的调整可能性
        
        Args:
            subsequent_shifts: 后续班次列表
            target_line: 目标产线
            compensation_needed: 需要补偿的产量
            
        Returns:
            每个班次的调整评估结果列表
        """
        adjustment_options = []
        
        try:
            viable_count = 0
            total_potential_adjustment = 0
            
            for shift_info in subsequent_shifts:
                date = shift_info["date"]
                shift = shift_info["shift"]
                sequence = shift_info.get("sequence", 0)
                
                # 获取该班次在目标产线的计划产量
                planned_production = self._get_forecast_value(date, shift, target_line)
                
                # 简单的可行性评估逻辑
                # 假设如果该班次有计划产量，就有调整的可能性
                viable = planned_production > 0
                potential_adjustment = min(planned_production * 0.2, compensation_needed) if viable else 0  # 假设最多可调整20%
                
                option = {
                    "date": date,
                    "shift": shift,
                    "sequence": sequence,
                    "planned_production": planned_production,
                    "viable": viable,
                    "potential_adjustment": potential_adjustment,
                    "adjustment_ratio": potential_adjustment / compensation_needed if compensation_needed > 0 else 0
                }
                
                adjustment_options.append(option)
                
                if viable:
                    viable_count += 1
                    total_potential_adjustment += potential_adjustment
            
            # 只输出汇总信息
            self.logger.info(f"后续班次评估: {viable_count}/{len(subsequent_shifts)}班次可调整, 总潜在调整量{total_potential_adjustment:.0f}")
            
            return adjustment_options
            
        except Exception:
            return []
    
    def _check_event_conflicts_in_next_shifts(self, adjustment_options: List[Dict[str, Any]], 
                                            target_line: str) -> Dict[str, Any]:
        """
        检查前N个可调整班次的事件数量
        
        检查的事件类型：
        1. LCA/Manual Rework计划
        2. RecycleHGA  
        3. PM
        
        Args:
            adjustment_options: 调整选项列表
            target_line: 目标产线（保留参数以备将来使用）
            
        Returns:
            事件数量检查结果字典
        """
        try:
            # 获取配置的检查班次数量
            check_count = self.db_manager.get_shift_check_count()
            self.logger.info(f"🔍 检查前{check_count}班次事件数量")
            
            # 获取前N个可调整的班次
            viable_shifts = [opt for opt in adjustment_options if opt["viable"]][:check_count]
            
            if not viable_shifts:
                return {
                    "status": "no_shifts",
                    "message": "无可调整班次需要检查",
                    "conflict_shifts": [],
                    "has_conflicts": False
                }
            
            # 获取Daily Plan数据
            daily_plan = self._get_daily_plan_with_shifts()
            if daily_plan is None:
                return {
                    "status": "error",
                    "message": "无法获取Daily Plan数据",
                    "conflict_shifts": [],
                    "has_conflicts": False
                }
            
            conflict_results = []
            total_events = 0
            
            for shift_opt in viable_shifts:
                date = shift_opt["date"]
                shift = shift_opt["shift"]
                
                # 检查该班次的事件信息（数量和类型）
                event_info_result = self._count_events_in_shift(
                    daily_plan, date, shift
                )
                
                event_info = {
                    "date": date,
                    "shift": shift,
                    "sequence": shift_opt.get("sequence", 0),
                    "planned_production": shift_opt.get("planned_production", 0),
                    "event_count": event_info_result["count"],
                    "event_types": event_info_result["types"],
                    "event_details": event_info_result["details"],
                    "has_events": event_info_result["count"] > 0
                }
                
                conflict_results.append(event_info)
                total_events += event_info_result["count"]
            
            # 判断是否有任何事件
            has_any_events = any(result["has_events"] for result in conflict_results)
            
            # 输出详细的事件检查结果并计算可抵偿产量
            shifts_with_events = sum(1 for result in conflict_results if result["has_events"])
            
            # 汇总所有事件类型
            all_event_types = set()
            for result in conflict_results:
                all_event_types.update(result.get("event_types", []))
            
            if shifts_with_events == 0:
                self.logger.info(f"后续{len(viable_shifts)}班次均无冲突事件")
            else:
                self.logger.info(f"后续{len(viable_shifts)}班次中{shifts_with_events}班次有冲突事件")
                
                # 计算每个班次的事件可抵偿产量
                for result in conflict_results:
                    if result["has_events"]:
                        date = result["date"]
                        shift = result["shift"]
                        event_types = result.get("event_types", [])
                        planned_production = result.get("planned_production", 0)
                        
                        # 计算该班次事件的可抵偿产量
                        compensation_by_events = self._calculate_event_compensation_capacity(
                            date, shift, target_line, event_types, planned_production
                        )
                        
                        # 更新结果中的抵偿信息
                        result["compensation_capacity"] = compensation_by_events
                        
                        if event_types:
                            types_str = ', '.join(event_types)
                            total_compensation = sum(compensation_by_events.values())
                            self.logger.info(f"  {date} {shift}: {types_str} (可抵偿{total_compensation:.0f})")
                        else:
                            self.logger.info(f"  {date} {shift}: 有事件")
            
            return {
                "status": "success",
                "message": f"检查了{len(viable_shifts)}个班次的事件数量",
                "checked_shifts": conflict_results,
                "has_events": has_any_events,
                "total_events": total_events,
                "event_types_found": list(all_event_types),
                "shifts_with_events": shifts_with_events,
                "check_count": check_count
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查事件数量时出错: {str(e)}",
                "checked_shifts": [],
                "has_events": False
            }
    
    def _count_events_in_shift(self, daily_plan: pd.DataFrame, 
                             date: str, shift: str) -> Dict[str, Any]:
        """
        统计指定班次的事件信息（数量和类型）
        
        Args:
            daily_plan: Daily Plan DataFrame
            date: 日期
            shift: 班次
            
        Returns:
            事件信息字典，包含数量和类型列表
        """
        event_count = 0
        event_types = []
        
        try:
            # 目标事件类型
            target_event_types = [
                "LCA", "Manual", "Recycle HGA", "PM"
            ]
            
            # 找到目标日期和班次对应的列
            target_column = None
            for col in daily_plan.columns:
                if isinstance(col, tuple) and len(col) >= 3:
                    date_obj = col[0]
                    col_shift = col[2]
                    
                    # 处理日期格式转换
                    formatted_date = self._format_date_from_column(date_obj)
                    
                    if formatted_date == date and col_shift == shift:
                        target_column = col
                        break
            
            if target_column is None:
                return {"count": 0, "types": [], "details": []}
            
            # 检查Line列中的事件类型
            line_column = daily_plan.columns[0]
            event_details = []
            
            for row_idx, row in daily_plan.iterrows():
                line_value = row[line_column]
                
                if pd.notna(line_value):
                    line_str = str(line_value).strip()
                    
                    # 检查是否包含目标事件类型
                    for event_type in target_event_types:
                        if event_type in line_str:
                            # 检查该事件在目标班次是否有数值
                            event_value = row[target_column]
                            
                            if pd.notna(event_value) and event_value != 0:
                                event_count += 1
                                if event_type not in event_types:
                                    event_types.append(event_type)
                                event_details.append({
                                    "type": event_type,
                                    "line_description": line_str,
                                    "value": event_value
                                })
                                break  # 避免同一行重复计数
            
            return {
                "count": event_count,
                "types": event_types,
                "details": event_details
            }
            
        except Exception:
            return {"count": 0, "types": [], "details": []}
    
    def _calculate_event_compensation_capacity(self, date: str, shift: str, 
                                             target_line: str, event_types: List[str], 
                                             planned_production: float) -> Dict[str, float]:
        """
        计算不同事件类型的可抵偿产量
        
        Args:
            date: 日期
            shift: 班次
            target_line: 目标产线
            event_types: 事件类型列表
            planned_production: 计划产量
            
        Returns:
            各事件类型的可抵偿产量字典
        """
        compensation_by_events = {}
        
        try:
            # 获取产线总产能 (假设从capacity数据或固定值获取)
            line_capacity = self._get_line_capacity(target_line)
            
            # 添加调试信息
            self.logger.info(f"抵偿产量计算 - 产线{target_line}总产能: {line_capacity}, 计划产量: {planned_production}")
            
            for event_type in event_types:
                if event_type in ["LCA", "Manual"]:
                    # LCA/Manual Rework: 按产线空余产能计算
                    spare_capacity = max(0, line_capacity - planned_production)
                    compensation_by_events[event_type] = spare_capacity
                    self.logger.info(f"  {event_type}事件: 空余产能 = {line_capacity} - {planned_production} = {spare_capacity}")
                    
                elif "Recycle" in event_type or "HGA" in event_type:
                    # Recycle HGA: 按产线空余产能计算  
                    spare_capacity = max(0, line_capacity - planned_production)
                    compensation_by_events[event_type] = spare_capacity
                    self.logger.info(f"  {event_type}事件: 空余产能 = {line_capacity} - {planned_production} = {spare_capacity}")
                    
                elif event_type == "PM":
                    # PM: 固定占用2小时，按比例计算 (2/11 × 总产量)
                    pm_compensation = (2.0 / 11.0) * planned_production
                    compensation_by_events[event_type] = pm_compensation
                    self.logger.info(f"  {event_type}事件: 2小时抵偿 = 2/11 × {planned_production} = {pm_compensation:.0f}")
                    
                else:
                    # 其他未知事件类型，暂时设为0
                    compensation_by_events[event_type] = 0.0
                    self.logger.info(f"  {event_type}事件: 未知类型，设为0")
            
            return compensation_by_events
            
        except Exception as e:
            self.logger.error(f"计算事件抵偿产量失败: {str(e)}")
            return {event_type: 0.0 for event_type in event_types}
    
    def _get_line_capacity(self, target_line: str) -> float:
        """
        获取产线总产能
        
        Args:
            target_line: 目标产线
            
        Returns:
            产线总产能，默认7000
        """
        try:
            # 尝试从capacity数据获取
            capacity_data = self.data_loader.get_data("capacity")
            if capacity_data is not None:
                # 查找目标产线的产能信息
                for idx, row in capacity_data.iterrows():
                    if target_line in str(row.iloc[0]):  # 假设第一列是产线名称
                        # 查找产能相关的列
                        for col in capacity_data.columns:
                            if "capacity" in str(col).lower() or "产能" in str(col):
                                capacity_value = row[col]
                                if pd.notna(capacity_value) and capacity_value > 0:
                                    return float(capacity_value)
            
            # 如果没有找到capacity数据，使用默认值
            # 可以根据产线类型设置不同的默认值
            default_capacities = {
                "F16": 6000,
                "F25": 7000, 
                "F29": 8000,
                "F32": 7500
            }
            
            for line_code, capacity in default_capacities.items():
                if line_code in target_line:
                    return capacity
            
            # 通用默认值
            return 7000.0
            
        except Exception:
            return 7000.0
    
    def _format_date_from_column(self, date_obj) -> str:
        """
        从列对象中格式化日期
        
        Args:
            date_obj: 列中的日期对象
            
        Returns:
            格式化后的日期字符串 (YYYY-MM-DD)
        """
        try:
            if hasattr(date_obj, 'strftime'):
                return date_obj.strftime('%Y-%m-%d')
            elif isinstance(date_obj, str) and '-' in date_obj:
                day, month = date_obj.split('-')
                month_map = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                if month in month_map:
                    return f"2025-{month_map[month]}-{day.zfill(2)}"
            return ""
        except Exception:
            return ""
