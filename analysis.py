import json
from datetime import datetime, timezone
import pandas as pd
from metrics import analyze_ticker

with open("watchlist.json") as f:
    TICKERS = json.load(f)

rows = []
for ticker, name in TICKERS.items():
    row = analyze_ticker(ticker, name)
    if row:
        rows.append(row)

df = pd.DataFrame(rows).drop(columns=["SMA50", "SMA200"])
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 80)
print(df.to_string(index=False))
df.to_csv("analysis_result.csv", index=False)

with open("docs/data.json", "w") as f:
    json.dump({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tickers": rows,
    }, f, ensure_ascii=False, indent=2, default=lambda x: None if pd.isna(x) else x)
