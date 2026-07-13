import os
from datetime import datetime, timezone
import pandas as pd

AVISO_LABEL = {
    "revisar_entrada": "vale la pena mirarla este mes para una posible entrada",
    "ya_corrio_mucho": "ya subió bastante y está cerca de máximos, sin descuento por ahora",
}

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

    prev_aviso = prev.get("Aviso")
    prev_aviso = None if pd.isna(prev_aviso) else prev_aviso
    new_aviso = row.get("Aviso")
    new_aviso = None if pd.isna(new_aviso) else new_aviso
    if new_aviso and new_aviso != prev_aviso:
        notes.append(AVISO_LABEL[new_aviso])

    if prev["Tendencia"] != row["Tendencia"]:
        notes.append(f"la tendencia de fondo pasó a {row['Tendencia']}")

    if notes:
        changes.append(f"- **{ticker}** ({row['Empresa']}): {'; '.join(notes)}. Precio actual: ${row['Precio']}.")

if changes:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = [
        f"# Señales — {today}",
        "",
        "Pensado para revisión mensual con horizonte de ~1 año, no para trading de corto plazo. No es recomendación de inversión.",
        "",
        *changes,
    ]
    with open("latest_report.md", "w") as f:
        f.write("\n".join(report) + "\n")
    print(f"latest_report.md actualizado con {len(changes)} cambios.")
else:
    print("Sin cambios relevantes a un año, latest_report.md sin tocar.")

new.reset_index().to_csv("state_previous_run.csv", index=False)
with open("last_run.txt", "w") as f:
    f.write(datetime.now(timezone.utc).isoformat() + "\n")
