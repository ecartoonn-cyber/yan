# 恐慌贪婪指数追踪器

[![Last Update](https://img.shields.io/static/v1?label=Last+Update&message=2026-02-20&color=blue)]()
[![Records](https://img.shields.io/static/v1?label=Records&message=3818&color=green)]()
[![Status](https://img.shields.io/static/v1?label=Status&message=Fear&color=orange)]()

自动追踪CNN恐慌贪婪指数，支持定时更新、可视化和历史版本管理。

## 项目简介

本项目自动从CNN获取恐慌贪婪指数(Fear & Greed Index)数据，提供：

- **自动数据获取**：定时从CNN API获取最新数据
- **本地数据缓存**：SQLite数据库存储，支持增量更新
- **可视化图表**：自动生成趋势图和分布统计
- **版本历史管理**：Git自动提交 + 时间戳备份

## 数据统计

### 当前状态

| 指标 | 数值 |
|------|------|
| 最新日期 | 2026-02-20 |
| **最新指数** | **38** |
| 情绪状态 | 恐惧 (Fear) |
| 7日均值 | 48.51 |
| 30日均值 | 48.51 |

### 历史极值

| 指标 | 数值 | 日期 |
|------|------|------|
| 历史最低 | 1 | 2011-08-08 |
| 历史最高 | 97 | 2020-01-02 |
| 历史均值 | 48.51 | - |

### 分布统计

| 情绪状态 | 天数 | 占比 |
|----------|------|------|
| 极度恐惧 (0-25) | 582 | 15.2% |
| 恐惧 (25-45) | 971 | 25.4% |
| 中性 (45-55) | 648 | 17.0% |
| 贪婪 (55-75) | 1217 | 31.9% |
| 极度贪婪 (75-100) | 400 | 10.5% |

**数据总量**: 3818 条记录


## 趋势图表

### 近30日趋势

![趋势图](output\charts\trend_30d.png)

### 历史分布

![分布图](output\charts\distribution.png)

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

- 最近更新: 2026-02-20 11:51:28
- 数据范围: - 至 2026-02-20

## 许可证

MIT License

---

*本文档由自动化系统生成，每次数据更新后自动刷新。*
