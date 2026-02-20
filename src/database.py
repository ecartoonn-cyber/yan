"""
数据库模块 - SQLite数据存储和查询
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from .config import DB_PATH, ensure_dirs


@dataclass
class FngRecord:
    """恐慌贪婪指数记录"""
    date: str
    value: int
    
    def to_tuple(self) -> tuple:
        return (self.date, self.value)


class FngDatabase:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        ensure_dirs()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fng_data (
                    date TEXT PRIMARY KEY,
                    value INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date ON fng_data(date)
            """)
            conn.commit()
    
    def get_latest_date(self) -> Optional[datetime]:
        """获取数据库中最新日期"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(date) FROM fng_data WHERE value > 0")
            result = cursor.fetchone()[0]
            if result:
                return datetime.strptime(result, "%Y-%m-%d")
            return None
    
    def get_earliest_date(self) -> Optional[datetime]:
        """获取数据库中最早日期"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(date) FROM fng_data WHERE value > 0")
            result = cursor.fetchone()[0]
            if result:
                return datetime.strptime(result, "%Y-%m-%d")
            return None
    
    def insert_records(self, records: list[FngRecord]) -> int:
        """批量插入记录，已存在则更新"""
        if not records:
            return 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO fng_data (date, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(date) DO UPDATE SET 
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, [r.to_tuple() for r in records])
            conn.commit()
            return cursor.rowcount
    
    def get_all_records(self) -> list[FngRecord]:
        """获取所有记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, value FROM fng_data 
                WHERE value > 0 
                ORDER BY date ASC
            """)
            return [FngRecord(date=row[0], value=row[1]) for row in cursor.fetchall()]
    
    def get_records_by_range(self, start_date: str, end_date: str) -> list[FngRecord]:
        """获取指定日期范围的记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, value FROM fng_data 
                WHERE date BETWEEN ? AND ? AND value > 0
                ORDER BY date ASC
            """, (start_date, end_date))
            return [FngRecord(date=row[0], value=row[1]) for row in cursor.fetchall()]
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 基本统计
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    AVG(value) as avg_value
                FROM fng_data WHERE value > 0
            """)
            row = cursor.fetchone()
            
            # 最新值
            cursor.execute("""
                SELECT date, value FROM fng_data 
                WHERE value > 0 
                ORDER BY date DESC LIMIT 1
            """)
            latest = cursor.fetchone()
            
            # 最近7日均值
            cursor.execute("""
                SELECT AVG(value) FROM fng_data 
                WHERE value > 0 
                ORDER BY date DESC LIMIT 7
            """)
            avg_7d = cursor.fetchone()[0]
            
            # 最近30日均值
            cursor.execute("""
                SELECT AVG(value) FROM fng_data 
                WHERE value > 0 
                ORDER BY date DESC LIMIT 30
            """)
            avg_30d = cursor.fetchone()[0]
            
            # 极值日期
            cursor.execute("""
                SELECT date FROM fng_data 
                WHERE value = (SELECT MIN(value) FROM fng_data WHERE value > 0)
                LIMIT 1
            """)
            min_date = cursor.fetchone()
            
            cursor.execute("""
                SELECT date FROM fng_data 
                WHERE value = (SELECT MAX(value) FROM fng_data)
                LIMIT 1
            """)
            max_date = cursor.fetchone()
            
            return {
                "total_records": row[0],
                "min_value": row[1],
                "max_value": row[2],
                "avg_value": round(row[3], 2) if row[3] else 0,
                "latest_date": latest[0] if latest else None,
                "latest_value": latest[1] if latest else None,
                "avg_7d": round(avg_7d, 2) if avg_7d else 0,
                "avg_30d": round(avg_30d, 2) if avg_30d else 0,
                "min_date": min_date[0] if min_date else None,
                "max_date": max_date[0] if max_date else None,
            }
    
    def get_distribution(self) -> dict:
        """获取恐慌贪婪分布统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 按等级分组
            ranges = [
                ("极度恐惧", 0, 25),
                ("恐惧", 25, 45),
                ("中性", 45, 55),
                ("贪婪", 55, 75),
                ("极度贪婪", 75, 101),
            ]
            
            distribution = {}
            for name, low, high in ranges:
                cursor.execute("""
                    SELECT COUNT(*) FROM fng_data 
                    WHERE value >= ? AND value < ? AND value > 0
                """, (low, high))
                distribution[name] = cursor.fetchone()[0]
            
            return distribution
    
    def record_count(self) -> int:
        """获取记录总数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fng_data WHERE value > 0")
            return cursor.fetchone()[0]


# 全局实例
db = FngDatabase()
