import os, time

BAND_RET_METRICS = {"159915": "etf", "上证指数": "sh", "创业板指": "sz", "0AMV": "oamv"}

class BandEngine:
    def __init__(self, cache_path=None):
        self.df = None
        self.oamv = None
        self.oamv_pct = None
        self.bands = []
        self.raw_bands = []
        self.open_band_start = None
        self.open_band_peak = None
        self.last_fetch_date = None
        self.bear_market_start = None

        self.sh = None
        self.sz = None
        self.etf = None

        self._stock_band_cache = {}

        self.strategy = {"entry": 3.0, "exit_dd": -7.0, "merge_gap": 10, "sma_n": 10, "sma_m": 2}
        self.cache_path = cache_path or os.path.join(os.getenv("APPDATA", ""), "0AMVMonitor", "cache.pkl")

    def load_cache(self):
        try:
            import pickle
            with open(self.cache_path, "rb") as f:
                data = pickle.load(f)
            if data.get("version") not in (1, 2, 3, 4):
                return False
            self.df = data["df"]
            self.sh = data.get("sh")
            self.sz = data.get("sz")
            self.etf = data.get("etf")
            self.oamv = data["oamv"]
            self.oamv_pct = data["oamv_pct"]
            self.bands = data["bands"]
            self.raw_bands = data.get("raw_bands", [])
            self.open_band_start = data.get("open_band_start")
            self.open_band_peak = data.get("open_band_peak")
            self.last_fetch_date = data["fetch_date"]
            self.bear_market_start = data.get("bear_market_start")
            if self.bear_market_start is None and self.bands:
                self.bear_market_start = self.bands[-1][1]
            if data.get("version", 1) < 4:
                self._stock_band_cache = {}
            else:
                self._stock_band_cache = data.get("stock_band_cache", {})
            return True
        except Exception:
            return False

    def save_cache(self):
        try:
            import pickle
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "wb") as f:
                pickle.dump({
                    "version": 4,
                    "fetch_date": self.last_fetch_date,
                    "df": self.df,
                    "sh": self.sh,
                    "sz": self.sz,
                    "etf": self.etf,
                    "oamv": self.oamv,
                    "oamv_pct": self.oamv_pct,
                    "bands": self.bands,
                    "raw_bands": self.raw_bands,
                    "open_band_start": self.open_band_start,
                    "open_band_peak": self.open_band_peak,
                    "bear_market_start": self.bear_market_start,
                    "stock_band_cache": self._stock_band_cache,
                }, f)
        except Exception:
            pass

    def fetch_all(self):
        import akshare as ak
        import pandas as pd
        for i in range(5):
            try:
                df = ak.stock_zh_index_hist_csindex(symbol='000985', start_date='20100101', end_date='20261231')
                df = df.rename(columns={'日期': 'date', '成交金额': 'amount_yi'})
                df['date'] = pd.to_datetime(df['date'])
                self.df = df.sort_values('date').reset_index(drop=True)
                self.last_fetch_date = self.df['date'].max()
                break
            except Exception as e:
                time.sleep(5)
        if self.df is None:
            raise Exception('000985 fetch failed')

        self.sh = pd.DataFrame()
        self.sz = pd.DataFrame()
        self.etf = pd.DataFrame()
        for i in range(5):
            try:
                self.sh = ak.stock_zh_index_hist_csindex(symbol='000001', start_date='20100101', end_date='20261231')
                self.sh['date'] = pd.to_datetime(self.sh['日期'])
                self.sh = self.sh.sort_values('date').set_index('date')
                break
            except:
                time.sleep(5)
        for i in range(5):
            try:
                self.sz = ak.stock_zh_index_daily_tx(symbol='sz399006')
                self.sz['date'] = pd.to_datetime(self.sz['date'])
                self.sz = self.sz.sort_values('date').set_index('date')
                break
            except:
                time.sleep(3)
        for i in range(5):
            try:
                self.etf = ak.stock_zh_index_daily_tx(symbol='sz159915')
                self.etf['date'] = pd.to_datetime(self.etf['date'])
                self.etf = self.etf.sort_values('date').set_index('date')
                break
            except:
                time.sleep(3)

        self._compute()
        self._detect()
        self.save_cache()

    def _compute(self):
        import numpy as np
        self.oamv = np.zeros(len(self.df))
        N = self.strategy['sma_n']
        M = self.strategy['sma_m']
        a = self.df['amount_yi'].values
        for i in range(len(a)):
            self.oamv[i] = a[i] if i == 0 else (M * a[i] + (N - M) * self.oamv[i-1]) / N
        self.oamv_pct = np.diff(self.oamv) / self.oamv[:-1] * 100
        self.oamv_pct = np.insert(self.oamv_pct, 0, 0)

    def _detect(self):
        import pandas as pd
        entry = self.strategy['entry']
        exit_dd = self.strategy['exit_dd']
        merge_gap = self.strategy['merge_gap']

        data = self.df[self.df['date'] >= '2022-01-01'].copy()
        oamv = self.oamv[self.df['date'] >= '2022-01-01']
        pct = self.oamv_pct[self.df['date'] >= '2022-01-01']
        dates = data['date'].values

        raw = []
        start = None
        peak = None
        for i in range(len(dates)):
            if start is None:
                if pct[i] >= entry:
                    start = pd.Timestamp(dates[i])
                    peak = oamv[i]
            else:
                if oamv[i] > peak:
                    peak = oamv[i]
                dd = (oamv[i] / peak - 1) * 100
                if dd <= exit_dd:
                    raw.append((start, pd.Timestamp(dates[i])))
                    start = None
                    peak = None

        raw = [(s, e) for s, e in raw if s >= pd.Timestamp('2023-01-01')]

        bands = []
        if raw:
            bands = [raw[0]]
            for bs, be in raw[1:]:
                if (bs - bands[-1][1]).days <= merge_gap:
                    bands[-1] = (bands[-1][0], max(bands[-1][1], be))
                else:
                    bands.append((bs, be))

        self.raw_bands = raw
        self.bands = bands
        self.open_band_start = start
        self.open_band_peak = peak

    def refresh(self, strategy=None):
        import akshare as ak
        import pandas as pd
        if strategy:
            self.strategy.update(strategy)
        try:
            for i in range(3):
                try:
                    df_new = ak.stock_zh_index_hist_csindex(symbol='000985', start_date='20200101', end_date='20261231')
                    df_new = df_new.rename(columns={'日期': 'date', '成交金额': 'amount_yi'})
                    df_new['date'] = pd.to_datetime(df_new['date'])
                    df_new = df_new.sort_values('date').reset_index(drop=True)
                    self.df = df_new
                    self.last_fetch_date = self.df['date'].max()
                    break
                except:
                    time.sleep(5)
            self._compute()
            self._detect()
            if self.bands:
                self.bear_market_start = self.bands[-1][1]
        except:
            pass
        return self.get_status()

    def get_stock_band_return(self, code, start, end):
        cache_key = (code, start, end)
        if cache_key in self._stock_band_cache:
            return self._stock_band_cache[cache_key]

        raw = code[2:] if code[:2] in ('sh', 'sz', 'bj') else code
        if raw == "000001":
            ret = self.get_band_return(start, end, "sh")
            self._stock_band_cache[cache_key] = ret
            return ret
        if raw == "399006":
            ret = self.get_band_return(start, end, "sz")
            self._stock_band_cache[cache_key] = ret
            return ret
        if raw == "159915":
            ret = self.get_band_return(start, end, "etf")
            self._stock_band_cache[cache_key] = ret
            return ret

        import akshare as ak
        import pandas as pd
        df = None
        try:
            df = ak.stock_zh_a_hist(symbol=raw, period='daily',
                start_date=start.strftime('%Y%m%d'),
                end_date=end.strftime('%Y%m%d'), adjust='qfq')
        except:
            pass
        if df is None or len(df) < 2:
            try:
                df = ak.fund_etf_hist_em(symbol=raw, period='daily',
                    start_date=start.strftime('%Y%m%d'),
                    end_date=end.strftime('%Y%m%d'), adjust='qfq')
            except:
                pass
        if df is None or len(df) < 2:
            try:
                df = ak.stock_zh_index_daily_tx(symbol=code)
            except:
                pass
        if df is not None and len(df) >= 2:
            col = '收盘' if '收盘' in df.columns else ('close' if 'close' in df.columns else None)
            dcol = '日期' if '日期' in df.columns else ('date' if 'date' in df.columns else None)
            if col and dcol:
                dates = pd.to_datetime(df[dcol].values)
                idx_s = dates.searchsorted(start, side='right') - 1
                idx_e = dates.searchsorted(end, side='right') - 1
                if 0 <= idx_s < len(dates) and 0 <= idx_e < len(dates):
                    s_close = float(df[col].iloc[idx_s])
                    e_close = float(df[col].iloc[idx_e])
                    ret = (e_close / s_close - 1) * 100
                    self._stock_band_cache[cache_key] = ret
                    return ret
        self._stock_band_cache[cache_key] = None
        return None

    def get_band_return(self, s, e, metric="etf"):
        if metric == "oamv":
            idx_s = self.df['date'].searchsorted(s)
            idx_e = self.df['date'].searchsorted(e)
            if 0 <= idx_s < len(self.oamv) and 0 <= idx_e < len(self.oamv):
                return (self.oamv[idx_e] / self.oamv[idx_s] - 1) * 100
            return None
        src = {"sh": self.sh, "sz": self.sz, "etf": self.etf}.get(metric)
        if src is None or len(src) == 0:
            return None
        col = 'close' if metric in ('sz', 'etf') else '收盘'
        if col not in src.columns:
            return None
        s_close = src[col][src.index <= s]
        e_close = src[col][src.index <= e]
        if len(s_close) and len(e_close):
            return (e_close.iloc[-1] / s_close.iloc[-1] - 1) * 100
        return None

    def get_status(self):
        import pandas as pd
        in_band = self.open_band_start is not None
        now = self.df['date'].max()
        oamv_now = self.oamv[-1]
        oamv_pct_now = self.oamv_pct[-1]

        result = {
            "in_band": in_band,
            "oamv_value": oamv_now,
            "oamv_pct": oamv_pct_now,
            "last_date": now,
            "bands": [],
        }

        if in_band:
            start = pd.Timestamp(self.open_band_start)
            peak = self.open_band_peak
            idx = self.df['date'].searchsorted(start)
            oamv_start = self.oamv[idx] if 0 <= idx < len(self.oamv) else None
            peak_pct = (peak / oamv_start - 1) * 100 if oamv_start else 0
            dd = (oamv_now / peak - 1) * 100
            result["band_start"] = start
            result["band_days"] = (now - start).days
            result["peak_gain"] = peak_pct
            result["drawdown"] = dd
            result["exit_threshold"] = self.strategy['exit_dd']

        for s, e in reversed(self.bands):
            result["bands"].append({"start": s, "end": e, "days": (e - s).days})

        return result
