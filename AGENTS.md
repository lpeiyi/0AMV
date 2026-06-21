# AGENTS.md

## 项目

0AMV（活跃市值指数）= SMA(成交额, 10, 2)。Python 3.12 + PySide6 桌面浮窗 + CLI 分析。
`APP_NAME = "0AMVMonitor"`，缓存目录 `%APPDATA%\0AMVMonitor\`。

## 目录

```
v1_trail7_merge10/            核心算法 + 浮窗 widget（所有文件在此）
├── band_monitor.py           入口：QApp + 系统托盘 + 配置持久化
├── band_panel.py             透明浮窗 UI（状态栏 + 股票表 + 历史波段）
├── band_engine.py            0AMV 计算 + 波段检测 + 指数/ETF 收益查询
├── band_stocks.py            Sina 实时行情 + normalize_code + QTableModel
├── band_settings.py          6 选项卡设置对话框
├── analyze.py                CLI 波段分析
├── total_return.py           CLI 总收益对比
├── 0AMV.ico                  exe 图标
├── tests/                     测试套件
│   ├── run_tests.py          统一测试运行器
│   ├── gen_report.py         生成 Markdown 测试报告
│   ├── tests_comprehensive.py 综合单元测试（62项，含 normalize_code/Engine/Model/Settings/Panel/Config/Cache/CLI/信号）
│   ├── tests_integration.py   SettingsDialog 集成测试（25项，含表格CRUD/勾选/名称刷新/Apply/策略参数联动/缓存目录/忙碌锁）
│   └── test_report.md         最新测试报告
├── dist/0AMVMonitor.exe      打包 exe（80MB）
StockWidget_repo/             PySide6 股票浮窗参考项目（UI 模式借鉴）
data/                         共享数据池 CSV
experiments/                  跨算法探索脚本
```

- 所有 widget 代码在同一目录，无包结构。import 用 `from band_x import Y`。
- `band_settings.py` 有 6 个 tab：自选列表(0) → 显示数据(1) → 外观(2) → 策略参数(3) → 波段(4, `insertTab`) → 常规(5)

## 核心算法

**0AMV**: `SMA_t = (M × amount_t + (N-M) × SMA_{t-1}) / N`，默认 N=10, M=2
- 基于中证全指 **000985** 成交金额，**必须**获取
- 其他数据不可用时自动回退到 0AMV 算波收益

**波段检测 (`_detect`)**:
- 从 2022-01-01 扫描，过滤 2023-01-01 后入场
- 入场：0AMV 日涨跌幅 ≥ entry（默认 +3.0%）
- 退出：从区间峰值回撤 ≤ exit_dd（默认 -7.0%）
- 合并：相邻波段间隔 ≤ merge_gap（默认 10天）
- `bear_market_start` 在数据刷新和策略参数修改时都更新（`_do_refresh_strategy` 中 `_detect` 后立即设置）

**指数数据预加载 (`ensure_index_data`)**:
- `BandEngine.ensure_index_data()` 在 `_update_band_returns` 和 `_do_refresh_strategy` 中调用
- 轻量抓取：单次尝试，无重试，静默失败
- 抓取 sh000001（CSIndex）、sz399006（QQ）、sz159915（QQ）三个指数/ETF
- 确保股票表的波收益总是显示各品种独立值，不会全部回退到 159915 的收益

## 数据源

| 数据 | API | 列名 |
|------|-----|------|
| 000985/000001 | `ak.stock_zh_index_hist_csindex` | 中文（日期/收盘/成交金额） |
| sz399006/sz159915 | `ak.stock_zh_index_daily_tx` | 英文（date/close） |
| 个股/ETF 历史 | `ak.stock_zh_a_hist` / `ak.fund_etf_hist_em` | 中文（收盘） |
| 实时行情 | `hq.sinajs.cn` (Sina) | CSV parts[0..33] |
| 指数 | `ak.stock_zh_index_daily_tx` | 英文（close） |

- CSIndex 列名必须用中文，QQ/Sina 列名必须用英文
- Sina API timeout=3s，无备用源
- `stock_zh_index_daily_tx` 忽略 start/end_date 返回全量数据，需 searchsorted 手动过滤
- East Money `stock_zh_a_hist` 只对 6xxxxx 设 market_id=1，5xxxxx ETF 用 `fund_etf_hist_em` 后备
- `ensure_index_data()` 在策略刷新/波收益计算前预加载 sh/sz/etf，单次尝试静默失败

## 运行

```powershell
# Python 3.12 路径（非标准安装）
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"

# CLI 分析
& $py v1_trail7_merge10\analyze.py
& $py v1_trail7_merge10\total_return.py

# GUI 浮窗（或双击 dist/0AMVMonitor.exe）
& $py v1_trail7_merge10\band_monitor.py

# 测试
& $py v1_trail7_merge10\tests\run_tests.py
& $py v1_trail7_merge10\tests\gen_report.py    # 生成 test_report.md
```

## 打包

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$akshare_folder = & $py -c "import akshare;print(akshare.__file__.replace('__init__.py','file_fold'))" 2>$null
$ico = "G:\products\指南针股票app活跃市值指数0AMV\v1_trail7_merge10\0AMV.ico"
& $py -m PyInstaller --noconsole --onefile --name 0AMVMonitor --icon "$ico" `
  --distpath v1_trail7_merge10\dist `
  --add-data "${akshare_folder};akshare\file_fold" `
  v1_trail7_merge10\band_monitor.py
```

坑：akshare 的 `file_fold/calendar.json` 不会自动打包，缺则启动报错 `FileNotFoundError`。

## 已知坑点

- **中文路径**：PowerShell 传参中文路径乱码，用 `workdir` 参数或 VBS 启动绕过
- **`WA_TranslucentBackground` + 背景不透明度 100%**：QLabel 必须设显式 `background: rgba(...)`，否则文字渲染错误
- **波段收益回退**：QQ/East Money 数据不可用时自动回退到 0AMV 计算
- **搜索时序退**：`stock_zh_index_daily_tx` 返回全量数据，用 `searchsorted(side='right')-1` 定位正确日期
- **`_stock_band_cache`** 持久化 pickle v4，启动时检测版本 < 4 则清空
- **两阶段启动**：先显示临时值 → QTimer 延迟计算未缓存的品种波收益
- **新增算法**：复制 `v1_trail7_merge10/` → `v2_xxx/` 改 `analyze.py`，保持接口统一
