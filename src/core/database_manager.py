"""
数据库管理器 - SQLite数据库操作
Database Manager - SQLite database operations for event persistence
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging


class DatabaseManager:
    """
    SQLite数据库管理器
    负责事件数据的持久化存储和查询
    """
    
    def __init__(self, db_path: str = "data/events.db", logger=None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
            logger: 日志记录器
        """
        self.db_path = db_path
        self.logger = logger or logging.getLogger(__name__)
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建事件表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT UNIQUE NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT NOT NULL,  -- JSON格式存储事件详细数据
                        created_time TEXT NOT NULL,
                        updated_time TEXT NOT NULL,
                        status TEXT DEFAULT 'active'  -- active, deleted, processed
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_time ON events(created_time)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON events(status)')
                
                # 创建LCA产能损失详细表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lca_capacity_loss (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL,
                        affect_date TEXT NOT NULL,
                        affect_shift TEXT NOT NULL,
                        production_line TEXT NOT NULL,
                        product_pn TEXT,
                        loss_hours REAL NOT NULL,
                        lost_quantity REAL,
                        remaining_repair_time REAL,
                        daily_plan_quantity REAL,  -- 从Daily Plan获取的计划产量
                        created_time TEXT NOT NULL,
                        FOREIGN KEY (event_id) REFERENCES events(event_id)
                    )
                ''')
                
                # 创建事件处理结果表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS event_processing_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL,
                        processing_step TEXT NOT NULL,
                        result_data TEXT NOT NULL,  -- JSON格式存储处理结果
                        processing_time TEXT NOT NULL,
                        status TEXT NOT NULL,  -- success, failed, pending
                        FOREIGN KEY (event_id) REFERENCES events(event_id)
                    )
                ''')
                
                conn.commit()
                self.logger.info("数据库初始化完成")
                
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    def create_event(self, event_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        创建新事件
        
        Args:
            event_data: 事件数据字典
            
        Returns:
            (是否成功, 消息)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 生成事件ID
                cursor.execute("SELECT COUNT(*) FROM events")
                count = cursor.fetchone()[0]
                event_id = f"EVT_{count + 1:04d}"
                
                # 添加元数据
                current_time = datetime.now().isoformat()
                event_data["事件ID"] = event_id
                event_data["创建时间"] = current_time
                
                # 插入主事件表
                cursor.execute('''
                    INSERT INTO events (event_id, event_type, event_data, created_time, updated_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    event_id,
                    event_data.get("事件类型", "Unknown"),
                    json.dumps(event_data, ensure_ascii=False),
                    current_time,
                    current_time
                ))
                
                # 如果是LCA产能损失事件，插入详细表
                if event_data.get("事件类型") == "LCA产能损失":
                    cursor.execute('''
                        INSERT INTO lca_capacity_loss (
                            event_id, affect_date, affect_shift, production_line,
                            product_pn, loss_hours, lost_quantity, remaining_repair_time,
                            created_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event_id,
                        event_data.get("选择影响日期"),
                        event_data.get("选择影响班次"),
                        event_data.get("选择产线"),
                        event_data.get("确认产品PN"),
                        event_data.get("输入XX小时", 0),
                        event_data.get("已经损失的产量"),
                        event_data.get("剩余修理时间"),
                        current_time
                    ))
                
                conn.commit()
                self.logger.info(f"事件创建成功: {event_id}")
                return True, f"事件 {event_id} 创建成功"
                
        except Exception as e:
            error_msg = f"创建事件失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_all_events(self, status: str = "active") -> List[Dict[str, Any]]:
        """
        获取所有事件
        
        Args:
            status: 事件状态筛选
            
        Returns:
            事件列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT event_data FROM events 
                    WHERE status = ? 
                    ORDER BY created_time DESC
                ''', (status,))
                
                events = []
                for row in cursor.fetchall():
                    event_data = json.loads(row[0])
                    events.append(event_data)
                
                return events
                
        except Exception as e:
            self.logger.error(f"获取事件列表失败: {str(e)}")
            return []
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            事件数据或None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT event_data FROM events 
                    WHERE event_id = ? AND status = 'active'
                ''', (event_id,))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None
                
        except Exception as e:
            self.logger.error(f"获取事件失败: {str(e)}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """
        删除事件（软删除）
        
        Args:
            event_id: 事件ID
            
        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE events SET status = 'deleted', updated_time = ?
                    WHERE event_id = ?
                ''', (datetime.now().isoformat(), event_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"事件已删除: {event_id}")
                    return True
                else:
                    self.logger.warning(f"事件不存在: {event_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"删除事件失败: {str(e)}")
            return False
    
    def get_lca_events_by_criteria(self, date: str = None, line: str = None, 
                                  product_pn: str = None) -> List[Dict[str, Any]]:
        """
        根据条件查询LCA产能损失事件
        
        Args:
            date: 影响日期
            line: 生产线
            product_pn: 产品PN
            
        Returns:
            匹配的LCA事件列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                conditions = ["e.status = 'active'", "e.event_type = 'LCA产能损失'"]
                params = []
                
                if date:
                    conditions.append("l.affect_date = ?")
                    params.append(date)
                if line:
                    conditions.append("l.production_line = ?")
                    params.append(line)
                if product_pn:
                    conditions.append("l.product_pn = ?")
                    params.append(product_pn)
                
                query = f'''
                    SELECT e.event_data, l.* FROM events e
                    JOIN lca_capacity_loss l ON e.event_id = l.event_id
                    WHERE {" AND ".join(conditions)}
                    ORDER BY e.created_time DESC
                '''
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    event_data = json.loads(row[0])
                    # 添加详细数据
                    event_data["_lca_details"] = {
                        "id": row[1],
                        "event_id": row[2],
                        "affect_date": row[3],
                        "affect_shift": row[4],
                        "production_line": row[5],
                        "product_pn": row[6],
                        "loss_hours": row[7],
                        "lost_quantity": row[8],
                        "remaining_repair_time": row[9],
                        "daily_plan_quantity": row[10],
                        "created_time": row[11]
                    }
                    results.append(event_data)
                
                return results
                
        except Exception as e:
            self.logger.error(f"查询LCA事件失败: {str(e)}")
            return []
    
    def update_lca_daily_plan_quantity(self, event_id: str, quantity: float) -> bool:
        """
        更新LCA事件的Daily Plan产量数据
        
        Args:
            event_id: 事件ID
            quantity: 计划产量
            
        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE lca_capacity_loss 
                    SET daily_plan_quantity = ?
                    WHERE event_id = ?
                ''', (quantity, event_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"更新LCA产量数据失败: {str(e)}")
            return False
    
    def save_processing_result(self, event_id: str, step: str, result_data: Dict[str, Any], 
                              status: str = "success") -> bool:
        """
        保存事件处理结果
        
        Args:
            event_id: 事件ID
            step: 处理步骤
            result_data: 结果数据
            status: 处理状态
            
        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO event_processing_results 
                    (event_id, processing_step, result_data, processing_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    event_id,
                    step,
                    json.dumps(result_data, ensure_ascii=False),
                    datetime.now().isoformat(),
                    status
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"保存处理结果失败: {str(e)}")
            return False
    
    def export_to_excel(self, file_path: str) -> bool:
        """
        导出事件数据到Excel
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            是否成功
        """
        try:
            import pandas as pd
            
            events = self.get_all_events()
            if not events:
                return False
            
            df = pd.DataFrame(events)
            df.to_excel(file_path, index=False)
            self.logger.info(f"数据已导出到: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 总事件数
                cursor.execute("SELECT COUNT(*) FROM events WHERE status = 'active'")
                stats["total_events"] = cursor.fetchone()[0]
                
                # 按类型统计
                cursor.execute('''
                    SELECT event_type, COUNT(*) FROM events 
                    WHERE status = 'active' 
                    GROUP BY event_type
                ''')
                stats["events_by_type"] = dict(cursor.fetchall())
                
                # LCA事件数
                cursor.execute("SELECT COUNT(*) FROM lca_capacity_loss")
                stats["lca_events"] = cursor.fetchone()[0]
                
                # 数据库文件大小
                if os.path.exists(self.db_path):
                    stats["db_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
                
                return stats
                
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {}