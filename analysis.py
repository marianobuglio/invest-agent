import json
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd

with open("watchlist.json") as f:
    TICKERS = json.load(f)


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    return macd_line, signal_line


def atr(hist, period=14):
    high, low, close = hist["High"], hist["Low"], hist["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def macd_cross_recent(macd_line, signal_line, lookback=5):
    diff = macd_line - signal_line
    recent = diff.iloc[-lookback:]
    if recent.iloc[-1] > 0 and (recent < 0).any():
        return "cruce alcista reciente"
    if recent.iloc[-1] < 0 and (recent > 0).any():
        return "cruce bajista reciente"
    return None


def trend_zone(row):
    return "alcista" if row["SMA50"] > row["SMA200"] else "bajista"


def drawdown_band(row):
    if row["% vs max 52w"] > -5:
        return "cerca_maximos"
    elif row["% vs max 52w"] > -20:
        return "correccion_moderada"
    return "caida_profunda"


def rsi_zone(row):
    if row["RSI14"] > 70:
        return "sobrecomprado"
    elif row["RSI14"] < 35:
        return "sobrevendido"
    return "neutral"


DRAWDOWN_LABEL = {
    "cerca_maximos": "cerca de máximos de 52 semanas",
    "correccion_moderada": "corrección moderada desde máximos",
    "caida_profunda": "caída profunda desde máximos",
}
RSI_LABEL = {
    "sobrecomprado": "sobrecomprado",
    "sobrevendido": "sobrevendido",
    "neutral": "momentum neutral",
}


def momento(row):
    parts = [
        f"tendencia de fondo {row['Tendencia']}",
        DRAWDOWN_LABEL[row["Banda 52w"]],
        RSI_LABEL[row["Zona RSI"]],
    ]
    if row["MACD cross"]:
        parts.append(row["MACD cross"])
    return ", ".join(parts)


rows = []
for ticker, name in TICKERS.items():
    hist = yf.Ticker(ticker).history(period="3y")
    if hist.empty:
        continue
    close = hist["Close"]
    price = close.iloc[-1]

    max_2y = close.max()
    max_52w = close.iloc[-252:].max()
    min_52w = close.iloc[-252:].min()

    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1]
    ema20 = close.ewm(span=20).mean().iloc[-1]
    rsi14 = rsi(close).iloc[-1]

    macd_line, signal_line = macd(close)
    cross = macd_cross_recent(macd_line, signal_line)

    atr14 = atr(hist).iloc[-1]
    atr_pct = atr14 / price * 100

    row = {
        "Ticker": ticker,
        "Empresa": name,
        "Precio": round(price, 2),
        "% vs max 2a": round((price / max_2y - 1) * 100, 1),
        "% vs max 52w": round((price / max_52w - 1) * 100, 1),
        "% vs min 52w": round((price / min_52w - 1) * 100, 1),
        "% vs EMA20": round((price / ema20 - 1) * 100, 1),
        "SMA50": sma50,
        "SMA200": sma200,
        "RSI14": round(rsi14, 1),
        "MACD cross": cross,
        "Volatilidad (ATR%)": round(atr_pct, 1),
    }
    row["Tendencia"] = trend_zone(row)
    row["Banda 52w"] = drawdown_band(row)
    row["Zona RSI"] = rsi_zone(row)
    row["Momento"] = momento(row)
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
