"""
文档生成模块 - 自动生成README.md
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import PROJECT_ROOT, CHARTS_DIR, get_level_info
from .database import FngDatabase
from .visualizer import FngVisualizer


class DocGenerator:
    """文档生成器"""
    
    def __init__(self, db: FngDatabase = None):
        self.db = db or FngDatabase()
        self.visualizer = FngVisualizer(self.db)
    
    def generate_readme(self, output_path: str = None) -> str:
        """生成完整的README.md"""
        stats = self.db.get_stats()
        
        # 获取当前情绪状态
        latest_value = stats.get("latest_value", 0)
        level_cn, level_en, _ = get_level_info(latest_value)
        
        # 生成图表
        charts = self.visualizer.generate_all_charts()
        
        # 计算相对路径（使用正斜杠，兼容GitHub）
        trend_rel = Path(charts["trend_chart"]).relative_to(PROJECT_ROOT).as_posix() if charts["trend_chart"] else ""
        dist_rel = Path(charts["distribution_chart"]).relative_to(PROJECT_ROOT).as_posix() if charts["distribution_chart"] else ""
        
        # 生成文档内容
        content = f"""# 恐慌贪婪指数追踪器

[![Last Update](https://img.shields.io/static/v1?label=Last+Update&message={stats.get("latest_date", "-")}&color=blue)]()
[![Records](https://img.shields.io/static/v1?label=Records&message={stats.get("total_records", 0)}&color=green)]()
[![Status](https://img.shields.io/static/v1?label=Status&message={level_en}&color={self._get_color(latest_value)})]()

自动追踪CNN恐慌贪婪指数，支持定时更新、可视化和历史版本管理。

## 项目简介

本项目自动从CNN获取恐慌贪婪指数(Fear & Greed Index)数据，提供：

- **自动数据获取**：定时从CNN API获取最新数据
- **本地数据缓存**：SQLite数据库存储，支持增量更新
- **可视化图表**：自动生成趋势图和分布统计
- **版本历史管理**：Git自动提交 + 时间戳备份

## 相关链接

- **CNN原始页面**: https://edition.cnn.com/markets/fear-and-greed
- **原始代码**: https://github.com/gman4774/Fear_and_Greed_Index

**本项目迭代说明**：

本项目基于 [gman4774/Fear_and_Greed_Index](https://github.com/gman4774/Fear_and_Greed_Index) 进行了以下迭代和增强：

- 📊 **本地数据缓存**：使用SQLite数据库存储历史数据，支持快速查询和增量更新
- 📈 **可视化图表**：自动生成趋势图和分布统计图，直观展示数据变化
- 🔄 **自动更新**：支持定时自动获取最新数据，无需手动运行
- 📝 **动态文档**：README.md自动更新，实时反映最新数据状态
- 🔒 **版本管理**：Git自动提交 + 时间戳备份双重保障历史版本
- 📦 **模块化设计**：代码结构清晰，易于维护和扩展

{charts["stats_table"]}

## 趋势图表

### 近30日趋势

![趋势图]({trend_rel})

### 历史分布

![分布图]({dist_rel})

## 安装与使用

### 环境要求

- Python 3.8+
- 依赖库见 `requirements.txt`

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用方式

**手动更新（单次执行）**

```bash
python main.py --mode once
```

**启动定时任务（后台运行）**

```bash
python main.py --mode auto
```

**手动触发更新**

```bash
python main.py --mode manual
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 运行模式: `once`(单次), `auto`(定时), `manual`(手动) | `once` |
| `--interval` | 定时间隔(小时) | 24 |
| `--no-git` | 禁用Git提交 | False |

## 项目结构

```
Fear_and_Greed_Index/
├── src/                    # 源代码模块
│   ├── config.py          # 配置常量
│   ├── database.py        # 数据库操作
│   ├── fetcher.py         # 数据获取
│   ├── visualizer.py      # 图表生成
│   ├── doc_generator.py   # 文档生成
│   ├── version_control.py # 版本管理
│   └── scheduler.py       # 定时调度
├── output/                 # 输出目录
│   ├── charts/            # 图表文件
│   └── backups/           # 历史备份
├── main.py                 # 主入口
├── fng_data.db            # SQLite数据库
├── requirements.txt        # 依赖清单
└── README.md              # 项目文档
```

## 数据来源

数据来自 [CNN Money Fear & Greed Index](https://edition.cnn.com/markets/fear-and-greed)。

恐慌贪婪指数是一个从0到100的指标，用于衡量市场情绪：

| 指数范围 | 情绪状态 |
|----------|----------|
| 0-25 | 极度恐惧 |
| 25-45 | 恐惧 |
| 45-55 | 中性 |
| 55-75 | 贪婪 |
| 75-100 | 极度贪婪 |

## 更新记录

- 最近更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 数据范围: {stats.get("earliest_date", "-")} 至 {stats.get("latest_date", "-")}

## 许可证

MIT License

---

*本文档由自动化系统生成，每次数据更新后自动刷新。*
"""
        
        # 写入文件
        if output_path is None:
            output_path = PROJECT_ROOT / "README.md"
        else:
            output_path = Path(output_path)
        
        output_path.write_text(content, encoding="utf-8")
        
        return str(output_path)
    
    def _get_color(self, value: int) -> str:
        """根据值返回徽章颜色"""
        if value < 25:
            return "red"
        elif value < 45:
            return "orange"
        elif value < 55:
            return "yellow"
        elif value < 75:
            return "green"
        else:
            return "brightgreen"


def generate_documentation() -> dict:
    """
    生成文档（供外部调用）
    返回生成结果
    """
    generator = DocGenerator()
    readme_path = generator.generate_readme()
    
    return {
        "readme_path": readme_path,
        "generated_at": datetime.now().isoformat(),
    }


# 全局实例
doc_generator = DocGenerator()
