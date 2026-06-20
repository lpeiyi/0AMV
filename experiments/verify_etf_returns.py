import akshare as ak
import pandas as pd

print("下载159915ETF数据(腾讯源)...")
df = ak.stock_zh_index_daily_tx(symbol='sz159915')
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')

pairs = [
    (1,  '2023-01-30', '2023-04-21'),
    (2,  '2023-07-31', '2023-08-07'),
    (3,  '2023-08-29', '2023-09-14'),
    (4,  '2023-10-25', '2023-11-22'),
    (5,  '2023-12-28', '2024-01-17'),
    (6,  '2024-01-25', '2024-01-30'),
    (7,  '2024-02-06', '2024-03-14'),
    (8,  '2024-04-17', '2024-05-15'),
    (9,  '2024-07-31', '2024-08-12'),
    (10, '2024-08-30', '2024-10-08'),
    (11, '2024-10-18', '2024-11-14'),
    (12, '2025-01-14', '2025-01-27'),
    (13, '2025-02-06', '2025-02-28'),
    (14, '2025-04-08', '2025-04-14'),
    (15, '2025-05-06', '2025-05-15'),
    (16, '2025-06-25', '2025-09-04'),
    (17, '2026-01-05', '2026-02-02'),
    (18, '2026-04-08', '2026-05-27'),
    (19, '2026-06-15', None),
]

# 用户提供的数据
user_values = {
    1: -12.84, 2: 1.02, 3: -2.49, 4: 3.66, 5: -6.07,
    6: -6.42, 7: 19.97, 8: 4.90, 9: -2.37, 10: 77.00,
    11: 14.69, 12: 4.43, 13: 5.14, 14: 6.76, 15: 4.74,
    16: 34.59, 17: 2.07, 18: 28.72, 19: 11.00,
}

print(f"{'序号':>3} {'开始':<12} {'结束':<12} {'我的计算':>8} {'你的数据':>8} {'差异':>7}")
print("-" * 50)
total_mine = 1.0
total_yours = 1.0
for n, s, e in pairs:
    if e is None:
        end_ts = pd.Timestamp.today()
        e_str = end_ts.strftime('%Y-%m-%d')
    else:
        end_ts = pd.Timestamp(e)
        e_str = e
    s_ts = pd.Timestamp(s)
    s_close = df[df.index <= s_ts].iloc[-1]['close'] if len(df[df.index <= s_ts]) > 0 else None
    e_close = df[df.index <= end_ts].iloc[-1]['close'] if len(df[df.index <= end_ts]) > 0 else None
    if s_close and e_close:
        ret = (e_close / s_close - 1) * 100
        diff = ret - user_values[n]
        total_mine *= (1 + ret / 100)
        total_yours *= (1 + user_values[n] / 100)
        print(f"{n:>3} {s:<12} {e_str:<12} {ret:>7.2f}% {user_values[n]:>7.2f}% {diff:>+6.2f}%")
    else:
        print(f"{n:>3} {s:<12} {e_str:<12} {'N/A':>8}")

total_mine_ret = (total_mine - 1) * 100
total_yours_ret = (total_yours - 1) * 100
print("-" * 50)
print(f"{'总收益(复利)':>29} {total_mine_ret:>7.2f}% {total_yours_ret:>7.2f}%")
