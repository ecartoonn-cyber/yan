#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恐慌贪婪指数数据导出脚本
=========================
功能：
1. 从CNN API获取恐慌贪婪指数历史数据
2. 筛选2021年1月1日至今的数据
3. 按指定格式保存为CSV文件（date, value, rating）
4. 包含错误处理和数据验证

数据来源：CNN Money Fear & Greed Index API
"""

import csv
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from fake_useragent import UserAgent


# ==================== 配置参数 ====================
START_DATE = "2021-01-01"  # 数据起始日期
OUTPUT_FILE = "fear_greed_index_2021.csv"  # 输出文件名
DB_FILE = "fng_data.db"  # 本地数据库文件
CNN_API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
API_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5


# ==================== 恐慌贪婪等级定义 ====================
def get_rating(value: int) -> str:
    """
    根据指数值返回情绪等级
    
    Args:
        value: 恐慌贪婪指数值 (0-100)
    
    Returns:
        情绪等级字符串
    """
    if value < 25:
        return "Extreme Fear"
    elif value < 45:
        return "Fear"
    elif value < 55:
        return "Neutral"
    elif value < 75:
        return "Greed"
    else:
        return "Extreme Greed"


# ==================== 数据获取类 ====================
class FearGreedDataFetcher:
    """恐慌贪婪指数数据获取器"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
    
    def _get_headers(self) -> dict:
        """生成请求头"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "application/json",
            "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        }
    
    def fetch_from_api(self, start_date: str) -> Optional[list]:
        """
        从CNN API获取历史数据
        
        Args:
            start_date: 起始日期 (YYYY-MM-DD格式)
        
        Returns:
            数据列表，格式为 [(date, value, rating), ...]
        """
        url = f"{CNN_API_URL}{start_date}"
        
        for attempt in range(MAX_RETRIES):
            try:
                print(f"[API] 正在请求 {url} ...")
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=API_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                return self._parse_api_data(data)
                
            except requests.RequestException as e:
                print(f"[警告] 请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    print(f"[等待] {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"[错误] API请求最终失败: {e}")
                    return None
    
    def _parse_api_data(self, data: dict) -> list:
        """
        解析API返回的JSON数据
        
        Args:
            data: API返回的JSON数据
        
        Returns:
            解析后的数据列表
        """
        records = []
        
        if not data or "fear_and_greed_historical" not in data:
            print("[警告] API返回数据格式异常")
            return records
        
        historical_data = data["fear_and_greed_historical"].get("data", [])
        
        # 筛选起始日期
        start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
        
        for item in historical_data:
            timestamp = item.get("x")
            value = item.get("y")
            
            if timestamp is None or value is None:
                continue
            
            # 转换时间戳为日期
            dt = datetime.fromtimestamp(timestamp / 1000)
            
            # 筛选2021年及之后的数据
            if dt < start_dt:
                continue
            
            date_str = dt.strftime("%Y-%m-%d")
            
            # 验证数据范围
            if not (0 <= value <= 100):
                print(f"[警告] 数据异常: {date_str} = {value} (超出范围)")
                continue
            
            rating = get_rating(int(value))
            records.append((date_str, int(value), rating))
        
        return records
    
    def fetch_from_database(self) -> Optional[list]:
        """
        从本地SQLite数据库获取数据
        
        Returns:
            数据列表，格式为 [(date, value, rating), ...]
        """
        db_path = Path(DB_FILE)
        
        if not db_path.exists():
            print(f"[信息] 本地数据库不存在: {DB_FILE}")
            return None
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT date, value FROM fng_data
                WHERE date >= ?
                ORDER BY date ASC
            ''', (START_DATE,))
            
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for date_str, value in rows:
                rating = get_rating(value)
                records.append((date_str, value, rating))
            
            print(f"[数据库] 成功获取 {len(records)} 条记录")
            return records
            
        except sqlite3.Error as e:
            print(f"[错误] 数据库查询失败: {e}")
            return None
    
    def close(self):
        """关闭会话"""
        self.session.close()


# ==================== CSV导出函数 ====================
def save_to_csv(data: list, filename: str) -> bool:
    """
    将数据保存为CSV文件
    
    Args:
        data: 数据列表，格式为 [(date, value, rating), ...]
        filename: 输出文件名
    
    Returns:
        是否成功保存
    """
    if not data:
        print("[错误] 无数据可保存")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow(['date', 'value', 'rating'])
            
            # 写入数据（按日期升序排列）
            for row in sorted(data, key=lambda x: x[0]):
                writer.writerow(row)
        
        print(f"[成功] 数据已保存到: {filename}")
        print(f"[统计] 共 {len(data)} 条记录")
        
        # 显示数据范围
        dates = [row[0] for row in data]
        print(f"[范围] {min(dates)} 至 {max(dates)}")
        
        return True
        
    except IOError as e:
        print(f"[错误] 文件写入失败: {e}")
        return False


# ==================== 主函数 ====================
def main():
    """主函数"""
    print("=" * 60)
    print("恐慌贪婪指数数据导出脚本")
    print("=" * 60)
    print(f"数据起始日期: {START_DATE}")
    print(f"输出文件: {OUTPUT_FILE}")
    print("-" * 60)
    
    fetcher = FearGreedDataFetcher()
    all_data = []
    
    # 方案1: 尝试从本地数据库获取
    print("\n[步骤1] 尝试从本地数据库获取数据...")
    db_data = fetcher.fetch_from_database()
    
    if db_data:
        all_data = db_data
        print(f"[信息] 从数据库获取到 {len(db_data)} 条记录")
    else:
        # 方案2: 从API获取数据
        print("\n[步骤2] 本地数据库无数据，从CNN API获取...")
        api_data = fetcher.fetch_from_api(START_DATE)
        
        if api_data:
            all_data = api_data
            print(f"[信息] 从API获取到 {len(api_data)} 条记录")
        else:
            print("[错误] 无法获取数据")
            fetcher.close()
            return
    
    # 数据验证
    print("\n[步骤3] 验证数据完整性...")
    if not all_data:
        print("[错误] 无有效数据")
        fetcher.close()
        return
    
    # 统计各等级分布
    rating_counts = {}
    for _, _, rating in all_data:
        rating_counts[rating] = rating_counts.get(rating, 0) + 1
    
    print("[统计] 情绪等级分布:")
    for rating, count in sorted(rating_counts.items()):
        percentage = (count / len(all_data)) * 100
        print(f"  {rating}: {count} ({percentage:.1f}%)")
    
    # 保存为CSV
    print("\n[步骤4] 保存数据到CSV文件...")
    save_to_csv(all_data, OUTPUT_FILE)
    
    fetcher.close()
    
    print("\n" + "=" * 60)
    print("数据导出完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
