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
        self.logger.info("=" * 60)
        self.logger.info("🚀 开始处理LCA产能损失事件")
        self.logger.info(f"📋 当前事件信息: 日期={event_data.get('选择影响日期')}, 班次={event_data.get('选择影响班次')}, 产线={event_data.get('选择产线')}")
        
        try:
            # 第一步：检查前3个班次都有报告损失，且累计损失超过10K
            self.logger.info("🔍 步骤1: 开始检查前3个班次的损失情况...")
            check_result = self._check_previous_shifts_loss(event_data)
            
            self.logger.info(f"📊 检查结果统计:")
            self.logger.info(f"   - 检查班次数: {check_result.get('shifts_checked', 0)}")
            self.logger.info(f"   - 有损失班次: {check_result.get('shifts_with_loss', 0)}")
            self.logger.info(f"   - 累计损失: {check_result.get('total_loss', 0):.0f}")
            self.logger.info(f"   - 所有班次都有损失: {check_result.get('all_shifts_have_loss', False)}")
            self.logger.info(f"   - 损失超过10K: {check_result.get('total_exceeds_10k', False)}")
            
            if check_result["has_sufficient_loss"]:
                self.logger.info("✅ 判定结果: 前3个班次累计损失超过10K，建议加线")
                self.logger.info("🏭 输出建议: 产线状况不佳，考虑加线")
                return {
                    "status": "add_line_required",
                    "message": "产线状况不佳，考虑加线",
                    "step": "检查前3班次损失",
                    "check_result": check_result,
                    "recommendation": "加线",
                    "event_data": event_data
                }
            else:
                self.logger.info("ℹ️  判定结果: 未达到加线条件，继续正常流程")
                self.logger.info(f"📝 原因: {check_result.get('reason', '未知')}")
                
                # TODO: 这里将添加下一步的处理逻辑
                self.logger.info("⏸️  暂停：等待下一步业务逻辑的定义")
                
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
            self.logger.error(f"❌ {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "event_data": event_data
            }
        finally:
            self.logger.info("=" * 60)
    
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
            self.logger.info(f"📅 计算得出前3个班次:")
            for i, shift in enumerate(previous_shifts, 1):
                self.logger.info(f"   {i}. {shift['date']} {shift['shift']}")
            
            # 检查每个班次是否有损失报告
            self.logger.info(f"🔍 开始查询各班次的损失数据...")
            shifts_with_loss = []
            total_loss = 0
            
            for i, shift_info in enumerate(previous_shifts, 1):
                self.logger.info(f"   查询第{i}个班次: {shift_info['date']} {shift_info['shift']}")
                loss_data = self._get_shift_loss_data(shift_info, current_line, daily_plan_data)
                
                if loss_data["has_loss"]:
                    shifts_with_loss.append(loss_data)
                    total_loss += loss_data["loss_amount"]
                    self.logger.info(f"   ✅ 找到损失记录: {loss_data['loss_amount']:.0f}")
                else:
                    self.logger.info(f"   ❌ 无损失记录: {loss_data.get('reason', '未找到匹配事件')}")
            
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
            self.logger.info(f"📊 从Daily Plan提取到 {len(available_shifts)} 个可用班次")
            
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
                else:
                    self.logger.info(f"无法找到第{i}个前置班次（索引超出范围）")
            
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
            
            self.logger.info(f"提取到 {len(available_shifts)} 个可用班次")
            if available_shifts:
                self.logger.info("可用班次示例:")
                for shift in available_shifts[:5]:  # 显示前5个作为示例
                    self.logger.info(f"  {shift['date']} {shift['shift']} ({shift['day_of_week']})")
            
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
                self.logger.info(f"找到当前班次位置: 索引 {i}")
                return i
        
        self.logger.warning(f"未找到当前班次 {current_date} {current_shift}")
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
        """
        计算预测损失后新DOS
        
        Args:
            event_data: 事件数据
            
        Returns:
            DOS计算结果
        """
        self.logger.info("🔮 步骤2: 开始预测损失后新DOS计算...")
        
        try:
            # 获取基本信息
            current_date = event_data.get('选择影响日期')
            current_shift = event_data.get('选择影响班次')
            line = event_data.get('选择产线')
            part_number = event_data.get('确认产品PN')
            predicted_loss = float(event_data.get('已经损失的产量', 0))
            
            self.logger.info(f"📋 计算参数: 日期={current_date}, 班次={current_shift}, 产线={line}, PN={part_number}")
            self.logger.info(f"📉 预测损失: {predicted_loss}")
            
            # 步骤1: 获取上一个班的合计EOH(库存)
            previous_eoh = self._get_previous_shift_eoh(part_number)
            self.logger.info(f"📦 上一班次合计EOH: {previous_eoh}")
            
            # 步骤2: 获取本班预计产量
            planned_production = self._get_planned_production(current_date, current_shift, line, part_number)
            self.logger.info(f"🏭 本班计划产量: {planned_production}")
            
            # 考虑损失后的实际产量
            actual_production = max(0, planned_production - predicted_loss)
            self.logger.info(f"📊 损失后实际产量: {actual_production} (计划{planned_production} - 损失{predicted_loss})")
            
            # 步骤3: 获取本班出货计划
            current_shipment = self._get_shipment_plan(current_date, current_shift, part_number)
            self.logger.info(f"🚛 本班出货计划: {current_shipment}")
            
            # 步骤4: 获取下两个班次的出货计划
            next_shipments = self._get_next_two_shifts_shipment(current_date, current_shift, part_number)
            total_next_shipment = sum(next_shipments)
            self.logger.info(f"📅 下两班次出货计划: {next_shipments} (合计: {total_next_shipment})")
            
            # 步骤5: 计算本班预计的EOH
            predicted_eoh = previous_eoh + actual_production - current_shipment
            self.logger.info(f"📈 本班预计EOH: {previous_eoh} + {actual_production} - {current_shipment} = {predicted_eoh}")
            
            # 步骤6: 计算预测损失后新DOS
            if total_next_shipment > 0:
                new_dos = predicted_eoh / total_next_shipment
                self.logger.info(f"📊 预测损失后新DOS: {predicted_eoh} / {total_next_shipment} = {new_dos:.2f}")
            else:
                new_dos = float('inf')
                self.logger.warning("⚠️  下两班次无出货计划，DOS无法计算")
            
            # 判断DOS水平
            dos_analysis = self._analyze_dos_level(new_dos)
            
            return {
                "success": True,
                "previous_eoh": previous_eoh,
                "planned_production": planned_production,
                "actual_production": actual_production,
                "current_shipment": current_shipment,
                "next_shipments": next_shipments,
                "predicted_eoh": predicted_eoh,
                "new_dos": new_dos,
                "analysis": dos_analysis,
                "recommendation": dos_analysis.get("recommendation", "继续监控")
            }
            
        except Exception as e:
            error_msg = f"DOS计算失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "recommendation": "无法完成DOS分析，建议人工检查"
            }
    
    def _get_previous_shift_eoh(self, part_number: str) -> float:
        """
        获取上一个班次的合计EOH(库存)
        
        Args:
            part_number: 产品料号
            
        Returns:
            上一班次的EOH总量
        """
        try:
            # 获取EOH数据
            self.logger.info("正在尝试获取EOH数据...")
            eoh_data = self.data_loader.get_data('HSA FG EOH')
            
            if eoh_data is None:
                self.logger.warning("EOH数据为None，使用默认值")
                return 1000.0  # 默认值
            elif eoh_data.empty:
                self.logger.warning("EOH数据为空DataFrame，使用默认值")
                return 1000.0  # 默认值
            else:
                self.logger.info(f"成功获取EOH数据，形状: {eoh_data.shape}")
            
            self.logger.info(f"EOH表列名: {list(eoh_data.columns)}")
            
            # 转换料号为数字格式（EOH表中的P/N是浮点数）
            try:
                target_pn = float(part_number)
            except ValueError:
                self.logger.warning(f"无法将PN {part_number} 转换为数字格式")
                return 1000.0
            
            # 查找目标PN的EOH数据
            matching_rows = eoh_data[eoh_data['P/N'] == target_pn]
            
            if not matching_rows.empty:
                # 获取TTL QTY（总库存量）
                if 'TTL  QTY' in eoh_data.columns:
                    target_eoh = matching_rows['TTL  QTY'].iloc[0]
                    self.logger.info(f"找到PN {part_number} 的EOH: {target_eoh}")
                    
                    # 根据业务规则：需要计算相同Head的产品合计EOH
                    head_qty = matching_rows['Head_Qty'].iloc[0]
                    self.logger.info(f"PN {part_number} 的Head数量: {head_qty}")
                    
                    # 查找相同Head数量的所有产品
                    same_head_rows = eoh_data[eoh_data['Head_Qty'] == head_qty]
                    total_eoh = same_head_rows['TTL  QTY'].sum()
                    
                    self.logger.info(f"相同Head({head_qty})的总库存: {total_eoh}")
                    return float(total_eoh)
                else:
                    self.logger.warning("EOH表中未找到'TTL  QTY'列")
            else:
                self.logger.warning(f"未找到PN {part_number} 的EOH数据")
            
            return 1000.0  # 默认值
            
        except Exception as e:
            self.logger.error(f"获取EOH数据时发生错误: {str(e)}")
            return 1000.0  # 默认值
    
    def _get_planned_production(self, date: str, shift: str, line: str, part_number: str) -> float:
        """
        从Daily Plan获取计划产量
        
        Args:
            date: 日期
            shift: 班次
            line: 产线
            part_number: 产品料号
            
        Returns:
            计划产量
        """
        try:
            # 使用现有的Daily Plan数据获取逻辑
            daily_plan = self._get_daily_plan_with_shifts()
            if daily_plan is None:
                return 2000.0  # 默认值
            
            self.logger.info(f"Daily Plan数据形状: {daily_plan.shape}")
            self.logger.info(f"查找条件: 产线={line}, PN={part_number}, 日期={date}, 班次={shift}")
            
            # 显示可用的产线列表
            available_lines = daily_plan.iloc[:, 0].unique()[:10]  # 前10个
            self.logger.info(f"可用产线: {list(available_lines)}")
            
            # 查找匹配的行和列
            line_rows = daily_plan[daily_plan.iloc[:, 0] == line]
            self.logger.info(f"找到产线 {line} 的行数: {len(line_rows)}")
            
            if not line_rows.empty:
                # 显示该产线的产品列表
                available_pns = line_rows.iloc[:, 2].unique()[:5]  # 前5个
                self.logger.info(f"产线 {line} 的可用PN: {list(available_pns)}")
                
                # 处理数据类型匹配问题
                try:
                    # 尝试数字匹配
                    pn_numeric = float(part_number)
                    pn_rows = line_rows[line_rows.iloc[:, 2] == pn_numeric]
                except ValueError:
                    # 字符串匹配
                    pn_rows = line_rows[line_rows.iloc[:, 2] == part_number]
                
                self.logger.info(f"找到PN {part_number} 的行数: {len(pn_rows)}")
                
                # 如果还是找不到，尝试字符串匹配
                if len(pn_rows) == 0:
                    pn_rows = line_rows[line_rows.iloc[:, 2].astype(str) == str(part_number)]
                    self.logger.info(f"使用字符串匹配找到PN {part_number} 的行数: {len(pn_rows)}")
                
                if not pn_rows.empty:
                    # 查找对应的日期-班次列
                    matching_col = None
                    for col in daily_plan.columns:
                        if isinstance(col, tuple) and len(col) >= 3:
                            col_date = col[0]
                            col_shift = col[2]
                            if isinstance(col_date, str):
                                col_date_formatted = col_date
                            else:
                                col_date_formatted = col_date.strftime('%Y-%m-%d')
                            
                            if col_date_formatted == date and col_shift == shift:
                                matching_col = col
                                break
                    
                    if matching_col:
                        value = pn_rows[matching_col].iloc[0]
                        self.logger.info(f"找到匹配列 {matching_col}，值: {value}")
                        if pd.notna(value) and value != 0:
                            return float(value)
                        else:
                            self.logger.warning(f"匹配列的值为空或0: {value}")
                    else:
                        self.logger.warning(f"未找到匹配的日期-班次列: {date} {shift}")
                        # 显示前几个可用的日期-班次列
                        sample_cols = [col for col in daily_plan.columns if isinstance(col, tuple) and len(col) >= 3][:5]
                        self.logger.info(f"可用日期-班次列示例: {sample_cols}")
            else:
                self.logger.warning(f"未找到产线 {line}")
            
            self.logger.warning(f"未找到 {date} {shift} {line} {part_number} 的计划产量，使用默认值")
            return 2000.0  # 默认值
            
        except Exception as e:
            self.logger.error(f"获取计划产量时发生错误: {str(e)}")
            return 2000.0  # 默认值
    
    def _get_shipment_plan(self, date: str, shift: str, part_number: str) -> float:
        """
        获取出货计划（暂时使用模拟数据）
        
        Args:
            date: 日期
            shift: 班次
            part_number: 产品料号
            
        Returns:
            出货计划量
        """
        # TODO: 实现真实的出货计划表读取
        # 目前使用模拟数据
        return 800.0
    
    def _get_next_two_shifts_shipment(self, current_date: str, current_shift: str, part_number: str) -> List[float]:
        """
        获取下两个班次的出货计划
        
        Args:
            current_date: 当前日期
            current_shift: 当前班次
            part_number: 产品料号
            
        Returns:
            下两个班次的出货计划列表
        """
        # TODO: 实现真实的出货计划表读取
        # 目前使用模拟数据
        return [600.0, 700.0]
    
    def _analyze_dos_level(self, dos: float) -> Dict[str, Any]:
        """
        分析DOS水平并给出建议
        
        Args:
            dos: DOS值
            
        Returns:
            分析结果和建议
        """
        if dos == float('inf'):
            return {
                "level": "无法计算",
                "status": "warning",
                "message": "下两班次无出货计划，DOS无法计算",
                "recommendation": "确认出货计划并重新计算"
            }
        elif dos < 0.5:
            return {
                "level": "严重不足",
                "status": "critical", 
                "message": f"DOS={dos:.2f}天，库存严重不足",
                "recommendation": "紧急增产或调整出货计划"
            }
        elif dos < 1.0:
            return {
                "level": "不足",
                "status": "warning",
                "message": f"DOS={dos:.2f}天，库存不足",
                "recommendation": "考虑增产或延期出货"
            }
        elif dos < 2.0:
            return {
                "level": "偏低",
                "status": "caution",
                "message": f"DOS={dos:.2f}天，库存偏低",
                "recommendation": "密切监控库存水平"
            }
        else:
            return {
                "level": "正常",
                "status": "good",
                "message": f"DOS={dos:.2f}天，库存水平正常",
                "recommendation": "继续按计划执行"
            }