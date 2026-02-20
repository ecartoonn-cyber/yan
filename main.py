#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恐慌贪婪指数自动化更新系统 - 主入口

使用方式:
    python main.py --mode once        # 单次执行
    python main.py --mode auto        # 定时运行
    python main.py --mode manual      # 手动触发
    python main.py --init             # 初始化数据库
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from src.config import ensure_dirs
from src.database import FngDatabase
from src.fetcher import FngFetcher
from src.doc_generator import DocGenerator
from src.scheduler import FngScheduler
from src.version_control import VersionControl


def init_database():
    """初始化数据库并导入历史数据"""
    print("=" * 50)
    print("初始化数据库")
    print("=" * 50)
    
    ensure_dirs()
    db = FngDatabase()
    
    # 检查是否已有数据
    count = db.record_count()
    if count > 0:
        print(f"数据库已有 {count} 条记录")
        choice = input("是否重新导入? (y/N): ").strip().lower()
        if choice != 'y':
            return
    
    # 导入现有CSV数据
    csv_files = [
        Path("fear-greed.csv"),
        Path("all_fng_csv.csv"),
    ]
    
    fetcher = FngFetcher(db)
    
    for csv_file in csv_files:
        if csv_file.exists():
            print(f"正在导入 {csv_file}...")
            imported, message = fetcher.import_from_csv(str(csv_file))
            print(f"  {message}")
    
    # 从API获取最新数据
    print("从API获取最新数据...")
    imported, message = fetcher.fetch_incremental(days_back=365)
    print(f"  {message}")
    
    # 显示统计
    stats = db.get_stats()
    print(f"\n数据库初始化完成:")
    print(f"  总记录数: {stats['total_records']}")
    print(f"  数据范围: {stats.get('earliest_date', '-')} 至 {stats['latest_date']}")
    print(f"  最新指数: {stats['latest_value']}")


def run_once(no_git: bool = False):
    """单次执行更新"""
    print("=" * 50)
    print(f"单次更新 - {datetime.now()}")
    print("=" * 50)
    
    # 更新数据
    fetcher = FngFetcher()
    count, message = fetcher.fetch_incremental()
    print(f"数据更新: {message}")
    
    # 生成文档
    doc_gen = DocGenerator()
    readme_path = doc_gen.generate_readme()
    print(f"文档生成: {readme_path}")
    
    # 版本控制
    if not no_git:
        vc = VersionControl()
        db = FngDatabase()
        
        files_to_backup = [
            Path(readme_path),
            db.db_path,
        ]
        files_to_backup = [f for f in files_to_backup if f.exists()]
        
        result = vc.create_version(files_to_backup)
        print(f"备份文件: {len(result['backups'])} 个")
        print(f"Git提交: {'成功' if result['git_committed'] else '跳过'}")
    
    # 显示统计
    stats = fetcher.db.get_stats()
    print(f"\n当前状态:")
    print(f"  最新日期: {stats['latest_date']}")
    print(f"  最新指数: {stats['latest_value']}")
    print(f"  总记录数: {stats['total_records']}")


def run_auto(interval: int, no_git: bool = False):
    """启动定时调度"""
    print("=" * 50)
    print(f"启动定时调度 (间隔: {interval} 小时)")
    print("=" * 50)
    
    scheduler = FngScheduler()
    
    # 如果禁用Git，修改版本控制行为
    if no_git:
        original_create_version = scheduler.version_control.create_version
        def create_version_no_git(files, message=None):
            result = original_create_version(files, message)
            result["git_committed"] = False
            result["git_pushed"] = False
            return result
        scheduler.version_control.create_version = create_version_no_git
    
    scheduler.start(interval_hours=interval)


def run_manual():
    """手动触发更新（交互模式）"""
    print("=" * 50)
    print("手动更新模式")
    print("=" * 50)
    
    db = FngDatabase()
    stats = db.get_stats()
    
    print(f"\n当前数据状态:")
    print(f"  最新日期: {stats['latest_date']}")
    print(f"  最新指数: {stats['latest_value']}")
    print(f"  总记录数: {stats['total_records']}")
    
    choice = input("\n是否执行更新? (y/N): ").strip().lower()
    if choice == 'y':
        run_once()
    else:
        print("已取消")


def show_status():
    """显示当前状态"""
    db = FngDatabase()
    stats = db.get_stats()
    distribution = db.get_distribution()
    
    print("=" * 50)
    print("恐慌贪婪指数 - 当前状态")
    print("=" * 50)
    
    print(f"\n数据统计:")
    print(f"  最新日期: {stats['latest_date']}")
    print(f"  最新指数: {stats['latest_value']}")
    print(f"  7日均值: {stats['avg_7d']}")
    print(f"  30日均值: {stats['avg_30d']}")
    print(f"  历史最低: {stats['min_value']} ({stats['min_date']})")
    print(f"  历史最高: {stats['max_value']} ({stats['max_date']})")
    print(f"  总记录数: {stats['total_records']}")
    
    print(f"\n情绪分布:")
    for name, count in distribution.items():
        pct = count / stats['total_records'] * 100 if stats['total_records'] > 0 else 0
        print(f"  {name}: {count} ({pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="恐慌贪婪指数自动化更新系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --init           # 初始化数据库
  python main.py --mode once      # 单次执行
  python main.py --mode auto      # 定时运行（默认24小时）
  python main.py --mode auto --interval 12  # 12小时间隔
  python main.py --status         # 显示状态
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["once", "auto", "manual"],
        default="once",
        help="运行模式: once(单次), auto(定时), manual(手动)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=24,
        help="定时运行间隔(小时)，默认24"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="初始化数据库"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="显示当前状态"
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="禁用Git提交"
    )
    
    args = parser.parse_args()
    
    # 初始化
    if args.init:
        init_database()
        return
    
    # 显示状态
    if args.status:
        show_status()
        return
    
    # 运行模式
    if args.mode == "once":
        run_once(args.no_git)
    elif args.mode == "auto":
        run_auto(args.interval, args.no_git)
    elif args.mode == "manual":
        run_manual()


if __name__ == "__main__":
    main()
