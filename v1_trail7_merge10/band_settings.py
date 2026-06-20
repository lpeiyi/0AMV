from functools import partial
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFontDatabase, QKeySequence
from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QPushButton, QSlider, QGroupBox, QLabel, QColorDialog, QComboBox, QAbstractItemView, QCheckBox, QListWidget, QListWidgetItem, QKeySequenceEdit

from band_panel import BandPanel
from band_stocks import ALL_HEADERS

class SettingsDialog(QDialog):
    def __init__(self, panel: BandPanel, parent: QWidget, app=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.panel = panel
        self.app = app
        self.setModal(False)

        main = QHBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)
        self.tabs = QTabWidget()
        main.addWidget(self.tabs)

        from PySide6.QtWidgets import QScrollArea
        self.tab_sizes = {0: QSize(340, 320), 1: QSize(480, 500), 2: QSize(360, 350), 3: QSize(340, 280), 4: QSize(340, 220)}
        self._apply_tab_size(0)

        # ---- Tab 0: 自选列表 ----
        tab0 = QWidget()
        v0 = QVBoxLayout(tab0)
        g_codes = QGroupBox("自选列表")
        g_codes.setContentsMargins(3, 12, 3, 6)
        lay_codes = QHBoxLayout(g_codes)
        self.list_codes = QListWidget()
        self.list_codes.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed)
        self.list_codes.setFixedWidth(160)
        for c in self.panel.codes:
            it = QListWidgetItem(c)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            it.setCheckState(Qt.Checked if c in getattr(self.panel, 'checked_codes', []) else Qt.Unchecked)
            it.setData(Qt.UserRole, c)
            self.list_codes.addItem(it)
        btn_col = QVBoxLayout()
        self.btn_add = QPushButton("添加"); self.btn_add.setFixedWidth(60)
        self.btn_del = QPushButton("删除"); self.btn_del.setFixedWidth(60)
        self.btn_up = QPushButton("上移"); self.btn_up.setFixedWidth(60)
        self.btn_dn = QPushButton("下移"); self.btn_dn.setFixedWidth(60)
        for b in (self.btn_add, self.btn_del, self.btn_up, self.btn_dn):
            btn_col.addWidget(b)
        btn_col.addStretch(1)
        lay_codes.addWidget(self.list_codes, 1)
        lay_codes.addLayout(btn_col)
        v0.addWidget(g_codes)
        self.tabs.addTab(tab0, "自选列表")

        # ---- Tab 1: 显示数据 ----
        tab1 = QScrollArea()
        tab1.setWidgetResizable(True)
        tab1_content = QWidget()
        v1 = QVBoxLayout(tab1_content)

        # 刷新间隔
        g_interval = QGroupBox("刷新间隔")
        g_interval.setContentsMargins(3, 12, 3, 6)
        self.cmb_interval = QComboBox()
        self.cmb_interval.setFixedWidth(120)
        for s in [1, 2, 3, 5, 10, 15, 30, 60]:
            self.cmb_interval.addItem(f"{s} 秒", userData=s)
        idx = self.cmb_interval.findData(self.panel.refresh_seconds)
        self.cmb_interval.setCurrentIndex(idx if idx >= 0 else 1)
        v_interval = QVBoxLayout(g_interval)
        v_interval.setContentsMargins(6, 6, 6, 6)
        v_interval.addWidget(self.cmb_interval)
        v1.addWidget(g_interval)

        # 显示指标（分组）
        g_flags = QGroupBox("显示指标")
        g_flags.setContentsMargins(3, 12, 3, 6)
        gl_flags = QGridLayout(g_flags)

        # 名称组
        g_name = QGroupBox("名称")
        gl_name = QGridLayout(g_name)
        self.cb_code = QCheckBox("代码")
        self.cb_code.setChecked(self.panel.header_is_visible("代码"))
        gl_name.addWidget(self.cb_code, 0, 0)
        self.cb_short_code = QCheckBox("仅显示数字")
        self.cb_short_code.setChecked(self.panel.short_code)
        self.cb_short_code.setEnabled(self.panel.header_is_visible("代码"))
        gl_name.addWidget(self.cb_short_code, 0, 1)
        self.cb_name = QCheckBox("名称")
        self.cb_name.setChecked(self.panel.header_is_visible("名称"))
        gl_name.addWidget(self.cb_name, 1, 0)
        self.cmb_name_len = QComboBox()
        self.cmb_name_len.setFixedWidth(80)
        for l in [0, 1, 2, 3, 4]:
            self.cmb_name_len.addItem(f"{l}个字" if l > 0 else "完整", userData=l)
        idx_nl = self.cmb_name_len.findData(self.panel.name_length)
        self.cmb_name_len.setCurrentIndex(idx_nl if idx_nl >= 0 else 0)
        self.cmb_name_len.setEnabled(self.panel.header_is_visible("名称"))
        gl_name.addWidget(self.cmb_name_len, 1, 1)
        gl_flags.addWidget(g_name, 0, 0)

        # 价格组
        g_price = QGroupBox("价格")
        gl_price = QGridLayout(g_price)
        self.cb_price = QCheckBox("现价")
        self.cb_price.setChecked(self.panel.header_is_visible("现价"))
        gl_price.addWidget(self.cb_price, 0, 0)
        self.cb_change = QCheckBox("涨跌值")
        self.cb_change.setChecked(self.panel.header_is_visible("涨跌值"))
        gl_price.addWidget(self.cb_change, 1, 0)
        self.cb_change_pct = QCheckBox("涨跌幅")
        self.cb_change_pct.setChecked(self.panel.header_is_visible("涨跌幅"))
        gl_price.addWidget(self.cb_change_pct, 2, 0)
        gl_flags.addWidget(g_price, 1, 0)

        # 盘口组
        g_order = QGroupBox("盘口")
        gl_order = QGridLayout(g_order)
        self.cb_b1s1 = QCheckBox("买一/卖一")
        self.cb_b1s1.setChecked(self.panel.b1s1_visible)
        gl_order.addWidget(self.cb_b1s1, 0, 0)
        self.cmb_b1s1_display = QComboBox()
        self.cmb_b1s1_display.setFixedWidth(100)
        self.cmb_b1s1_display.addItem("数量", userData="qty")
        self.cmb_b1s1_display.addItem("价格", userData="price")
        self.cmb_b1s1_display.addItem("数量和价格", userData="both")
        cur_mode = getattr(self.panel, 'b1s1_display', 'qty')
        idx_mode = self.cmb_b1s1_display.findData(cur_mode)
        self.cmb_b1s1_display.setCurrentIndex(idx_mode if idx_mode >= 0 else 0)
        self.cmb_b1s1_display.setEnabled(self.panel.b1s1_visible)
        gl_order.addWidget(self.cmb_b1s1_display, 0, 1)
        self.cb_commi = QCheckBox("委比")
        self.cb_commi.setChecked(self.panel.header_is_visible("委比"))
        gl_order.addWidget(self.cb_commi, 1, 0)
        gl_flags.addWidget(g_order, 0, 1)

        # 成交组
        g_deal = QGroupBox("成交")
        gl_deal = QGridLayout(g_deal)
        self.cb_vol = QCheckBox("成交量")
        self.cb_vol.setChecked(self.panel.header_is_visible("成交量"))
        gl_deal.addWidget(self.cb_vol, 0, 0)
        self.cb_amount = QCheckBox("成交额")
        self.cb_amount.setChecked(self.panel.header_is_visible("成交额"))
        gl_deal.addWidget(self.cb_amount, 1, 0)
        gl_flags.addWidget(g_deal, 1, 1)

        # 其他组
        g_other = QGroupBox("其他")
        gl_other = QGridLayout(g_other)
        self.cb_avg = QCheckBox("均价")
        self.cb_avg.setChecked(self.panel.header_is_visible("均价"))
        gl_other.addWidget(self.cb_avg, 0, 0)
        self.cb_band_ret = QCheckBox("波收益")
        self.cb_band_ret.setChecked(self.panel.band_ret_visible)
        gl_other.addWidget(self.cb_band_ret, 1, 0)
        gl_flag_band = QHBoxLayout()
        gl_flag_band.addWidget(QLabel("收益品种:"))
        self.cmb_band_metric = QComboBox()
        for m in ["159915", "上证指数", "创业板指", "0AMV"]:
            self.cmb_band_metric.addItem(m, userData=m)
        idx_m = self.cmb_band_metric.findData(self.panel.band_return_metric)
        self.cmb_band_metric.setCurrentIndex(idx_m if idx_m >= 0 else 0)
        gl_flag_band.addWidget(self.cmb_band_metric)
        gl_other.addLayout(gl_flag_band, 2, 0, 1, 2)
        gl_flags.addWidget(g_other, 2, 0)

        v1.addWidget(g_flags)

        self.chk_header = QCheckBox("显示表头")
        self.chk_header.setChecked(self.panel.header_visible)
        self.chk_grid = QCheckBox("显示网格")
        self.chk_grid.setChecked(self.panel.grid_visible)
        hl_options = QHBoxLayout()
        hl_options.addWidget(self.chk_header)
        hl_options.addWidget(self.chk_grid)
        hl_options.addStretch()
        v1.addLayout(hl_options)
        v1.addStretch()
        tab1.setWidget(tab1_content)
        self.tabs.addTab(tab1, "显示数据")

        # ---- Tab 2: 外观 ----
        tab2 = QWidget()
        v2 = QVBoxLayout(tab2)

        g_color = QGroupBox("颜色与透明度")
        g_color.setContentsMargins(3, 12, 3, 6)
        gl_color = QGridLayout(g_color)
        self.chk_default_color = QCheckBox("默认颜色")
        self.chk_default_color.setChecked(self.panel.default_color)
        self.btn_fg = QPushButton("文字颜色…")
        self.btn_fg.setFixedWidth(90)
        self.btn_fg.setEnabled(not self.panel.default_color)
        self.btn_bg = QPushButton("背景颜色…")
        self.btn_bg.setFixedWidth(90)
        self.slider_bg_alpha = QSlider(Qt.Horizontal)
        self.slider_bg_alpha.setRange(1, 100)
        self.slider_bg_alpha.setMinimumWidth(150)
        self.slider_bg_alpha.setValue(int(round(self.panel.bg.alpha() / 2.55)))
        self.lbl_bg_alpha = QLabel(f"{self.slider_bg_alpha.value()}%")
        self.slider_win_opacity = QSlider(Qt.Horizontal)
        self.slider_win_opacity.setRange(20, 100)
        self.slider_win_opacity.setMinimumWidth(150)
        self.slider_win_opacity.setValue(int(round(self.panel.windowOpacity() * 100)))
        self.lbl_win_opacity = QLabel(f"{self.slider_win_opacity.value()}%")
        gl_color.addWidget(self.chk_default_color, 0, 0, 1, 2)
        gl_color.addWidget(self.btn_fg, 0, 2, 1, 2)
        gl_color.addWidget(self.btn_bg, 0, 4, 1, 2)
        gl_color.addWidget(QLabel("背景不透明度:"), 1, 0, 1, 2)
        gl_color.addWidget(self.slider_bg_alpha, 1, 2, 1, 3)
        gl_color.addWidget(self.lbl_bg_alpha, 1, 5, 1, 1)
        gl_color.addWidget(QLabel("整体不透明度:"), 2, 0, 1, 2)
        gl_color.addWidget(self.slider_win_opacity, 2, 2, 1, 3)
        gl_color.addWidget(self.lbl_win_opacity, 2, 5, 1, 1)
        v2.addWidget(g_color)

        g_font = QGroupBox("字体与行距")
        g_font.setContentsMargins(3, 12, 3, 6)
        gl_font = QGridLayout(g_font)
        self.cmb_family = QComboBox()
        self.cmb_family.setFixedWidth(200)
        for fam in sorted(QFontDatabase.families()):
            self.cmb_family.addItem(fam)
        fi = self.cmb_family.findText(self.panel.font.family())
        self.cmb_family.setCurrentIndex(fi if fi >= 0 else 0)
        self.slider_font = QSlider(Qt.Horizontal)
        self.slider_font.setRange(8, 15)
        self.slider_font.setMinimumWidth(150)
        self.slider_font.setValue(self.panel.font.pointSize())
        self.lbl_font = QLabel(f"{self.slider_font.value()} pt")
        self.slider_line = QSlider(Qt.Horizontal)
        self.slider_line.setRange(0, 20)
        self.slider_line.setMinimumWidth(150)
        self.slider_line.setValue(getattr(self.panel, "line_extra_px", 1))
        self.lbl_line = QLabel(f"+{self.slider_line.value()} px")
        gl_font.addWidget(QLabel("字体:"), 0, 0)
        gl_font.addWidget(self.cmb_family, 0, 1, 1, 4)
        gl_font.addWidget(QLabel("字号:"), 1, 0)
        gl_font.addWidget(self.slider_font, 1, 1, 1, 3)
        gl_font.addWidget(self.lbl_font, 1, 4)
        gl_font.addWidget(QLabel("行距:"), 2, 0)
        gl_font.addWidget(self.slider_line, 2, 1, 1, 3)
        gl_font.addWidget(self.lbl_line, 2, 4)
        v2.addWidget(g_font)
        v2.addStretch()
        self.tabs.addTab(tab2, "外观")

        # ---- Tab 3: 策略参数 ----
        tab3 = QWidget()
        v3 = QVBoxLayout(tab3)

        g_strat = QGroupBox("波段策略参数")
        g_strat.setContentsMargins(3, 12, 3, 6)
        gl_s = QGridLayout(g_strat)

        strat = self.panel.engine.strategy
        gl_s.addWidget(QLabel("入场阈值 ≥"), 0, 0)
        self.slider_entry = QSlider(Qt.Horizontal)
        self.slider_entry.setRange(20, 100)
        self.slider_entry.setValue(int(strat["entry"] * 10))
        self.lbl_entry = QLabel(f"{strat['entry']:.1f}%")
        gl_s.addWidget(self.slider_entry, 0, 1)
        gl_s.addWidget(self.lbl_entry, 0, 2)

        gl_s.addWidget(QLabel("退出回撤 ≤"), 1, 0)
        self.slider_exit = QSlider(Qt.Horizontal)
        self.slider_exit.setRange(20, 200)
        self.slider_exit.setValue(int(abs(strat["exit_dd"]) * 10))
        self.lbl_exit = QLabel(f"{strat['exit_dd']:.0f}%")
        gl_s.addWidget(self.slider_exit, 1, 1)
        gl_s.addWidget(self.lbl_exit, 1, 2)

        gl_s.addWidget(QLabel("合并间隔 ≤"), 2, 0)
        self.slider_merge = QSlider(Qt.Horizontal)
        self.slider_merge.setRange(1, 30)
        self.slider_merge.setValue(strat["merge_gap"])
        self.lbl_merge = QLabel(f"{strat['merge_gap']}天")
        gl_s.addWidget(self.slider_merge, 2, 1)
        gl_s.addWidget(self.lbl_merge, 2, 2)

        gl_s.addWidget(QLabel("SMA N:"), 3, 0)
        self.cmb_sma_n = QComboBox()
        for n in [5, 8, 10, 15, 20]:
            self.cmb_sma_n.addItem(str(n), userData=n)
        idx_n = self.cmb_sma_n.findData(strat["sma_n"])
        self.cmb_sma_n.setCurrentIndex(idx_n if idx_n >= 0 else 2)
        gl_s.addWidget(self.cmb_sma_n, 3, 1)

        gl_s.addWidget(QLabel("SMA M:"), 4, 0)
        self.cmb_sma_m = QComboBox()
        for m in [1, 2, 3]:
            self.cmb_sma_m.addItem(str(m), userData=m)
        idx_m = self.cmb_sma_m.findData(strat["sma_m"])
        self.cmb_sma_m.setCurrentIndex(idx_m if idx_m >= 0 else 1)
        gl_s.addWidget(self.cmb_sma_m, 4, 1)

        v3.addWidget(g_strat)
        v3.addStretch()
        self.tabs.addTab(tab3, "策略参数")

        # ---- Tab 4: 常规 ----
        tab4 = QWidget()
        v4 = QVBoxLayout(tab4)

        g_hk = QGroupBox("快捷键")
        g_hk.setContentsMargins(3, 12, 3, 6)
        gl_hk = QGridLayout(g_hk)
        gl_hk.addWidget(QLabel("显示/隐藏:"), 0, 0)
        self.edit_hotkey = QKeySequenceEdit()
        self.edit_hotkey.setKeySequence(QKeySequence("Ctrl+Alt+F"))
        gl_hk.addWidget(self.edit_hotkey, 0, 1)
        self.chk_start = QCheckBox("开机启动")
        self.chk_start.setChecked(False)
        v4.addWidget(self.chk_start)
        v4.addWidget(g_hk)
        v4.addStretch()
        self.tabs.addTab(tab4, "常规")

        # ---- 信号连接 ----
        self.list_codes.itemChanged.connect(self._on_codes_changed)
        self.btn_add.clicked.connect(self._add_code)
        self.btn_del.clicked.connect(self._del_code)
        self.btn_up.clicked.connect(self._move_up)
        self.btn_dn.clicked.connect(self._move_down)
        self.cmb_interval.currentIndexChanged.connect(self._on_interval_changed)
        self.cmb_band_metric.currentIndexChanged.connect(self._on_band_metric_changed)
        self.chk_default_color.toggled.connect(self._on_default_color)
        self.btn_fg.clicked.connect(self._pick_fg)
        self.btn_bg.clicked.connect(self._pick_bg)
        self.slider_bg_alpha.valueChanged.connect(self._apply_bg_alpha)
        self.slider_win_opacity.valueChanged.connect(self._apply_win_opacity)
        self.cmb_family.currentTextChanged.connect(self._on_family)
        self.slider_font.valueChanged.connect(self._apply_font)
        self.slider_line.valueChanged.connect(self._on_line)
        self.chk_header.toggled.connect(self._on_header)
        self.chk_grid.toggled.connect(self._on_grid)
        self.slider_entry.valueChanged.connect(self._on_strat_entry)
        self.slider_exit.valueChanged.connect(self._on_strat_exit)
        self.slider_merge.valueChanged.connect(self._on_strat_merge)
        self.cmb_sma_n.currentIndexChanged.connect(self._on_strat_sma)
        self.cmb_sma_m.currentIndexChanged.connect(self._on_strat_sma)
        self.edit_hotkey.editingFinished.connect(self._on_hotkey)
        self.tabs.currentChanged.connect(self._apply_tab_size)
        # column visibility
        self.cb_code.toggled.connect(partial(self._on_cb_changed, "代码"))
        self.cb_name.toggled.connect(partial(self._on_cb_changed, "名称"))
        self.cb_price.toggled.connect(partial(self._on_cb_changed, "现价"))
        self.cb_change.toggled.connect(partial(self._on_cb_changed, "涨跌值"))
        self.cb_change_pct.toggled.connect(partial(self._on_cb_changed, "涨跌幅"))
        self.cb_b1s1.toggled.connect(self._on_b1s1_toggled)
        self.cb_commi.toggled.connect(partial(self._on_cb_changed, "委比"))
        self.cb_vol.toggled.connect(partial(self._on_cb_changed, "成交量"))
        self.cb_amount.toggled.connect(partial(self._on_cb_changed, "成交额"))
        self.cb_avg.toggled.connect(partial(self._on_cb_changed, "均价"))
        self.cb_band_ret.toggled.connect(partial(self._on_cb_changed, "波收益"))
        self.cb_short_code.toggled.connect(self._on_short_code)
        self.cmb_name_len.currentIndexChanged.connect(self._on_name_length)
        self.cmb_b1s1_display.currentIndexChanged.connect(self._on_b1s1_display)

    def _apply_tab_size(self, idx):
        size = self.tab_sizes.get(idx, QSize(480, 500))
        if idx == 1:
            self.setMinimumSize(480, 400)
            self.resize(480, 500)
        else:
            self.setFixedSize(size)

    def _collect_codes(self):
        from band_stocks import normalize_code
        codes = []
        seen = set()
        for i in range(self.list_codes.count()):
            txt = self.list_codes.item(i).text()
            norm = normalize_code(txt)
            if norm:
                if norm not in seen:
                    seen.add(norm)
                    codes.append(norm)
                it = self.list_codes.item(i)
                if it.text() != norm:
                    self.list_codes.blockSignals(True)
                    it.setText(norm)
                    it.setData(Qt.UserRole, norm)
                    self.list_codes.blockSignals(False)
            else:
                it = self.list_codes.item(i)
                prev = it.data(Qt.UserRole)
                if prev:
                    self.list_codes.blockSignals(True)
                    it.setText(prev)
                    self.list_codes.blockSignals(False)
                else:
                    self.list_codes.takeItem(i)
                    return self._collect_codes()
        return codes

    def _on_codes_changed(self, _):
        codes = self._collect_codes()
        self.panel.set_codes(codes)
        checked = [self.list_codes.item(i).text().split()[0] for i in range(self.list_codes.count()) if self.list_codes.item(i).checkState() == Qt.Checked]
        self.panel.set_checked_codes(checked)

    def _add_code(self):
        it = QListWidgetItem("sh000001")
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        it.setCheckState(Qt.Unchecked)
        it.setData(Qt.UserRole, "sh000001")
        self.list_codes.addItem(it)
        self.list_codes.setCurrentItem(it)
        self.list_codes.editItem(it)
        self._on_codes_changed(it)

    def _del_code(self):
        row = self.list_codes.currentRow()
        if row >= 0:
            self.list_codes.takeItem(row)
            self._on_codes_changed(None)

    def _move_up(self):
        row = self.list_codes.currentRow()
        if row > 0:
            it = self.list_codes.takeItem(row)
            self.list_codes.insertItem(row - 1, it)
            self.list_codes.setCurrentRow(row - 1)
            self._on_codes_changed(None)

    def _move_down(self):
        row = self.list_codes.currentRow()
        if 0 <= row < self.list_codes.count() - 1:
            it = self.list_codes.takeItem(row)
            self.list_codes.insertItem(row + 1, it)
            self.list_codes.setCurrentRow(row + 1)
            self._on_codes_changed(None)

    def _on_interval_changed(self, idx):
        sec = self.cmb_interval.currentData()
        if isinstance(sec, int):
            self.panel.set_refresh_interval(sec)

    def _on_band_metric_changed(self, idx):
        val = self.cmb_band_metric.currentData()
        if val:
            self.panel.set_band_return_metric(val)

    def _on_default_color(self, checked):
        self.btn_fg.setEnabled(not checked)
        self.panel.set_default_color(checked)

    def _on_header(self, checked):
        self.panel.set_header_visible(checked)

    def _on_grid(self, checked):
        self.panel.set_grid_visible(checked)

    def _pick_fg(self):
        c = QColorDialog.getColor(self.panel.fg, self, "选择文字颜色")
        if c.isValid():
            self.panel.set_fg_color(c)

    def _pick_bg(self):
        base = QColor(self.panel.bg)
        base.setAlpha(255)
        c = QColorDialog.getColor(base, self, "选择背景颜色")
        if c.isValid():
            self.panel.set_bg_rgb_keep_alpha(c)

    def _apply_bg_alpha(self, v):
        self.lbl_bg_alpha.setText(f"{v}%")
        self.panel.set_bg_alpha_percent(v)

    def _apply_win_opacity(self, v):
        self.lbl_win_opacity.setText(f"{v}%")
        self.panel.set_window_opacity_percent(v)

    def _on_family(self, fam):
        self.panel.set_font_family(fam)

    def _apply_font(self, v):
        self.lbl_font.setText(f"{v} pt")
        self.panel.set_font_size(v)

    def _on_line(self, v):
        self.lbl_line.setText(f"+{v} px")
        self.panel.set_line_extra(v)

    def _on_strat_entry(self, v):
        val = v / 10.0
        self.lbl_entry.setText(f"{val:.1f}%")
        self.panel.engine.strategy["entry"] = val
        self._refresh_strategy()

    def _on_strat_exit(self, v):
        val = -v / 10.0
        self.lbl_exit.setText(f"{val:.0f}%")
        self.panel.engine.strategy["exit_dd"] = val
        self._refresh_strategy()

    def _on_strat_merge(self, v):
        self.lbl_merge.setText(f"{v}天")
        self.panel.engine.strategy["merge_gap"] = v
        self._refresh_strategy()

    def _on_strat_sma(self):
        n = self.cmb_sma_n.currentData()
        m = self.cmb_sma_m.currentData()
        if n and m:
            self.panel.engine.strategy["sma_n"] = n
            self.panel.engine.strategy["sma_m"] = m
            self._refresh_strategy()

    def _refresh_strategy(self):
        self.panel.engine._compute()
        self.panel.engine._detect()
        self.panel._refresh_engine()

    def _on_hotkey(self):
        hk = self.edit_hotkey.keySequence().toString()
        try:
            if hasattr(self, 'app') and self.app is not None:
                try:
                    self.app.set_hotkey(hk)
                except:
                    pass
        except:
            pass

    def _on_cb_changed(self, header, state):
        self.panel.set_header_flag(header, state)
        if header == "代码":
            self.cb_short_code.setEnabled(state)
        elif header == "名称":
            self.cmb_name_len.setEnabled(state)

    def _on_b1s1_toggled(self, state):
        self.panel.set_header_flag("买一", state)
        self.cmb_b1s1_display.setEnabled(state)

    def _on_short_code(self, checked):
        self.panel.set_short_code(checked)

    def _on_name_length(self, idx):
        length = self.cmb_name_len.currentData()
        if length is not None:
            self.panel.set_name_length(length)

    def _on_b1s1_display(self, idx):
        val = self.cmb_b1s1_display.currentData()
        if val:
            self.panel.set_b1s1_display(val)
