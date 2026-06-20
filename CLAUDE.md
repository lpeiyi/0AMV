# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

0AMV（活跃市值指数）= SMA(成交额, 10, 2)，基于中证全指 000985 成交金额计算。Python 3.12 + PySide6 桌面浮窗 + CLI 分析。

- `analyze.py` — CLI 波段分析
- `total_return.py` — CLI 总收益对比
- `band_monitor.py` — 入口：QApp + 系统托盘 + 配置持久化
- `band_panel.py` — 透明浮窗 UI（状态栏 + 股票表 + 历史波段）
- `band_engine.py` — 0AMV 计算 + 波段检测 + 指数/ETF 收益查询
- `band_stocks.py` — Sina 实时行情 + normalize_code + QTableModel
- `band_settings.py` — 5 选项卡设置对话框

`StockWidget_repo/` 是独立的参考项目（UI 模式和设置布局的灵感来源），`data/` 存放共享数据池 CSV。

## 核心算法

**0AMV**: `SMA_t = (2 × amount_t + 8 × SMA_{t-1}) / 10`，参数 N=10, M=2

**波段规则**（v1）:
- 入场：0AMV 日涨跌幅 ≥ +3.0%
- 退出：从区间峰值回撤 ≤ -7.0%
- 合并：间隔 ≤10 天的相邻波段合并
- 从 2022-01-01 开始检测，过滤 2023-01-01 起的波段

## 数据源

| 数据 | API | 列名 |
|------|-----|------|
| 000985/000001 | `ak.stock_zh_index_hist_csindex` | 中文（日期/收盘/成交金额） |
| sz399006/sz159915 | `ak.stock_zh_index_daily_tx` | 英文（date/close） |
| 实时行情 | `hq.sinajs.cn` (Sina) | CSV parts[0..33] |

CSIndex 列名必须用中文，QQ/Sina 列名必须用英文。所有 API 内置 3-5 次重试。159915 QQ 数据为未复权。

## 运行命令

```powershell
# Python 3.12 路径（非标准安装）
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"

# CLI 分析
& $py v1_trail7_merge10\analyze.py
& $py v1_trail7_merge10\total_return.py

# GUI 浮窗
& $py v1_trail7_merge10\band_monitor.py
```

## 打包

```powershell
pyinstaller --noconsole --onefile --name BandMonitor --distpath .\dist `
  --add-data "$(python -c "import akshare;print(akshare.__file__.replace('__init__.py','file_fold')" );akshare\file_fold" `
  band_monitor.py
```

akshare 的 `file_fold/calendar.json` 不会自动打包，缺则启动报错 `FileNotFoundError`。

## 已知坑点

- **中文路径**：PowerShell 传参时中文路径会乱码。优先用 `workdir` 参数或 VBS 方式启动
- **WA_TranslucentBackground + 背景不透明度 100%**：QLabel 必须设显式 `background: rgba(...)`，否则文字渲染错误
- **波段收益回退**：159915/上证指数等 QQ 数据不可用时，自动回退到 0AMV 计算收益
- **新增算法**：复制 `v1_trail7_merge10/` → `v2_xxx/` 改 `analyze.py`，保持接口统一
- **Sina API timeout=3s**，无备用源
- 所有 widget 代码在同一目录（`v1_trail7_merge10/`），无包结构，import 用 `from band_x import Y`
