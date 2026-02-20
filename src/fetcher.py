"""
数据获取模块 - 从CNN API获取恐慌贪婪指数数据
"""
import time
from datetime import datetime, timedelta
from typing import Optional

import requests
from fake_useragent import UserAgent

from .config import (
    CNN_API_URL,
    API_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from .database import FngDatabase, FngRecord


class FngFetcher:
    """数据获取器"""
    
    def __init__(self, db: FngDatabase = None):
        self.db = db or FngDatabase()
        self.ua = UserAgent()
    
    def _get_headers(self) -> dict:
        """生成请求头"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "application/json",
        }
    
    def _fetch_from_api(self, start_date: str) -> Optional[dict]:
        """从API获取数据，带重试机制"""
        url = f"{CNN_API_URL}{start_date}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    timeout=API_TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"API请求失败: {e}")
        return None
    
    def _parse_api_data(self, data: dict) -> list[FngRecord]:
        """解析API返回数据"""
        records = []
        
        if not data or "fear_and_greed_historical" not in data:
            return records
        
        historical_data = data["fear_and_greed_historical"].get("data", [])
        
        for item in historical_data:
            timestamp = item.get("x")
            value = item.get("y")
            
            if timestamp and value is not None:
                # 转换时间戳
                dt = datetime.fromtimestamp(timestamp / 1000)
                date_str = dt.strftime("%Y-%m-%d")
                
                # 校验数据范围
                if 0 <= value <= 100:
                    records.append(FngRecord(date=date_str, value=int(value)))
        
        return records
    
    def fetch_incremental(self, days_back: int = 30) -> tuple[int, str]:
        """
        增量获取数据
        返回: (新增记录数, 状态消息)
        """
        # 获取数据库最新日期
        latest_date = self.db.get_latest_date()
        
        if latest_date:
            # 从最新日期的下一天开始获取
            start_date = latest_date + timedelta(days=1)
        else:
            # 数据库为空，获取过去days_back天的数据
            start_date = datetime.now() - timedelta(days=days_back)
        
        start_str = start_date.strftime("%Y-%m-%d")
        
        # 如果start_date是今天或未来，无需更新
        if start_date.date() >= datetime.now().date():
            return 0, "数据已是最新"
        
        # 获取数据
        api_data = self._fetch_from_api(start_str)
        records = self._parse_api_data(api_data)
        
        if not records:
            return 0, "API返回无新数据"
        
        # 写入数据库
        inserted = self.db.insert_records(records)
        
        return inserted, f"成功获取 {inserted} 条记录"
    
    def fetch_full(self, start_date: str = "2011-01-01") -> tuple[int, str]:
        """
        全量获取数据（用于初始化）
        返回: (记录数, 状态消息)
        """
        api_data = self._fetch_from_api(start_date)
        records = self._parse_api_data(api_data)
        
        if not records:
            return 0, "API返回无数据"
        
        inserted = self.db.insert_records(records)
        return inserted, f"成功获取 {inserted} 条记录"
    
    def import_from_csv(self, csv_path: str) -> tuple[int, str]:
        """从CSV文件导入历史数据"""
        import pandas as pd
        
        try:
            df = pd.read_csv(csv_path)
            
            # 查找包含日期和数值的列
            date_col = None
            value_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if "date" in col_lower:
                    date_col = col
                if "fear" in col_lower or "greed" in col_lower or "value" in col_lower:
                    value_col = col
            
            if not date_col or not value_col:
                return 0, "CSV格式不匹配"
            
            records = []
            for _, row in df.iterrows():
                date_val = row[date_col]
                value_val = row[value_col]
                
                if pd.isna(date_val) or pd.isna(value_val):
                    continue
                
                # 处理日期
                if isinstance(date_val, str):
                    date_str = date_val[:10]
                else:
                    date_str = str(date_val)[:10]
                
                # 处理数值
                try:
                    value = int(float(value_val))
                    if 0 <= value <= 100:
                        records.append(FngRecord(date=date_str, value=value))
                except (ValueError, TypeError):
                    continue
            
            inserted = self.db.insert_records(records)
            return inserted, f"成功导入 {inserted} 条记录"
            
        except Exception as e:
            return 0, f"导入失败: {e}"


def update_data() -> dict:
    """
    执行数据更新（供外部调用）
    返回更新结果
    """
    fetcher = FngFetcher()
    count, message = fetcher.fetch_incremental()
    
    stats = fetcher.db.get_stats()
    
    return {
        "records_updated": count,
        "message": message,
        "latest_date": stats.get("latest_date"),
        "latest_value": stats.get("latest_value"),
        "total_records": stats.get("total_records"),
    }


# 全局实例
fetcher = FngFetcher()
