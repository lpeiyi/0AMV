import akshare as ak, pandas as pd, numpy as np, time

def cs(s,start,end,retries=5):
    for i in range(retries):
        try: return ak.stock_zh_index_hist_csindex(symbol=s,start_date=start,end_date=end)
        except: time.sleep(5)
    raise Exception('fail')
def qq(s,retries=5):
    for i in range(retries):
        try: return ak.stock_zh_index_daily_tx(symbol=s)
        except: time.sleep(3)
    raise Exception('fail')

df = cs('000985','20100101','20260619')
df = df.rename(columns={'日期':'date','成交金额':'a'})
df['date']=pd.to_datetime(df['date']); df=df.sort_values('date').reset_index(drop=True)
a = df['a'].values
sma = np.zeros(len(a))
for i in range(len(a)):
    sma[i] = a[i] if i==0 else (2*a[i]+8*sma[i-1])/10
pct = np.diff(sma)/sma[:-1]*100; pct=np.insert(pct,0,0)
raw=[]; start=None; pv=None
for i in range(len(pct)):
    if start is None:
        if pct[i]>=3.0: start=df['date'].iloc[i]; pv=sma[i]
    else:
        if sma[i]>pv: pv=sma[i]
        if (sma[i]/pv-1)*100<=-7.0: raw.append((start,df['date'].iloc[i])); start=None
raw=[(s,e) for s,e in raw if s>=pd.Timestamp('2023-01-01')]
bands=[raw[0]]
for bs,be in raw[1:]:
    if (bs-bands[-1][1]).days<=10: bands[-1]=(bands[-1][0],max(bands[-1][1],be))
    else: bands.append((bs,be))

sh=cs('000001','20100101','20260619')
sh['date']=pd.to_datetime(sh['日期']); sh=sh.sort_values('date').set_index('date')
sz=qq('sz399006'); sz['date']=pd.to_datetime(sz['date']); sz=sz.sort_values('date').set_index('date')
etf=qq('sz159915'); etf['date']=pd.to_datetime(etf['date']); etf=etf.sort_values('date').set_index('date')

rows=[]
for i,(s,e) in enumerate(bands,1):
    shr=(sh['收盘'][sh.index<=e].iloc[-1]/sh['收盘'][sh.index<=s].iloc[-1]-1)*100
    szr=(sz['close'][sz.index<=e].iloc[-1]/sz['close'][sz.index<=s].iloc[-1]-1)*100
    etfr=(etf['close'][etf.index<=e].iloc[-1]/etf['close'][etf.index<=s].iloc[-1]-1)*100
    rows.append([i,str(s.date()),str(e.date()),(e-s).days,f'{shr:.2f}%',f'{szr:.2f}%',f'{etfr:.2f}%'])

out=pd.DataFrame(rows,columns=['波段','起点','终点','天数','上证指数','创业板指','159915'])
out.to_csv('bands_returns.csv',index=False,encoding='utf-8-sig')
print(out.to_string(index=False))
print(f'\n已保存 bands_returns.csv ({len(rows)}个波段)')
