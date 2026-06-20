from functools import partial
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QFontMetrics, QAction, QColor
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QVBoxLayout, QLabel, QTableView, QHeaderView, QAbstractItemView, QFrame, QListWidget, QListWidgetItem, QHBoxLayout

from band_stocks import QuotesFetcher, QuoteTableModel, ALL_HEADERS
from band_engine import BandEngine, BAND_RET_METRICS

class BandPanel(QWidget):
    hotkey_triggered = Signal()
    def __init__(self, cfg: dict, engine: BandEngine = None):
        super().__init__()
        self._on_change = lambda: None
        self._open_settings_cb = None
        self.engine = engine

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)

        codes = cfg.get("codes", ["sh000001", "sz399006", "sz159915"])
        self.codes = [str(c).strip() for c in codes if str(c).strip()]
        self.checked_codes = [str(c).strip() for c in cfg.get("checked_codes", self.codes) if str(c).strip() in self.codes]
        if not self.checked_codes:
            self.checked_codes = self.codes[:]

        self.refresh_seconds = int(cfg.get("refresh_seconds", 5))
        font_family = cfg.get("font_family", "Microsoft YaHei")
        font_size = int(cfg.get("font_size", 10))
        self.line_extra_px = int(cfg.get("line_extra_px", 1))
        self.fg = QColor(cfg.get("fg", "#FFFFFF"))
        bg = cfg.get("bg", {"r": 0, "g": 0, "b": 0, "a": 191})
        self.bg = QColor(bg["r"], bg["g"], bg["b"], bg["a"])
        self.default_color = bool(cfg.get("default_color", True))
        self.opacity_pct = int(cfg.get("opacity_pct", 90))
        self.header_visible = bool(cfg.get("header_visible", False))
        self.grid_visible = bool(cfg.get("grid_visible", False))
        self.band_return_metric = cfg.get("band_return_metric", "159915")

        # Column visibility flags
        self.code_visible = bool(cfg.get("code_visible", True))
        self.name_visible = bool(cfg.get("name_visible", True))
        self.price_visible = bool(cfg.get("price_visible", True))
        self.change_visible = bool(cfg.get("change_visible", False))
        self.change_pct_visible = bool(cfg.get("change_pct_visible", True))
        self.b1s1_visible = bool(cfg.get("b1s1_visible", False))
        self.commi_visible = bool(cfg.get("commi_visible", False))
        self.vol_visible = bool(cfg.get("vol_visible", False))
        self.amount_visible = bool(cfg.get("amount_visible", False))
        self.avg_visible = bool(cfg.get("avg_visible", False))
        self.band_ret_visible = bool(cfg.get("band_ret_visible", True))
        self.short_code = bool(cfg.get("short_code", False))
        self.name_length = int(cfg.get("name_length", 0))
        self.b1s1_display = cfg.get("b1s1_display", "qty")

        self.quote_fetcher = QuotesFetcher()
        self.quote_fetcher.short_code = self.short_code
        self.quote_fetcher.name_length = self.name_length
        self.quote_fetcher.b1s1_display = self.b1s1_display
        self.font = QFont(font_family, max(8, min(15, font_size)))

        self.setWindowOpacity(self.opacity_pct / 100.0)

        self.panel = QWidget(self)
        self.panel.setObjectName("panel")
        self.vbox = QVBoxLayout(self.panel)
        self.vbox.setContentsMargins(8, 5, 8, 5)
        self.vbox.setSpacing(2)

        # Top: band status
        self.status_label = QLabel("", self.panel)
        self.status_label.setWordWrap(False)
        self.metrics_label = QLabel("", self.panel)
        self.metrics_label.setWordWrap(False)
        self.vbox.addWidget(self.status_label)
        self.vbox.addWidget(self.metrics_label)

        # Separator
        self.sep1 = QLabel("─" * 40, self.panel)
        self.vbox.addWidget(self.sep1)

        # Middle: stock table
        self.table = QTableView(self.panel)
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(self.header_visible)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setFont(self.font)
        self.table.horizontalHeader().setFont(self.font)
        self.table.verticalHeader().setMinimumSectionSize(1)
        self.table.verticalHeader().setDefaultSectionSize(1)
        self.table.horizontalHeader().setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.table.setTextElideMode(Qt.ElideNone)
        self.vbox.addWidget(self.table)

        self.model = QuoteTableModel(self.table)
        self.model.set_color_scheme(self.default_color, self.fg)
        self.table.setModel(self.model)

        # Bottom: band history
        self.sep2 = QLabel("─" * 40, self.panel)
        self.vbox.addWidget(self.sep2)

        hist_header = QHBoxLayout()
        self.hist_title = QLabel(f"历史波段 [{self.band_return_metric}]", self.panel)
        hist_header.addWidget(self.hist_title)
        hist_header.addStretch()
        self.vbox.addLayout(hist_header)

        self.hist_list = QListWidget(self.panel)
        self.hist_list.setFrameShape(QFrame.NoFrame)
        self.hist_list.setFocusPolicy(Qt.NoFocus)
        self.hist_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hist_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hist_list.setFont(self.font)
        self.hist_list.setSpacing(0)
        self.hist_list.setContentsMargins(0, 0, 0, 0)
        self.hist_list.setMaximumHeight(1)
        self.vbox.addWidget(self.hist_list)

        self.vbox.addStretch(0)

        for w in (self.panel, self.table, self.table.viewport(),
                  self.table.horizontalHeader(), self.table.verticalHeader(),
                  self.status_label, self.metrics_label, self.sep1, self.sep2,
                  self.hist_title, self.hist_list, self.hist_list.viewport()):
            w.installEventFilter(self)

        self.apply_style()

        # 先设置加载文字再 _fit()，保证窗口尺寸正确
        if self.engine is None:
            fg_hex = self.fg.name()
            self.status_label.setText(f'<span style="color:{fg_hex};font-size:11pt;">⏳ 加载中… 正在获取数据</span>')

        self._fit()

        scr = QApplication.primaryScreen().availableGeometry()
        pos = cfg.get("pos")
        if isinstance(pos, dict) and "x" in pos and "y" in pos:
            x, y = int(pos["x"]), int(pos["y"])
            x = max(scr.left(), min(x, scr.right() - self.width()))
            y = max(scr.top(), min(y, scr.bottom() - self.height()))
            self.move(x, y)
        else:
            self.move(scr.right() - self.width() - 40, scr.bottom() - self.height() - 80)

        self._drag_pos = None

        self.stock_timer = QTimer(self)
        self.stock_timer.setInterval(max(1, self.refresh_seconds) * 1000)
        self.stock_timer.timeout.connect(self._refresh_stocks)

        self.engine_timer = QTimer(self)
        self.engine_timer.setInterval(60000)
        self.engine_timer.timeout.connect(self._refresh_engine)

        if self.engine is not None:
            self.stock_timer.start()
            self.engine_timer.start()
            self._refresh_engine()
            self._refresh_stocks()

    def on_engine_ready(self):
        if self.engine is None:
            return
        self._refresh_stocks()
        self._refresh_engine(force_fetch=False)
        self._fit()
        self.stock_timer.start()
        self.engine_timer.start()

    def set_open_settings_callback(self, fn):
        self._open_settings_cb = fn

    def set_on_change(self, fn):
        self._on_change = fn or (lambda: None)

    def _notify(self):
        self._on_change()

    def current_config(self):
        return {
            "codes": self.codes,
            "checked_codes": self.checked_codes,
            "refresh_seconds": self.refresh_seconds,
            "fg": self.fg.name(QColor.HexRgb),
            "bg": {"r": self.bg.red(), "g": self.bg.green(), "b": self.bg.blue(), "a": self.bg.alpha()},
            "opacity_pct": int(round(self.windowOpacity() * 100)),
            "font_family": self.font.family(),
            "font_size": self.font.pointSize(),
            "line_extra_px": self.line_extra_px,
            "default_color": self.default_color,
            "header_visible": self.header_visible,
            "grid_visible": self.grid_visible,
            "pos": {"x": self.x(), "y": self.y()},
            "band_return_metric": self.band_return_metric,
            "code_visible": self.code_visible,
            "name_visible": self.name_visible,
            "price_visible": self.price_visible,
            "change_visible": self.change_visible,
            "change_pct_visible": self.change_pct_visible,
            "b1s1_visible": self.b1s1_visible,
            "commi_visible": self.commi_visible,
            "vol_visible": self.vol_visible,
            "amount_visible": self.amount_visible,
            "avg_visible": self.avg_visible,
            "band_ret_visible": self.band_ret_visible,
            "short_code": self.short_code,
            "name_length": self.name_length,
            "b1s1_display": self.b1s1_display,
            "cache_path": self.engine.cache_path if self.engine else "",
        }

    def header_is_visible(self, header):
        if header == "代码": return self.code_visible
        if header == "名称": return self.name_visible
        if header == "现价": return self.price_visible
        if header == "涨跌值": return self.change_visible
        if header == "涨跌幅": return self.change_pct_visible
        if header in ("买一", "卖一"): return self.b1s1_visible
        if header == "委比": return self.commi_visible
        if header == "成交量": return self.vol_visible
        if header == "成交额": return self.amount_visible
        if header == "均价": return self.avg_visible
        if header == "波收益": return self.band_ret_visible
        return False

    def set_header_flag(self, header, checked):
        checked = bool(checked)
        if header == "代码": self.code_visible = checked
        elif header == "名称": self.name_visible = checked
        elif header == "现价": self.price_visible = checked
        elif header == "涨跌值": self.change_visible = checked
        elif header == "涨跌幅": self.change_pct_visible = checked
        elif header in ("买一", "卖一"): self.b1s1_visible = checked
        elif header == "委比": self.commi_visible = checked
        elif header == "成交量": self.vol_visible = checked
        elif header == "成交额": self.amount_visible = checked
        elif header == "均价": self.avg_visible = checked
        elif header == "波收益": self.band_ret_visible = checked
        else: return
        self._notify()
        self._refresh_stocks()

    def apply_style(self):
        r, g, b, a = self.bg.red(), self.bg.green(), self.bg.blue(), self.bg.alpha()
        fg_r, fg_g, fg_b = self.fg.red(), self.fg.green(), self.fg.blue()
        fg_hex = self.fg.name()
        line_col = f"rgba({fg_r},{fg_g},{fg_b},80)"
        bg_rgba = f"rgba({r},{g},{b},{a})"
        self.panel.setStyleSheet(f"""
            QWidget#panel {{
                background: {bg_rgba};
                border-radius: 5px;
            }}
            QTableView {{
                background: transparent;
                border: {f"1px solid {line_col}" if self.grid_visible else "none"};
                border-radius: 3px;
                {"color: " + fg_hex + ";" if not self.default_color else ""}
                outline: none;
            }}
            QTableView::item {{
                border-right: {f"1px solid {line_col}" if self.grid_visible else "none"};
                border-bottom: {f"1px solid {line_col}" if self.grid_visible else "none"};
            }}
            QHeaderView {{
                background: transparent;
            }}
            QHeaderView::section {{
                background: {bg_rgba};
                border: none;
                border-bottom: 1px solid {line_col};
                font-weight: 600;
                {"color: " + fg_hex + ";" if not self.default_color else ""}
                padding: 2px 4px;
            }}
            QLabel {{
                background: {bg_rgba};
                {"color: " + fg_hex + ";" if not self.default_color else ""}
                border: none;
            }}
            QListWidget {{
                background: {bg_rgba};
                border: none;
            }}
            QListWidget::item {{
                {"color: " + fg_hex + ";" if not self.default_color else ""}
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: rgba({fg_r},{fg_g},{fg_b},30);
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba({fg_r},{fg_g},{fg_b},80);
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        self.table.setFont(self.font)
        self.table.horizontalHeader().setFont(self.font)
        self.status_label.setFont(self.font)
        self.metrics_label.setFont(self.font)
        self.hist_title.setFont(self.font)
        self.sep1.setStyleSheet(f"color: rgba(128,128,128,120); font-size: 8pt;")
        self.sep2.setStyleSheet(f"color: rgba(128,128,128,120); font-size: 8pt;")
        self.hist_title.setStyleSheet(f"font-weight: 600; {'color: ' + fg_hex + ';' if not self.default_color else ''}")
        self._fit()

    def _fit(self):
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.resizeColumnsToContents()
        self._apply_row_heights()

        cols = self.model.columnCount()
        rows = self.model.rowCount()
        total_w = self.table.verticalHeader().width() + 2 * self.table.frameWidth()
        for c in range(cols):
            total_w += self.table.columnWidth(c)
        hh = self.table.horizontalHeader().height() if self.table.horizontalHeader().isVisible() else 0
        total_h = hh + 2 * self.table.frameWidth()
        for r in range(rows):
            total_h += self.table.rowHeight(r)
        self.table.setFixedSize(max(1, total_w), max(1, total_h))

        item_font = QFont(self.font)
        item_font.setPointSize(max(6, self.font.pointSize() - 1))
        fm_item = QFontMetrics(item_font)
        item_h = fm_item.height() + max(0, self.line_extra_px)
        self.hist_list.setMaximumHeight(item_h * 3 + 2)

        self.hist_list.setMinimumHeight(1)
        self.hist_list.setSpacing(0)

        self.panel.adjustSize()
        self.resize(self.panel.size())

    def _apply_row_heights(self):
        fm = self.table.fontMetrics()
        h = fm.height() + max(0, self.line_extra_px)
        self.table.verticalHeader().setDefaultSectionSize(h)
        for r in range(self.model.rowCount()):
            self.table.setRowHeight(r, h)

    def _get_visible_headers(self):
        return [h for h in ALL_HEADERS if self.header_is_visible(h)]

    def _refresh_engine(self, force_fetch=True):
        if self.engine is None:
            return
        if force_fetch:
            try:
                status = self.engine.refresh()
            except:
                status = self.engine.get_status()
        else:
            status = self.engine.get_status()
        self._update_status_bar(status)
        self._update_band_returns(status)

    def _update_status_bar(self, status):
        font_pt = self.font.pointSize()
        if status["in_band"]:
            start = status["band_start"]
            days = status["band_days"]
            peak = status["peak_gain"]
            dd = status["drawdown"]
            exit_th = status["exit_threshold"]
            self.status_label.setText(
                f'<span style="color:#dd2100;font-size:{font_pt+2}pt;font-weight:600;">🔴 多头区间</span>'
                f'<span style="font-size:{font_pt}pt;">  {start.date()}起 ({days}天)</span>'
            )
            self.metrics_label.setText(
                f'<span style="font-size:{font_pt}pt;">'
                f'0AMV <b>{status["oamv_value"]:,.0f}亿</b>  '
                f'峰值 <b style="color:#dd2100;">+{peak:.1f}%</b>  '
                f'回撤 <b style="color:{"#ff6600" if dd < exit_th * 0.7 else "#dd2100" if dd < exit_th * 0.9 else "#ffcc00"};">{dd:.1f}%</b> / {exit_th:.0f}%'
                f'</span>'
            )
        else:
            if status["bands"]:
                last_end = status["bands"][-1]["end"]
                bear_days = (status["last_date"] - last_end).days
                date_str = f'{last_end.date()}起 ({bear_days}天)'
            else:
                date_str = f'{status["last_date"].date()}起'
            self.status_label.setText(
                f'<span style="color:#00cc66;font-size:{font_pt+2}pt;font-weight:600;">🟢 空头区间</span>'
                f'<span style="font-size:{font_pt}pt;">  {date_str}</span>'
            )
            self.metrics_label.setText(
                f'<span style="font-size:{font_pt}pt;">'
                f'0AMV <b>{status["oamv_value"]:,.0f}亿</b>  '
                f'日涨跌 <b style="color:{"#dd2100" if status["oamv_pct"]>0 else "#019933" if status["oamv_pct"]<0 else "#999"};">{status["oamv_pct"]:+.2f}%</b>'
                f'</span>'
            )

        self._update_band_history(status)

    def _update_band_history(self, status):
        self.hist_list.clear()
        metric_key = BAND_RET_METRICS.get(self.band_return_metric, None)
        fg_hex = self.fg.name()
        item_font = QFont(self.font)
        item_font.setPointSize(max(6, self.font.pointSize() - 1))
        item_h = QFontMetrics(item_font).height() + max(0, self.line_extra_px)
        max_completed = 2 if status["in_band"] else 3
        needs_defer = False
        for b in status["bands"][:max_completed]:
            if metric_key:
                ret = self.engine.get_band_return(b["start"], b["end"], metric_key)
            else:
                ck = (self.band_return_metric, b["start"], b["end"])
                if ck in self.engine._stock_band_cache:
                    ret = self.engine._stock_band_cache[ck]
                else:
                    ret = self.engine.get_band_return(b["start"], b["end"], "oamv")
                    needs_defer = True
                    text_suffix = ' <span style="color:#999999;font-weight:400;">计算中…</span>'
            ret_str = f"+{ret:.2f}%" if ret is not None and ret >= 0 else (f"{ret:.2f}%" if ret is not None else "N/A")
            color = "#dd2100" if ret is not None and ret > 0 else "#019933" if ret is not None and ret < 0 else "#999999"
            text = f'{b["start"].strftime("%Y-%m-%d")} → {b["end"].strftime("%Y-%m-%d")} ({b["days"]}d)  <span style="color:{color};font-weight:600;">{ret_str}</span>'
            if not metric_key and ck not in self.engine._stock_band_cache:
                text += text_suffix
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, item_h))
            lbl = QLabel(text, self.hist_list)
            lbl.setStyleSheet(f"color: {fg_hex if not self.default_color else '#CCCCCC'}; font-size: {item_font.pointSize()}pt; background: transparent;")
            self.hist_list.addItem(item)
            self.hist_list.setItemWidget(item, lbl)

        if status["in_band"]:
            text = f'🔄 {status["band_start"].strftime("%Y-%m-%d")} → 进行中 ({status["band_days"]}d)'
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, item_h))
            lbl = QLabel(text, self.hist_list)
            lbl.setStyleSheet(f"color: #00cc66; font-size: {item_font.pointSize()}pt; background: transparent;")
            self.hist_list.insertItem(0, item)
            self.hist_list.setItemWidget(item, lbl)

        self._fit()
        if needs_defer:
            QTimer.singleShot(0, lambda: self._deferred_hist_return(status))

    def _deferred_hist_return(self, status):
        metric_key = BAND_RET_METRICS.get(self.band_return_metric, None)
        if metric_key:
            return
        max_completed = 2 if status["in_band"] else 3
        for b in status["bands"][:max_completed]:
            ck = (self.band_return_metric, b["start"], b["end"])
            if ck in self.engine._stock_band_cache:
                continue
            ret = self.engine.get_stock_band_return(self.band_return_metric, b["start"], b["end"])
            if ret is not None:
                self.engine._stock_band_cache[ck] = ret
        self._update_band_history(status)

    def _update_band_returns(self, status):
        self.quote_fetcher.band_returns = {}
        metric_key = BAND_RET_METRICS.get(self.band_return_metric, "etf")
        if status["in_band"]:
            start = status["band_start"]
            end = status["last_date"]
        elif status["bands"]:
            last = status["bands"][-1]
            start = last["end"]
            end = status["last_date"]
        else:
            for code in self.checked_codes:
                self.quote_fetcher.band_returns[code] = "0.00%"
            self._refresh_stocks()
            return

        fallback = self.engine.get_band_return(start, end, metric_key)
        if fallback is None:
            fallback = self.engine.get_band_return(start, end, "oamv")
        fallback_str = f"{fallback:+.2f}%" if fallback is not None else "N/A"

        needs_api = False
        for code in self.checked_codes:
            ck = (code, start, end)
            if ck in self.engine._stock_band_cache:
                continue
            raw = code[2:] if code[:2] in ('sh', 'sz', 'bj') else code
            if raw not in ("000001", "399006", "159915"):
                needs_api = True
                break

        if not needs_api:
            for code in self.checked_codes:
                ret = self.engine.get_stock_band_return(code, start, end)
                self.quote_fetcher.band_returns[code] = f"{ret:+.2f}%" if ret is not None else fallback_str
            self._refresh_stocks()
        else:
            for code in self.checked_codes:
                self.quote_fetcher.band_returns[code] = fallback_str
            self._refresh_stocks()
            self._deferred_start = start
            self._deferred_end = end
            self._deferred_fallback = fallback_str
            self._deferred_codes = list(self.checked_codes)
            self._deferred_idx = 0
            QTimer.singleShot(0, self._deferred_band_returns)

    def _deferred_band_returns(self):
        while self._deferred_idx < len(self._deferred_codes):
            code = self._deferred_codes[self._deferred_idx]
            if (code, self._deferred_start, self._deferred_end) not in self.engine._stock_band_cache:
                break
            ret = self.engine.get_stock_band_return(code, self._deferred_start, self._deferred_end)
            if ret is not None:
                self.quote_fetcher.band_returns[code] = f"{ret:+.2f}%"
            self._deferred_idx += 1
        if self._deferred_idx >= len(self._deferred_codes):
            self._refresh_stocks()
            return
        code = self._deferred_codes[self._deferred_idx]
        ret = self.engine.get_stock_band_return(code, self._deferred_start, self._deferred_end)
        if ret is not None:
            self.quote_fetcher.band_returns[code] = f"{ret:+.2f}%"
        self._deferred_idx += 1
        if self._deferred_idx >= len(self._deferred_codes):
            self._refresh_stocks()
        else:
            QTimer.singleShot(0, self._deferred_band_returns)

    def _refresh_stocks(self):
        try:
            rows, signs = self.quote_fetcher.get_quotes(self.checked_codes)
        except Exception as e:
            return
        headers = self._get_visible_headers()

        col_map = {h: i for i, h in enumerate(ALL_HEADERS)}
        h_idx = [col_map[h] for h in headers]
        proj = [[r[i] for i in h_idx] for r in rows]
        self.model.set_data(proj, headers, signs)
        self._fit()

    def get_code_name(self, code):
        names = self.quote_fetcher.code_names()
        return names.get(code, code)

    def set_codes(self, codes_list):
        seen = set()
        new = []
        for c in codes_list:
            s = str(c).strip().lower()
            if s and s not in seen:
                seen.add(s)
                new.append(s)
        if not new:
            new = ["sh000001"]
        self.codes = new
        self._notify()
        self._refresh_stocks()

    def set_checked_codes(self, codes_list):
        seen = set()
        new = []
        for c in codes_list:
            s = str(c).strip().lower()
            if s and s not in seen:
                seen.add(s)
                new.append(s)
        if not new:
            new = ["sh000001"]
        self.checked_codes = new
        self._notify()
        self._refresh_stocks()

    def set_refresh_interval(self, seconds):
        if seconds in {1, 2, 3, 5, 10, 15, 30, 60}:
            self.refresh_seconds = seconds
            self.stock_timer.setInterval(seconds * 1000)
            self._notify()

    def set_fg_color(self, c):
        if isinstance(c, QColor) and c.isValid():
            self.fg = QColor(c)
            self.model.set_color_scheme(self.default_color, self.fg)
            self.apply_style()
            self._notify()

    def set_bg_rgb_keep_alpha(self, c):
        if isinstance(c, QColor) and c.isValid():
            c2 = QColor(c)
            c2.setAlpha(self.bg.alpha())
            self.bg = c2
            self.apply_style()
            self._notify()

    def set_bg_alpha_percent(self, p):
        p = max(1, min(100, int(p)))
        self.bg.setAlpha(int(round(p * 2.55)))
        self.apply_style()
        self._notify()

    def set_window_opacity_percent(self, p):
        p = max(20, min(100, int(p)))
        self.setWindowOpacity(p / 100.0)
        self._notify()

    def set_font_size(self, pt):
        pt = max(8, min(15, int(pt)))
        self.font.setPointSize(pt)
        self.apply_style()
        self._notify()

    def set_font_family(self, family):
        if family and family != self.font.family():
            self.font.setFamily(family)
            self.apply_style()
            self._notify()

    def set_line_extra(self, px):
        self.line_extra_px = max(0, int(px))
        self.apply_style()
        self._notify()

    def set_default_color(self, enabled):
        self.default_color = bool(enabled)
        self.model.set_color_scheme(self.default_color, self.fg)
        self.apply_style()
        self._notify()

    def set_header_visible(self, vis):
        self.header_visible = bool(vis)
        self.table.horizontalHeader().setVisible(self.header_visible)
        self._notify()
        self._fit()

    def set_grid_visible(self, vis):
        self.grid_visible = bool(vis)
        self.apply_style()
        self._notify()

    def set_band_return_metric(self, metric):
        self.band_return_metric = metric
        self.hist_title.setText(f"历史波段 [{self.band_return_metric}]")
        if self.engine is None:
            return
        status = self.engine.get_status()
        QTimer.singleShot(0, lambda: self._deferred_update_metric(status))

    def _deferred_update_metric(self, status):
        self._update_band_history(status)
        self._update_band_returns(status)
        self._notify()

    def set_short_code(self, enabled):
        self.short_code = bool(enabled)
        self.quote_fetcher.short_code = self.short_code
        self._notify()
        self._refresh_stocks()

    def set_name_length(self, length):
        self.name_length = max(0, int(length))
        self.quote_fetcher.name_length = self.name_length
        self._notify()
        self._refresh_stocks()

    def set_b1s1_display(self, mode):
        if mode in ("qty", "price", "both"):
            self.b1s1_display = mode
            self.quote_fetcher.b1s1_display = mode
            self._notify()
            self._refresh_stocks()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        sub_cols = QMenu("显示指标", menu)
        col_groups = [("代码", "名称"), ("现价", "涨跌值", "涨跌幅"),
                      ("买一/卖一",), ("委比",), ("成交量", "成交额"), ("均价",), ("波收益",)]
        single_map = {"买一/卖一": "买一"}
        for group in col_groups:
            if len(group) == 1:
                name = group[0]
                key = single_map.get(name, name)
                act = QAction(name, sub_cols, checkable=True)
                act.setChecked(self.header_is_visible(key))
                act.toggled.connect(partial(self.set_header_flag, key))
                sub_cols.addAction(act)
            else:
                for name in group:
                    act = QAction(name, sub_cols, checkable=True)
                    act.setChecked(self.header_is_visible(name))
                    act.toggled.connect(partial(self.set_header_flag, name))
                    sub_cols.addAction(act)
        menu.addMenu(sub_cols)

        act_header = QAction("显示表头", menu, checkable=True)
        act_header.setChecked(self.header_visible)
        act_header.toggled.connect(self.set_header_visible)
        menu.addAction(act_header)

        act_grid = QAction("显示网格", menu, checkable=True)
        act_grid.setChecked(self.grid_visible)
        act_grid.toggled.connect(self.set_grid_visible)
        menu.addAction(act_grid)

        act_color = QAction("默认颜色", menu, checkable=True)
        act_color.setChecked(self.default_color)
        act_color.toggled.connect(self.set_default_color)
        menu.addAction(act_color)

        menu.addSeparator()
        if self._open_settings_cb:
            act_settings = QAction("设置…", menu)
            act_settings.triggered.connect(self._open_settings_cb)
            menu.addAction(act_settings)

        menu.addSeparator()
        act_hide = QAction("隐藏浮窗", menu)
        act_hide.triggered.connect(self.hide)
        menu.addAction(act_hide)

        menu.exec(event.globalPos())

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setFocus(Qt.MouseFocusReason)

    def mouseMoveEvent(self, e):
        if getattr(self, "_drag_pos", None) and (e.buttons() & Qt.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = None
            self._notify()

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = None
            self.hide()

    def eventFilter(self, obj, ev):
        from PySide6.QtCore import QEvent
        if ev.type() == QEvent.Wheel:
            return True
        if ev.type() == QEvent.MouseButtonDblClick and hasattr(ev, "button") and ev.button() == Qt.LeftButton:
            self._drag_pos = None
            self.hide()
            return True
        if ev.type() == QEvent.MouseButtonPress and hasattr(ev, "button") and ev.button() == Qt.LeftButton:
            self._drag_pos = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setFocus(Qt.MouseFocusReason)
            return True
        if ev.type() == QEvent.MouseMove and hasattr(ev, "buttons") and (ev.buttons() & Qt.LeftButton) and getattr(self, "_drag_pos", None):
            self.move(ev.globalPosition().toPoint() - self._drag_pos)
            return True
        if ev.type() == QEvent.MouseButtonRelease and hasattr(ev, "button") and ev.button() == Qt.LeftButton:
            self._drag_pos = None
            self._notify()
            return True
        return QWidget.eventFilter(self, obj, ev)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def showEvent(self, event):
        super().showEvent(event)
        if self.stock_timer and not self.stock_timer.isActive():
            self.stock_timer.start()
        if self.engine_timer and not self.engine_timer.isActive():
            self.engine_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.stock_timer and self.stock_timer.isActive():
            self.stock_timer.stop()
        if self.engine_timer and self.engine_timer.isActive():
            self.engine_timer.stop()

    def toggle_win(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
