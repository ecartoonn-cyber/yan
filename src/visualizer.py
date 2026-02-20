"""
可视化模块 - 生成图表和统计表格
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import (
    CHARTS_DIR,
    CHART_DPI,
    CHART_FIGSIZE,
    TREND_DAYS,
    get_level_info,
    ensure_dirs,
)
from .database import FngDatabase, FngRecord


class FngVisualizer:
    """可视化生成器"""
    
    def __init__(self, db: FngDatabase = None):
        self.db = db or FngDatabase()
        ensure_dirs()
    
    def generate_trend_chart(self, days: int = None, output_path: str = None) -> str:
        """生成趋势图"""
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import matplotlib.patches as mpatches
        
        days = days or TREND_DAYS
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        records = self.db.get_records_by_range(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        if not records:
            return None
        
        # 准备数据
        dates = [datetime.strptime(r.date, "%Y-%m-%d") for r in records]
        values = [r.value for r in records]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=CHART_FIGSIZE, facecolor='#F8FAFC')
        ax.set_facecolor('#F8FAFC')
        
        # 绘制填充区域
        ax.fill_between(dates, values, alpha=0.3, color='#2563EB')
        ax.plot(dates, values, color='#2563EB', linewidth=2, marker='o', markersize=4)
        
        # 添加参考线
        ax.axhline(y=25, color='#EF4444', linestyle='--', alpha=0.5, label='Extreme Fear')
        ax.axhline(y=75, color='#10B981', linestyle='--', alpha=0.5, label='Extreme Greed')
        ax.axhline(y=50, color='#6B7280', linestyle='-', alpha=0.3)
        
        # 设置样式
        ax.set_xlim(dates[0], dates[-1])
        ax.set_ylim(0, 100)
        ax.set_ylabel('Fear & Greed Index', fontsize=12, fontweight=500)
        ax.set_xlabel('Date', fontsize=12, fontweight=500)
        ax.set_title(f'Fear & Greed Index - {days} Day Trend', fontsize=14, fontweight=600, pad=15)
        
        # 日期格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.xticks(rotation=45, ha='right')
        
        # 网格
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # 添加色带区域
        zones = [
            (0, 25, '#FEE2E2', 'Extreme Fear'),
            (25, 45, '#FED7AA', 'Fear'),
            (45, 55, '#FEF3C7', 'Neutral'),
            (55, 75, '#D1FAE5', 'Greed'),
            (75, 100, '#A7F3D0', 'Extreme Greed'),
        ]
        
        for low, high, color, label in zones:
            ax.axhspan(low, high, alpha=0.1, color=color)
        
        # 图例
        legend_elements = [
            mpatches.Patch(facecolor='#FEE2E2', alpha=0.5, label='Extreme Fear (0-25)'),
            mpatches.Patch(facecolor='#FED7AA', alpha=0.5, label='Fear (25-45)'),
            mpatches.Patch(facecolor='#FEF3C7', alpha=0.5, label='Neutral (45-55)'),
            mpatches.Patch(facecolor='#D1FAE5', alpha=0.5, label='Greed (55-75)'),
            mpatches.Patch(facecolor='#A7F3D0', alpha=0.5, label='Extreme Greed (75-100)'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.9)
        
        plt.tight_layout()
        
        # 保存
        if output_path is None:
            output_path = CHARTS_DIR / f"trend_{days}d.png"
        else:
            output_path = Path(output_path)
        
        fig.savefig(output_path, dpi=CHART_DPI, bbox_inches='tight', facecolor='#F8FAFC')
        plt.close(fig)
        
        return str(output_path)
    
    def generate_distribution_chart(self, output_path: str = None) -> str:
        """生成分布直方图"""
        import matplotlib.pyplot as plt
        import numpy as np
        
        records = self.db.get_all_records()
        
        if not records:
            return None
        
        values = [r.value for r in records]
        
        fig, ax = plt.subplots(figsize=CHART_FIGSIZE, facecolor='#F8FAFC')
        ax.set_facecolor('#F8FAFC')
        
        # 创建直方图
        bins = np.arange(0, 105, 5)
        n, bins_out, patches = ax.hist(values, bins=bins, edgecolor='white', linewidth=0.5)
        
        # 为每个柱子上色
        colors = []
        for i in range(len(patches)):
            center = (bins_out[i] + bins_out[i+1]) / 2
            if center < 25:
                colors.append('#EF4444')
            elif center < 45:
                colors.append('#F97316')
            elif center < 55:
                colors.append('#F59E0B')
            elif center < 75:
                colors.append('#10B981')
            else:
                colors.append('#059669')
        
        for patch, color in zip(patches, colors):
            patch.set_facecolor(color)
        
        ax.set_xlabel('Fear & Greed Index', fontsize=12, fontweight=500)
        ax.set_ylabel('Frequency', fontsize=12, fontweight=500)
        ax.set_title('Fear & Greed Index Distribution', fontsize=14, fontweight=600, pad=15)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if output_path is None:
            output_path = CHARTS_DIR / "distribution.png"
        else:
            output_path = Path(output_path)
        
        fig.savefig(output_path, dpi=CHART_DPI, bbox_inches='tight', facecolor='#F8FAFC')
        plt.close(fig)
        
        return str(output_path)
    
    def generate_stats_table(self) -> str:
        """生成Markdown格式的统计表格"""
        stats = self.db.get_stats()
        distribution = self.db.get_distribution()
        
        if not stats.get("latest_value"):
            return ""
        
        latest_value = stats["latest_value"]
        level_cn, level_en, color = get_level_info(latest_value)
        
        # 主统计表
        table = """## 数据统计

### 当前状态

| 指标 | 数值 |
|------|------|
| 最新日期 | {latest_date} |
| **最新指数** | **{latest_value}** |
| 情绪状态 | {level_cn} ({level_en}) |
| 7日均值 | {avg_7d} |
| 30日均值 | {avg_30d} |

### 历史极值

| 指标 | 数值 | 日期 |
|------|------|------|
| 历史最低 | {min_value} | {min_date} |
| 历史最高 | {max_value} | {max_date} |
| 历史均值 | {avg_value} | - |

### 分布统计

| 情绪状态 | 天数 | 占比 |
|----------|------|------|
| 极度恐惧 (0-25) | {extreme_fear} | {extreme_fear_pct:.1%} |
| 恐惧 (25-45) | {fear} | {fear_pct:.1%} |
| 中性 (45-55) | {neutral} | {neutral_pct:.1%} |
| 贪婪 (55-75) | {greed} | {greed_pct:.1%} |
| 极度贪婪 (75-100) | {extreme_greed} | {extreme_greed_pct:.1%} |

**数据总量**: {total_records} 条记录
""".format(
            latest_date=stats.get("latest_date", "-"),
            latest_value=latest_value,
            level_cn=level_cn,
            level_en=level_en,
            avg_7d=stats.get("avg_7d", "-"),
            avg_30d=stats.get("avg_30d", "-"),
            min_value=stats.get("min_value", "-"),
            min_date=stats.get("min_date", "-"),
            max_value=stats.get("max_value", "-"),
            max_date=stats.get("max_date", "-"),
            avg_value=stats.get("avg_value", "-"),
            extreme_fear=distribution.get("极度恐惧", 0),
            extreme_fear_pct=distribution.get("极度恐惧", 0) / stats.get("total_records", 1),
            fear=distribution.get("恐惧", 0),
            fear_pct=distribution.get("恐惧", 0) / stats.get("total_records", 1),
            neutral=distribution.get("中性", 0),
            neutral_pct=distribution.get("中性", 0) / stats.get("total_records", 1),
            greed=distribution.get("贪婪", 0),
            greed_pct=distribution.get("贪婪", 0) / stats.get("total_records", 1),
            extreme_greed=distribution.get("极度贪婪", 0),
            extreme_greed_pct=distribution.get("极度贪婪", 0) / stats.get("total_records", 1),
            total_records=stats.get("total_records", 0),
        )
        
        return table
    
    def generate_all_charts(self) -> dict:
        """生成所有图表"""
        trend_path = self.generate_trend_chart()
        dist_path = self.generate_distribution_chart()
        
        return {
            "trend_chart": trend_path,
            "distribution_chart": dist_path,
            "stats_table": self.generate_stats_table(),
        }


# 全局实例
visualizer = FngVisualizer()
