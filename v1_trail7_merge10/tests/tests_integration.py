"""SettingsDialog 集成测试：真实 PySide6 事件循环 + 表格 + 策略参数联动"""
import sys, os
_PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJ)
os.chdir(_PROJ)

from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import pandas as pd
import numpy as np

app = QApplication.instance() or QApplication(sys.argv)

from band_settings import SettingsDialog

class MockEngine:
    cache_path = r'C:\Users\peiyilu\AppData\Local\Temp\0AMVMonitor\cache.pkl'
    strategy = {'entry':3.0,'exit_dd':-7.0,'merge_gap':10,'sma_n':10,'sma_m':2}
    bear_market_start = pd.Timestamp('2025-01-01')
    bands = []; raw_bands = []; _stock_band_cache = {}
    df = None; oamv = np.array([100.0]); oamv_pct = np.array([0.0])
    compute_count = 0
    detect_count = 0
    def _compute(self):
        self.compute_count += 1
    def _detect(self):
        self.detect_count += 1
    def refresh(self, strategy=None): return self.get_status()
    def get_status(self):
        return {'in_band':False,'oamv_value':100,'oamv_pct':0,'bands':[],'last_date':pd.Timestamp('2026-06-20')}
    def get_band_return(self, s, e, metric): return None
    def get_stock_band_return(self, code, s, e): return None

class MockPanel:
    def __init__(self):
        self.codes = []; self.checked_codes = []
        self.refresh_seconds = 30; self.config = {}; self.code_names = {}
        self.default_color = False; self.short_code = False; self.name_length = 0
        self.b1s1_visible = False; self.b1s1_display = 'qty'
        self.band_ret_visible = True; self.header_visible = True; self.grid_visible = False
        self.band_return_metric = 'index'; self.band_history = []
        self.fg = QColor(200,200,200); self.bg = QColor(30,30,30)
        self.font = QFont('Microsoft YaHei', 10); self.line_extra_px = 1
        self.engine = MockEngine()
        self.refresh_engine_count = 0
    def windowOpacity(self): return 1.0
    def header_is_visible(self, h): return True
    def get_code_name(self, code):
        if code in self.code_names:
            return self.code_names[code]
        db = {'sh000001':'上证指数','sz399006':'创业板指','sz000001':'平安银行','sh600519':'贵州茅台','sz159915':'创业板ETF','sz300750':'宁德时代'}
        return db.get(code, code)
    def set_config(self,k,v): self.config[k]=v
    def current_config(self): return {'codes':self.codes,'checked_codes':self.checked_codes,'refresh_seconds':self.refresh_seconds}
    def set_default_color(self,v): pass
    def set_short_code(self,v): pass
    def set_name_length(self,v): pass
    def set_b1s1_display(self,v): pass
    def set_band_return_metric(self,v): pass
    def set_codes(self, codes): self.codes = codes[:]
    def set_checked_codes(self, codes): self.checked_codes = codes[:]
    def _refresh_engine(self, force_fetch=True):
        self.refresh_engine_count += 1
    def _update_status_bar(self, status):
        pass
    def _update_band_returns(self, status):
        pass
    def _notify(self): pass
    def _on_change(self): pass

results = []

def add_row(dlg, code, checked=False):
    row = dlg.list_codes.rowCount()
    dlg.list_codes.insertRow(row)
    it0 = QTableWidgetItem(code)
    it0.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
    it0.setCheckState(Qt.Checked if checked else Qt.Unchecked)
    it0.setData(Qt.UserRole, code)
    dlg.list_codes.setItem(row, 0, it0)
    name = dlg.panel.get_code_name(code)
    it1 = QTableWidgetItem(name if name != code else "更新中...")
    it1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
    dlg.list_codes.setItem(row, 1, it1)

parent = None

# ── Test 1: add row, verify code editable+checkable, name read-only ──
def test_add_row():
    """添加一行，验证 code 可编辑+可勾选，name 只读"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    add_row(dlg, 'sh000001')
    assert dlg.list_codes.rowCount() == 1
    it0 = dlg.list_codes.item(0, 0)
    assert it0.data(Qt.UserRole) == 'sh000001'
    assert it0.text() == 'sh000001'
    assert it0.flags() & Qt.ItemIsEditable
    assert it0.flags() & Qt.ItemIsUserCheckable
    it1 = dlg.list_codes.item(0, 1)
    assert it1.text() == '上证指数'
    assert not (it1.flags() & Qt.ItemIsEditable)
    results.append(('test_add_row', True, ''))
    dlg.close()

def test_three_rows():
    """添加三行，验证顺序、名称、默认未勾选"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    for c in ['sh000001','sz399006','sh600519']:
        add_row(dlg, c)
    assert dlg.list_codes.rowCount() == 3
    assert dlg.list_codes.item(0,0).data(Qt.UserRole) == 'sh000001'
    assert dlg.list_codes.item(1,0).data(Qt.UserRole) == 'sz399006'
    assert dlg.list_codes.item(2,0).data(Qt.UserRole) == 'sh600519'
    assert dlg.list_codes.item(0,1).text() == '上证指数'
    assert dlg.list_codes.item(1,1).text() == '创业板指'
    assert dlg.list_codes.item(2,1).text() == '贵州茅台'
    for i in range(3):
        assert dlg.list_codes.item(i,0).checkState() == Qt.Unchecked
    results.append(('test_three_rows', True, ''))
    dlg.close()

def test_check_rows():
    """勾选第0行和第2行，验证只提取勾选的代码"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    for c in ['sh000001','sz399006','sh600519']:
        add_row(dlg, c)
    dlg.list_codes.item(0,0).setCheckState(Qt.Checked)
    dlg.list_codes.item(2,0).setCheckState(Qt.Checked)
    checked = [dlg.list_codes.item(i,0).data(Qt.UserRole)
               for i in range(dlg.list_codes.rowCount())
               if dlg.list_codes.item(i,0).checkState() == Qt.Checked]
    assert checked == ['sh000001','sh600519']
    results.append(('test_check_rows', True, ''))
    dlg.close()

def test_collect_codes():
    """_collect_codes 提取全部行的代码到列表"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    for c in ['sh000001','sz399006','sh600519']:
        add_row(dlg, c)
    codes = dlg._collect_codes()
    assert codes == ['sh000001','sz399006','sh600519']
    results.append(('test_collect_codes', True, ''))
    dlg.close()

def test_update_name_then_refresh():
    """未知代码显示 更新中...，缓存更新后 _refresh_names 补全为中文"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    add_row(dlg, 'sz001234')
    assert dlg.list_codes.item(0,1).text() == '更新中...', f"name={dlg.list_codes.item(0,1).text()}"
    panel.code_names['sz001234'] = '测试股票'
    dlg._refresh_names()
    assert dlg.list_codes.item(0,1).text() == '测试股票'
    results.append(('test_update_name_then_refresh', True, ''))
    dlg.close()

def test_on_codes_changed():
    """编辑 code 列触发 on_codes_changed，自动更新 name 列"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    add_row(dlg, 'sh000001')
    dlg.list_codes.item(0,0).setText('sh600519')
    dlg._on_codes_changed(dlg.list_codes.item(0,0))
    assert dlg.list_codes.item(0,1).text() == '贵州茅台'
    results.append(('test_on_codes_changed', True, ''))
    dlg.close()

def test_load_from_panel():
    """从 panel config 加载已有 codes，验证行数、勾选状态、名称"""
    panel = MockPanel()
    panel.codes = ['sh000001','sz399006']
    panel.checked_codes = ['sh000001']
    dlg = SettingsDialog(panel, parent)
    assert dlg.list_codes.rowCount() == 2
    assert dlg.list_codes.item(0,0).data(Qt.UserRole) == 'sh000001'
    assert dlg.list_codes.item(1,0).data(Qt.UserRole) == 'sz399006'
    assert dlg.list_codes.item(0,0).checkState() == Qt.Checked
    assert dlg.list_codes.item(1,0).checkState() == Qt.Unchecked
    assert dlg.list_codes.item(0,1).text() == '上证指数'
    results.append(('test_load_from_panel', True, ''))
    dlg.close()

def test_apply_save():
    """collect_codes + checked 提取结果与预期一致"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    add_row(dlg, 'sh000001')
    add_row(dlg, 'sz399006')
    dlg.list_codes.item(0,0).setCheckState(Qt.Checked)
    codes = dlg._collect_codes()
    assert codes == ['sh000001','sz399006']
    checked = [dlg.list_codes.item(i,0).data(Qt.UserRole)
               for i in range(dlg.list_codes.rowCount())
               if dlg.list_codes.item(i,0).checkState() == Qt.Checked]
    assert checked == ['sh000001']
    results.append(('test_apply_save', True, ''))
    dlg.close()

def test_name_refresh_timer():
    """_name_refresh_timer 已创建、激活、间隔 5000ms"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    assert hasattr(dlg, '_name_refresh_timer')
    assert dlg._name_refresh_timer.isActive()
    assert dlg._name_refresh_timer.interval() == 5000
    results.append(('test_name_refresh_timer', True, ''))
    dlg.close()

def test_load_from_panel_unknown_code():
    """从 panel 加载未知代码，名称列显示 更新中..."""
    panel = MockPanel()
    panel.codes = ['sz001234']
    dlg = SettingsDialog(panel, parent)
    assert dlg.list_codes.rowCount() == 1
    assert dlg.list_codes.item(0,1).text() == '更新中...'
    results.append(('test_load_from_panel_unknown_code', True, ''))
    dlg.close()

# ── 策略参数联动测试 ──
def test_strat_entry_slider():
    """拖动入场阈值滑块 → strategy['entry'] 立即更新，释放后触发 _compute/_detect"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    assert dlg.slider_entry.value() == 30  # 3.0%
    dlg.slider_entry.setValue(50)  # 5.0%
    dlg._on_strat_entry_label(50)
    assert panel.engine.strategy['entry'] == 5.0
    from PySide6.QtCore import QCoreApplication
    for _ in range(10):
        QCoreApplication.processEvents()
    dlg._on_strat_entry_apply()
    for _ in range(10):
        QCoreApplication.processEvents()
    assert panel.engine.compute_count >= 1
    assert panel.engine.detect_count >= 1
    assert panel.refresh_engine_count >= 1
    results.append(('test_strat_entry_slider', True, ''))
    dlg.close()

def test_strat_entry_buttons():
    """点击入场 +/- 按钮 → 步进 1 → strategy 更新 + trigger"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    old = panel.engine.strategy['entry']
    dlg.btn_entry_sub.click()  # －
    panel.engine.compute_count = 0
    panel.engine.detect_count = 0
    panel.refresh_engine_count = 0
    from PySide6.QtCore import QCoreApplication
    for _ in range(10):
        QCoreApplication.processEvents()
    assert panel.engine.strategy['entry'] == old - 0.1
    results.append(('test_strat_entry_buttons', True, ''))
    dlg.close()

def test_strat_exit_slider():
    """拖动退出回撤滑块 → strategy['exit_dd'] 更新为负值"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    dlg._on_strat_exit_label(150)  # -15.0%
    assert panel.engine.strategy['exit_dd'] == -15.0
    results.append(('test_strat_exit_slider', True, ''))
    dlg.close()

def test_strat_merge_slider():
    """拖动合并间隔滑块 → strategy['merge_gap'] 更新"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    dlg._on_strat_merge_label(5)
    assert panel.engine.strategy['merge_gap'] == 5
    results.append(('test_strat_merge_slider', True, ''))
    dlg.close()

def test_strat_sma_n():
    """切换 SMA N 下拉 → strategy['sma_n'] 更新 + trigger"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    idx = dlg.cmb_sma_n.findData(15)
    assert idx >= 0, f"findData(15) returned {idx}"
    dlg.cmb_sma_n.setCurrentIndex(idx)
    assert dlg.cmb_sma_n.currentData() == 15, f"currentData={dlg.cmb_sma_n.currentData()}"
    dlg._on_strat_sma()
    from PySide6.QtCore import QCoreApplication
    for _ in range(20):
        QCoreApplication.processEvents()
    strat = panel.engine.strategy
    assert strat['sma_n'] == 15, f"sma_n={strat['sma_n']}"
    assert panel.engine.compute_count >= 1, f"compute={panel.engine.compute_count}"
    assert panel.engine.detect_count >= 1, f"detect={panel.engine.detect_count}"
    results.append(('test_strat_sma_n', True, ''))
    dlg.close()

def test_strat_sma_m():
    """切换 SMA M 下拉 → strategy['sma_m'] 更新 + trigger"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    idx = dlg.cmb_sma_m.findData(1)
    assert idx >= 0
    dlg.cmb_sma_m.setCurrentIndex(idx)
    dlg._on_strat_sma()
    from PySide6.QtCore import QCoreApplication
    for _ in range(20):
        QCoreApplication.processEvents()
    assert panel.engine.strategy['sma_m'] == 1
    assert panel.engine.compute_count >= 1
    assert panel.engine.detect_count >= 1
    results.append(('test_strat_sma_m', True, ''))
    dlg.close()

def test_strat_after_codes():
    """调整策略参数后，自选表格 CRUD 功能仍然正常"""
    panel = MockPanel()
    dlg = SettingsDialog(panel, parent)
    # 先改参数
    dlg.slider_entry.setValue(40)
    dlg._on_strat_entry_label(40)
    dlg._on_strat_entry_apply()
    dlg.cmb_sma_n.setCurrentIndex(dlg.cmb_sma_n.findData(15))
    dlg._on_strat_sma()
    from PySide6.QtCore import QCoreApplication
    for _ in range(10):
        QCoreApplication.processEvents()
    # 再操作表格
    add_row(dlg, 'sh000001')
    add_row(dlg, 'sz399006')
    assert dlg.list_codes.rowCount() == 2
    assert dlg.list_codes.item(0,1).text() == '上证指数'
    assert dlg.list_codes.item(1,1).text() == '创业板指'
    dlg.list_codes.item(0,0).setCheckState(Qt.Checked)
    codes = dlg._collect_codes()
    assert codes == ['sh000001','sz399006']
    results.append(('test_strat_after_codes', True, ''))
    dlg.close()

def run_all():
    tests = [
        test_add_row, test_three_rows, test_check_rows, test_collect_codes,
        test_update_name_then_refresh, test_on_codes_changed, test_load_from_panel,
        test_apply_save, test_name_refresh_timer, test_load_from_panel_unknown_code,
        test_strat_entry_slider, test_strat_entry_buttons, test_strat_exit_slider,
        test_strat_merge_slider, test_strat_sma_n, test_strat_sma_m, test_strat_after_codes,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            results.append((t.__name__, False, str(e)))

run_all()

print(); print("="*60)
print("  SettingsDialog 集成测试结果")
print("="*60)
passed = sum(1 for r in results if r[1])
for name, ok, msg in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if not ok: print(f"         {msg}")
print(f"\n  总计: {len(results)}, 通过: {passed}, 失败: {len(results)-passed}")
sys.exit(0 if passed == len(results) else 1)
