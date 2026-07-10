import os
from datetime import datetime, timezone
import pandas as pd

new = pd.read_csv("analysis_result.csv").set_index("Ticker")

if os.path.exists("state_previous_run.csv"):
    old = pd.read_csv("state_previous_run.csv").set_index("Ticker")
else:
    old = pd.DataFrame(columns=new.columns)

changes = []
for ticker, row in new.iterrows():
    prev = old.loc[ticker] if ticker in old.index else None

    if prev is None:
        changes.append(f"- **{ticker}** ({row['Empresa']}): se sumó al watchlist. {row['Momento']}.")
        continue

    notes = []

    prev_cross = prev.get("MACD cross")
    new_cross = row.get("MACD cross")
    prev_cross = None if pd.isna(prev_cross) else prev_cross
    new_cross = None if pd.isna(new_cross) else new_cross
    if new_cross and new_cross != prev_cross:
        notes.append(f"nuevo {new_cross}")

    if prev["Zona RSI"] != row["Zona RSI"] and row["Zona RSI"] != "neutral":
        notes.append(f"RSI pasó a {row['Zona RSI']} ({row['RSI14']})")

    if prev["Banda 52w"] != row["Banda 52w"]:
        notes.append(f"pasó de '{prev['Banda 52w']}' a '{row['Banda 52w']}' vs. máximo de 52 semanas")

    if notes:
        changes.append(f"- **{ticker}** ({row['Empresa']}): {'; '.join(notes)}. Precio actual: ${row['Precio']}.")

if changes:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = [
        f"# Señales — {today}",
        "",
        "No es recomendación de inversión, es lectura técnica automática (SMA50/200, RSI14, cruces de MACD, distancia a máximos de 52 semanas).",
        "",
        *changes,
    ]
    with open("latest_report.md", "w") as f:
        f.write("\n".join(report) + "\n")
    print(f"latest_report.md actualizado con {len(changes)} cambios.")
else:
    print("Sin cambios relevantes, latest_report.md sin tocar.")

new.reset_index().to_csv("state_previous_run.csv", index=False)
with open("last_run.txt", "w") as f:
    f.write(datetime.now(timezone.utc).isoformat() + "\n")
