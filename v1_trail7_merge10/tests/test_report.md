# 0AMVMonitor 测试报告

**生成时间**: 2026-06-21 13:35:56

---

## 综合单元测试 (62项)

**脚本**: `tests_comprehensive.py`

  Total:   62
  Passed:  62
  Rate:    100.0%

### 测试项详情

  - ✅ **normalize_code: sh prefix kept**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **normalize_code: 6-digit -> bj (4xxxxx)**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **Signal: table itemChanged triggers on_codes_changed**
    > 信号集成：QTableWidget 编辑触发 on_codes_changed
  - ✅ **normalize_code: 6-digit -> bj (92xxxx)**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **normalize_code: empty -> None**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **normalize_code: whitespace stripped**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **normalize_code: uppercase -> lowercase**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **normalize_code: None -> None**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **normalize_code: garbage -> None**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **normalize_code: sz prefix kept**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **BandEngine: 0AMV SMA matches manual**
    > 0AMV 核心算法验证：SMA 计算、波段入场/退出检测、区间收益查询、状态字典格式
  - ✅ **BandEngine: _compute with no data crashes -> need df**
    > 0AMV 计算异常处理：无数据时是否正确报错
  - ✅ **BandEngine: _detect finds bands**
    > 波段检测逻辑验证：入场阈值 ≥3%、退出回撤 ≤-7%、合并间隔、日期过滤
  - ✅ **BandEngine: get_band_return with oamv**
    > 波段区间收益查询：0AMV 自身收益计算
  - ✅ **BandEngine: get_stock_band_return -> None (no data)**
    > 个股/ETF 波段收益查询：数据不可用时返回 None
  - ✅ **BandEngine: get_status returns dict**
    > 状态字典格式验证：返回字段完整
  - ✅ **normalize_code: bj prefix kept**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **QuotesFetcher: code_names init empty**
    > 实时行情获取器初始化：code_names 缓存为空
  - ✅ **QuoteTableModel: init empty**
    > 行情表格模型初始化：空表行数列数正确
  - ✅ **QuoteTableModel: set_data + rowCount**
    > 行情表格填充数据：行数正确
  - ✅ **QuoteTableModel: data returns correct value**
    > 行情表格取值：各列数据正确返回
  - ✅ **QuoteTableModel: headerData**
    > 行情表格表头：列名正确
  - ✅ **QuoteTableModel: color scheme changes**
    > 行情表格颜色方案：切换颜色后列头更新
  - ✅ **normalize_code: 6-digit -> sh (6xxxxx)**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **Settings: table 3x2 init**
    > 设置对话框表格初始化：3×2 结构、行列头
  - ✅ **Settings: row 0 data**
    > 设置对话框表格第0行：UserRole 存储标准化代码
  - ✅ **Settings: row 2 unchecked**
    > 设置对话框表格勾选状态：默认未勾选
  - ✅ **Settings: code editable + checkable**
    > 设置对话框代码列：可编辑、可勾选
  - ✅ **Settings: name NOT editable**
    > 设置对话框名称列：只读不可编辑
  - ✅ **Settings: add_code with default name**
    > 设置对话框添加行：默认代码 sh000001、名称上证指数
  - ✅ **Settings: del_code**
    > 设置对话框删除行：中间行删除后顺序正确
  - ✅ **Settings: move_up reorder**
    > 设置对话框上移：顺序重排正确
  - ✅ **Settings: move_down reorder**
    > 设置对话框下移：顺序重排正确
  - ✅ **Settings: collect_codes**
    > 设置对话框提取全部代码：含勾选行
  - ✅ **normalize_code: 6-digit -> sh (5xxxxx ETF)**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **Settings: update_name known code**
    > 设置对话框名称自动补全：已知代码立即显示中文名
  - ✅ **Settings: update_name unknown -> 更新中...**
    > 设置对话框名称自动补全：未知代码暂时显示"更新中..."
  - ✅ **Settings: refresh_names fills cache**
    > 设置对话框名称定时刷新：缓存更新后从"更新中..."变为中文名
  - ✅ **Settings: checked extraction from UserRole**
    > 设置对话框勾选提取：UserRole 方式获取代码
  - ✅ **Settings: on_codes_changed(None) no crash**
    > 设置对话框信号处理：item=None 不崩溃
  - ✅ **Settings: on_codes_changed(item) no crash**
    > 设置对话框信号处理：item 触发名称更新
  - ✅ **Settings: name refresh timer active**
    > 设置对话框名称刷新定时器：5秒间隔，启动后激活
  - ✅ **Settings: make_combo_label**
    > 设置对话框下拉标签：格式正确
  - ✅ **Settings: band metric combo populated**
    > 设置对话框波段收益品种下拉：列表正确
  - ✅ **Settings: export code combo populated**
    > 设置对话框导出代码下拉：列表正确
  - ✅ **normalize_code: 6-digit -> sz (0xxxxx)**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **BandPanel: instantiate**
    > 浮窗面板初始化：带 mock engine 全程无异常
  - ✅ **BandPanel: get_code_name fallback**
    > 浮窗面板名称查询：未知代码回退到代码自身
  - ✅ **BandPanel: header_is_visible**
    > 浮窗面板表头可见性查询：功能正常
  - ✅ **BandPanel: set_codes**
    > 浮窗面板设置自选列表：功能正常
  - ✅ **BandPanel: set_checked_codes fallback to default**
    > 浮窗面板设置勾选列表：空列表自动默认
  - ✅ **BandPanel: set_checked_codes**
    > 浮窗面板设置勾选列表：功能正常
  - ✅ **normalize_code: 6-digit -> sz (3xxxxx)**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **load_config returns dict**
    > 配置加载：load_config 返回 dict
  - ✅ **save/load roundtrip**
    > 配置持久化：保存→加载 完全一致
  - ✅ **normalize_code: 6-digit -> sz (2xxxxx)**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **save/load pickle**
    > 缓存持久化：pickle 保存/加载正常
  - ✅ **load_cache missing -> False**
    > 缓存读取：文件不存在返回 False
  - ✅ **normalize_code: 6-digit -> bj (8xxxxx)**
    > 股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式
  - ✅ **analyze.py syntax OK**
    > CLI 分析脚本语法正确
  - ✅ **total_return.py syntax OK**
    > CLI 收益对比脚本语法正确
  - ✅ **band_monitor.py syntax OK**
    > GUI 入口脚本语法正确

**结果**: ✅ 全部通过 (62/62)


---

## Settings 集成测试 (10项)

**脚本**: `tests_integration.py`


### 测试项详情

  - ✅ **test_add_row**
    > 添加一行，验证 code 可编辑+可勾选、name 只读、UserRole 存储标准化代码
  - ✅ **test_three_rows**
    > 添加三行，验证顺序、中文名称、默认未勾选状态
  - ✅ **test_check_rows**
    > 勾选第0行和第2行，验证 checked 提取只返回勾选项
  - ✅ **test_collect_codes**
    > _collect_codes 正确提取全部行的代码列表
  - ✅ **test_update_name_then_refresh**
    > 未知代码显示"更新中..."，缓存更新后 _refresh_names 补全中文名
  - ✅ **test_on_codes_changed**
    > 编辑 code 列触发 on_codes_changed，自动更新 name 列
  - ✅ **test_load_from_panel**
    > 从 panel config 加载已有 codes，验证行数、勾选状态、名称
  - ✅ **test_apply_save**
    > collect_codes + checked 提取结果与预期一致
  - ✅ **test_name_refresh_timer**
    > _name_refresh_timer 已创建、激活、间隔 5000ms
  - ✅ **test_load_from_panel_unknown_code**
    > 从 panel 加载未知代码，名称列显示"更新中..."
  - ✅ **test_strat_entry_slider**
    > 拖动入场阈值滑块，strategy 立即更新，释放后触发 _compute/_detect
  - ✅ **test_strat_entry_buttons**
    > 点击入场 +/- 按钮，步进 0.1%，strategy 更新并触发重算
  - ✅ **test_strat_exit_slider**
    > 拖动退出回撤滑块，strategy["exit_dd"] 更新为负值
  - ✅ **test_strat_merge_slider**
    > 拖动合并间隔滑块，strategy["merge_gap"] 更新
  - ✅ **test_strat_sma_n**
    > 切换 SMA N 下拉，strategy["sma_n"] 更新并触发重算
  - ✅ **test_strat_sma_m**
    > 切换 SMA M 下拉，strategy["sma_m"] 更新并触发重算
  - ✅ **test_strat_after_codes**
    > 调整策略参数后，自选表格 CRUD 功能仍然正常

**结果**: ✅ 全部通过 (17/17)


---

## 汇总

| # | 套件 | 通过 | 失败 | 状态 |
|---|------|------|------|------|
| 1 | 综合单元测试 (62项) | 62 | 0 | ✅ |
| 2 | Settings 集成测试 (10项) | 17 | 0 | ✅ |
| | **合计** | **79** | **0** | 🎉 全部通过 |

🎉 **全部 79 项测试通过，无失败。**