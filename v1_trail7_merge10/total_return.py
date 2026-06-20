import akshare as ak
import pandas as pd
import numpy as np
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

# 算法波段
print("获取数据...")
df = fetch_csindex('000985','20100101','20260619')
df = df.rename(columns={'日期':'date','成交金额':'amount_yi'})
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
a = df['amount_yi'].values
N,M,ent,ext = 10,2,3.0,-7.0
sma = np.zeros(len(a))
for i in range(len(a)):
    sma[i] = a[i] if i==0 else (M*a[i]+(N-M)*sma[i-1])/N
pct = np.diff(sma)/sma[:-1]*100
pct = np.insert(pct,0,0)
# 峰值回撤跟踪止损
raw_bands = []
start = None
peak_val = None
for i in range(len(pct)):
    if start is None:
        if pct[i] >= ent:
            start = df['date'].iloc[i]
            peak_val = sma[i]
    else:
        if sma[i] > peak_val: peak_val = sma[i]
        dd = (sma[i]/peak_val-1)*100
        if dd <= ext:
            raw_bands.append((start, df['date'].iloc[i]))
            start = None
raw_bands = [(s,e) for s,e in raw_bands if s >= pd.Timestamp('2023-01-01')]
# 合并间隔<=10天
bands = [raw_bands[0]] if raw_bands else []
for bs,be in raw_bands[1:]:
    if (bs-bands[-1][1]).days <= 10:
        bands[-1] = (bands[-1][0], max(bands[-1][1], be))
    else:
        bands.append((bs,be))

sh = fetch_csindex('000001','20100101','20260619')
sh['date'] = pd.to_datetime(sh['日期'])
sh = sh.sort_values('date').set_index('date')
cy = fetch_qq('sz399006')
cy['date'] = pd.to_datetime(cy['date'])
cy = cy.sort_values('date').set_index('date')
etf = fetch_qq('sz159915')
etf['date'] = pd.to_datetime(etf['date'])
etf = etf.sort_values('date').set_index('date')

def comp_ret(pairs, label):
    sh_c = cy_c = et_c = 1.0
    for s_str, e_str in pairs:
        sd = pd.Timestamp(s_str); ed = pd.Timestamp(e_str)
        s_sh = sh['收盘'][sh.index<=sd].iloc[-1]; e_sh = sh['收盘'][sh.index<=ed].iloc[-1]
        s_cy = cy['close'][cy.index<=sd].iloc[-1]; e_cy = cy['close'][cy.index<=ed].iloc[-1]
        s_et = etf['close'][etf.index<=sd].iloc[-1]; e_et = etf['close'][etf.index<=ed].iloc[-1]
        sh_c *= (e_sh/s_sh); cy_c *= (e_cy/s_cy); et_c *= (e_et/s_et)
    print(f'\n{label}:')
    print(f'  上证指数: {(sh_c-1)*100:.2f}%')
    print(f'  创业板指: {(cy_c-1)*100:.2f}%')
    print(f'  159915:   {(et_c-1)*100:.2f}%')

comp_ret([(str(s.date()),str(e.date())) for s,e in bands], '=== 算法波段 总收益率(复利) ===')

user = [('2023-01-30','2023-04-21'),('2023-07-31','2023-08-07'),('2023-08-29','2023-09-14'),
        ('2023-10-25','2023-11-22'),('2023-12-28','2024-01-17'),('2024-01-25','2024-01-30'),
        ('2024-02-06','2024-03-14'),('2024-04-17','2024-05-15'),('2024-07-31','2024-08-12'),
        ('2024-08-30','2024-10-08'),('2024-10-18','2024-11-14'),('2025-01-14','2025-01-27'),
        ('2025-02-06','2025-02-28'),('2025-04-08','2025-04-14'),('2025-05-06','2025-05-15'),
        ('2025-06-25','2025-09-04'),('2026-01-05','2026-02-02'),('2026-04-08','2026-05-27'),
        ('2026-06-15','2026-06-19')]
comp_ret(user, '=== 用户区间 总收益率(复利) ===')

# 2023-01-01到2026-06-19的全程买入持有
print('\n=== 全程买入持有 2023-01-01 ~ 2026-06-19 ===')
sd = pd.Timestamp('2023-01-01'); ed = pd.Timestamp('2026-06-19')
s_sh = sh['收盘'][sh.index<=sd].iloc[-1]; e_sh = sh['收盘'][sh.index<=ed].iloc[-1]
s_cy = cy['close'][cy.index<=sd].iloc[-1]; e_cy = cy['close'][cy.index<=ed].iloc[-1]
s_et = etf['close'][etf.index<=sd].iloc[-1]; e_et = etf['close'][etf.index<=ed].iloc[-1]
print(f'  上证指数: {(e_sh/s_sh-1)*100:.2f}%')
print(f'  创业板指: {(e_cy/s_cy-1)*100:.2f}%')
print(f'  159915:   {(e_et/s_et-1)*100:.2f}%')
