"""生成测试报告到文件"""
import subprocess, sys, os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PY = sys.executable
REPORT_PATH = os.path.join(HERE, "test_report.md")

# ── 测试项中文备注 ──
CN_NOTES = {
    'normalize_code': '股票代码标准化：验证多种格式（sh/sz/bj 前缀、纯数字、空、None、非法字符）都能正确转换为统一格式',
    'BandEngine: 0AMV': '0AMV 核心算法验证：SMA 计算、波段入场/退出检测、区间收益查询、状态字典格式',
    'BandEngine: _compute': '0AMV 计算异常处理：无数据时是否正确报错',
    'BandEngine: _detect': '波段检测逻辑验证：入场阈值 ≥3%、退出回撤 ≤-7%、合并间隔、日期过滤',
    'BandEngine: get_band_return': '波段区间收益查询：0AMV 自身收益计算',
    'BandEngine: get_stock_band_return': '个股/ETF 波段收益查询：数据不可用时返回 None',
    'BandEngine: get_status': '状态字典格式验证：返回字段完整',
    'QuotesFetcher: code_names': '实时行情获取器初始化：code_names 缓存为空',
    'QuoteTableModel: init': '行情表格模型初始化：空表行数列数正确',
    'QuoteTableModel: set_data': '行情表格填充数据：行数正确',
    'QuoteTableModel: data returns': '行情表格取值：各列数据正确返回',
    'QuoteTableModel: headerData': '行情表格表头：列名正确',
    'QuoteTableModel: color scheme': '行情表格颜色方案：切换颜色后列头更新',
    'Settings: table 3x2': '设置对话框表格初始化：3×2 结构、行列头',
    'Settings: row 0 data': '设置对话框表格第0行：UserRole 存储标准化代码',
    'Settings: row 2 unchecked': '设置对话框表格勾选状态：默认未勾选',
    'Settings: code editable': '设置对话框代码列：可编辑、可勾选',
    'Settings: name NOT editable': '设置对话框名称列：只读不可编辑',
    'Settings: add_code': '设置对话框添加行：默认代码 sh000001、名称上证指数',
    'Settings: del_code': '设置对话框删除行：中间行删除后顺序正确',
    'Settings: move_up': '设置对话框上移：顺序重排正确',
    'Settings: move_down': '设置对话框下移：顺序重排正确',
    'Settings: collect_codes': '设置对话框提取全部代码：含勾选行',
    'Settings: update_name known': '设置对话框名称自动补全：已知代码立即显示中文名',
    'Settings: update_name unknown': '设置对话框名称自动补全：未知代码暂时显示"更新中..."',
    'Settings: refresh_names': '设置对话框名称定时刷新：缓存更新后从"更新中..."变为中文名',
    'Settings: checked extraction': '设置对话框勾选提取：UserRole 方式获取代码',
    'Settings: on_codes_changed(None)': '设置对话框信号处理：item=None 不崩溃',
    'Settings: on_codes_changed(item)': '设置对话框信号处理：item 触发名称更新',
    'Settings: name refresh timer': '设置对话框名称刷新定时器：5秒间隔，启动后激活',
    'Settings: make_combo_label': '设置对话框下拉标签：格式正确',
    'Settings: band metric combo': '设置对话框波段收益品种下拉：列表正确',
    'Settings: export code combo': '设置对话框导出代码下拉：列表正确',
    'BandPanel: instantiate': '浮窗面板初始化：带 mock engine 全程无异常',
    'BandPanel: get_code_name': '浮窗面板名称查询：未知代码回退到代码自身',
    'BandPanel: header_is_visible': '浮窗面板表头可见性查询：功能正常',
    'BandPanel: set_codes': '浮窗面板设置自选列表：功能正常',
    'BandPanel: set_checked_codes fallback': '浮窗面板设置勾选列表：空列表自动默认',
    'BandPanel: set_checked_codes': '浮窗面板设置勾选列表：功能正常',
    'load_config returns': '配置加载：load_config 返回 dict',
    'save/load roundtrip': '配置持久化：保存→加载 完全一致',
    'save/load pickle': '缓存持久化：pickle 保存/加载正常',
    'load_cache missing': '缓存读取：文件不存在返回 False',
    'analyze.py syntax': 'CLI 分析脚本语法正确',
    'total_return.py syntax': 'CLI 收益对比脚本语法正确',
    'band_monitor.py syntax': 'GUI 入口脚本语法正确',
    'Signal: table itemChanged': '信号集成：QTableWidget 编辑触发 on_codes_changed',
    # ── 集成测试 ──
    'test_add_row': '添加一行，验证 code 可编辑+可勾选、name 只读、UserRole 存储标准化代码',
    'test_three_rows': '添加三行，验证顺序、中文名称、默认未勾选状态',
    'test_check_rows': '勾选第0行和第2行，验证 checked 提取只返回勾选项',
    'test_collect_codes': '_collect_codes 正确提取全部行的代码列表',
    'test_update_name_then_refresh': '未知代码显示"更新中..."，缓存更新后 _refresh_names 补全中文名',
    'test_on_codes_changed': '编辑 code 列触发 on_codes_changed，自动更新 name 列',
    'test_load_from_panel': '从 panel config 加载已有 codes，验证行数、勾选状态、名称',
    'test_apply_save': 'collect_codes + checked 提取结果与预期一致',
    'test_name_refresh_timer': '_name_refresh_timer 已创建、激活、间隔 5000ms',
    'test_load_from_panel_unknown_code': '从 panel 加载未知代码，名称列显示"更新中..."',
    'test_strat_entry_slider': '拖动入场阈值滑块，strategy 立即更新，释放后触发 _compute/_detect',
    'test_strat_entry_buttons': '点击入场 +/- 按钮，步进 0.1%，strategy 更新并触发重算',
    'test_strat_exit_slider': '拖动退出回撤滑块，strategy["exit_dd"] 更新为负值',
    'test_strat_merge_slider': '拖动合并间隔滑块，strategy["merge_gap"] 更新',
    'test_strat_sma_n': '切换 SMA N 下拉，strategy["sma_n"] 更新并触发重算',
    'test_strat_sma_m': '切换 SMA M 下拉，strategy["sma_m"] 更新并触发重算',
    'test_strat_after_codes': '调整策略参数后，自选表格 CRUD 功能仍然正常',
}

def cn_for(name):
    best = ''
    for key, note in CN_NOTES.items():
        if name.startswith(key) and len(key) > len(best):
            best = key
    return CN_NOTES.get(best, '')

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def run_and_capture(label, script):
    path = os.path.join(HERE, script)
    proc = subprocess.run(
        [PY, path], cwd=PROJ,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    return strip_ansi(proc.stdout.decode('utf-8', errors='replace')), proc.returncode

lines = []
def L(*args):
    lines.append(''.join(str(a) for a in args))

L("# 0AMVMonitor 测试报告\n")
L(f"**生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
L("---\n")

total_pass = 0
total_fail = 0
results = []

for label, script in [
    ("综合单元测试 (62项)", "tests_comprehensive.py"),
    ("Settings 集成测试 (10项)", "tests_integration.py"),
]:
    L(f"## {label}\n")
    L(f"**脚本**: `{script}`\n")

    out, rc = run_and_capture(label, script)

    passed = 0
    failed = 0
    test_details = []
    current_cn = ''

    for line in out.split('\n'):
        stripped = line.strip()
        if stripped.startswith('OK ') or stripped.startswith('OK\t'):
            passed += 1
            name = stripped[3:].strip()
            note = cn_for(name)
            test_details.append(f"  - ✅ **{name}**")
            if note:
                test_details.append(f"    > {note}")
        elif stripped.startswith('FAIL ') or stripped.startswith('FAIL\t'):
            failed += 1
            name = stripped[5:].strip()
            test_details.append(f"  - ❌ **{name}**")
        elif stripped.startswith('[PASS]'):
            passed += 1
            name = stripped[6:].strip()
            note = cn_for(name)
            test_details.append(f"  - ✅ **{name}**")
            if note:
                test_details.append(f"    > {note}")
        elif stripped.startswith('[FAIL]'):
            failed += 1
            name = stripped[6:].strip()
            test_details.append(f"  - ❌ **{name}**")
        elif 'Total:' in stripped:
            L(f"  {stripped}")
        elif 'Passed:' in stripped and 'FAILED' not in stripped and 'DETAILS' not in stripped:
            L(f"  {stripped}")
        elif stripped.startswith('Rate:'):
            L(f"  {stripped}")

    if test_details:
        L(f"\n### 测试项详情\n")
        for d in test_details:
            L(d)

    total_pass += passed
    total_fail += failed
    results.append((label, passed, failed, rc))

    if failed == 0:
        L(f"\n**结果**: ✅ 全部通过 ({passed}/{passed})\n")
    else:
        L("")
        L(f"**结果**: ❌ {failed} 项失败")
    L("")
    L("---")
    L("")

L("## 汇总")
L("")
L("| # | 套件 | 通过 | 失败 | 状态 |")
L("|---|------|------|------|------|")
for i, (lbl, p, f, rc) in enumerate(results, 1):
    L(f"| {i} | {lbl} | {p} | {f} | {'✅' if rc == 0 else '❌'} |")
L(f"| | **合计** | **{total_pass}** | **{total_fail}** | {'🎉 全部通过' if total_fail == 0 else '⚠️ 有失败'} |")
L("")
if total_fail == 0:
    L(f"🎉 **全部 {total_pass} 项测试通过，无失败。**")
else:
    L(f"⚠️ **{total_fail} 项测试失败。**")

with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"报告已生成: {REPORT_PATH}")
print(f"共 {total_pass} 项通过, {total_fail} 项失败")
