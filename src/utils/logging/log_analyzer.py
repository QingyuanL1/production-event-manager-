"""
日志分析器
Log Analyzer

分析系统日志，提供统计信息和错误报告
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter


class LogAnalyzer:
    """日志分析器，用于分析和统计系统日志"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志分析器
        
        Args:
            log_dir: 日志目录路径
        """
        self.log_dir = log_dir
        self.log_pattern = re.compile(r'\[(\d{2}:\d{2}:\d{2})\]\s*(?:🔍|ℹ️|⚠️|❌|🚨)?\s*(\w+):\s*(.*)')
    
    def get_log_files(self, date_filter: Optional[str] = None) -> List[str]:
        """
        获取日志文件列表
        
        Args:
            date_filter: 日期过滤器 (YYYY-MM-DD格式)
            
        Returns:
            日志文件路径列表
        """
        if not os.path.exists(self.log_dir):
            return []
        
        log_files = []
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                if date_filter is None or date_filter in filename:
                    log_files.append(os.path.join(self.log_dir, filename))
        
        return sorted(log_files)
    
    def parse_log_file(self, file_path: str) -> List[Dict]:
        """
        解析单个日志文件
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            解析后的日志条目列表
        """
        log_entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    match = self.log_pattern.match(line)
                    if match:
                        time_str, level, message = match.groups()
                        
                        entry = {
                            'file': os.path.basename(file_path),
                            'line_number': line_num,
                            'time': time_str,
                            'level': level,
                            'message': message,
                            'raw_line': line
                        }
                        log_entries.append(entry)
        
        except Exception as e:
            print(f"Error parsing log file {file_path}: {e}")
        
        return log_entries
    
    def analyze_logs(self, date_filter: Optional[str] = None) -> Dict:
        """
        分析日志文件，生成统计报告
        
        Args:
            date_filter: 日期过滤器
            
        Returns:
            日志分析报告
        """
        log_files = self.get_log_files(date_filter)
        all_entries = []
        
        # 解析所有日志文件
        for file_path in log_files:
            entries = self.parse_log_file(file_path)
            all_entries.extend(entries)
        
        # 统计分析
        level_counts = Counter(entry['level'] for entry in all_entries)
        hourly_distribution = defaultdict(int)
        error_messages = []
        warning_messages = []
        
        for entry in all_entries:
            # 按小时分布统计
            hour = entry['time'][:2]
            hourly_distribution[hour] += 1
            
            # 收集错误和警告信息
            if entry['level'] == 'ERROR':
                error_messages.append(entry)
            elif entry['level'] == 'WARNING':
                warning_messages.append(entry)
        
        # 生成报告
        report = {
            'summary': {
                'total_entries': len(all_entries),
                'files_analyzed': len(log_files),
                'analysis_date': datetime.now().isoformat(),
                'date_filter': date_filter
            },
            'level_distribution': dict(level_counts),
            'hourly_distribution': dict(hourly_distribution),
            'errors': error_messages[-10:],  # 最近10个错误
            'warnings': warning_messages[-10:],  # 最近10个警告
            'files': [os.path.basename(f) for f in log_files]
        }
        
        return report
    
    def find_lca_events(self, date_filter: Optional[str] = None) -> List[Dict]:
        """
        查找LCA事件相关的日志条目
        
        Args:
            date_filter: 日期过滤器
            
        Returns:
            LCA事件日志列表
        """
        log_files = self.get_log_files(date_filter)
        lca_events = []
        
        lca_keywords = ['LCA', 'DOS', '产量损失', '补偿产量', '班次检查']
        
        for file_path in log_files:
            entries = self.parse_log_file(file_path)
            
            for entry in entries:
                if any(keyword in entry['message'] for keyword in lca_keywords):
                    lca_events.append(entry)
        
        return lca_events
    
    def generate_daily_report(self, date: Optional[str] = None) -> str:
        """
        生成每日日志报告
        
        Args:
            date: 日期 (YYYY-MM-DD格式)，默认为今天
            
        Returns:
            格式化的报告字符串
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        report = self.analyze_logs(date)
        
        report_lines = [
            f"📊 日志分析报告 - {date}",
            "=" * 50,
            f"📄 分析文件数: {report['summary']['files_analyzed']}",
            f"📝 总日志条目: {report['summary']['total_entries']}",
            "",
            "📈 日志级别分布:",
        ]
        
        for level, count in report['level_distribution'].items():
            report_lines.append(f"  {level}: {count}")
        
        if report['errors']:
            report_lines.extend([
                "",
                "❌ 最近错误 (最多10条):",
            ])
            for error in report['errors']:
                report_lines.append(f"  [{error['time']}] {error['message']}")
        
        if report['warnings']:
            report_lines.extend([
                "",
                "⚠️ 最近警告 (最多10条):",
            ])
            for warning in report['warnings']:
                report_lines.append(f"  [{warning['time']}] {warning['message']}")
        
        report_lines.extend([
            "",
            "📁 分析的日志文件:",
        ])
        for file_name in report['files']:
            report_lines.append(f"  - {file_name}")
        
        return "\n".join(report_lines)
    
    def export_report(self, output_file: str, date_filter: Optional[str] = None):
        """
        导出日志分析报告到文件
        
        Args:
            output_file: 输出文件路径
            date_filter: 日期过滤器
        """
        report = self.analyze_logs(date_filter)
        
        try:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"报告已导出到: {output_file}")
        except Exception as e:
            print(f"导出报告失败: {e}")