import akshare as ak
import pandas as pd

# 159915 前复权数据 - 用不同数据源尝试
print("尝试获取159915前复权数据...")

# 尝试 stock_zh_a_hist 带 adjust 参数 (East Money, 前复权)
try:
    df = ak.stock_zh_a_hist(symbol='159915', period='daily', start_date='20230101', end_date='20260619', adjust='qfq')
    print("East Money 前复权成功")
except Exception as e:
    print(f"East Money qfq 失败: {e}")
    df = None

if df is None:
    # 尝试 stock_zh_a_daily Sina (可能包含复权)
    try:
        df = ak.stock_zh_a_daily(symbol='sz159915', adjust='qfq')
        print("Sina 前复权成功")
    except Exception as e:
        print(f"Sina qfq 失败: {e}")
        df = None

if df is not None:
    print(df.columns.tolist())
    print(df.tail(3))
else:
    print("所有数据源均失败")
