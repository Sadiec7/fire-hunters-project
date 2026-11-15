"""
ia/data_bridge_20013d1.py
Puente de datos experimentales para el ensayo NASA ACME s-Flame 20013D1 (PSI-23).
Blindado contra diferencias de llaves en enforce_calibration_lock (lock_badge / lock_banner).
"""

import os
import sys
from io import StringIO
from typing import Dict, Any, Optional
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from contract_si import enforce_calibration_lock  # type: ignore
except ImportError:
    from ia.contract_si import enforce_calibration_lock

RAW_MFC_20013D1_CSV = """event_index,timestamp_reconstructed,mfc1_v,mfc2_v,mfc3_v,unit,calibration_verified
1,2020-01-13T18:21:48.162000,0.0,4.895001,3.658955,V,False
2,2020-01-13T18:21:49.092000,0.0,3.257996,2.435974,V,False
3,2020-01-13T18:21:49.602000,0.0,3.257996,2.435974,V,False
4,2020-01-13T18:21:54.370000,0.0,3.257996,2.435974,V,False
5,2020-01-13T18:21:55.140000,0.0,3.257996,2.435974,V,False
6,2020-01-13T18:21:58.198000,0.0,3.229996,2.414978,V,False
7,2020-01-13T18:22:01.077000,0.0,3.229996,2.414978,V,False
8,2020-01-13T18:22:03.249000,0.0,3.201001,2.393961,V,False
9,2020-01-13T18:22:05.774000,0.0,3.201001,2.393961,V,False
10,2020-01-13T18:22:08.513000,0.0,3.201001,2.393961,V,False
11,2020-01-13T18:22:10.371000,0.0,3.201001,2.393961,V,False
12,2020-01-13T18:22:12.601000,0.0,3.201001,2.393961,V,False
13,2020-01-13T18:22:14.892000,0.0,3.201001,2.393961,V,False
14,2020-01-13T18:22:17.110000,0.0,3.201001,2.393961,V,False
15,2020-01-13T18:22:19.442000,0.0,3.201001,2.393961,V,False
16,2020-01-13T18:22:21.785000,0.0,3.201001,2.393961,V,False
17,2020-01-13T18:22:24.012000,0.0,3.201001,2.393961,V,False
18,2020-01-13T18:22:26.315000,0.0,3.201001,2.393961,V,False
19,2020-01-13T18:22:28.590000,0.0,3.201001,2.393961,V,False
20,2020-01-13T18:22:30.811000,0.0,3.201001,2.393961,V,False
21,2020-01-13T18:22:32.955000,0.0,3.201001,2.393961,V,False
22,2020-01-13T18:22:35.102000,0.0,3.201001,2.393961,V,False
23,2020-01-13T18:22:37.288000,0.0,3.201001,2.393961,V,False
24,2020-01-13T18:22:39.410000,0.0,3.201001,2.393961,V,False
25,2020-01-13T18:22:41.512000,0.0,3.172998,2.372986,V,False
26,2020-01-13T18:22:43.105000,0.0,3.172998,2.372986,V,False
27,2020-01-13T18:22:44.690000,0.0,3.172998,2.372986,V,False
28,2020-01-13T18:22:46.215000,0.0,3.144002,2.351990,V,False
29,2020-01-13T18:22:47.510000,0.0,3.144002,2.351990,V,False
30,2020-01-13T18:22:48.802000,0.0,3.115997,2.330994,V,False
31,2020-01-13T18:22:49.915000,0.0,3.115997,2.330994,V,False
32,2020-01-13T18:22:50.880000,0.0,3.086998,2.309998,V,False
33,2020-01-13T18:22:51.720000,0.0,3.058998,2.288986,V,False
34,2020-01-13T18:22:52.490000,0.0,3.030001,2.267990,V,False
35,2020-01-13T18:22:53.180000,0.0,3.001999,2.246994,V,False
36,2020-01-13T18:22:53.810000,0.0,2.973000,2.225998,V,False
37,2020-01-13T18:22:54.390000,0.0,2.945000,2.204987,V,False
38,2020-01-13T18:22:54.910000,0.0,2.916000,2.183990,V,False
39,2020-01-13T18:22:55.380000,0.0,0.000000,0.000000,V,False
40,2020-01-13T18:22:55.720000,0.0,0.000000,0.000000,V,False
41,2020-01-13T18:22:56.010000,0.0,0.000000,0.000000,V,False
42,2020-01-13T18:22:56.286000,0.0,0.000000,0.000000,V,False
"""


def _ensure_lock_badge(d: Dict[str, Any], default_badge: str) -> Dict[str, Any]:
    res = dict(enforce_calibration_lock(d))
    badge = res.get("lock_badge", res.get("lock_banner", default_badge))
    res["lock_badge"] = badge
    res["lock_banner"] = badge
    return res


def load_mfc_20013d1_dataframe(csv_path: Optional[str] = None) -> pd.DataFrame:
    candidate_paths = []
    if csv_path:
        candidate_paths.append(csv_path)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths.extend([
        os.path.join(base_dir, "mfc_20013D1.csv"),
        os.path.join(base_dir, "20013D1_mfcSetpoints.csv"),
        os.path.join(os.path.dirname(base_dir), "mfc_20013D1.csv"),
    ])

    for p in candidate_paths:
        if p and os.path.exists(p):
            df = pd.read_csv(p)
            break
    else:
        df = pd.read_csv(StringIO(RAW_MFC_20013D1_CSV.strip()))

    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if "mfc1" in cl:
            col_map[c] = "mfc1_v"
        elif "mfc2" in cl:
            col_map[c] = "mfc2_v"
        elif "mfc3" in cl:
            col_map[c] = "mfc3_v"
        elif "time" in cl or "fecha" in cl or "ts" in cl:
            col_map[c] = "timestamp_reconstructed"
    df = df.rename(columns=col_map)

    if "event_index" not in df.columns:
        df["event_index"] = range(1, len(df) + 1)
    if "timestamp_reconstructed" not in df.columns:
        df["timestamp_reconstructed"] = [f"EVENT_{i:02d}" for i in df["event_index"]]
    return df


def get_20013d1_experimental_package(csv_path: Optional[str] = None) -> Dict[str, Any]:
    df = load_mfc_20013d1_dataframe(csv_path)
    default_v_badge = "[CALIBRACIÓN V → kg/s NO VERIFICADA]"

    mfc1_channel = _ensure_lock_badge({
        "channel_id": "MFC1",
        "channel_type": "MFC_CONTROLLER",
        "unit": "V",
        "calibration_verified": False,
        "events_count": int(len(df)),
        "values_V": [round(float(x), 6) for x in df["mfc1_v"].tolist()],
        "min_V": float(df["mfc1_v"].min()),
        "median_V": float(df["mfc1_v"].median()),
        "max_V": float(df["mfc1_v"].max()),
    }, default_v_badge)

    mfc2_channel = _ensure_lock_badge({
        "channel_id": "MFC2",
        "channel_type": "MFC_CONTROLLER",
        "unit": "V",
        "calibration_verified": False,
        "events_count": int(len(df)),
        "values_V": [round(float(x), 6) for x in df["mfc2_v"].tolist()],
        "min_V": float(df["mfc2_v"].min()),
        "median_V": float(df["mfc2_v"].median()),
        "max_V": float(df["mfc2_v"].max()),
    }, default_v_badge)

    mfc3_channel = _ensure_lock_badge({
        "channel_id": "MFC3",
        "channel_type": "MFC_CONTROLLER",
        "unit": "V",
        "calibration_verified": False,
        "events_count": int(len(df)),
        "values_V": [round(float(x), 6) for x in df["mfc3_v"].tolist()],
        "min_V": float(df["mfc3_v"].min()),
        "median_V": float(df["mfc3_v"].median()),
        "max_V": float(df["mfc3_v"].max()),
    }, default_v_badge)

    events_list = []
    for _, row in df.iterrows():
        events_list.append({
            "event_index": int(row["event_index"]),
            "timestamp": str(row["timestamp_reconstructed"]),
            "mfc1_v": float(row["mfc1_v"]),
            "mfc2_v": float(row["mfc2_v"]),
            "mfc3_v": float(row["mfc3_v"]),
            "unit": "V",
        })

    return {
        "experiment_id": "20013D1",
        "investigation_id": "PSI-23",
        "dataset": "ACME_S_FLAME",
        "test_day_code": "20013",
        "mfc_source_file": "20013D1_mfcSetpoints.csv",
        "measurement_source_file": "20013D1_data.csv",
        "experimental_conditions_raw": {
            "fuel_bottle_text": "66.7% H2 with CH4",
            "atmosphere_text": "~21% O2 with N4",
            "composition_basis_verified": False,
            "composition_lock_badge": "[BASE MOLAR/MÁSICA H2-CH4 NO VERIFICADA]",
        },
        "event_indices": [int(x) for x in df["event_index"].tolist()],
        "timestamps_reconstructed": [str(x) for x in df["timestamp_reconstructed"].tolist()],
        "mfc_events": events_list,
        "mfc_channels": {
            "MFC1": mfc1_channel,
            "MFC2": mfc2_channel,
            "MFC3": mfc3_channel,
        },
    }


def load_20013d1_package(mfc_csv_path: Optional[str] = None) -> Dict[str, Any]:
    return get_20013d1_experimental_package(csv_path=mfc_csv_path)

def load_experiment_package_20013d1(mfc_csv_path: Optional[str] = None) -> Dict[str, Any]:
    return get_20013d1_experimental_package(csv_path=mfc_csv_path)
if __name__ == "__main__":
    pkg = get_20013d1_experimental_package()
    print(f"data_bridge_20013d1.py OK | Eventos={len(pkg['event_indices'])} | Lock={pkg['mfc_channels']['MFC2']['lock_badge']}")