import os
from functools import partial
from PySide6.QtCore import Qt, QSize, QDate, QTimer
from PySide6.QtGui import QColor, QFontDatabase, QKeySequence
from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QPushButton, QSlider, QGroupBox, QLabel, QColorDialog, QComboBox, QAbstractItemView, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QKeySequenceEdit, QLineEdit, QFileDialog, QDateEdit, QMessageBox

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
        self.tabs.setElideMode(Qt.ElideNone)
        self.tabs.setUsesScrollButtons(False)
        main.addWidget(self.tabs)

        from PySide6.QtWidgets import QScrollArea
        self.tab_sizes = {0: QSize(540, 320), 1: QSize(560, 480), 2: QSize(540, 350), 3: QSize(540, 280), 4: QSize(560, 300), 5: QSize(540, 280)}
        self._apply_tab_size(0)

        # ---- Tab 0: 自选列表 ----
        tab0 = QWidget()
        v0 = QVBoxLayout(tab0)
        g_codes = QGroupBox("自选列表")
        g_codes.setContentsMargins(3, 12, 3, 6)
        lay_codes = QHBoxLayout(g_codes)
        self.list_codes = QTableWidget(0, 2)
        self.list_codes.setHorizontalHeaderLabels(["代码", "名称"])
        self.list_codes.horizontalHeader().setStretchLastSection(True)
        self.list_codes.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed)
        self.list_codes.setMinimumWidth(260)
        self.list_codes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.list_codes.setSelectionMode(QAbstractItemView.SingleSelection)
        for c in self.panel.codes:
            row = self.list_codes.rowCount()
            self.list_codes.insertRow(row)
            it0 = QTableWidgetItem(c)
            it0.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
            it0.setCheckState(Qt.Checked if c in getattr(self.panel, 'checked_codes', []) else Qt.Unchecked)
            it0.setData(Qt.UserRole, c)
            self.list_codes.setItem(row, 0, it0)
            name = self.panel.get_code_name(c)
            name_text = name if name != c else "更新中..."
            it1 = QTableWidgetItem(name_text)
            it1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.list_codes.setItem(row, 1, it1)
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
        self.lbl_entry.setFixedWidth(45)
        self.btn_entry_sub = QPushButton("－")
        self.btn_entry_sub.setFixedWidth(24)
        self.btn_entry_add = QPushButton("＋")
        self.btn_entry_add.setFixedWidth(24)
        gl_s.addWidget(self.slider_entry, 0, 1)
        gl_s.addWidget(self.lbl_entry, 0, 2)
        hl_entry = QHBoxLayout()
        hl_entry.addWidget(self.btn_entry_sub)
        hl_entry.addWidget(self.btn_entry_add)
        gl_s.addLayout(hl_entry, 0, 3)

        gl_s.addWidget(QLabel("退出回撤 ≤"), 1, 0)
        self.slider_exit = QSlider(Qt.Horizontal)
        self.slider_exit.setRange(20, 200)
        self.slider_exit.setValue(int(abs(strat["exit_dd"]) * 10))
        self.lbl_exit = QLabel(f"{strat['exit_dd']:.1f}%")
        self.lbl_exit.setFixedWidth(45)
        self.btn_exit_sub = QPushButton("－")
        self.btn_exit_sub.setFixedWidth(24)
        self.btn_exit_add = QPushButton("＋")
        self.btn_exit_add.setFixedWidth(24)
        gl_s.addWidget(self.slider_exit, 1, 1)
        gl_s.addWidget(self.lbl_exit, 1, 2)
        hl_exit = QHBoxLayout()
        hl_exit.addWidget(self.btn_exit_sub)
        hl_exit.addWidget(self.btn_exit_add)
        gl_s.addLayout(hl_exit, 1, 3)

        gl_s.addWidget(QLabel("合并间隔 ≤"), 2, 0)
        self.slider_merge = QSlider(Qt.Horizontal)
        self.slider_merge.setRange(1, 30)
        self.slider_merge.setValue(strat["merge_gap"])
        self.lbl_merge = QLabel(f"{strat['merge_gap']}天")
        self.lbl_merge.setFixedWidth(45)
        self.btn_merge_sub = QPushButton("－")
        self.btn_merge_sub.setFixedWidth(24)
        self.btn_merge_add = QPushButton("＋")
        self.btn_merge_add.setFixedWidth(24)
        gl_s.addWidget(self.slider_merge, 2, 1)
        gl_s.addWidget(self.lbl_merge, 2, 2)
        hl_merge = QHBoxLayout()
        hl_merge.addWidget(self.btn_merge_sub)
        hl_merge.addWidget(self.btn_merge_add)
        gl_s.addLayout(hl_merge, 2, 3)

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

        g_info = QGroupBox("参数说明")
        g_info.setContentsMargins(3, 12, 3, 6)
        info_text = QLabel(
            "入场阈值：0AMV 一天涨了 ≥ 此百分比就入场买入（默认 +3%）\n"
            "退出回撤：入场后涨到最高点又跌回 ≤ 此百分比就卖出（默认 -7%）\n"
            "合并间隔：两次买卖之间相隔 ≤ 此天数，视为同一轮操作合并计算（默认 10天）\n"
            "SMA N：看过去多少天的成交额来算平均值，N 越大曲线越平滑（默认 10天）\n"
            "SMA M：最近一天的成交额占多少比重，M 越大对最新行情越敏感（默认 2）"
        )
        info_text.setWordWrap(True)
        vi = QVBoxLayout(g_info)
        vi.addWidget(info_text)
        v3.addWidget(g_info)
        v3.addStretch()
        self.tabs.addTab(tab3, "策略参数")

        # ---- Tab 4: 波段 ----
        tab4 = QWidget()
        v4 = QVBoxLayout(tab4)

        g_band_cfg = QGroupBox("历史波段配置")
        g_band_cfg.setContentsMargins(3, 12, 3, 6)
        gl_band_cfg = QGridLayout(g_band_cfg)
        gl_band_cfg.addWidget(QLabel("收益品种:"), 0, 0)
        self.cmb_band_metric = QComboBox()
        self.cmb_band_metric.setMinimumWidth(240)
        self.cmb_band_metric.view().setMinimumWidth(280)
        gl_band_cfg.addWidget(self.cmb_band_metric, 0, 1)
        self._refresh_band_metric_combo()
        gl_band_cfg.addWidget(QLabel("(选择后底部历史波段同步更新)"), 1, 0, 1, 2)
        v4.addWidget(g_band_cfg)

        g_export = QGroupBox("导出波段收益")
        g_export.setContentsMargins(3, 12, 3, 6)
        gl_export = QGridLayout(g_export)
        gl_export.addWidget(QLabel("品种:"), 0, 0)
        self.cmb_export_code = QComboBox()
        self.cmb_export_code.setMinimumWidth(240)
        self.cmb_export_code.view().setMinimumWidth(280)
        gl_export.addWidget(self.cmb_export_code, 0, 1)
        self._refresh_export_code_combo()
        gl_export.addWidget(QLabel("起始日期:"), 1, 0)
        self.date_export_start = QDateEdit()
        self.date_export_start.setCalendarPopup(True)
        self.date_export_start.setDate(QDate.currentDate().addYears(-1))
        gl_export.addWidget(self.date_export_start, 1, 1)
        gl_export.addWidget(QLabel("结束日期:"), 2, 0)
        self.date_export_end = QDateEdit()
        self.date_export_end.setCalendarPopup(True)
        self.date_export_end.setDate(QDate.currentDate())
        gl_export.addWidget(self.date_export_end, 2, 1)
        self.btn_export = QPushButton("导出 CSV")
        self.btn_export.setFixedWidth(100)
        gl_export.addWidget(self.btn_export, 3, 0, 1, 2)
        v4.addWidget(g_export)
        v4.addStretch()
        self.tabs.insertTab(4, tab4, "波段")

        # ---- Tab 5: 常规 ----
        tab5 = QWidget()
        v5 = QVBoxLayout(tab5)

        g_cache = QGroupBox("缓存")
        g_cache.setContentsMargins(3, 12, 3, 6)
        gl_cache = QGridLayout(g_cache)
        gl_cache.addWidget(QLabel("缓存目录:"), 0, 0)
        self.edit_cache_path = QLineEdit()
        cache_dir = os.path.dirname(self.panel.engine.cache_path) if self.panel.engine else ""
        self.edit_cache_path.setText(cache_dir)
        gl_cache.addWidget(self.edit_cache_path, 0, 1)
        self.btn_cache_browse = QPushButton("浏览…")
        self.btn_cache_browse.setFixedWidth(60)
        gl_cache.addWidget(self.btn_cache_browse, 0, 2)
        v5.addWidget(g_cache)

        g_hk = QGroupBox("快捷键")
        g_hk.setContentsMargins(3, 12, 3, 6)
        gl_hk = QGridLayout(g_hk)
        gl_hk.addWidget(QLabel("显示/隐藏:"), 0, 0)
        self.edit_hotkey = QKeySequenceEdit()
        self.edit_hotkey.setKeySequence(QKeySequence("Ctrl+Alt+F"))
        gl_hk.addWidget(self.edit_hotkey, 0, 1)
        self.chk_start = QCheckBox("开机启动")
        self.chk_start.setChecked(False)
        v5.addWidget(self.chk_start)
        v5.addWidget(g_hk)
        v5.addStretch()
        self.tabs.addTab(tab5, "常规")

        # ---- 信号连接 ----
        self.list_codes.itemChanged.connect(self._on_codes_changed)
        self.btn_add.clicked.connect(self._add_code)
        self.btn_del.clicked.connect(self._del_code)
        self.btn_up.clicked.connect(self._move_up)
        self.btn_dn.clicked.connect(self._move_down)
        self.cmb_interval.currentIndexChanged.connect(self._on_interval_changed)
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
        self.slider_entry.valueChanged.connect(self._on_strat_entry_label)
        self.slider_entry.sliderReleased.connect(self._on_strat_entry_apply)
        self.btn_entry_sub.clicked.connect(lambda: self._strat_btn_adj(self.slider_entry, -1, self._on_strat_entry_apply))
        self.btn_entry_add.clicked.connect(lambda: self._strat_btn_adj(self.slider_entry, 1, self._on_strat_entry_apply))
        self.slider_exit.valueChanged.connect(self._on_strat_exit_label)
        self.slider_exit.sliderReleased.connect(self._on_strat_exit_apply)
        self.btn_exit_sub.clicked.connect(lambda: self._strat_btn_adj(self.slider_exit, -1, self._on_strat_exit_apply))
        self.btn_exit_add.clicked.connect(lambda: self._strat_btn_adj(self.slider_exit, 1, self._on_strat_exit_apply))
        self.slider_merge.valueChanged.connect(self._on_strat_merge_label)
        self.slider_merge.sliderReleased.connect(self._on_strat_merge_apply)
        self.btn_merge_sub.clicked.connect(lambda: self._strat_btn_adj(self.slider_merge, -1, self._on_strat_merge_apply))
        self.btn_merge_add.clicked.connect(lambda: self._strat_btn_adj(self.slider_merge, 1, self._on_strat_merge_apply))
        self.cmb_sma_n.currentIndexChanged.connect(self._on_strat_sma)
        self.cmb_sma_m.currentIndexChanged.connect(self._on_strat_sma)
        self.edit_hotkey.editingFinished.connect(self._on_hotkey)
        self.btn_cache_browse.clicked.connect(self._browse_cache)
        self.edit_cache_path.editingFinished.connect(self._on_cache_path_changed)
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
        self.cmb_band_metric.currentIndexChanged.connect(self._on_band_metric_changed)
        self.btn_export.clicked.connect(self._on_export_bands)

        self._name_refresh_timer = QTimer(self)
        self._name_refresh_timer.timeout.connect(self._refresh_names)
        self._name_refresh_timer.start(5000)

    def _apply_tab_size(self, idx):
        size = self.tab_sizes.get(idx, QSize(560, 480))
        self.setMinimumSize(max(560, size.width()), 400)
        self.resize(size)
        self.tabs.setMinimumSize(size.width(), size.height() - 30)

    def _collect_codes(self):
        from band_stocks import normalize_code
        codes = []
        seen = set()
        for row in range(self.list_codes.rowCount()):
            it0 = self.list_codes.item(row, 0)
            if it0 is None:
                continue
            txt = it0.text()
            raw = it0.data(Qt.UserRole) or txt
            if txt != raw:
                norm = normalize_code(txt)
                if norm:
                    self.list_codes.blockSignals(True)
                    it0.setData(Qt.UserRole, norm)
                    if it0.text() != norm:
                        it0.setText(norm)
                    self.list_codes.blockSignals(False)
                    raw = norm
            else:
                norm = normalize_code(raw)
            if norm:
                if norm not in seen:
                    seen.add(norm)
                    codes.append(norm)
                if raw != norm:
                    self.list_codes.blockSignals(True)
                    it0.setData(Qt.UserRole, norm)
                    if it0.text() != norm:
                        it0.setText(norm)
                    self.list_codes.blockSignals(False)
            else:
                prev = it0.data(Qt.UserRole)
                if prev:
                    self.list_codes.blockSignals(True)
                    it0.setText(prev)
                    self.list_codes.blockSignals(False)
                else:
                    self.list_codes.removeRow(row)
                    return self._collect_codes()
        return codes

    def _update_name_for_row(self, row):
        it0 = self.list_codes.item(row, 0)
        it1 = self.list_codes.item(row, 1)
        if it0 is None or it1 is None:
            return
        code = it0.data(Qt.UserRole) or it0.text()
        name = self.panel.get_code_name(code)
        new_name = name if name != code else "更新中..."
        if it1.text() != new_name:
            self.list_codes.blockSignals(True)
            it1.setText(new_name)
            self.list_codes.blockSignals(False)

    def _refresh_names(self):
        for row in range(self.list_codes.rowCount()):
            it1 = self.list_codes.item(row, 1)
            if it1 and it1.text() == "更新中...":
                self._update_name_for_row(row)

    def _on_codes_changed(self, item):
        codes = self._collect_codes()
        self.panel.set_codes(codes)
        checked = [self.list_codes.item(i, 0).data(Qt.UserRole) for i in range(self.list_codes.rowCount()) if self.list_codes.item(i, 0).checkState() == Qt.Checked]
        self.panel.set_checked_codes(checked)
        if item and item.column() == 0:
            self._update_name_for_row(item.row())
        self._refresh_band_metric_combo()
        self._refresh_export_code_combo()

    def _add_code(self):
        c = "sh000001"
        row = self.list_codes.rowCount()
        self.list_codes.insertRow(row)
        it0 = QTableWidgetItem(c)
        it0.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
        it0.setCheckState(Qt.Unchecked)
        it0.setData(Qt.UserRole, c)
        self.list_codes.setItem(row, 0, it0)
        name = self.panel.get_code_name(c)
        name_text = name if name != c else "更新中..."
        it1 = QTableWidgetItem(name_text)
        it1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.list_codes.setItem(row, 1, it1)
        self.list_codes.setCurrentCell(row, 0)
        self.list_codes.edit(self.list_codes.model().index(row, 0))

    def _del_code(self):
        row = self.list_codes.currentRow()
        if row >= 0:
            self.list_codes.removeRow(row)
            self._on_codes_changed(None)

    def _move_up(self):
        row = self.list_codes.currentRow()
        if row > 0:
            items0 = self.list_codes.takeItem(row, 0)
            items1 = self.list_codes.takeItem(row, 1)
            self.list_codes.removeRow(row)
            self.list_codes.insertRow(row - 1)
            self.list_codes.setItem(row - 1, 0, items0)
            self.list_codes.setItem(row - 1, 1, items1)
            self.list_codes.setCurrentCell(row - 1, 0)
            self._on_codes_changed(None)

    def _move_down(self):
        row = self.list_codes.currentRow()
        if 0 <= row < self.list_codes.rowCount() - 1:
            items0 = self.list_codes.takeItem(row, 0)
            items1 = self.list_codes.takeItem(row, 1)
            self.list_codes.removeRow(row)
            self.list_codes.insertRow(row + 1)
            self.list_codes.setItem(row + 1, 0, items0)
            self.list_codes.setItem(row + 1, 1, items1)
            self.list_codes.setCurrentCell(row + 1, 0)
            self._on_codes_changed(None)

    def _on_interval_changed(self, idx):
        sec = self.cmb_interval.currentData()
        if isinstance(sec, int):
            self.panel.set_refresh_interval(sec)

    def _on_band_metric_changed(self, idx):
        val = self.cmb_band_metric.currentData()
        if val:
            self.panel.set_band_return_metric(val)

    def _make_combo_label(self, code):
        if code == "0AMV":
            return code
        name = self.panel.get_code_name(code)
        return f"{code} - {name}" if name != code else code

    def _refresh_band_metric_combo(self):
        self.cmb_band_metric.blockSignals(True)
        current = self.cmb_band_metric.currentData()
        self.cmb_band_metric.clear()
        for code in self.panel.checked_codes:
            lbl = self._make_combo_label(code)
            self.cmb_band_metric.addItem(lbl, userData=code)
        self.cmb_band_metric.addItem("0AMV", userData="0AMV")
        idx = self.cmb_band_metric.findData(current) if current else -1
        if idx >= 0:
            self.cmb_band_metric.setCurrentIndex(idx)
        self.cmb_band_metric.blockSignals(False)

    def _refresh_export_code_combo(self):
        self.cmb_export_code.blockSignals(True)
        self.cmb_export_code.clear()
        for code in self.panel.checked_codes:
            lbl = self._make_combo_label(code)
            self.cmb_export_code.addItem(lbl, userData=code)
        self.cmb_export_code.addItem("0AMV", userData="0AMV")
        self.cmb_export_code.blockSignals(False)

    def _on_export_bands(self):
        code = self.cmb_export_code.currentData()
        if not code:
            return
        start_dt = self.date_export_start.date().toPython()
        end_dt = self.date_export_end.date().toPython()
        if start_dt >= end_dt:
            QMessageBox.warning(self, "提示", "起始日期必须早于结束日期")
            return
        import csv, os, pandas as pd
        from datetime import datetime
        start_ts = pd.Timestamp(start_dt)
        end_ts = pd.Timestamp(end_dt)
        engine = self.panel.engine
        rows = []
        cumul = 1.0
        for s, e in engine.bands:
            if e < start_ts or s > end_ts:
                continue
            ret = engine.get_stock_band_return(code, s, e)
            ret_str = f"{ret:+.2f}%" if ret is not None else "N/A"
            rows.append([s.strftime('%Y-%m-%d'), e.strftime('%Y-%m-%d'), (e - s).days, ret_str])
            if ret is not None:
                cumul *= (1 + ret / 100)
        if not rows:
            QMessageBox.information(self, "提示", "所选时间范围内无波段数据")
            return
        total_ret = (cumul - 1) * 100
        n_years = (end_ts - start_ts).days / 365.25
        annualized = ((cumul ** (1 / n_years)) - 1) * 100 if n_years > 0 else 0.0
        rows.append([])
        rows.append(["累计收益", f"{total_ret:+.2f}%"])
        rows.append(["年化收益", f"{annualized:+.2f}%"])
        rows.append(["复利因子", f"{cumul:.4f}"])
        cache_dir = os.path.dirname(engine.cache_path) if engine.cache_path else ""
        if not cache_dir:
            cache_dir = os.path.join(os.getenv("APPDATA", ""), "0AMVMonitor")
            os.makedirs(cache_dir, exist_ok=True)
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_str = start_dt.strftime('%Y%m%d')
        end_str = end_dt.strftime('%Y%m%d')
        filename = f"0amv_returns_{code}_{start_str}_{end_str}.csv"
        filepath = os.path.join(cache_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['band_start', 'band_end', 'days', 'return_pct'])
            writer.writerows(rows)
        QMessageBox.information(self, "导出完成", f"已保存 {len(rows)} 条记录到:\n{filepath}")

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

    def _on_strat_entry_label(self, v):
        val = v / 10.0
        self.lbl_entry.setText(f"{val:.1f}%")
        self.panel.engine.strategy["entry"] = val

    def _on_strat_entry_apply(self):
        self._refresh_strategy()

    def _on_strat_exit_label(self, v):
        val = -v / 10.0
        self.lbl_exit.setText(f"{val:.1f}%")
        self.panel.engine.strategy["exit_dd"] = val

    def _on_strat_exit_apply(self):
        self._refresh_strategy()

    def _on_strat_merge_label(self, v):
        self.lbl_merge.setText(f"{v}天")
        self.panel.engine.strategy["merge_gap"] = v

    def _on_strat_merge_apply(self):
        self._refresh_strategy()

    def _on_strat_sma(self):
        n = self.cmb_sma_n.currentData()
        m = self.cmb_sma_m.currentData()
        if n and m:
            self.panel.engine.strategy["sma_n"] = n
            self.panel.engine.strategy["sma_m"] = m
            self._refresh_strategy()

    def _refresh_strategy(self):
        QTimer.singleShot(0, lambda: self._do_refresh_strategy())

    def _strat_btn_adj(self, slider, delta, apply_fn):
        v = slider.value() + delta
        v = max(slider.minimum(), min(slider.maximum(), v))
        slider.setValue(v)
        apply_fn()

    def _do_refresh_strategy(self):
        self.panel.engine._compute()
        self.panel.engine._detect()
        self.panel._refresh_engine(force_fetch=False)

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

    def _browse_cache(self):
        cur = self.edit_cache_path.text()
        d = QFileDialog.getExistingDirectory(self, "选择缓存目录", cur if os.path.isdir(cur) else "")
        if d:
            self.edit_cache_path.setText(d)
            self._on_cache_path_changed()

    def _on_cache_path_changed(self):
        new_dir = self.edit_cache_path.text().strip()
        if new_dir and self.panel.engine:
            new_path = os.path.normpath(os.path.join(new_dir, "cache.pkl"))
            if new_path != self.panel.engine.cache_path:
                self.panel.engine.cache_path = new_path
                self.panel._notify()

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
