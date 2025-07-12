#!/usr/bin/env python3
"""
增强产能分析器 - Enhanced Capacity Analyzer

基于Daily Plan数据的智能产能分析工具，用于准确获取产线实际产能信息
支持多sheet分析、历史数据融合、产能趋势分析等功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import logging
from datetime import datetime
import os

class EnhancedCapacityAnalyzer:
    """
    增强产能分析器
    
    从Daily Plan数据中智能分析和推算各产线的实际产能
    提供多种产能获取策略和数据验证功能
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化产能分析器
        
        Args:
            data_dir: 数据文件目录
        """
        self.data_dir = data_dir
        self.daily_plan_file = os.path.join(data_dir, "daily plan.xlsx")
        self.capacity_file = os.path.join(data_dir, "capacity .xlsx")
        
        # 设置日志
        self.logger = self._setup_logger()
        
        # 产能分析结果缓存
        self.capacity_cache = {}
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('CapacityAnalyzer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def analyze_all_production_lines(self) -> Dict[str, Dict[str, Any]]:
        """
        分析所有产线的产能信息
        
        Returns:
            包含所有产线产能分析结果的字典
        """
        self.logger.info("🚀 开始分析所有产线产能...")
        
        # 获取所有可用的sheet
        try:
            xlsx = pd.ExcelFile(self.daily_plan_file)
            sheet_names = xlsx.sheet_names
            self.logger.info(f"发现Daily Plan sheets: {sheet_names}")
        except Exception as e:
            self.logger.error(f"无法读取Daily Plan文件: {e}")
            return {}
        
        all_lines_capacity = {}
        
        # 分析每个sheet
        for sheet_name in sheet_names:
            self.logger.info(f"\n--- 分析Sheet: {sheet_name} ---")
            sheet_analysis = self._analyze_sheet_capacity(sheet_name)
            
            # 合并结果
            for line, capacity_info in sheet_analysis.items():
                if line not in all_lines_capacity:
                    all_lines_capacity[line] = {
                        'sheets_data': {},
                        'combined_analysis': {}
                    }
                
                all_lines_capacity[line]['sheets_data'][sheet_name] = capacity_info
        
        # 生成综合分析
        for line in all_lines_capacity:
            all_lines_capacity[line]['combined_analysis'] = self._generate_combined_analysis(
                line, all_lines_capacity[line]['sheets_data']
            )
        
        self.capacity_cache = all_lines_capacity
        return all_lines_capacity
    
    def _analyze_sheet_capacity(self, sheet_name: str) -> Dict[str, Dict[str, Any]]:
        """
        分析单个sheet的产能数据
        
        Args:
            sheet_name: sheet名称
            
        Returns:
            产线产能分析结果
        """
        try:
            # 读取数据，使用3级表头
            df = pd.read_excel(self.daily_plan_file, sheet_name=sheet_name, header=[0,1,2])
            
            # 获取产线列
            line_col = df.iloc[:, 0]
            
            # 找出所有F系列产线
            f_lines = [line for line in line_col.dropna().unique() 
                      if isinstance(line, str) and line.startswith('F') and line != 'Forecast']
            
            sheet_capacity = {}
            
            for line in f_lines:
                capacity_info = self._analyze_line_capacity_in_sheet(df, line, sheet_name)
                if capacity_info:
                    sheet_capacity[line] = capacity_info
            
            return sheet_capacity
            
        except Exception as e:
            self.logger.error(f"分析sheet {sheet_name} 时出错: {e}")
            return {}
    
    def _analyze_line_capacity_in_sheet(self, df: pd.DataFrame, line: str, sheet_name: str) -> Optional[Dict[str, Any]]:
        """
        分析特定产线在特定sheet中的产能
        
        Args:
            df: Daily Plan数据框
            line: 产线名称
            sheet_name: sheet名称
            
        Returns:
            产线产能分析结果
        """
        line_col = df.iloc[:, 0]
        line_mask = line_col == line
        line_data = df[line_mask]
        
        if len(line_data) == 0:
            return None
        
        # 收集所有产量数据
        all_productions = []
        shift_productions = {}
        product_productions = {}
        
        for _, row in line_data.iterrows():
            # 获取产品信息
            build_type = row.iloc[1] if len(row) > 1 else 'Unknown'
            part_number = row.iloc[2] if len(row) > 2 else 'Unknown'
            
            # 分析生产数据列（跳过前3列和最后的Total列）
            for j in range(3, len(row)-1):
                val = row.iloc[j]
                if pd.notna(val) and val > 0:
                    all_productions.append(val)
                    
                    # 解析班次信息
                    col_tuple = df.columns[j]
                    if len(col_tuple) >= 3:
                        date_info = col_tuple[0]
                        weekday = col_tuple[1]
                        shift = col_tuple[2]
                        shift_key = f"{weekday}_{shift}"
                        
                        if shift_key not in shift_productions:
                            shift_productions[shift_key] = []
                        shift_productions[shift_key].append(val)
                        
                        # 按产品统计
                        if build_type not in product_productions:
                            product_productions[build_type] = []
                        product_productions[build_type].append(val)
        
        if not all_productions:
            return {
                'max_shift_output': 0,
                'avg_shift_output': 0,
                'total_output': 0,
                'active_shifts': 0,
                'products': [],
                'confidence': 0.0,
                'data_quality': 'No production data'
            }
        
        # 计算统计数据
        max_production = max(all_productions)
        avg_production = np.mean(all_productions)
        total_production = sum(all_productions)
        active_shifts = len(all_productions)
        
        # 分析班次模式
        shift_analysis = {}
        for shift_key, productions in shift_productions.items():
            shift_analysis[shift_key] = {
                'max': max(productions),
                'avg': np.mean(productions),
                'count': len(productions)
            }
        
        # 产品分析
        product_analysis = {}
        for product, productions in product_productions.items():
            product_analysis[product] = {
                'max': max(productions),
                'avg': np.mean(productions),
                'count': len(productions)
            }
        
        # 数据质量评估
        data_quality = self._assess_data_quality(all_productions, active_shifts)
        
        # 置信度计算
        confidence = self._calculate_confidence(all_productions, active_shifts, len(line_data))
        
        return {
            'max_shift_output': max_production,
            'avg_shift_output': avg_production,
            'total_output': total_production,
            'active_shifts': active_shifts,
            'shift_analysis': shift_analysis,
            'product_analysis': product_analysis,
            'products': list(product_productions.keys()),
            'confidence': confidence,
            'data_quality': data_quality,
            'raw_data': all_productions
        }
    
    def _assess_data_quality(self, productions: List[float], active_shifts: int) -> str:
        """评估数据质量"""
        if not productions:
            return "No data"
        
        if active_shifts >= 10:
            return "High quality"
        elif active_shifts >= 5:
            return "Medium quality"
        elif active_shifts >= 2:
            return "Low quality"
        else:
            return "Very low quality"
    
    def _calculate_confidence(self, productions: List[float], active_shifts: int, line_rows: int) -> float:
        """计算置信度"""
        if not productions:
            return 0.0
        
        # 基于数据量的置信度
        data_confidence = min(1.0, active_shifts / 10.0)
        
        # 基于数据一致性的置信度
        if len(productions) > 1:
            cv = np.std(productions) / np.mean(productions)  # 变异系数
            consistency_confidence = max(0.0, 1.0 - cv)
        else:
            consistency_confidence = 0.5
        
        # 基于产线配置数的置信度
        config_confidence = min(1.0, line_rows / 3.0)
        
        # 综合置信度
        total_confidence = (data_confidence * 0.5 + consistency_confidence * 0.3 + config_confidence * 0.2)
        
        return round(total_confidence, 2)
    
    def _generate_combined_analysis(self, line: str, sheets_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成多sheet的综合分析结果
        
        Args:
            line: 产线名称
            sheets_data: 各sheet的分析数据
            
        Returns:
            综合分析结果
        """
        all_max_outputs = []
        all_avg_outputs = []
        all_products = set()
        total_active_shifts = 0
        weighted_confidence = 0
        
        for sheet_name, data in sheets_data.items():
            if data['max_shift_output'] > 0:
                all_max_outputs.append(data['max_shift_output'])
                all_avg_outputs.append(data['avg_shift_output'])
                total_active_shifts += data['active_shifts']
                weighted_confidence += data['confidence'] * data['active_shifts']
                all_products.update(data['products'])
        
        if not all_max_outputs:
            return {
                'recommended_capacity': 0,
                'capacity_range': (0, 0),
                'data_source': 'No data available',
                'confidence': 0.0,
                'products': []
            }
        
        # 推荐产能计算
        max_observed = max(all_max_outputs)
        avg_max = np.mean(all_max_outputs)
        
        # 应用产能系数 (基于数据质量调整)
        avg_confidence = weighted_confidence / total_active_shifts if total_active_shifts > 0 else 0
        capacity_factor = 1.1 + (0.2 * avg_confidence)  # 1.1 到 1.3 之间
        
        recommended_capacity = max_observed * capacity_factor
        
        # 产能范围
        min_capacity = max_observed * 1.05
        max_capacity = max_observed * 1.4
        
        return {
            'recommended_capacity': round(recommended_capacity, 0),
            'capacity_range': (round(min_capacity, 0), round(max_capacity, 0)),
            'max_observed_output': max_observed,
            'avg_max_output': round(avg_max, 1),
            'total_active_shifts': total_active_shifts,
            'data_source': f"Daily Plan analysis ({len(sheets_data)} sheets)",
            'confidence': round(avg_confidence, 2),
            'products': list(all_products),
            'capacity_factor': round(capacity_factor, 2)
        }
    
    def get_line_capacity(self, target_line: str) -> Dict[str, Any]:
        """
        获取指定产线的产能信息
        
        Args:
            target_line: 目标产线
            
        Returns:
            产能分析结果
        """
        # 如果还没有分析过，先进行全量分析
        if not self.capacity_cache:
            self.analyze_all_production_lines()
        
        # 查找目标产线
        for line, capacity_data in self.capacity_cache.items():
            if target_line in line:
                result = capacity_data['combined_analysis'].copy()
                result['line'] = line
                result['detailed_data'] = capacity_data['sheets_data']
                return result
        
        # 如果没找到，返回默认信息
        return {
            'line': target_line,
            'recommended_capacity': 8000,
            'capacity_range': (7000, 9000),
            'data_source': 'Default fallback',
            'confidence': 0.0,
            'products': []
        }
    
    def generate_capacity_report(self) -> str:
        """
        生成产能分析报告
        
        Returns:
            格式化的产能报告字符串
        """
        if not self.capacity_cache:
            self.analyze_all_production_lines()
        
        report = ["=" * 80]
        report.append("产线产能分析报告")
        report.append("=" * 80)
        report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"分析产线数量: {len(self.capacity_cache)}")
        report.append("")
        
        # 按产线排序
        sorted_lines = sorted(self.capacity_cache.keys())
        
        for line in sorted_lines:
            data = self.capacity_cache[line]
            combined = data['combined_analysis']
            
            report.append(f"📍 {line}产线")
            report.append("-" * 40)
            report.append(f"推荐产能: {combined.get('recommended_capacity', 0):.0f}")
            report.append(f"产能范围: {combined.get('capacity_range', (0, 0))}")
            report.append(f"最大观测产量: {combined.get('max_observed_output', 0):.0f}")
            report.append(f"数据来源: {combined.get('data_source', 'Unknown')}")
            report.append(f"置信度: {combined.get('confidence', 0):.2f}")
            report.append(f"支持产品: {', '.join(combined.get('products', []))}")
            
            # 各sheet详情
            report.append("  各Sheet数据:")
            for sheet_name, sheet_data in data['sheets_data'].items():
                report.append(f"    {sheet_name}: 最大{sheet_data['max_shift_output']}, "
                             f"平均{sheet_data['avg_shift_output']:.1f}, "
                             f"班次{sheet_data['active_shifts']}, "
                             f"质量{sheet_data['data_quality']}")
            
            report.append("")
        
        return "\n".join(report)

def main():
    """主函数 - 演示产能分析器的使用"""
    
    print("🚀 启动增强产能分析器...")
    
    analyzer = EnhancedCapacityAnalyzer()
    
    # 分析所有产线
    results = analyzer.analyze_all_production_lines()
    
    # 生成报告
    report = analyzer.generate_capacity_report()
    print(report)
    
    # 特定产线查询示例
    print("\n" + "=" * 60)
    print("特定产线查询示例")
    print("=" * 60)
    
    for line in ['F25', 'F29', 'F16']:
        print(f"\n🔍 查询{line}产线产能:")
        capacity_info = analyzer.get_line_capacity(line)
        print(f"  推荐产能: {capacity_info.get('recommended_capacity', 0)}")
        print(f"  置信度: {capacity_info.get('confidence', 0)}")
        print(f"  数据来源: {capacity_info.get('data_source', 'Unknown')}")

if __name__ == "__main__":
    main()