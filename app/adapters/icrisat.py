"""
ICRISAT District Level Database (DLD) Ingestion & Verification Adapter.
Inspects data/icrisat/ for empirical district crop statistics (area, production, yield).
Fails with a clear message if files are missing. Never fabricates yield rows.
"""
import os
import time
import pandas as pd
from typing import Optional, Dict, Any

from app.adapters.base import SourceResult

DATASET_ID = "ICRISAT_DLD_DISTRICT_YIELDS_V1"
ICRISAT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "icrisat")


def fetch_icrisat_records() -> SourceResult:
    """
    Verify and read ICRISAT DLD CSV datasets if present.
    """
    t0 = time.time()
    if not os.path.exists(ICRISAT_DATA_DIR):
        os.makedirs(ICRISAT_DATA_DIR, exist_ok=True)

    csv_files = [f for f in os.listdir(ICRISAT_DATA_DIR) if f.endswith(".csv")]
    if not csv_files:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="ICRISAT District Level Database",
            dataset_id=DATASET_ID,
            status="SKIPPED-no-data",
            latency_ms=latency,
            error=f"No CSV files found in {ICRISAT_DATA_DIR}. Place ICRISAT DLD CSVs (crop yield, area, production) to enable trained ML modeling."
        )

    # Read and inspect real schema
    total_rows = 0
    schemas = {}
    for f in csv_files:
        path = os.path.join(ICRISAT_DATA_DIR, f)
        df = pd.read_csv(path, nrows=5)
        schemas[f] = list(df.columns)
        # count rows
        with open(path, 'rb') as fp:
            total_rows += sum(1 for _ in fp) - 1

    latency = int((time.time() - t0) * 1000)
    return SourceResult(
        source="ICRISAT District Level Database",
        dataset_id=DATASET_ID,
        status="live",
        observed_through=None,
        latency_ms=latency,
        n_obs=total_rows,
        units="Yield: kg/ha, Area: ha, Production: tonnes",
        data={"files": csv_files, "total_rows": total_rows, "schemas": schemas}
    )

