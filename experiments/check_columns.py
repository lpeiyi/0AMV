import akshare as ak
import pandas as pd

df = ak.stock_zh_index_hist_csindex(symbol='000001', start_date='20230101', end_date='20260619')
print("列名:", df.columns.tolist())
print(df.head(2))
print("---")
print(df.tail(2))
