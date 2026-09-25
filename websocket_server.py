# MIT License
#
# @title Copyright (c) 2026 KOUAME Koffi Fidèle
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""
MediCare+ real-time WebSocket API.

Streams the dashboard indicators computed on the clean register
(data/hospital_clean.csv, written by MediCare-Hospital-Analytics.ipynb).
Every indicator uses the same base as the report:
    - length of stay on valid stays only (LOS_valid),
    - revenue on genuine bills only (Bill_clean).

Usage:
    python websocket_server.py
    python websocket_server.py --host 127.0.0.1 --port 8765 --interval 3

Protocol (JSON messages): see WEBSOCKET.md.
"""

# ===============================================================
# @title 📦 Import libraries
# ===============================================================

# Standard library imports
import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

# Third-party imports
import pandas as pd

try:
    import websockets
    from websockets.asyncio.server import serve
except ImportError:
    raise SystemExit("Install the dependency first: pip install websockets")


# ===============================================================
# @title Paths and protocol constants
# ===============================================================

PROJECT_PATH = Path(__file__).resolve().parent
CLEAN_FILE = PROJECT_PATH / "data" / "hospital_clean.csv"

PROTOCOL_VERSION = "2.0"

# Dashboard filter key -> column of the clean register
FILTER_COLUMNS = {
    "month": "AdmitMonthName",
    "doctor": "Doctor",
    "diagnosis": "Diagnosis",
    "insurance": "Insurance",
    "gender": "Gender",
    "severity": "Severity",
}
SEARCH_COLUMNS = ["PatientName", "Doctor", "Diagnosis", "EpisodeID"]


# ===============================================================
# @title Load the clean register
# ===============================================================

def load_register(path: Path = CLEAN_FILE) -> pd.DataFrame:
    """
    Loads the clean register written by the analysis notebook.

    Args:
        path: The path to hospital_clean.csv.

    Returns:
        The clean register, one row per admission episode.
    """
    if not path.exists():
        raise SystemExit(f"❌ {path} not found. Run MediCare-Hospital-Analytics.ipynb first.")
    register = pd.read_csv(path)
    missing = {"LOS_valid", "Bill_clean", "Bill", *FILTER_COLUMNS.values()} - set(register.columns)
    if missing:
        raise SystemExit(f"❌ Columns missing from {path.name}: {sorted(missing)}")
    return register


# ===============================================================
# @title Indicators and filters
# ===============================================================

def compute_kpis(df: pd.DataFrame) -> dict:
    """
    Computes the indicators streamed to the dashboard, on the report's bases.

    Args:
        df: The (possibly filtered) clean register.

    Returns:
        A dictionary of indicators. total_revenue is the validated revenue;
        raw_bill_sum is sent for reconciliation only.
    """
    los = df["LOS_valid"].dropna()
    bills = df["Bill_clean"].dropna()
    return {
        "total_admissions": int(len(df)),
        "total_patients": int(df["PatientName"].nunique()),
        "total_doctors": int(df["Doctor"].nunique()),
        "total_diagnoses": int(df["Diagnosis"].nunique()),
        "total_revenue": round(float(bills.sum()), 2),
        "validated_revenue": round(float(bills.sum()), 2),
        "genuine_bills": int(len(bills)),
        "raw_bill_sum": round(float(df["Bill"].sum()), 2),
        "avg_los": round(float(los.mean()), 2) if len(los) else None,
        "valid_stays": int(len(los)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Applies the dashboard filters and the free-text search.

    Args:
        df: The clean register.
        filters: The filter values sent by the dashboard ("All" means no filter).

    Returns:
        The rows that match every active filter.
    """
    mask = pd.Series(True, index=df.index)
    for key, column in FILTER_COLUMNS.items():
        value = filters.get(key)
        if value and value != "All":
            mask &= df[column].astype(str) == str(value)
    query = (filters.get("q") or "").strip().lower()
    if query:
        text = df[SEARCH_COLUMNS].astype(str).agg(" ".join, axis=1).str.lower()
        mask &= text.str.contains(query, regex=False)
    return df[mask]


def kpi_message(df: pd.DataFrame, filters: dict, source: str) -> str:
    """
    Builds a kpi_update message for the current filters.

    Args:
        df: The clean register.
        filters: The active filters.
        source: Why the update is sent: "snapshot", "filter" or "stream".

    Returns:
        The JSON message.
    """
    subset = apply_filters(df, filters)
    return json.dumps({"type": "kpi_update", "kpis": compute_kpis(subset),
                       "filtered": int(len(subset)), "source": source})


# ===============================================================
# @title Connection handler
# ===============================================================

async def handle_client(websocket, register: pd.DataFrame, interval: float):
    """
    Serves one dashboard connection: answers requests and streams updates.

    Args:
        websocket: The client connection.
        register: The clean register.
        interval: Seconds between two streamed updates.
    """
    filters: dict = {}

    await websocket.send(json.dumps({
        "type": "hello", "version": PROTOCOL_VERSION,
        "service": "MediCare+ Realtime API", "rows": int(len(register)),
        "interval_sec": interval,
    }))
    await websocket.send(kpi_message(register, filters, "snapshot"))

    async def reader():
        nonlocal filters
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"type": "error", "message": "invalid JSON"}))
                continue
            kind = msg.get("type")
            if kind == "ping":
                await websocket.send(json.dumps(
                    {"type": "pong", "ts": datetime.now(timezone.utc).isoformat()}))
            elif kind == "filter":
                filters = {key: msg.get(key, "All") for key in FILTER_COLUMNS}
                filters["q"] = msg.get("q") or ""
                await websocket.send(kpi_message(register, filters, "filter"))
            elif kind == "subscribe":
                await websocket.send(json.dumps(
                    {"type": "subscribed", "channel": msg.get("channel", "kpis")}))
            else:
                await websocket.send(json.dumps(
                    {"type": "error", "message": f"unknown type: {kind}"}))

    async def publisher():
        # Re-sends the indicators on the interval. Values are the real ones:
        # no random jitter is added, so a streamed figure always matches the report.
        while True:
            await asyncio.sleep(interval)
            await websocket.send(kpi_message(register, filters, "stream"))

    try:
        await asyncio.gather(reader(), publisher())
    except websockets.ConnectionClosed:
        pass


# ===============================================================
# @title 🚀 Start the server
# ===============================================================

async def main(host: str, port: int, interval: float):
    """
    Loads the register and serves the WebSocket API until interrupted.

    Args:
        host: The interface to listen on.
        port: The port to listen on.
        interval: Seconds between two streamed updates.
    """
    register = load_register()
    kpis = compute_kpis(register)
    print(f"✅ Loaded {len(register)} episodes from {CLEAN_FILE.name}")
    print(f"   Validated revenue {kpis['validated_revenue']:,.0f} on {kpis['genuine_bills']} genuine bills")
    print(f"   Mean length of stay {kpis['avg_los']:.2f} days on {kpis['valid_stays']} valid stays")
    print(f"🟢 WebSocket API listening on ws://{host}:{port}")

    async def handler(websocket):
        await handle_client(websocket, register, interval)

    async with serve(handler, host, port):
        await asyncio.Future()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediCare+ WebSocket API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--interval", type=float, default=3.0,
                        help="Seconds between two streamed updates")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.host, args.port, args.interval))
    except KeyboardInterrupt:
        print("🔴 Server stopped.")
