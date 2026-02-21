"""
补充缺失的历史数据脚本
功能：
1. 分析缺失日期的模式
2. 从CNN API获取缺失日期的数据
3. 验证数据完整性
"""
import time
from datetime import datetime, timedelta
from src.database import FngDatabase
from src.fetcher import FngFetcher


def analyze_missing_dates(db: FngDatabase, days: int = 90):
    """分析缺失日期的模式"""
    today = datetime.now()
    start_date = today - timedelta(days=days)
    
    records = db.get_records_by_range(
        start_date.strftime('%Y-%m-%d'),
        today.strftime('%Y-%m-%d')
    )
    
    record_dates = set(r.date for r in records)
    
    missing_dates = []
    missing_weekends = []
    missing_weekdays = []
    
    current = start_date
    while current <= today:
        date_str = current.strftime('%Y-%m-%d')
        if date_str not in record_dates:
            missing_dates.append(date_str)
            # 判断是否为周末
            if current.weekday() >= 5:  # 5=周六, 6=周日
                missing_weekends.append(date_str)
            else:
                missing_weekdays.append(date_str)
        current += timedelta(days=1)
    
    return {
        'total_missing': len(missing_dates),
        'weekend_missing': len(missing_weekends),
        'weekday_missing': len(missing_weekdays),
        'weekend_dates': missing_weekends,
        'weekday_dates': missing_weekdays,
        'all_missing': missing_dates
    }


def fetch_missing_data(fetcher: FngFetcher, dates: list, batch_size: int = 7):
    """
    批量获取缺失日期的数据
    CNN API一次可能返回多天数据，所以批量请求
    """
    if not dates:
        return 0, "无缺失数据"
    
    total_inserted = 0
    errors = []
    
    # 按日期排序
    sorted_dates = sorted(dates)
    
    print(f"\n开始获取 {len(sorted_dates)} 个日期的数据...")
    
    # 批量请求：每次请求一个起始日期，API会返回该日期之后的数据
    for i, date in enumerate(sorted_dates):
        print(f"进度: {i+1}/{len(sorted_dates)} - 尝试获取 {date} 的数据", end='\r')
        
        try:
            api_data = fetcher._fetch_from_api(date)
            records = fetcher._parse_api_data(api_data)
            
            if records:
                inserted = fetcher.db.insert_records(records)
                total_inserted += inserted
            
            # 避免请求过快
            time.sleep(1)
            
        except Exception as e:
            errors.append(f"{date}: {str(e)}")
    
    print()  # 换行
    
    status = f"成功插入 {total_inserted} 条记录"
    if errors:
        status += f", {len(errors)} 个日期获取失败"
    
    return total_inserted, status


def main():
    print("=" * 60)
    print("恐慌贪婪指数数据补充脚本")
    print("=" * 60)
    
    db = FngDatabase()
    fetcher = FngFetcher()
    
    # 1. 分析缺失数据
    print("\n[1] 分析缺失数据...")
    analysis = analyze_missing_dates(db, days=90)
    
    print(f"\n缺失数据统计:")
    print(f"  总缺失天数: {analysis['total_missing']}")
    print(f"  周末缺失: {analysis['weekend_missing']} (正常，股市休市)")
    print(f"  工作日缺失: {analysis['weekday_missing']} (需要补充)")
    
    if analysis['weekday_missing'] > 0:
        print(f"\n缺失的工作日:")
        for date in analysis['weekday_dates'][:10]:
            dt = datetime.strptime(date, '%Y-%m-%d')
            weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            print(f"  {date} ({weekday_names[dt.weekday()]})")
        if analysis['weekday_missing'] > 10:
            print(f"  ... 还有 {analysis['weekday_missing'] - 10} 个")
    
    # 2. 获取缺失的工作日数据
    if analysis['weekday_missing'] > 0:
        print(f"\n[2] 开始获取缺失的工作日数据...")
        inserted, status = fetch_missing_data(fetcher, analysis['weekday_dates'])
        print(f"\n结果: {status}")
    else:
        print("\n[2] 无需补充，工作日数据完整")
    
    # 3. 再次验证
    print("\n[3] 验证数据完整性...")
    analysis_after = analyze_missing_dates(db, days=90)
    
    print(f"\n验证结果:")
    print(f"  补充前工作日缺失: {analysis['weekday_missing']}")
    print(f"  补充后工作日缺失: {analysis_after['weekday_missing']}")
    print(f"  改善: {analysis['weekday_missing'] - analysis_after['weekday_missing']} 条")
    
    # 4. 显示最新统计
    stats = db.get_stats()
    print(f"\n数据库统计:")
    print(f"  总记录数: {stats.get('total_records', 0)}")
    print(f"  最新日期: {stats.get('latest_date', '无')}")
    
    print("\n" + "=" * 60)
    print("数据补充完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
