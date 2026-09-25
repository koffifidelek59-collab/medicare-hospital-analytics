# MediCare+ Real-time WebSocket API

`websocket_server.py` streams the dashboard indicators from the clean register
(`data/hospital_clean.csv`, written by `MediCare-Hospital-Analytics.ipynb`).

The dashboard works without the server, on its embedded dataset. The server adds live
indicator streaming and filter synchronisation.

## Start the server

```bash
pip install -r requirements.txt
python websocket_server.py
# optional
python websocket_server.py --host 127.0.0.1 --port 8765 --interval 3
```

The server listens on **ws://127.0.0.1:8765** and prints the headline figures on start:

```
✅ Loaded 247 episodes from hospital_clean.csv
   Validated revenue 153,155 on 52 genuine bills
   Mean length of stay 6.74 days on 218 valid stays
🟢 WebSocket API listening on ws://127.0.0.1:8765
```

## Connect from the dashboard

1. Open `dashboard.html` in a modern browser.
2. In the LIVE bar, check that the URL reads `ws://127.0.0.1:8765`.
3. Click **Connect**. The status changes from **WS OFFLINE** to **WS LIVE**.
4. The indicator strip now follows the server, and every filter change is sent to it.

## Indicator bases

The server uses the same bases as the report, so a streamed figure always matches it.

| Indicator | Base |
|---|---|
| `total_revenue`, `validated_revenue` | Sum of `Bill_clean`: genuine bills only (placeholders 999 and 3,852 excluded) |
| `raw_bill_sum` | Sum of `Bill`: sent for reconciliation only, not for decisions |
| `avg_los` | Mean of `LOS_valid`: valid stays only (29 date errors excluded) |
| `genuine_bills`, `valid_stays` | The number of episodes each indicator rests on |

When connected, the dashboard's revenue tile is labelled **Validated revenue**. When
offline, the tile shows the raw billed sum, as described in section 9.1 of the report.

## Message protocol (JSON)

### Client → Server

| Message | Effect |
|---|---|
| `{"type":"ping"}` | Answered by `pong` |
| `{"type":"subscribe","channel":"kpis"}` | Answered by `subscribed` |
| `{"type":"filter","month":"Aug","doctor":"All","diagnosis":"All","insurance":"All","gender":"All","severity":"All","q":""}` | Sets the filters; answered by a `kpi_update` for the filtered selection |

`"All"` means no filter on that field. `q` is a free-text search on patient, physician,
diagnosis and episode identifier.

### Server → Client

| Message | When |
|---|---|
| `{"type":"hello","version":"2.0","rows":247,"interval_sec":3.0}` | On connection |
| `{"type":"kpi_update","kpis":{...},"filtered":247,"source":"snapshot"}` | On connection |
| `{"type":"kpi_update","kpis":{...},"filtered":10,"source":"filter"}` | After each `filter` message |
| `{"type":"kpi_update","kpis":{...},"filtered":10,"source":"stream"}` | Every `interval` seconds, for the current filters |
| `{"type":"pong","ts":"..."}` | After `ping` |
| `{"type":"error","message":"..."}` | Invalid JSON or unknown message type |

Streamed values are the real ones: no random variation is added.

## Changes from version 1.0

- Mean length of stay is computed on `LOS_valid`. Version 1.0 read a `LOS` column that does
  not exist in the clean register, so it always sent 0.
- Revenue is computed on genuine bills. Version 1.0 summed the raw column (618,995).
- The random variation added to revenue on every update is removed.
- The dashboard now sends its filters to the server on every change. Before, the stream
  overwrote the filtered indicators with the unfiltered ones every few seconds.
