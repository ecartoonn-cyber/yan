"""
配置模块 - 定义所有常量和路径
"""
from pathlib import Path
from datetime import time

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# CNN API 配置
CNN_API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
API_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒

# 数据库配置
DB_PATH = PROJECT_ROOT / "fng_data.db"

# 输出目录
CHARTS_DIR = PROJECT_ROOT / "output" / "charts"
BACKUPS_DIR = PROJECT_ROOT / "output" / "backups"

# 定时配置
UPDATE_INTERVAL_HOURS = 24
SCHEDULE_TIME = time(hour=6, minute=0)  # 每天6:00更新

# 备份配置
MAX_BACKUPS = 10

# 可视化配置
CHART_DPI = 150
CHART_FIGSIZE = (12, 6)
TREND_DAYS = 30  # 趋势图显示天数

# 恐惧贪婪等级定义
FNG_LEVELS = {
    (0, 25): ("极度恐惧", "Extreme Fear", "#EF4444"),
    (25, 45): ("恐惧", "Fear", "#F97316"),
    (45, 55): ("中性", "Neutral", "#F59E0B"),
    (55, 75): ("贪婪", "Greed", "#10B981"),
    (75, 100): ("极度贪婪", "Extreme Greed", "#059669"),
}


def get_level_info(value: float) -> tuple:
    """获取恐慌贪婪等级信息"""
    for (low, high), info in FNG_LEVELS.items():
        if low <= value < high:
            return info
    return FNG_LEVELS[(75, 100)]


def ensure_dirs():
    """确保所有必需目录存在"""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
