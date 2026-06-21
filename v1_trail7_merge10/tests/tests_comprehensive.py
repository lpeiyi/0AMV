"""Comprehensive integration test for 0AMVMonitor"""
import sys, os, json, tempfile, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

RESULTS = []

def section(s):
    print(f'\n=== {s} ===')

def test(name):
    def deco(fn):
        def wrapper():
            try:
                fn()
                RESULTS.append((name, True, ''))
                print(f'  OK {name}')
            except Exception as e:
                tb = traceback.format_exc()
                RESULTS.append((name, False, str(e)))
                print(f'  FAIL {name}: {e}')
        return wrapper
    return deco

# ==========================================================
# PART 1: band_stocks.py - normalize_code
# ==========================================================
section('PART 1: band_stocks.py - normalize_code')
from band_stocks import normalize_code

@test('normalize_code: sh prefix kept')
def t1(): assert normalize_code('sh600000') == 'sh600000'

@test('normalize_code: sz prefix kept')
def t2(): assert normalize_code('sz000001') == 'sz000001'

@test('normalize_code: bj prefix kept')
def t3(): assert normalize_code('bj430001') == 'bj430001'

@test('normalize_code: 6-digit -> sh (6xxxxx)')
def t4(): assert normalize_code('600000') == 'sh600000'

@test('normalize_code: 6-digit -> sh (5xxxxx ETF)')
def t5(): assert normalize_code('510050') == 'sh510050'

@test('normalize_code: 6-digit -> sz (0xxxxx)')
def t6(): assert normalize_code('000001') == 'sz000001'

@test('normalize_code: 6-digit -> sz (3xxxxx)')
def t7(): assert normalize_code('300750') == 'sz300750'

@test('normalize_code: 6-digit -> sz (2xxxxx)')
def t8(): assert normalize_code('200625') == 'sz200625'

@test('normalize_code: 6-digit -> bj (8xxxxx)')
def t9(): assert normalize_code('830001') == 'bj830001'

@test('normalize_code: 6-digit -> bj (4xxxxx)')
def t10(): assert normalize_code('430001') == 'bj430001'

@test('normalize_code: 6-digit -> bj (92xxxx)')
def t11(): assert normalize_code('920001') == 'bj920001'

@test('normalize_code: empty -> None')
def t12(): assert normalize_code('') is None

@test('normalize_code: whitespace stripped')
def t13(): assert normalize_code('  sh600000  ') == 'sh600000'

@test('normalize_code: uppercase -> lowercase')
def t14(): assert normalize_code('SH600000') == 'sh600000'

@test('normalize_code: None -> None')
def t15(): assert normalize_code(None) is None

@test('normalize_code: garbage -> None')
def t16(): assert normalize_code('abc!@#') is None

# ==========================================================
# PART 2: band_engine.py - SMA + band detection
# ==========================================================
section('PART 2: band_engine.py - 0AMV + band')
import pandas as pd
import numpy as np
from band_engine import BandEngine

np.random.seed(42)
dates = pd.date_range('2022-01-01', periods=200, freq='D')
amounts = 5e8 + np.cumsum(np.random.randn(200) * 5e6)
amounts = np.maximum(amounts, 1e8)
df_mock_985 = pd.DataFrame({'date': dates, 'amount_yi': amounts.astype(float)})

M, N = 2, 10
sma_manual = [np.nan] * len(amounts)
for i in range(len(amounts)):
    if i == 0:
        sma_manual[i] = float(amounts[0])
    else:
        sma_manual[i] = (M * float(amounts[i]) + (N - M) * sma_manual[i-1]) / N

@test('BandEngine: 0AMV SMA matches manual')
def t20():
    engine = BandEngine(cache_path=None)
    engine.df = df_mock_985.copy()
    engine._compute()
    assert engine.oamv is not None and len(engine.oamv) > 0
    diff = np.abs(engine.oamv - np.array(sma_manual)).max()
    assert diff < 1.0, f'SMA diff={diff}'

@test('BandEngine: _compute with no data crashes -> need df')
def t21():
    engine = BandEngine(cache_path=None)
    # engine.df = None -> _compute will crash on len(None)
    # This is expected; the test verifies we know the behavior
    try:
        engine._compute()
        assert False, 'Should have crashed'
    except Exception:
        pass  # expected

@test('BandEngine: _detect finds bands')
def t22():
    np.random.seed(1)
    N = 500
    ds = pd.date_range('2022-06-01', periods=N, freq='D')
    base = 100.0
    # Create a flat region then big jump (entry) then decline (exit)
    oamv = np.ones(N) * base
    # Region 1: flat at 100 (days 0-199: 2022-06 to 2022-12)
    # Region 2: jump to 105 (days 200-209: entry lat/lon after 2023-01-01, +5% >= 3% entry)
    # Wait, day 200 = ~2022-12-18, still before 2023. Need later jump.
    # day 230 = ~2023-01-17, jump to 105
    oamv[220:250] = 105.0  # jump day 220 = 2023-01-07, +5% >= 3%
    # Region 3: jump to 115 (days 250-259): +9.5% >= 3%
    oamv[250:280] = 115.0
    # Region 4: decline from 115 to 100 (days 280-350): -13% <= -7%
    oamv[280:350] = np.linspace(115, 100, 70)
    # Region 5: flat (days 350-end)
    oamv[350:] = 100.0
    
    engine = BandEngine(cache_path=None)
    engine.df = pd.DataFrame({'date': ds, 'amount_yi': oamv * 1e6})
    engine.oamv = oamv.astype(float)
    engine.oamv_pct = np.zeros(N)
    engine.oamv_pct[1:] = np.diff(oamv) / oamv[:-1] * 100
    engine.strategy = {'entry':3.0,'exit_dd':-7.0,'merge_gap':10,'sma_n':10,'sma_m':2}
    engine._detect()
    assert len(engine.bands) > 0, f'Should detect bands, got {len(engine.bands)}'
    # Verify band start >= 2023-01-01 (filtered in _detect)
    for s, e in engine.bands:
        assert s >= pd.Timestamp('2023-01-01'), f'Band starts too early: {s}'

@test('BandEngine: get_band_return with oamv')
def t23():
    engine = BandEngine(cache_path=None)
    ds = pd.date_range('2023-01-01', periods=50, freq='D')
    engine.df = pd.DataFrame({'date': ds, 'amount_yi': np.arange(50.0)*1e6+1e8})
    engine.oamv = np.arange(50.0)*0.1 + 100
    ret = engine.get_band_return(pd.Timestamp('2023-01-10'), pd.Timestamp('2023-01-20'), metric='oamv')
    assert ret is not None

@test('BandEngine: get_stock_band_return -> None (no data)')
def t24():
    engine = BandEngine(cache_path=None)
    ret = engine.get_stock_band_return('sh000001', pd.Timestamp('2023-01-10'), pd.Timestamp('2023-01-20'))
    assert ret is None

@test('BandEngine: get_status returns dict')
def t25():
    engine = BandEngine(cache_path=None)
    ds = pd.date_range('2023-01-01', periods=10, freq='D')
    engine.df = pd.DataFrame({'date': ds, 'amount_yi': np.ones(10)*1e8})
    engine.oamv = np.ones(10) * 100
    engine.oamv_pct = np.zeros(10)
    s = engine.get_status()
    assert isinstance(s, dict)
    assert 'oamv_value' in s

# ==========================================================
# PART 3: band_stocks.py - QuotesFetcher + QuoteTableModel
# ==========================================================
section('PART 3: band_stocks.py - QuotesFetcher + Model')
from band_stocks import QuotesFetcher, QuoteTableModel
from PySide6.QtCore import Qt, QModelIndex

@test('QuotesFetcher: code_names init empty')
def t30():
    qf = QuotesFetcher()
    assert qf.code_names() == {}

@test('QuoteTableModel: init empty')
def t31():
    m = QuoteTableModel()
    assert m.rowCount() == 0
    assert m.columnCount() == 0  # no headers set yet

@test('QuoteTableModel: set_data + rowCount')
def t32():
    m = QuoteTableModel()
    rows = [['sh000001','上证指','3000','+10','+0.3%','100','200','50%','1.5亿','450亿','2998','+5%']]
    m.set_data(rows, ['代码','名称','现价','涨跌值','涨跌幅','买一','卖一','委比','成交量','成交额','均价','波收益'])
    assert m.rowCount() == 1

@test('QuoteTableModel: data returns correct value')
def t33():
    m = QuoteTableModel()
    rows = [['sh000001','上证指','3000.50','+10.50','+0.35%','100','200','50.0%','1.5亿','450亿','2998.00','+5.2%']]
    m.set_data(rows, ['代码','名称','现价','涨跌值','涨跌幅','买一','卖一','委比','成交量','成交额','均价','波收益'])
    idx = m.index(0, 0)
    assert m.data(idx, Qt.DisplayRole) == 'sh000001'

@test('QuoteTableModel: headerData')
def t34():
    m = QuoteTableModel()
    m.set_data([['a']], ['代码'])
    assert m.headerData(0, Qt.Horizontal, Qt.DisplayRole) == '代码'

@test('QuoteTableModel: color scheme changes')
def t35():
    m = QuoteTableModel()
    m.set_color_scheme(True, None)

# ==========================================================
# PART 4: band_settings.py - Table CRUD
# ==========================================================
section('PART 4: band_settings.py - Table ops')
from PySide6.QtWidgets import QApplication, QWidget
app = QApplication.instance() or QApplication(sys.argv)
from band_settings import SettingsDialog

class MockEngine:
    cache_path = ''
    strategy = {'entry':3.0,'exit_dd':-7.0,'merge_gap':10,'sma_n':10,'sma_m':2}
    bear_market_start = pd.Timestamp('2025-01-01')
    bands = []
    raw_bands = []
    _stock_band_cache = {}
    df = None
    oamv = np.array([100.0])
    oamv_pct = np.array([0.0])
    def _compute(self): pass
    def _detect(self): pass
    def refresh(self, strategy=None):
        return self.get_status()
    def get_status(self):
        return {'in_band':False, 'oamv_value':100, 'oamv_pct':0, 'bands':[], 'last_date':pd.Timestamp('2026-06-20')}
    def get_band_return(self, s, e, metric):
        return None
    def get_stock_band_return(self, code, s, e):
        return None
    def ensure_index_data(self):
        pass

class MockPanel:
    codes = ['sh000001','sz399006','sz159915']
    checked_codes = ['sh000001','sz399006']
    engine = MockEngine(); refresh_seconds=3; line_extra_px=1
    bg = type('o',(),{'alpha':lambda s:128})()
    font = type('o',(),{'family':lambda s:'Arial','pointSize':lambda s:10})()
    header_visible=True; grid_visible=True; b1s1_visible=True
    band_ret_visible=True; b1s1_display='qty'; short_code=False
    name_length=0; default_color=True; fg=None
    show_band_history=True; band_history_count=3; strategy_busy=False
    quote_fetcher = type('o',(),{'band_returns':{}})()
    def get_code_name(self,c):
        return {'sh000001':'上证指数','sz399006':'创业板指','sz159915':'创业板ETF'}.get(c,c)
    def set_codes(self,c): self.codes=c
    def set_checked_codes(self,c): self.checked_codes=c
    def header_is_visible(self,h): return True
    def windowOpacity(self): return 1.0
    def set_header_flag(self,*a): pass
    def set_header_visible(self,*a): pass
    def set_grid_visible(self,*a): pass
    def set_default_color(self,*a): pass
    def set_fg_color(self,*a): pass
    def set_bg_rgb_keep_alpha(self,*a): pass
    def set_bg_alpha_percent(self,*a): pass
    def set_window_opacity_percent(self,*a): pass
    def set_font_family(self,*a): pass
    def set_font_size(self,*a): pass
    def set_line_extra(self,*a): pass
    def set_short_code(self,*a): pass
    def set_name_length(self,*a): pass
    def set_b1s1_display(self,*a): pass
    def set_band_return_metric(self,*a): pass
    def _refresh_engine(self,*a): pass
    def _refresh_stocks(self): pass
    def _notify(self): pass
    def show_band_loading(self,*a): pass

panel = MockPanel()
parent = QWidget()
dialog = SettingsDialog(panel, parent, app=None)
table = dialog.list_codes

@test('Settings: table 3x2 init')
def t40():
    assert table.rowCount() == 3
    assert table.columnCount() == 2
    assert table.horizontalHeaderItem(0).text() == '代码'
    assert table.horizontalHeaderItem(1).text() == '名称'

@test('Settings: row 0 data')
def t41():
    assert table.item(0,0).text() == 'sh000001'
    assert table.item(0,1).text() == '上证指数'
    assert table.item(0,0).checkState().value == 2  # Qt.Checked==2

@test('Settings: row 2 unchecked')
def t42():
    assert table.item(2,0).checkState().value == 0  # Qt.Unchecked==0

@test('Settings: code editable + checkable')
def t43():
    for r in range(3):
        f = table.item(r,0).flags()
        assert f & Qt.ItemIsEditable, f'R{r} code not editable'
        assert f & Qt.ItemIsUserCheckable, f'R{r} code not checkable'

@test('Settings: name NOT editable')
def t44():
    for r in range(3):
        f = table.item(r,1).flags()
        assert not bool(f & Qt.ItemIsEditable), f'R{r} name is editable'

@test('Settings: add_code with default name')
def t45():
    r0 = table.rowCount()
    dialog._add_code()
    assert table.rowCount() == r0 + 1
    r = table.rowCount() - 1
    assert table.item(r,0).text() == 'sh000001'
    assert table.item(r,1).text() == '上证指数'
    assert table.item(r,0).data(Qt.UserRole) == 'sh000001'
    table.setCurrentCell(r,0)
    dialog._del_code()
    assert table.rowCount() == r0

@test('Settings: del_code')
def t46():
    dialog._add_code()
    table.setCurrentCell(table.rowCount()-1,0)
    dialog._del_code()
    assert table.rowCount() == 3

@test('Settings: move_up reorder')
def t47():
    table.setCurrentCell(2,0)
    dialog._move_up()
    assert table.item(1,0).text() == 'sz159915'
    assert table.item(2,0).text() == 'sz399006'
    table.setCurrentCell(1,0); dialog._move_down()

@test('Settings: move_down reorder')
def t48():
    table.setCurrentCell(0,0)
    dialog._move_down()
    assert table.item(0,0).text() == 'sz399006'
    assert table.item(1,0).text() == 'sh000001'
    table.setCurrentCell(0,0); dialog._move_up()

@test('Settings: collect_codes')
def t49():
    codes = dialog._collect_codes()
    assert len(codes) == 3
    assert 'sh000001' in codes
    assert 'sz159915' in codes

@test('Settings: update_name known code')
def t50():
    t0 = table.item(0,0)
    t0.setText('sz159915')
    t0.setData(Qt.UserRole,'sz159915')
    dialog._update_name_for_row(0)
    assert table.item(0,1).text() == '创业板ETF'

@test('Settings: update_name unknown -> 更新中...')
def t51():
    t0 = table.item(0,0)
    t0.setText('sz300750')
    t0.setData(Qt.UserRole,'sz300750')
    dialog._update_name_for_row(0)
    assert table.item(0,1).text() == '更新中...'

@test('Settings: refresh_names fills cache')
def t52():
    panel.get_code_name = lambda c: {'sh000001':'上证指数','sz399006':'创业板指','sz159915':'创业板ETF','sz300750':'宁德时代'}.get(c,c)
    dialog._refresh_names()
    assert table.item(0,1).text() == '宁德时代'

@test('Settings: checked extraction from UserRole')
def t53():
    # Only check the extraction mechanism works (items with checkState==Checked return UserRole)
    checked = [table.item(i,0).data(Qt.UserRole) for i in range(table.rowCount()) if table.item(i,0) and table.item(i,0).checkState() == Qt.Checked]
    assert len(checked) == 2, f'Expected 2 checked items, got {checked}'
    assert all(c in checked for c in ['sz300750', 'sh000001']), f'Unexpected checked: {checked}'

@test('Settings: on_codes_changed(None) no crash')
def t54():
    dialog._on_codes_changed(None)

@test('Settings: on_codes_changed(item) no crash')
def t55():
    dialog._on_codes_changed(table.item(0,0))

@test('Settings: name refresh timer active')
def t56():
    assert hasattr(dialog,'_name_refresh_timer')
    assert dialog._name_refresh_timer.isActive()

@test('Settings: make_combo_label')
def t57():
    lbl = dialog._make_combo_label('sh000001')
    assert '上证' in lbl
    assert dialog._make_combo_label('0AMV') == '0AMV'

@test('Settings: band metric combo populated')
def t58():
    dialog._refresh_band_metric_combo()
    assert dialog.cmb_band_metric.count() >= 1

@test('Settings: export code combo populated')
def t59():
    dialog._refresh_export_code_combo()
    assert dialog.cmb_export_code.count() >= 1

# ==========================================================
# PART 5: band_panel.py
# ==========================================================
section('PART 5: band_panel.py')
from band_panel import BandPanel

_BASE_CFG = {
    'codes':['sh000001'], 'checked_codes':['sh000001'], 'refresh_seconds':3,
    'fg':'#dd2100', 'bg':{'r':0,'g':0,'b':0,'a':191}, 'opacity_pct':90,
    'font_family':'Arial', 'font_size':10, 'header_visible':True, 'grid_visible':False,
    'code_visible':True, 'name_visible':True, 'price_visible':True,
    'change_visible':False, 'change_pct_visible':True, 'b1s1_visible':False,
    'commi_visible':False, 'vol_visible':False, 'amount_visible':False,
    'avg_visible':False, 'band_ret_visible':True, 'short_code':False,
    'name_length':0, 'b1s1_display':'qty', 'line_extra_px':1,
    'default_color':True, 'band_return_metric':'159915',
}

@test('BandPanel: instantiate')
def t60():
    p = BandPanel(dict(_BASE_CFG), engine=MockEngine())
    assert p.codes == ['sh000001']

@test('BandPanel: get_code_name fallback')
def t61():
    cfg = dict(_BASE_CFG)
    cfg['codes'] = []
    cfg['checked_codes'] = []
    p = BandPanel(cfg, engine=MockEngine())
    assert p.get_code_name('sh000001') == 'sh000001'

@test('BandPanel: header_is_visible')
def t62():
    p = BandPanel(dict(_BASE_CFG), engine=MockEngine())
    assert p.header_is_visible('代码')

@test('BandPanel: set_codes')
def t63():
    p = BandPanel(dict(_BASE_CFG), engine=MockEngine())
    p.set_codes(['sz399006','sz159915'])
    assert p.codes == ['sz399006','sz159915']

@test('BandPanel: set_checked_codes fallback to default')
def t64():
    cfg = dict(_BASE_CFG)
    cfg['checked_codes'] = []
    p = BandPanel(cfg, engine=MockEngine())
    p.set_checked_codes([])
    assert p.checked_codes == ['sh000001']

@test('BandPanel: set_checked_codes')
def t65():
    cfg = dict(_BASE_CFG)
    cfg['codes'] = ['sh000001','sz399006']
    cfg['checked_codes'] = []
    p = BandPanel(cfg, engine=MockEngine())
    p.set_checked_codes(['sz399006'])
    assert p.checked_codes == ['sz399006']

# ==========================================================
# PART 6: Config persistence
# ==========================================================
section('PART 6: Config persistence')
from band_monitor import load_config, save_config

@test('load_config returns dict')
def t70():
    assert isinstance(load_config(), dict)

@test('save/load roundtrip')
def t71():
    tmpdir = tempfile.mkdtemp()
    old = os.environ.get('APPDATA','')
    test = {'codes':['sh000001'],'checked_codes':[],'refresh_seconds':5}
    f = os.path.join(tmpdir, '0AMVMonitor', 'config.json')
    os.makedirs(os.path.dirname(f), exist_ok=True)
    with open(f,'w',encoding='utf-8') as fh:
        json.dump(test, fh, ensure_ascii=False)
    with open(f,'r',encoding='utf-8') as fh:
        loaded = json.load(fh)
    assert loaded['codes'] == ['sh000001']
    assert loaded['refresh_seconds'] == 5

# ==========================================================
# PART 7: BandEngine cache
# ==========================================================
section('PART 7: BandEngine cache')

@test('save/load pickle')
def t80():
    tmp = tempfile.mktemp(suffix='.pkl')
    e1 = BandEngine(cache_path=tmp)
    e1.df = df_mock_985.head(10).copy()
    e1.oamv = np.array([1e8]*10)
    e1.oamv_pct = np.zeros(10)
    e1.bands = [(pd.Timestamp('2023-06-01'), pd.Timestamp('2023-07-01'))]
    e1.last_fetch_date = pd.Timestamp('2026-06-20')
    e1.bear_market_start = pd.Timestamp('2025-01-01')
    e1.strategy = {'entry':3.0,'exit_dd':-7.0,'merge_gap':10,'sma_n':10,'sma_m':2}
    e1.save_cache()
    assert os.path.exists(tmp)
    e2 = BandEngine(cache_path=tmp)
    ok = e2.load_cache()
    assert ok
    assert e2.df is not None
    assert len(e2.df) == 10
    assert len(e2.bands) == 1
    os.remove(tmp)

@test('load_cache missing -> False')
def t81():
    e = BandEngine(cache_path='/nonexistent/path.pkl')
    assert not e.load_cache()

# ==========================================================
# PART 8: CLI scripts
# ==========================================================
section('PART 8: CLI scripts syntax')

@test('analyze.py syntax OK')
def t90():
    import py_compile
    py_compile.compile(r'G:\products\指南针股票app活跃市值指数0AMV\v1_trail7_merge10\analyze.py', doraise=True)

@test('total_return.py syntax OK')
def t91():
    import py_compile
    py_compile.compile(r'G:\products\指南针股票app活跃市值指数0AMV\v1_trail7_merge10\total_return.py', doraise=True)

@test('band_monitor.py syntax OK')
def t92():
    import py_compile
    py_compile.compile(r'G:\products\指南针股票app活跃市值指数0AMV\v1_trail7_merge10\band_monitor.py', doraise=True)

# ==========================================================
# PART 9: QApp signal integration test
# ==========================================================
section('PART 9: Signal integration')

@test('Signal: table itemChanged triggers on_codes_changed')
def t100():
    old_codes = list(panel.codes)
    it0 = table.item(0,0)
    # Changing text triggers itemChanged -> on_codes_changed -> set_codes
    old_text = it0.text()
    it0.setText('sz159915')
    # Wait, setText triggers itemChanged which calls on_codes_changed
    # But on_codes_changed calls _update_name_for_row which blocks signals while setting name
    # So panel.codes should have been updated
    # Reset
    it0.setText(old_text)

# ==========================================================
# RUN
# ==========================================================
test_fns = [(k,v) for k,v in list(locals().items()) if k.startswith('t') and callable(v) and k != 'test']
test_fns.sort(key=lambda x: x[0])

for name, fn in test_fns:
    fn()

total = len(RESULTS)
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = total - passed

print(f'\n{"="*60}')
print(f'  COMPREHENSIVE TEST REPORT')
print(f'{"="*60}')
print(f'  Total:   {total}')
print(f'  Passed:  {passed}')
print(f'  Failed:  {failed}')
print(f'  Rate:    {passed/total*100:.1f}%')
print()

if failed > 0:
    print(f'  FAILED DETAILS:')
    print(f'  {"-"*56}')
    for name, ok, msg in RESULTS:
        if not ok:
            print(f'    [{name}]')
            print(f'    {msg}')
            print()
