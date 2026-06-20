import akshare as ak
import pandas as pd

# 尝试不同数据源获取159915复权数据
sources = []

# 1. 尝试 fund_etf_hist_em (东方财富 ETF 数据)
try:
    df = ak.fund_etf_hist_em(symbol="159915", period="daily", start_date="20230101", end_date="20260619", adjust="qfq")
    sources.append(("fund_etf_hist_em", df.columns.tolist(), len(df), df.tail(1)))
    print("fund_etf_hist_em 成功")
except Exception as e:
    print(f"fund_etf_hist_em 失败: {e}")

# 2. 尝试 stock_zh_a_hist (东方财富个股) qfq
try:
    df = ak.stock_zh_a_hist(symbol="159915", period="daily", start_date="20230101", end_date="20260619", adjust="qfq")
    sources.append(("stock_zh_a_hist_qfq", df.columns.tolist(), len(df), df.tail(1)))
    print("stock_zh_a_hist qfq 成功")
except Exception as e:
    print(f"stock_zh_a_hist qfq 失败: {e}")

# 3. 尝试 stock_zh_a_hist (东方财富个股) hfq
try:
    df2 = ak.stock_zh_a_hist(symbol="159915", period="daily", start_date="20230101", end_date="20260619", adjust="hfq")
    sources.append(("stock_zh_a_hist_hfq", df2.columns.tolist(), len(df2), df2.tail(1)))
    print("stock_zh_a_hist hfq 成功")
except Exception as e:
    print(f"stock_zh_a_hist hfq 失败: {e}")

print("\n成功的数据源:", sources)
