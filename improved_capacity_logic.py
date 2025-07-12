"""
改进的产能获取逻辑 - Improved Capacity Logic

这个模块包含了改进版的产能获取方法，可以直接集成到现有的LCA产能损失处理器中
基于实际Daily Plan数据进行智能产能分析，提供更准确的产能信息
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

def get_enhanced_line_capacity(data_loader, logger, target_line: str) -> Dict[str, Any]:
    """
    增强版产线产能获取方法
    
    Args:
        data_loader: 数据加载器实例
        logger: 日志记录器
        target_line: 目标产线名称
        
    Returns:
        包含产能信息的字典:
        {
            'capacity': float,           # 推荐的单班次产能
            'source': str,              # 数据来源说明
            'confidence': float,        # 置信度 (0-1)
            'max_observed': float,      # 观测到的最大产量
            'capacity_range': tuple,    # 产能范围 (min, max)
            'products': List[str],      # 支持的产品类型
            'analysis_details': dict    # 详细分析数据
        }
    """
    logger.info(f"🔍 开始智能分析{target_line}产线产能...")
    
    try:
        # 1. 首先尝试从capacity.xlsx获取标准产能数据
        capacity_from_file = _get_capacity_from_file(data_loader, logger, target_line)
        
        # 2. 从Daily Plan分析实际产能
        capacity_from_daily_plan = _analyze_capacity_from_daily_plan(data_loader, logger, target_line)
        
        # 3. 融合两种数据源的结果
        final_result = _merge_capacity_analysis(capacity_from_file, capacity_from_daily_plan, target_line)
        
        logger.info(f"✅ {target_line}产能分析完成:")
        logger.info(f"   推荐产能: {final_result['capacity']:.0f}")
        logger.info(f"   数据来源: {final_result['source']}")
        logger.info(f"   置信度: {final_result['confidence']:.2f}")
        
        return final_result
        
    except Exception as e:
        logger.error(f"产能分析失败: {str(e)}")
        return _get_fallback_capacity(target_line)

def _get_capacity_from_file(data_loader, logger, target_line: str) -> Optional[Dict[str, Any]]:
    """从capacity.xlsx文件获取产能信息"""
    try:
        capacity_data = data_loader.get_data("HSA Capacity")
        if capacity_data is None:
            logger.warning("无法获取HSA Capacity数据")
            return None
        
        logger.info(f"Capacity文件结构: {capacity_data.shape}, 列名: {list(capacity_data.columns)}")
        
        # 查找目标产线
        for idx, row in capacity_data.iterrows():
            line_value = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            if target_line in line_value:
                logger.info(f"在capacity文件中找到{target_line}: {dict(row)}")
                
                # 查找产能列
                capacity_keywords = ["prime capacity", "capacity", "产能", "prime", "max"]
                for col in capacity_data.columns:
                    col_str = str(col).lower()
                    if any(keyword in col_str for keyword in capacity_keywords):
                        capacity_value = row[col]
                        if pd.notna(capacity_value) and capacity_value > 0:
                            return {
                                'capacity': float(capacity_value),
                                'source': f'Capacity file ({col})',
                                'confidence': 0.9,
                                'product': row.get('Product', 'Unknown'),
                                'head_qty': row.get('Head_Qty', 'Unknown')
                            }
        
        logger.info(f"在capacity文件中未找到{target_line}的产能数据")
        return None
        
    except Exception as e:
        logger.warning(f"读取capacity文件失败: {e}")
        return None

def _analyze_capacity_from_daily_plan(data_loader, logger, target_line: str) -> Optional[Dict[str, Any]]:
    """从Daily Plan分析产能"""
    try:
        # 获取所有可用的sheet
        sheet_names = data_loader.get_sheet_names("HSA Daily Plan")
        if not sheet_names:
            logger.warning("无法获取Daily Plan sheet列表")
            return None
        
        logger.info(f"分析Daily Plan sheets: {sheet_names}")
        
        all_productions = []
        all_products = set()
        sheet_results = {}
        
        for sheet_name in sheet_names:
            sheet_result = _analyze_sheet_capacity(data_loader, logger, target_line, sheet_name)
            if sheet_result and sheet_result['max_production'] > 0:
                sheet_results[sheet_name] = sheet_result
                all_productions.extend(sheet_result['productions'])
                all_products.update(sheet_result['products'])
        
        if not all_productions:
            logger.warning(f"在Daily Plan中未找到{target_line}的生产数据")
            return None
        
        # 计算综合产能
        max_production = max(all_productions)
        avg_production = np.mean(all_productions)
        total_shifts = len(all_productions)
        
        # 计算产能系数 (基于数据质量)
        if total_shifts >= 10:
            capacity_factor = 1.2  # 数据充足，保守估算
            confidence = 0.8
        elif total_shifts >= 5:
            capacity_factor = 1.25  # 中等数据量
            confidence = 0.6
        else:
            capacity_factor = 1.3   # 数据较少，适当提高估算
            confidence = 0.4
        
        estimated_capacity = max_production * capacity_factor
        capacity_range = (max_production * 1.05, max_production * 1.4)
        
        result = {
            'capacity': estimated_capacity,
            'source': f'Daily Plan analysis ({len(sheet_results)} sheets, {total_shifts} shifts)',
            'confidence': confidence,
            'max_observed': max_production,
            'avg_observed': avg_production,
            'capacity_range': capacity_range,
            'products': list(all_products),
            'total_shifts': total_shifts,
            'sheet_details': sheet_results
        }
        
        logger.info(f"Daily Plan分析结果: 最大产量{max_production}, 估算产能{estimated_capacity:.0f}")
        return result
        
    except Exception as e:
        logger.error(f"Daily Plan产能分析失败: {e}")
        return None

def _analyze_sheet_capacity(data_loader, logger, target_line: str, sheet_name: str) -> Optional[Dict[str, Any]]:
    """分析单个sheet的产能数据"""
    try:
        df = data_loader.get_data_for_sheet("HSA Daily Plan", sheet_name)
        if df is None:
            return None
        
        # 查找目标产线的数据
        line_col = df.iloc[:, 0]
        line_mask = line_col == target_line
        line_data = df[line_mask]
        
        if len(line_data) == 0:
            return None
        
        productions = []
        products = set()
        
        for _, row in line_data.iterrows():
            # 获取产品信息
            if len(row) > 1:
                build_type = row.iloc[1]
                if pd.notna(build_type):
                    products.add(str(build_type))
            
            # 收集生产数据 (跳过前3列和最后的Total列)
            for j in range(3, len(row)-1):
                val = row.iloc[j]
                if pd.notna(val) and val > 0:
                    productions.append(float(val))
        
        if not productions:
            return None
        
        return {
            'max_production': max(productions),
            'avg_production': np.mean(productions),
            'productions': productions,
            'products': products,
            'shifts_count': len(productions)
        }
        
    except Exception as e:
        logger.warning(f"分析sheet {sheet_name} 失败: {e}")
        return None

def _merge_capacity_analysis(file_result: Optional[Dict], daily_plan_result: Optional[Dict], target_line: str) -> Dict[str, Any]:
    """融合多个数据源的产能分析结果"""
    
    # 如果两个数据源都有结果，选择置信度更高的
    if file_result and daily_plan_result:
        if file_result['confidence'] > daily_plan_result['confidence']:
            primary_result = file_result
            secondary_result = daily_plan_result
            source_note = f"{file_result['source']} (verified by Daily Plan)"
        else:
            primary_result = daily_plan_result
            secondary_result = file_result
            source_note = f"{daily_plan_result['source']} (cross-checked with capacity file)"
        
        # 如果两个结果差异很大，降低置信度
        capacity_diff_ratio = abs(primary_result['capacity'] - secondary_result['capacity']) / primary_result['capacity']
        if capacity_diff_ratio > 0.5:  # 差异超过50%
            adjusted_confidence = primary_result['confidence'] * 0.7
            source_note += " (large variance detected)"
        else:
            adjusted_confidence = min(1.0, primary_result['confidence'] * 1.1)
        
        return {
            'capacity': primary_result['capacity'],
            'source': source_note,
            'confidence': adjusted_confidence,
            'max_observed': daily_plan_result.get('max_observed', 0),
            'capacity_range': daily_plan_result.get('capacity_range', (0, 0)),
            'products': daily_plan_result.get('products', []),
            'analysis_details': {
                'file_result': file_result,
                'daily_plan_result': daily_plan_result
            }
        }
    
    # 只有一个数据源有结果
    elif daily_plan_result:
        return {
            'capacity': daily_plan_result['capacity'],
            'source': daily_plan_result['source'],
            'confidence': daily_plan_result['confidence'],
            'max_observed': daily_plan_result['max_observed'],
            'capacity_range': daily_plan_result['capacity_range'],
            'products': daily_plan_result['products'],
            'analysis_details': {'daily_plan_result': daily_plan_result}
        }
    
    elif file_result:
        return {
            'capacity': file_result['capacity'],
            'source': file_result['source'],
            'confidence': file_result['confidence'],
            'max_observed': 0,
            'capacity_range': (file_result['capacity'] * 0.9, file_result['capacity'] * 1.1),
            'products': [file_result.get('product', 'Unknown')],
            'analysis_details': {'file_result': file_result}
        }
    
    # 都没有结果，使用默认值
    else:
        return _get_fallback_capacity(target_line)

def _get_fallback_capacity(target_line: str) -> Dict[str, Any]:
    """获取默认产能值"""
    default_capacities = {
        "F16": 6000,
        "F25": 2800,  # 基于实际分析调整
        "F29": 12000, # 基于实际分析调整
        "F17": 10000,
        "F27": 10000,
        "F35": 8000
    }
    
    for line_code, capacity in default_capacities.items():
        if line_code in target_line:
            return {
                'capacity': capacity,
                'source': f'Default value for {line_code}',
                'confidence': 0.3,
                'max_observed': 0,
                'capacity_range': (capacity * 0.8, capacity * 1.2),
                'products': [],
                'analysis_details': {}
            }
    
    # 通用默认值
    return {
        'capacity': 8000,
        'source': 'Generic fallback',
        'confidence': 0.2,
        'max_observed': 0,
        'capacity_range': (6000, 10000),
        'products': [],
        'analysis_details': {}
    }

def get_simple_line_capacity(data_loader, logger, target_line: str) -> float:
    """
    简化版产能获取方法，返回单一数值
    这个方法可以直接替换现有的_get_line_capacity方法
    
    Args:
        data_loader: 数据加载器
        logger: 日志记录器 
        target_line: 目标产线
        
    Returns:
        产线单班次产能 (float)
    """
    result = get_enhanced_line_capacity(data_loader, logger, target_line)
    return result['capacity']

# 使用示例:
# 在lca_capacity_loss.py中替换_get_line_capacity方法:
#
# def _get_line_capacity(self, target_line: str) -> float:
#     from improved_capacity_logic import get_simple_line_capacity
#     return get_simple_line_capacity(self.data_loader, self.logger, target_line)