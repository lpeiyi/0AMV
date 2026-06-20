# StockWidget 代码分析

## 1. 项目概述

**技术栈**: Python 3.13 + PySide6 (Qt6) + requests  
**打包**: PyInstaller (-F -w) → 单文件 StockWidget.exe (49MB，含 UPX 压缩)  
**数据源**: 新浪财经 `hq.sinajs.cn` (GBK 编码, GET 请求)  
**配置存档**: `%APPDATA%\StockWidget\SW_config.json`

> 仓库副本内 `StockWidget.exe` 就是上述打包产物，Python 源码与其是一一对应的。

---

## 2. 文件依赖关系

```
StockWidget.py  ← 启动入口 (13行)
      │
      ▼
    App.py      ← 应用主控 (207行)
      │
      ├──────────────┐
      ▼              ▼
WidgetPanel.py   SettingPanel.py
  (871行)          (591行)
      │
      ▼
  Display.py
  (181行)
```

| 文件 | 行数 | 职责 |
|---|---|---|
| `StockWidget.py` | 13 | 入口，设置 AppUserModelID，启动 QApplication |
| `App.py` | 207 | 系统托盘、配置读写、设置面板管理、开机自启、图标切换 |
| `WidgetPanel.py` | 871 | **核心**：透明浮窗 UI、定时刷新、新浪行情解析、右键菜单、拖拽、快捷键 |
| `SettingPanel.py` | 591 | 设置对话框（4个 Tab 页）：自选列表管理、显示指标开关、外观、常规 |
| `Display.py` | 181 | 表格数据模型 `SimpleTableModel` + 当日 K 线绘制委托 `KLineDelegate` |
| `README.md` | 134 | 项目说明、功能介绍、运行/打包指令 |

---

## 3. 数据流与核心流程

### 3.1 启动流程 (App.py)

```python
QApplication.__init__()
  → 从 SW_config.json 加载配置
  → 创建 FloatLabel (WidgetPanel.py)  → 解析配置构建浮窗
  → 创建 QSystemTrayIcon (托盘)
  → 显示浮窗
  → 自动保存配置 (save_now)
```

### 3.2 定时刷新循环 (WidgetPanel.py)

```
QTimer (间隔 = refresh_seconds * 1000ms)
  ↓
_refresh_from_function()       ← 每次触发
  ↓
_get_price(checked_codes)      ← 调用新浪 API
  ↓
  ├─ requests.get(url)         ← https://hq.sinajs.cn/list=sh000001,sz000001,...
  │    (headers: Referer=finance.sina.com.cn, User-Agent=Mozilla/5.0)
  │    (timeout=3s)
  │
  └─ 解析响应文本 (GBK → str)
       │
       for each stock:
         line.split('="')      ← 拆出 code 和 CSV 数据
         parts.split(',')      ← 34 个字段
         │
         ├─ 字段映射 (见第4节)
         ├─ 颜色标记: delta(+1/0/-1), commi, avg, b1, s1
         ├─ 触及日高/日低 → "↑"/"↓" 箭头
         ├─ 触及买一/卖一价 → "<"/">" 标记
         └─ K线数据: {k: (今开, 现价, 最高, 最低, 昨收)}
       ↓
  ↓
_project_columns(full_rows, sign_data)   ← 按列可见性筛选 + 渲染
  ↓
  ├─ 从 ALL_HEADERS 过滤已启用的列
  ├─ 设置 SimpleTableModel 数据
  ├─ 设置 KLineDelegate (如 "K线" 列可见)
  └─ _fit_to_contents()        ← 自适应列宽/行高
```

### 3.3 配置变更→保存路径

```
设置面板 / 右键菜单 / 鼠标移动
  ↓
set_xxx() 方法 (WidgetPanel.py)
  ↓
_notify_change()
  ↓
App.save_now()
  ↓
json.dump → %APPDATA%/StockWidget/SW_config.json
```

---

## 4. 数据字段映射（新浪财经协议）

新浪 `hq.sinajs.cn` 返回格式：
```
var hq_str_sh000001="上证指数,3186...,...";
```

`parts = line.split('="')[1].split(',')` 共 34 段：

| 索引 | 字段名 | 类型 | 说明 |
|---|---|---|---|
| 0 | `name` | str | 股票名称 |
| 1 | `opening_price` | float | 今开 |
| 2 | `prev_close` | float | 昨收 |
| 3 | `current_price` | float | 现价（实时） |
| 4 | `high_price` | float | 当日最高 |
| 5 | `low_price` | float | 当日最低 |
| 6 | `first_pur` | float | 买一价 |
| 7 | `first_sell` | float | 卖一价 |
| 8 | `deals_vol` | float | 成交量（股） |
| 9 | `deals_amt` | float | 成交额（元） |
| 10-18 (步长2) | `purchaser` | int[] | 买盘5档，股数 |
| 11-19 (步长2) | `pur_price` | float[] | 买盘5档，价格 |
| 20-28 (步长2) | `seller` | int[] | 卖盘5档，股数 |
| 21-29 (步长2) | `sel_price` | float[] | 卖盘5档，价格 |
| 30 | `update_date` | str | 日期 `YYYY-MM-DD` |
| 31 | `update_time` | str | 时间 `HH:MM:SS` |

### 衍生计算

| 计算项 | 公式 |
|---|---|
| 涨跌值 change | `current_price - prev_close` |
| 涨跌幅 change_pct | `(current_price / prev_close - 1) * 100` |
| 均价 avg | `deals_amt / deals_vol` (成交额÷成交量) |
| 委比 committee | `(∑买方 - ∑卖方) / (∑买方 + ∑卖方) * 100` |
| ETF判断 | `code[2] in ('1','5')` → 3位小数精度 |

---

## 5. 界面层级与 UI 结构

```
QWidget (FloatLabel, 无框透明置顶)
  └── QWidget#panel (带圆角背景)
        ├── QLabel.error_label (红色错误提示，默认隐藏)
        └── QTableView (表格)
              ├── verticalHeader: 隐藏
              ├── horizontalHeader: 可选显示
              └── 每列自定义宽度 (ResizeToContents)
```

### 5.1 窗口属性

```python
self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
self.setAttribute(Qt.WA_TranslucentBackground, True)
```

### 5.2 颜色体系

| 模式 | 涨 | 跌 | 平 |
|---|---|---|---|
| 默认颜色(default_color=True) | `#dd2100` (红) | `#019933` (绿) | `#494949` (灰) |
| 纯色模式(default_color=False) | 统一: `fg` 配置色 |

### 5.3 列显示系统

`ALL_HEADERS = ["代码", "名称", "现价", "涨跌值", "涨跌幅", "买一", "卖一", "委比", "成交量", "成交额", "均价", "K线"]`

每列有独立布尔可见性（`code_visible`, `name_visible`, ...），通过右键菜单或设置面板切换。

---

## 6. 配置项全集 (SW_config.json)

| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `codes` | list[str] | `["sh000001"]` | 全部自选股(已规范化) |
| `checked_codes` | list[str] | 同 codes | 浮窗显示的股票 |
| `code_visible` ~ `kline_visible` | bool | false | 每列可见性(12个) |
| `short_code` | bool | false | 代码仅显示数字部分 |
| `name_length` | int | 0 | 名称截断字数(0=完整) |
| `b1s1_display` | "qty"\|"price"\|"both" | "qty" | 买一/卖一显示模式 |
| `header_visible` | bool | false | 表头可见 |
| `grid_visible` | bool | false | 网格可见 |
| `refresh_seconds` | int | 2 | 刷新间隔 (1/2/3/5/10/15/30/60) |
| `fg` | str(hex) | "#FFFFFF" | 文字颜色 |
| `bg` | dict | {r:0,g:0,b:0,a:191} | 背景RGBA |
| `opacity_pct` | int | 90 | 窗口不透明度(20-100) |
| `font_family` | str | "Microsoft YaHei" | 字体 |
| `font_size` | int | 10 | 字号(8-15pt) |
| `line_extra_px` | int | 1 | 行额外间距 |
| `default_color` | bool | false | 红涨绿跌模式 |
| `pos` | dict(x,y) | 右下角 | 窗口位置 |
| `hotkey` | str | "Ctrl+Alt+F" | 全局快捷键 |
| `start_on_boot` | bool | false | 开机自启 |
| `app_icon` | str | "default" | 程序图标选择 |

---

## 7. 买一/卖一显示逻辑（竞价 vs 连续竞价）

```python
if first_pur == first_sell > 0:
    # 集合竞价 (9:15-9:25, 14:57-15:00)
    # 配对量 = seller[0], 未配对量 = ±purchaser[1]/seller[1]
    # 颜色: 未配对量>0→红, <0→绿
else:
    # 连续竞价 (大部分交易时间)
    # 买一→红色, 卖一→绿色
    # 触及当前价时: 买一后加 "<", 卖一前加 ">"
```

---

## 8. 当日 K 线绘制 (KLineDelegate)

数据来自新浪：`{k: (今开, 现价, 最高, 最低, 昨收)}`

```
绘图流程:
  1. 计算 Y 轴映射：基于最高/最低/昨收 归一化
  2. 画昨收虚线 (中性色，有透明度)
  3. 画 K 线实体 (矩形):
     - 收>开 → 红色 (阳线，空心)
     - 收<开 → 绿色 (阴线，填充)
     - 收=开 → 一字线
  4. 画上下影线 (垂直线)
  5. 缩放系数: 随字号同步 (8pt=0.5, 15pt=1.5)
```

---

## 9. 快捷键与交互

| 操作 | 效果 |
|---|---|
| 左键拖拽 | 移动窗口 |
| 左键双击 | 隐藏浮窗 |
| 右键 | 弹出菜单(指标开关/表头/网格/颜色/设置) |
| 托盘左键 | 显示/隐藏浮窗 |
| 托盘右键 | 设置/退出 |
| Ctrl+Alt+F (可配置) | 显示/隐藏浮窗 |

---

## 10. 代码架构设计模式

### 10.1 观察者模式（配置变更通知）

```python
WidgetPanel.set_xxx() → _notify_change() → App.save_now()
                                          → json 持久化
```

### 10.2 委托模式（K线绘制）

```python
QTableView.setItemDelegateForColumn("K线", KLineDelegate)
# KLineDelegate 接管该列单元格的 paint() 方法
```

### 10.3 事件过滤（全局交互）

```python
panel/table/viewport/header 全部安装 eventFilter
统一处理鼠标事件(拖拽、双击隐藏)
```

### 10.4 信号/槽（PySide6 QTimer）

```
QTimer.timeout → _refresh_from_function(timer 驱动)
keyboard 全局热键 → hotkey_triggered Signal → toggle_win
```

---

## 11. 已知限制与潜在改进点

| 问题 | 位置 | 建议 |
|---|---|---|
| 新浪 API 超时 3s，网络差时卡 UI | `_get_price()` | 改用 QThread/异步请求 |
| `keep_top_timer` 每1s raise_ 一次，高耗 | `_ensure_on_top()` | 改用 Windows 原生置顶flag |
| 仅当日 K 线，无历史 | `KLineDelegate` | 接入 akshare/新浪历史接口 |
| 配置没有版本号，升级后可能不兼容 | `SW_config.json` | 增加 `config_version` 字段 |
| 打包 49MB 过大 | PyInstaller | 尝试 UPX 排除无用 DLL 或改用 Nuitka |
| 数据源单一，无备选 | `_get_price()` | 支持腾讯/东方财富 fallback |
| 无日志系统 | 全局 | 加入 logging 便于排查错误 |

---

*生成日期: 2026-06-20*
