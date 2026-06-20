# AGENTS.md

## 项目

0AMV（活跃市值指数）≈ SMA(成交额, 10, 2)。Python 3.12 + PySide6 桌面浮窗 + CLI 分析。

## 目录

```
AGENTS.md
v1_trail7_merge10/            ← 核心算法 + 浮窗 widget（所有文件在此）
├── analyze.py                CLI 波段分析
├── total_return.py           CLI 总收益对比
├── band_monitor.py           入口：QApp + 系统托盘 + 配置持久化
├── band_panel.py             透明浮窗 UI（状态栏 + 股票表 + 历史波段）
├── band_engine.py            0AMV 计算 + 波段检测 + 指数/ETF 收益查询
├── band_stocks.py            Sina 实时行情 + normaliz_code + QTableModel
├── band_settings.py          5 选项卡设置对话框
└── dist/BandMonitor.exe      打包 exe（74MB）
StockWidget_repo/             参考项目：PySide6 股票浮窗（UI 模式借鉴）
data/                         共享数据池（算法 v1 CSV）
experiments/                  跨算法探索脚本
```

- 所有 widget 代码在同一目录（`v1_trail7_merge10/`），无包结构。import 用 `from band_x import Y`。
- `StockWidget_repo/` 是独立参考项目，`band_*.py` 的 UI 模式和设置布局源自它。

## 核心算法（v1_trail7_merge10）

**0AMV**: `SMA_t = (2 × amount_t + 8 × SMA_{t-1}) / 10`，基于中证全指 000985 成交金额

**波段规则**:
- 入场：0AMV 日涨跌幅 ≥ +3.0%
- 退出：从区间峰值回撤 ≤ -7.0%
- 合并：间隔 ≤10 天的相邻波段合并
- 结果：20 个波段（2023 起），159915 总收益 **+183.49%**（vs 持有 +87.32%）

## 数据源

| 数据 | API | 列名 |
|------|-----|------|
| 000985/000001 | `ak.stock_zh_index_hist_csindex` | **中文**（日期/收盘/成交金额） |
| sz399006/sz159915 | `ak.stock_zh_index_daily_tx` | **英文**（date/close） |
| 实时行情 | `hq.sinajs.cn`（Sina） | CSV parts[0..33] |

- 000985 **必须**获取（算法依赖），其它数据不可用时自动回退到 0AMV 算波收益
- CSIndex 列名**必须用中文**，QQ/Sina 列名**必须用英文**
- QQ DNS (`proxy.finance.qq.com`) 间歇性故障，内置 5 次重试
- Sina API timeout=3s，无备用源
- 159915 QQ 数据为**未复权**，涨幅低于前复权数据

## 运行

```powershell
# Python 3.12 路径（非标准安装）
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"

# CLI 分析
& $py v1_trail7_merge10\analyze.py
& $py v1_trail7_merge10\total_return.py

# GUI 浮窗（或双击 dist/BandMonitor.exe）
& $py v1_trail7_merge10\band_monitor.py
```

**路径含中文**：PowerShell 传参时中文路径会乱码。用 `workdir` 参数或 VBS 绕过：

```powershell
# 方案 A：用 workdir
& $py band_monitor.py -WorkDir "G:\products\指南针股票app活跃市值指数0AMV\v1_trail7_merge10"

# 方案 B：VBS 启动（生产环境使用）
$tf = "$env:TEMP\launch.vbs"
Set-Content -Path $tf -Value 'CreateObject("WScript.Shell").Run """<exe_full_path>""", 1, False' -Encoding Default -NoNewline
Start-Process -FilePath wscript.exe -ArgumentList "`"$tf`"" -WindowStyle Hidden
```

## 打包

```powershell
# akshare 需要 --add-data 打包 calendar.json
pyinstaller --noconsole --onefile --name BandMonitor --distpath .\dist \
  --add-data "$(python -c "import akshare;print(akshare.__file__.replace('__init__.py','file_fold')" );akshare\file_fold" \
  band_monitor.py
```

坑：akshare 的 `file_fold/calendar.json` 不会自动打包，缺则启动报错 `FileNotFoundError`。

## 已知坑点

- **中文路径**：所有文件操作、`os.chdir`、`subprocess` 在包含中文的路径下可能异常，优先用 `workdir`
- **`WA_TranslucentBackground` + 背景不透明度 100%**：QLabel 必须设显式 `background: rgba(...)`，否则文字渲染错误
- **波段收益回退**：159915/上证指数等 QQ 数据不可用时，引擎自动回退到 0AMV 计算收益
- **新增算法**：复制 `v1_trail7_merge10/` → `v2_xxx/` 改 `analyze.py`，保持接口统一
