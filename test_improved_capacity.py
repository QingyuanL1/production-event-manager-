#!/usr/bin/env python3
"""
测试改进的产能逻辑
Test Improved Capacity Logic

验证新的产能获取方法在实际数据上的表现
"""

import sys
import os
sys.path.append('src')

from core.data_loader import DataLoader
from improved_capacity_logic import get_enhanced_line_capacity, get_simple_line_capacity
import logging

def setup_logger():
    """设置日志"""
    logger = logging.getLogger('CapacityTest')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def test_capacity_analysis():
    """测试产能分析功能"""
    
    print("🚀 开始测试改进的产能分析逻辑...")
    print("=" * 80)
    
    # 初始化数据加载器和日志
    data_loader = DataLoader()
    logger = setup_logger()
    
    # 加载必要的数据
    print("\n📊 加载数据...")
    success, msg, _ = data_loader.load_data("HSA Daily Plan")
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")
        return
    
    success, msg, _ = data_loader.load_data("HSA Capacity")
    if success:
        print(f"✅ {msg}")
    else:
        print(f"⚠️ {msg}")
    
    # 测试多个产线
    test_lines = ['F25', 'F29', 'F16', 'F17', 'F27', 'F35']
    
    print(f"\n🔍 测试产线: {test_lines}")
    print("=" * 80)
    
    results = {}
    
    for line in test_lines:
        print(f"\n📍 测试 {line} 产线")
        print("-" * 50)
        
        try:
            # 获取详细分析结果
            detailed_result = get_enhanced_line_capacity(data_loader, logger, line)
            
            # 获取简化结果 (用于现有代码集成)
            simple_capacity = get_simple_line_capacity(data_loader, logger, line)
            
            results[line] = {
                'detailed': detailed_result,
                'simple': simple_capacity
            }
            
            # 显示结果
            print(f"📊 详细分析结果:")
            print(f"   推荐产能: {detailed_result['capacity']:.0f}")
            print(f"   数据来源: {detailed_result['source']}")
            print(f"   置信度: {detailed_result['confidence']:.2f}")
            print(f"   最大观测: {detailed_result['max_observed']:.0f}")
            print(f"   产能范围: {detailed_result['capacity_range']}")
            print(f"   支持产品: {detailed_result['products']}")
            
            print(f"🔧 简化结果 (用于现有代码): {simple_capacity:.0f}")
            
        except Exception as e:
            print(f"❌ 测试 {line} 失败: {e}")
            results[line] = {'error': str(e)}
    
    # 生成对比报告
    print("\n" + "=" * 80)
    print("📋 产能分析对比报告")
    print("=" * 80)
    
    # 默认产能值 (当前系统使用的)
    current_defaults = {
        "F16": 6000,
        "F25": 9000,
        "F29": 8000,
        "F17": 8000,
        "F27": 8000,
        "F35": 8000
    }
    
    print(f"{'产线':<6} {'当前默认':<10} {'新推荐':<10} {'置信度':<8} {'数据来源':<30}")
    print("-" * 80)
    
    for line in test_lines:
        if line in results and 'detailed' in results[line]:
            result = results[line]['detailed']
            current_default = current_defaults.get(line, 8000)
            new_capacity = result['capacity']
            confidence = result['confidence']
            source = result['source'][:28] + "..." if len(result['source']) > 30 else result['source']
            
            print(f"{line:<6} {current_default:<10.0f} {new_capacity:<10.0f} {confidence:<8.2f} {source:<30}")
            
            # 标记重大差异
            diff_ratio = abs(new_capacity - current_default) / current_default
            if diff_ratio > 0.3:  # 差异超过30%
                if new_capacity > current_default:
                    print(f"       ⬆️ 比默认值高 {diff_ratio*100:.1f}%")
                else:
                    print(f"       ⬇️ 比默认值低 {diff_ratio*100:.1f}%")
        else:
            print(f"{line:<6} {'N/A':<10} {'错误':<10} {'0.00':<8} {'分析失败':<30}")
    
    print("\n💡 关键发现:")
    for line in test_lines:
        if line in results and 'detailed' in results[line]:
            result = results[line]['detailed']
            current_default = current_defaults.get(line, 8000)
            diff_ratio = abs(result['capacity'] - current_default) / current_default
            
            if diff_ratio > 0.3:
                if result['confidence'] > 0.5:
                    status = "🔴 建议更新"
                else:
                    status = "🟡 需要更多数据"
                
                print(f"   {line}: {status} (差异{diff_ratio*100:.1f}%, 置信度{result['confidence']:.2f})")
    
    return results

def test_integration_compatibility():
    """测试与现有代码的集成兼容性"""
    
    print("\n" + "=" * 80)
    print("🔧 测试与现有代码的集成兼容性")
    print("=" * 80)
    
    data_loader = DataLoader()
    logger = setup_logger()
    
    # 加载数据
    data_loader.load_data("HSA Daily Plan")
    data_loader.load_data("HSA Capacity")
    
    # 模拟现有代码的调用方式
    test_lines = ['F25', 'F29', 'F16']
    
    for line in test_lines:
        try:
            # 这是现有代码中会使用的调用方式
            capacity = get_simple_line_capacity(data_loader, logger, line)
            print(f"✅ {line} 产能: {capacity:.0f} (集成测试通过)")
        except Exception as e:
            print(f"❌ {line} 集成测试失败: {e}")

if __name__ == "__main__":
    # 运行测试
    test_results = test_capacity_analysis()
    test_integration_compatibility()
    
    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)
    print("📝 使用说明:")
    print("1. 将 improved_capacity_logic.py 复制到 src/core/ 目录")
    print("2. 在 lca_capacity_loss.py 中导入: from .improved_capacity_logic import get_simple_line_capacity")
    print("3. 替换 _get_line_capacity 方法的实现")
    print("4. 享受更准确的产能分析! 🎉")