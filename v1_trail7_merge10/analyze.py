import akshare as ak
import pandas as pd
import numpy as np

print("获取中证全指(000985)历史数据...")
df = ak.stock_zh_index_hist_csindex(
    symbol='000985',
    start_date='20100101',
    end_date='20260619'
)

df = df.rename(columns={
    '日期': 'date',
    '成交金额': 'amount_yi',  # 成交金额(亿元)
})
df['date'] = pd.to_datetime(df['date'])

df = df.sort_values('date').reset_index(drop=True)

# 0AMV ≈ SMA(成交金额, 10, 2)
# Tongdaxin SMA(X, N, M): SMA_t = (M * X_t + (N-M) * SMA_{t-1}) / N
# 参数优化: N=10, M=2, entry>=3%, exit=峰值回撤<=-7%, 合并间隔<=10d
sma_values = np.zeros(len(df))
for i in range(len(df)):
    if i == 0:
        sma_values[i] = df['amount_yi'].iloc[i]
    else:
        sma_values[i] = (2 * df['amount_yi'].iloc[i] + 8 * sma_values[i-1]) / 10

df['oamv'] = sma_values

# 日涨跌幅
df['oamv_pct'] = df['oamv'].pct_change() * 100

result = df[df['date'] >= '2010-01-01'].copy()

# 信号统计
print(f"\n数据范围: {result['date'].min().date()} ~ {result['date'].max().date()}")
print(f"总交易日: {len(result)}")

oamv_peak = result['oamv'].cummax()
drawdown = (result['oamv'] / oamv_peak - 1) * 100

# ============================================================
# 波段区间: 入口 >= +3% → 峰值回撤跟踪 → 回撤<=-7%退出 → 合并间隔<=10天
# ============================================================
print(f"\n{'='*60}")
print(f"波段区间: 入口>=+3% 峰值回撤<=-7%退出 合并间隔<=10天 (2023年起)")
print(f"{'='*60}")

data = result[result['date'] >= '2022-01-01'].copy()

raw_bands = []
start = None
peak_val = None

for _, row in data.iterrows():
    pct = row['oamv_pct']
    if start is None:
        if pct >= 3.0:
            start = row['date']
            peak_val = row['oamv']
    else:
        if row['oamv'] > peak_val:
            peak_val = row['oamv']
        dd = (row['oamv'] / peak_val - 1) * 100
        if dd <= -7.0:
            raw_bands.append((start, row['date']))
            start = None

# 过滤2023年起
raw_bands = [(s, e) for s, e in raw_bands if s >= pd.Timestamp('2023-01-01')]

# 合并间隔<=10天的相邻波段
merge_gap = 10
bands = []
if raw_bands:
    bands = [raw_bands[0]]
    for bs, be in raw_bands[1:]:
        if (bs - bands[-1][1]).days <= merge_gap:
            bands[-1] = (bands[-1][0], max(bands[-1][1], be))
        else:
            bands.append((bs, be))

print(f"  原始波段: {len(raw_bands)} | 合并后: {len(bands)}")

if bands:
    for s, e in bands:
        seg = data[(data['date'] >= s) & (data['date'] <= e)]
        max_pct = seg['oamv_pct'].max()
        print(f"  {s.date()} ~ {e.date()}  ({(e-s).days:>3}d, 区间内最大涨幅: {max_pct:.2f}%)")
else:
    print("  无完整区间")

if start is not None:
    print(f"\n  (未完成区间: {start.date()} 出发后至今未触发退出)")

# ============================================================
# 计算上证指数、创业板指、159915ETF在每个区间累计涨幅
# ============================================================
print(f"\n{'='*60}")
print(f"各区间指数/ETF累计涨幅")
print(f"{'='*60}")

import time

def fetch_csindex(s, start, end, retries=5):
    for i in range(retries):
        try: return ak.stock_zh_index_hist_csindex(symbol=s, start_date=start, end_date=end)
        except: time.sleep(5)
    raise Exception('fail')

def fetch_qq(s, retries=5):
    for i in range(retries):
        try: return ak.stock_zh_index_daily_tx(symbol=s)
        except: time.sleep(3)
    raise Exception('fail')

print("下载数据...")
sh = fetch_csindex('000001','20100101','20260619')
sh['date'] = pd.to_datetime(sh['日期'])
sh = sh.sort_values('date').set_index('date')

sz = fetch_qq('sz399006')
sz['date'] = pd.to_datetime(sz['date'])
sz = sz.sort_values('date').set_index('date')

etf = fetch_qq('sz159915')
etf['date'] = pd.to_datetime(etf['date'])
etf = etf.sort_values('date').set_index('date')

# 合并到bands
if bands:
    print(f"\n{' 起点':<12} {'终点':<12} {'上证指数':>8} {'创业板指':>8} {'159915':>8} {'0AMV':>10}")
    print(f"  {'-'*58}")
    for s, e in bands:
        sh_ret = (sh['收盘'][sh.index<=e].iloc[-1] / sh['收盘'][sh.index<=s].iloc[-1] - 1) * 100
        sz_ret = (sz['close'][sz.index<=e].iloc[-1] / sz['close'][sz.index<=s].iloc[-1] - 1) * 100
        etf_ret = (etf['close'][etf.index<=e].iloc[-1] / etf['close'][etf.index<=s].iloc[-1] - 1) * 100
        oamv_start = result[result['date'] == s]['oamv'].values
        oamv_end = result[result['date'] == e]['oamv'].values
        oamv_ret = (oamv_end[0] / oamv_start[0] - 1) * 100 if len(oamv_start) > 0 and len(oamv_end) > 0 else None
        oamv_str = f"{oamv_ret:>7.2f}%" if oamv_ret is not None else "   N/A"
        print(f"  {str(s.date()):<12} {str(e.date()):<12} {sh_ret:>7.2f}% {sz_ret:>7.2f}% {etf_ret:>7.2f}% {oamv_str:>10}")

    # 总收益率
    sh_c = sz_c = et_c = 1.0
    for s, e in bands:
        sh_c *= sh['收盘'][sh.index<=e].iloc[-1] / sh['收盘'][sh.index<=s].iloc[-1]
        sz_c *= sz['close'][sz.index<=e].iloc[-1] / sz['close'][sz.index<=s].iloc[-1]
        et_c *= etf['close'][etf.index<=e].iloc[-1] / etf['close'][etf.index<=s].iloc[-1]
    print(f"\n  总收益率(复利):  上证 {(sh_c-1)*100:.2f}%  创业板 {(sz_c-1)*100:.2f}%  159915 {(et_c-1)*100:.2f}%")
else:
    print("  无完整区间")
