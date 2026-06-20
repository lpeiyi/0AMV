import re, requests
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor

UP_COLOR = QColor("#dd2100")
DOWN_COLOR = QColor("#019933")
NEUTRAL_COLOR = QColor("#494949")

ALL_HEADERS = ["代码", "名称", "现价", "涨跌值", "涨跌幅", "买一", "卖一", "委比", "成交量", "成交额", "均价", "波收益"]

_re_full = re.compile(r'^(sh|sz|bj)\d+$')
_re_6 = re.compile(r'^\d{6}$')

def normalize_code(s):
    s = (s or "").strip().lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    if not s:
        return None
    if _re_full.match(s):
        return s
    if _re_6.match(s):
        if s[0] == '6' or s[0:2] == '90' or s[0] == '5':
            return 'sh' + s
        elif s[0] == '0' or s[0] == '3' or s[0] == '2' or s[0] == '1':
            return 'sz' + s
        elif s[0] == '8' or s[0] == '4' or s[0:2] == '92':
            return 'bj' + s
    return None

class QuotesFetcher:
    def __init__(self):
        self.band_returns = {}
        self.short_code = False
        self.name_length = 0
        self.b1s1_display = "qty"
        self._code_names = {}

    def code_names(self):
        return dict(self._code_names)

    def get_quotes(self, codes):
        if not codes:
            return [], []
        label = ",".join(codes)
        url = 'https://hq.sinajs.cn/list=' + label
        headers = {'Referer': 'https://finance.sina.com.cn', 'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=3)
        r.encoding = 'gbk'

        rows = []
        signs = []
        for line in r.text.split('\n'):
            if not line or '"' not in line:
                continue
            heads = line.split('="')[0].split('_')
            parts = line.split('="')[1].split(',')
            if len(parts) < 30:
                continue
            code = heads[2]
            name = parts[0]
            self._code_names[code] = name
            opening_price = float(parts[1] or 0)
            prev_close = float(parts[2] or 0)
            current_price = float(parts[3] or 0)
            high_price = float(parts[4] or 0)
            low_price = float(parts[5] or 0)
            first_pur = float(parts[6] or 0)
            first_sell = float(parts[7] or 0)
            deals_vol = float(parts[8] or 0)
            deals_amt = float(parts[9] or 0)
            purchaser = [int(x or 0) for x in parts[10:19:2]]
            pur_price = [float(x or 0) for x in parts[11:20:2]]
            seller = [int(x or 0) for x in parts[20:29:2]]
            sel_price = [float(x or 0) for x in parts[21:30:2]]

            if current_price == 0:
                current_price = prev_close
            if opening_price == 0:
                opening_price = current_price
                high_price = current_price
                low_price = current_price
            if prev_close == 0:
                prev_close = current_price

            change = current_price - prev_close
            change_pct = (current_price / prev_close - 1) * 100 if prev_close else 0.0

            etf = code[2] in ('1', '5')
            dec = 3 if etf else 2
            def almost_eq(a, b):
                try:
                    return round(float(a), dec) == round(float(b), dec)
                except:
                    return False

            buy_marker = " "
            sell_marker = " "
            if first_pur > 0 and almost_eq(current_price, first_pur):
                buy_marker = "<"
            if first_sell > 0 and almost_eq(current_price, first_sell):
                sell_marker = ">"

            b1_label = ""
            s1_label = ""
            b1_color_sign = 0
            s1_color_sign = 0

            if first_pur == first_sell > 0:
                current_price = first_sell
                paired = seller[0]
                unpaired_sign = -seller[1] if seller[1] > 0 else purchaser[1]
                paired_cnt = int(paired / 100)
                unpaired_cnt = int(unpaired_sign / 100)
                b_price = f"{first_pur:.3f}" if etf else f"{first_pur:.2f}"
                s_price = f"{first_sell:.3f}" if etf else f"{first_sell:.2f}"
                mode = self.b1s1_display
                if mode == 'price':
                    b1_label = b_price
                    s1_label = s_price
                elif mode == 'both':
                    b1_label = f"{paired_cnt:d}({b_price})"
                    s1_label = f"{unpaired_cnt:+d}({s_price})"
                else:
                    b1_label = f"{paired_cnt:d}"
                    s1_label = f"{unpaired_cnt:+d}"
                if unpaired_sign > 0:
                    b1_color_sign = 1
                    s1_color_sign = 1
                elif unpaired_sign < 0:
                    b1_color_sign = -1
                    s1_color_sign = -1
            else:
                if first_pur > 0:
                    cnt = f"{int(purchaser[0]/100)}"
                    b_price = f"{first_pur:.3f}" if etf else f"{first_pur:.2f}"
                    mode = self.b1s1_display
                    if mode == 'price':
                        b1_label = f"{b_price}{buy_marker}"
                    elif mode == 'both':
                        b1_label = f"{cnt}({b_price}){buy_marker}"
                    else:
                        b1_label = f"{cnt}{buy_marker}"
                else:
                    b1_label = f"-{buy_marker}"
                if first_sell > 0:
                    cnt = f"{int(seller[0]/100)}"
                    s_price = f"{first_sell:.3f}" if etf else f"{first_sell:.2f}"
                    mode = self.b1s1_display
                    if mode == 'price':
                        s1_label = f"{sell_marker}{s_price}"
                    elif mode == 'both':
                        s1_label = f"{sell_marker}{cnt}({s_price})"
                    else:
                        s1_label = f"{sell_marker}{cnt}"
                else:
                    s1_label = f"{sell_marker}-"
                b1_color_sign = 1
                s1_color_sign = -1

            arrow = " "
            if high_price > low_price:
                if current_price == high_price:
                    arrow = "↑"
                elif current_price == low_price:
                    arrow = "↓"

            price_str = f"{current_price:.3f}{arrow}" if etf else f"{current_price:.2f}{arrow}"
            change_str = f"{change:+.3f}" if etf else f"{change:+.2f}"
            pct_str = f"{change_pct:+.2f}%"

            avg_price = (deals_amt / deals_vol) if deals_vol > 0 else prev_close
            p_sum, s_sum = sum(purchaser), sum(seller)
            committee = (100 * (p_sum - s_sum) / (p_sum + s_sum)) if (p_sum + s_sum) > 0 else 0.0

            if etf:
                vol_str = f"{deals_vol:.0f}"
                amt_str = f"{deals_amt:.0f}"
                avg_str = f"{avg_price:.3f}"
            else:
                if deals_vol < 1e4:
                    vol_str = f"{deals_vol:.0f}"
                elif deals_vol < 1e8:
                    vol_str = f"{deals_vol/1e4:.2f}万"
                else:
                    vol_str = f"{deals_vol/1e8:.2f}亿"
                if deals_amt < 1e8:
                    amt_str = f"{deals_amt/1e4:.2f}万"
                elif deals_amt < 1e12:
                    amt_str = f"{deals_amt/1e8:.2f}亿"
                else:
                    amt_str = f"{deals_amt/1e12:.2f}万亿"
                avg_str = f"{avg_price:.2f}"

            band_ret = self.band_returns.get(code, "N/A")

            disp_code = code[2:] if self.short_code else code
            disp_name = name if self.name_length == 0 else name[:self.name_length]

            rows.append([disp_code, disp_name, price_str, change_str, pct_str,
                         b1_label, s1_label, f"{committee:+.2f}%", vol_str, amt_str, avg_str, band_ret])
            signs.append({
                "delta": (change > 0) - (change < 0),
                "commi": (committee > 0) - (committee < 0),
                "avg": (avg_price > prev_close) - (avg_price < prev_close),
                "b1": b1_color_sign,
                "s1": s1_color_sign,
            })

        return rows, signs


class QuoteTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._headers = []
        self._meta = []
        self.default_color = False
        self.fg_color = QColor("#FFFFFF")

    def set_color_scheme(self, default, fg):
        self.default_color = bool(default)
        self.fg_color = QColor(fg)

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers) if self._headers else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        cell = self._rows[r][c] if c < len(self._rows[r]) else ""

        if role == Qt.DisplayRole:
            return str(cell)

        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter if c <= 1 else Qt.AlignRight | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            if not self.default_color:
                return self.fg_color
            meta = self._meta[r] if r < len(self._meta) else {}
            header = self._headers[c] if c < len(self._headers) else ""
            sign = 0
            if header in ("涨跌值", "涨跌幅", "现价"):
                sign = int(meta.get("delta", 0))
            elif header == "委比":
                sign = int(meta.get("commi", 0))
            elif header == "均价":
                sign = int(meta.get("avg", 0))
            elif header == "买一":
                sign = int(meta.get("b1", 0))
            elif header == "卖一":
                sign = int(meta.get("s1", 0))
            elif header == "波收益":
                val = str(cell).strip("%").replace("+", "").replace("N/A", "0")
                try:
                    v = float(val)
                    return UP_COLOR if v > 0 else (DOWN_COLOR if v < 0 else self.fg_color)
                except:
                    return self.fg_color
            else:
                return self.fg_color

            if sign > 0:
                return UP_COLOR
            if sign < 0:
                return DOWN_COLOR
            return NEUTRAL_COLOR

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(self._headers):
            return self._headers[section]
        return None

    def set_data(self, rows, headers, meta=None):
        self.beginResetModel()
        self._rows = rows or []
        self._headers = headers or []
        self._meta = list(meta or [{} for _ in self._rows])
        self.endResetModel()
