import yfinance as yf
import pandas as pd

# Tickers mencionados en el portafolio del video (episodio #20, Joven Inversor)
TICKERS = {
    "MELI": "Mercado Libre",
    "MSFT": "Microsoft",
    "AMD": "AMD",
    "BABA": "Alibaba",
    "AAPL": "Apple",
    "META": "Meta",
    "NVDA": "Nvidia",
    "AMZN": "Amazon",
    "GOOGL": "Alphabet",
    "TSLA": "Tesla",
    "GGAL": "Grupo Galicia",
    "SPY": "S&P 500 (ETF)",
    "QQQ": "Nasdaq 100 (ETF, 'TripleQ')",
}

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

rows = []
for ticker, name in TICKERS.items():
    hist = yf.Ticker(ticker).history(period="2y")
    if hist.empty:
        rows.append({"Ticker": ticker, "Empresa": name, "Error": "sin datos"})
        continue
    close = hist["Close"]
    price = close.iloc[-1]
    ath_2y = close.max()
    ema20 = close.ewm(span=20).mean().iloc[-1]
    rsi14 = rsi(close).iloc[-1]
    dist_ath = (price / ath_2y - 1) * 100
    dist_ema20 = (price / ema20 - 1) * 100

    if dist_ath < -30 and rsi14 < 45:
        signal = "Posible oportunidad (caída fuerte + RSI bajo)"
    elif dist_ath < -15:
        signal = "Vigilar (caída moderada desde máximo)"
    elif rsi14 > 70:
        signal = "Sobrecomprado, cautela"
    else:
        signal = "Sin señal clara"

    rows.append({
        "Ticker": ticker,
        "Empresa": name,
        "Precio": round(price, 2),
        "% vs max 2a": round(dist_ath, 1),
        "% vs EMA20": round(dist_ema20, 1),
        "RSI(14)": round(rsi14, 1),
        "Señal": signal,
    })

df = pd.DataFrame(rows)
pd.set_option("display.width", 140)
print(df.to_string(index=False))
df.to_csv("scan_result.csv", index=False)
