import json
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory
import pandas as pd

from metrics import analyze_ticker, fetch_history, rsi, macd

app = Flask(__name__, static_folder=None)

WATCHLIST_PATH = "watchlist.json"
NOTES_PATH = "notes.json"


def load_watchlist():
    with open(WATCHLIST_PATH) as f:
        return json.load(f)


def save_watchlist(wl):
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(wl, f, ensure_ascii=False, indent=2)


def load_notes():
    if not os.path.exists(NOTES_PATH):
        return {}
    with open(NOTES_PATH) as f:
        return json.load(f)


def save_notes(notes):
    with open(NOTES_PATH, "w") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def clean(row):
    return {k: (None if pd.isna(v) else v) for k, v in row.items()}


@app.route("/")
@app.route("/detalle.html")
def index():
    return send_from_directory("local", request.path.lstrip("/") or "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("local", filename)


@app.route("/api/data")
def api_data():
    wl = load_watchlist()
    rows = []
    for ticker, name in wl.items():
        row = analyze_ticker(ticker, name)
        if row:
            rows.append(clean(row))
    return jsonify({"generated_at": datetime.now(timezone.utc).isoformat(), "tickers": rows})


@app.route("/api/watchlist", methods=["POST"])
def add_ticker():
    body = request.get_json()
    ticker = body["ticker"].strip().upper()
    name = body.get("name", "").strip() or ticker

    row = analyze_ticker(ticker, name)
    if row is None:
        return jsonify({"error": f"no encontré datos para '{ticker}' en yfinance"}), 400

    wl = load_watchlist()
    wl[ticker] = name
    save_watchlist(wl)
    return jsonify({"ok": True, "ticker": clean(row)})


@app.route("/api/watchlist/<ticker>", methods=["DELETE"])
def remove_ticker(ticker):
    wl = load_watchlist()
    ticker = ticker.upper()
    if ticker in wl:
        del wl[ticker]
        save_watchlist(wl)
    return jsonify({"ok": True})


@app.route("/api/summary/<ticker>")
def api_summary(ticker):
    ticker = ticker.upper()
    wl = load_watchlist()
    name = wl.get(ticker, ticker)
    row = analyze_ticker(ticker, name)
    if row is None:
        return jsonify({"error": "sin datos"}), 404
    return jsonify(clean(row))


@app.route("/api/chart/<ticker>")
def api_chart(ticker):
    hist = fetch_history(ticker.upper(), period="2y")
    if hist.empty:
        return jsonify({"error": "sin datos"}), 404

    close = hist["Close"]
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    rsi14 = rsi(close)
    macd_line, signal_line = macd(close)

    candles = []
    for date, row in hist.iterrows():
        candles.append({
            "time": date.strftime("%Y-%m-%d"),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
        })

    def series(s):
        return [
            {"time": d.strftime("%Y-%m-%d"), "value": round(v, 2)}
            for d, v in s.items() if pd.notna(v)
        ]

    return jsonify({
        "ticker": ticker.upper(),
        "candles": candles,
        "sma50": series(sma50),
        "sma200": series(sma200),
        "rsi14": series(rsi14),
        "macd": series(macd_line),
        "macd_signal": series(signal_line),
    })


@app.route("/api/notes/<ticker>", methods=["GET"])
def get_notes(ticker):
    notes = load_notes()
    return jsonify(notes.get(ticker.upper(), []))


@app.route("/api/notes/<ticker>", methods=["POST"])
def add_note(ticker):
    ticker = ticker.upper()
    body = request.get_json()
    text = body["text"].strip()
    if not text:
        return jsonify({"error": "nota vacía"}), 400

    notes = load_notes()
    notes.setdefault(ticker, [])
    notes[ticker].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "text": text,
    })
    save_notes(notes)
    return jsonify(notes[ticker])


@app.route("/api/notes/<ticker>/<int:index>", methods=["DELETE"])
def delete_note(ticker, index):
    ticker = ticker.upper()
    notes = load_notes()
    items = notes.get(ticker, [])
    if 0 <= index < len(items):
        items.pop(index)
        save_notes(notes)
    return jsonify(items)


if __name__ == "__main__":
    print("Corriendo en http://localhost:5050")
    app.run(port=5050, debug=True)
