"""
定时调度模块 - 后台定时任务
"""
import signal
import sys
import threading
from datetime import datetime
from typing import Callable, Optional

import schedule

from .config import UPDATE_INTERVAL_HOURS, SCHEDULE_TIME
from .fetcher import FngFetcher
from .doc_generator import DocGenerator
from .version_control import VersionControl
from .database import FngDatabase


class FngScheduler:
    """定时调度器"""
    
    def __init__(self):
        self.fetcher = FngFetcher()
        self.doc_generator = DocGenerator()
        self.version_control = VersionControl()
        self.db = FngDatabase()
        self._running = False
        self._stop_event = threading.Event()
    
    def run_update(self) -> dict:
        """
        执行完整更新流程
        1. 获取新数据
        2. 生成图表和文档
        3. 创建版本记录
        """
        results = {
            "started_at": datetime.now().isoformat(),
            "data_update": None,
            "doc_generated": False,
            "version_created": None,
            "error": None,
        }
        
        try:
            # 1. 获取数据
            count, message = self.fetcher.fetch_incremental()
            results["data_update"] = {
                "records": count,
                "message": message,
            }
            
            # 2. 生成文档
            readme_path = self.doc_generator.generate_readme()
            results["doc_generated"] = readme_path is not None
            
            # 3. 创建版本记录
            from pathlib import Path
            files_to_backup = [
                Path(readme_path) if readme_path else None,
                self.db.db_path,
            ]
            files_to_backup = [f for f in files_to_backup if f and f.exists()]
            
            version_result = self.version_control.create_version(files_to_backup)
            results["version_created"] = version_result
            
        except Exception as e:
            results["error"] = str(e)
        
        results["finished_at"] = datetime.now().isoformat()
        return results
    
    def start(self, interval_hours: int = None, schedule_time: str = None):
        """
        启动定时调度
        
        Args:
            interval_hours: 间隔小时数
            schedule_time: 定时执行时间 (HH:MM)
        """
        self._running = True
        
        # 设置定时任务
        if schedule_time:
            # 每天固定时间执行
            schedule.every().day.at(schedule_time).do(self._safe_run_update)
        else:
            # 按间隔执行
            interval = interval_hours or UPDATE_INTERVAL_HOURS
            schedule.every(interval).hours.do(self._safe_run_update)
        
        # 立即执行一次
        print(f"[{datetime.now()}] 启动调度器，首次运行...")
        self._safe_run_update()
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 运行循环
        while self._running and not self._stop_event.is_set():
            schedule.run_pending()
            self._stop_event.wait(timeout=60)
    
    def _safe_run_update(self):
        """安全执行更新（捕获异常）"""
        try:
            print(f"[{datetime.now()}] 开始更新...")
            result = self.run_update()
            
            if result.get("error"):
                print(f"[{datetime.now()}] 更新出错: {result['error']}")
            else:
                data_update = result.get("data_update", {})
                print(f"[{datetime.now()}] 更新完成: {data_update.get('message', '-')}")
                
        except Exception as e:
            print(f"[{datetime.now()}] 更新异常: {e}")
    
    def stop(self):
        """停止调度器"""
        self._running = False
        self._stop_event.set()
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print(f"\n[{datetime.now()}] 收到停止信号，正在退出...")
        self.stop()
        sys.exit(0)


def run_once() -> dict:
    """单次执行更新"""
    scheduler = FngScheduler()
    return scheduler.run_update()


def run_scheduled(interval_hours: int = None, schedule_time: str = None):
    """启动定时调度"""
    scheduler = FngScheduler()
    scheduler.start(interval_hours, schedule_time)


# 全局实例
scheduler = FngScheduler()
