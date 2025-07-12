# 日志包 (Logging Package)

这是生产排班系统的统一日志管理包，提供了完整的日志记录、分析和管理功能。

## 功能特性

### 🏭 专业日志管理
- **统一日志接口**: 为整个系统提供一致的日志记录方式
- **模块化设计**: 针对不同业务模块提供专用日志记录器
- **美观输出**: 支持emoji和颜色，提升日志可读性
- **文件记录**: 自动按日期分类保存日志文件

### 📊 日志分析
- **智能分析**: 自动统计日志级别分布、时间分布
- **错误追踪**: 快速定位系统错误和警告
- **事件查找**: 专门的LCA事件日志查找功能
- **报告生成**: 生成每日日志分析报告

### 🔧 灵活配置
- **多种输出**: 支持控制台输出和文件输出
- **日志级别**: 可配置的日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- **自定义格式**: 支持标准格式和结构化JSON格式

## 包结构

```
src/utils/logging/
├── __init__.py              # 包初始化
├── logger_factory.py        # 日志工厂类
├── log_formatter.py         # 日志格式化器
├── log_analyzer.py          # 日志分析器
├── integration.py           # 系统集成模块
├── example_usage.py         # 使用示例
└── README.md               # 说明文档
```

## 快速开始

### 1. 基本使用

```python
from src.utils.logging import LoggerFactory

# 获取LCA处理专用日志记录器
lca_logger = LoggerFactory.get_lca_logger()

# 记录日志
lca_logger.info("🚀 开始处理LCA产能损失事件")
lca_logger.warning("⚠️ DOS值低于阈值")
lca_logger.error("❌ 数据验证失败")
```

### 2. 系统集成

```python
from src.utils.logging.integration import setup_system_logging, log_lca_event_start

# 系统启动时设置日志
loggers = setup_system_logging()

# 在业务代码中使用
log_lca_event_start("EVT_001", event_data)
```

### 3. 日志分析

```python
from src.utils.logging import LogAnalyzer

# 创建分析器
analyzer = LogAnalyzer()

# 生成今日报告
report = analyzer.generate_daily_report()
print(report)

# 查找LCA事件
lca_events = analyzer.find_lca_events()
```

## 专用日志记录器

### LCA处理器日志
```python
lca_logger = LoggerFactory.get_lca_logger()
lca_logger.info("📊 DOS计算结果: 0.85天")
lca_logger.info("🔧 需要补偿产量: 261台")
```

### 系统运行日志
```python
system_logger = LoggerFactory.get_system_logger()
system_logger.info("✅ 系统启动成功")
system_logger.info("💾 数据库连接建立")
```

### 事件管理日志
```python
event_logger = LoggerFactory.get_event_logger()
event_logger.info("📝 创建新事件: EVT_001")
event_logger.info("🔍 事件验证通过")
```

### 数据加载日志
```python
data_logger = LoggerFactory.get_data_logger()
data_logger.info("📂 开始加载Daily Plan")
data_logger.info("✅ 数据加载完成: (307, 18)")
```

## 日志格式

### 控制台输出格式
```
[14:30:45] ℹ️ INFO: 🚀 开始处理LCA产能损失事件
[14:30:46] ⚠️ WARNING: DOS值低于阈值，需要补偿
[14:30:47] ❌ ERROR: 数据验证失败
```

### 文件日志格式
日志文件按模块和日期自动分类：
```
logs/
├── lca_processor_2025-07-12.log
├── system_2025-07-12.log
├── event_manager_2025-07-12.log
└── data_loader_2025-07-12.log
```

## 日志分析功能

### 每日报告
```python
analyzer = LogAnalyzer()
report = analyzer.generate_daily_report("2025-07-12")
```

输出示例：
```
📊 日志分析报告 - 2025-07-12
==================================================
📄 分析文件数: 4
📝 总日志条目: 156

📈 日志级别分布:
  INFO: 120
  WARNING: 25
  ERROR: 11

❌ 最近错误 (最多10条):
  [14:30:47] 数据验证失败
  [15:22:13] 数据库连接超时
```

### LCA事件追踪
```python
lca_events = analyzer.find_lca_events("2025-07-12")
print(f"今日处理了 {len(lca_events)} 个LCA事件")
```

## 与现有系统集成

### 在LCA处理器中使用

```python
# 在 lca_capacity_loss.py 中
from src.utils.logging.integration import get_module_logger

class LCACapacityLossProcessor:
    def __init__(self):
        self.logger = get_module_logger('lca_capacity_loss')
    
    def process_event(self, event_data):
        self.logger.info("🚀 开始LCA事件处理")
        # 处理逻辑...
        self.logger.info("✅ LCA事件处理完成")
```

### 在主界面中使用

```python
# 在 main_ui.py 中
from src.utils.logging.integration import log_system_startup, log_system_shutdown

class ProductionSchedulingSystem:
    def __init__(self):
        log_system_startup()
        # 初始化逻辑...
    
    def close(self):
        log_system_shutdown()
```

## 配置选项

### 自定义日志目录
```python
LoggerFactory.setup_log_directory("/custom/log/path")
```

### 自定义日志级别
```python
logger = LoggerFactory.get_logger(
    name="custom_module",
    level=logging.DEBUG,
    file_logging=True,
    console_logging=False
)
```

### 结构化日志输出
```python
from src.utils.logging.log_formatter import StructuredFormatter

# 创建JSON格式的日志
logger = LoggerFactory.get_logger("structured")
handler = logging.FileHandler("structured.log")
handler.setFormatter(StructuredFormatter())
logger.addHandler(handler)
```

## 最佳实践

### 1. 日志级别使用
- **DEBUG**: 详细的调试信息，仅在开发时使用
- **INFO**: 一般信息，记录系统运行状态
- **WARNING**: 警告信息，系统可以继续运行但需要注意
- **ERROR**: 错误信息，功能无法正常执行
- **CRITICAL**: 严重错误，系统可能无法继续运行

### 2. 日志消息格式
- 使用emoji使日志更直观：🚀 ✅ ⚠️ ❌ 📊 🔧
- 包含关键业务信息：事件ID、产线、班次、数值等
- 保持消息简洁但信息丰富

### 3. 性能考虑
- 数据加载日志默认不输出到控制台，减少噪音
- 大量调试信息使用DEBUG级别，生产环境可关闭
- 及时关闭日志文件句柄，避免资源泄露

## 故障排除

### 日志文件权限问题
```python
# 确保日志目录有写权限
import os
os.makedirs("logs", exist_ok=True)
os.chmod("logs", 0o755)
```

### 编码问题
```python
# 所有文件操作都使用UTF-8编码
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(log_content)
```

### 内存泄露
```python
# 程序结束时清理日志资源
LoggerFactory.close_all_loggers()
```

## 扩展功能

可以根据需要添加更多功能：
- 日志轮转（按大小或时间）
- 远程日志收集
- 日志告警机制
- 实时日志监控
- 日志可视化

---

## 技术支持

如有问题或建议，请参考：
- 使用示例：`example_usage.py`
- 集成指南：`integration.py`
- 系统日志：`logs/` 目录下的实际日志文件