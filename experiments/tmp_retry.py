import akshare as ak
import pandas as pd
import time

for i in range(3):
    try:
        df = ak.fund_etf_hist_em(symbol='159915', period='daily', start_date='20230101', end_date='20230131', adjust='qfq')
        print(f'尝试{i+1}: 成功, 行数={len(df)}')
        print(df.columns.tolist())
        print(df.head(2))
        break
    except Exception as e:
        print(f'尝试{i+1}: 失败 - {type(e).__name__}')
        time.sleep(3)
