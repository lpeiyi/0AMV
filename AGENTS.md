# AGENTS.md

## 项目

0AMV（活跃市值指数）= SMA(成交额, N=10, M=2)。Python 3.12 + PySide6 桌面浮窗 + CLI 分析。
`APP_NAME = "0AMVMonitor"`，缓存目录 `%APPDATA%\0AMVMonitor\`。

所有 widget 在 `v1_trail7_merge10/`，无包结构，import 用 `from band_x import Y`。

## 入口

| 文件 | 用途 |
|------|------|
| `band_monitor.py` | GUI 入口：QApp + 系统托盘 + 配置持久化 |
| `analyze.py` | CLI 波段分析 |
| `total_return.py` | CLI 总收益对比 |
| `band_settings.py` | 6 选项卡设置对话框（0自选列表/1显示数据/2外观/3策略参数/4波段/5常规） |

## 运行

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py v1_trail7_merge10\analyze.py              # CLI 波段分析
& $py v1_trail7_merge10\total_return.py          # CLI 总收益对比
& $py v1_trail7_merge10\band_monitor.py          # GUI 浮窗
& $py v1_trail7_merge10\tests\run_tests.py       # 全部测试（93项：68综合+25集成）
& $py v1_trail7_merge10\tests\gen_report.py      # 生成 test_report.md
```

## 核心算法

**0AMV**: `SMA_t = (M×amount_t + (N-M)×SMA_{t-1})/N`，默认 N=10, M=2。基于 000985 成交金额，必须获取。

**波段检测 (`_detect`)**:
- 扫描 2022-01-01 起，过滤 2023-01-01 后入场
- 入场：0AMV 日涨跌幅 ≥ entry（默认 +3.0%）
- 退出：从区间峰值回撤 ≤ exit_dd（默认 -7.0%）
- 合并：相邻波段间隔 ≤ merge_gap（默认 10天）
- `bear_market_start` = 最后波段结束日，刷新和策略参数修改时更新

**`get_status()` 返回**: `{"in_band", "oamv_value", "oamv_pct", "last_date", "bands": [{"start","end","days"}], "band_start", "band_days", "peak_gain", "drawdown", "exit_threshold"}`

## 指数数据预加载

`engine.ensure_index_data()` 单次尝试静默失败。抓取 sh000001（CSIndex）、sz399006（QQ）、sz159915（QQ）。在波收益计算和策略刷新前调用，确保各品种独立收益不回退到 159915。

## 数据源

| 数据 | API | 列名 |
|------|-----|------|
| 000985/000001 | `ak.stock_zh_index_hist_csindex` | 中文（日期/收盘/成交金额） |
| sz399006/sz159915 | `ak.stock_zh_index_daily_tx` | 英文（date/close） |
| 个股历史 | `ak.stock_zh_a_hist`（6xxxxx 设 `market_id=1`） | 中文 |
| ETF 后备 | `ak.fund_etf_hist_em`（5xxxxx 用） | 中文 |
| 实时行情 | `hq.sinajs.cn` (Sina) timeout=3s | CSV parts[0..33] |

- CSIndex 用中文列名，QQ/Sina 用英文列名
- `stock_zh_index_daily_tx` 忽略 start/end_date 返回全量数据，用 `searchsorted(side='right')-1` 定位日期
- `fetch_all()`: 5次重试（sleep 5/3s）；`refresh()`: 3次重试（sleep 5s）；`ensure_index_data()`: 无重试

## `normalize_code` 规则

| 输入前缀 | 映射 |
|----------|------|
| `sh`, `sz`, `bj` 已有 | 保留 |
| 6xxxxx / 5xxxxx / 90xxxx | `sh` |
| 0xxxxx / 3xxxxx / 2xxxxx / 1xxxxx | `sz` |
| 8xxxxx / 4xxxxx / 92xxxx | `bj` |
| 空/None/非法 | `None` |

## `_stock_band_cache`

持久化 pickle v4。启动时检测版本 < 4 则清空。两阶段启动：先显示临时值 → `QTimer.singleShot` 延迟计算未缓存品种的波收益。

## 打包

```powershell
# 关键：akshare 的 file_fold/calendar.json 不会自动打包，缺则启动报错 FileNotFoundError
$ico = "v1_trail7_merge10\0AMV.ico"
$akshare_folder = & $py -c "import akshare;print(akshare.__file__.replace('__init__.py','file_fold'))" 2>$null
& $py -m PyInstaller --noconsole --onefile --name 0AMVMonitor --icon "$ico" `
  --distpath v1_trail7_merge10\dist `
  --add-data "${akshare_folder};akshare\file_fold" `
  v1_trail7_merge10\band_monitor.py
```

也可直接修改 `v1_trail7_merge10/0AMVMonitor.spec` 后执行 `& $py -m PyInstaller v1_trail7_merge10\0AMVMonitor.spec`。

## 已知坑点

- **中文路径**：PowerShell 传参乱码，用 `workdir` 或 VBS 启动绕过
- **`WA_TranslucentBackground` + 背景不透明度 100%**：QLabel 必须设显式 `background: rgba(...)`
- **Sina timeout=3s**，无备用源
- **波段收益回退**：QQ/East Money 数据不可用时自动回退到 0AMV 计算
- **新增算法**：复制 `v1_trail7_merge10/` → `v2_xxx/` 改 `analyze.py`

## 之前修复的坑点（已修复，供参考）

- **#1 QThread 吞异常**：`EngineWorker` 加了 `error` 信号，`fetch_all` 失败不再卡在"加载中…"，而是显示错误提示
- **#2 `get_status()` 无数据崩溃**：已加 `if self.df is None` guard，返回安全默认值
- **#7 end_date 硬编码**：`band_engine.py`、`analyze.py`、`total_return.py` 改用 `pd.Timestamp.now()` 动态计算
- **#8 `bg` 配置损坏崩溃**：改用 `.get()` 安全读取，异常时 fallback 到默认值
- **#6 `_collect_codes` 递归风险**：改为 `while` 循环

## 参考

`CLAUDE.md` 存在但注意其不准确处：实际为 6 选项卡（非 5），且重试策略非均匀 3-5 次（fetch_all=5次, refresh=3次, ensure_index_data=0次）。
