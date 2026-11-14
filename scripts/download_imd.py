"""
Script to download official IMD Pune daily gridded rainfall (0.25°) and temperature (1.0°) data.
"""
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "imd")

def download_imd():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"IMD data directory initialized at: {DATA_DIR}")
    print("To download official IMD gridded datasets:")
    print("1. Install imdlib: pip install imdlib")
    print("2. Run automated download via imdlib for target years:")
    print("   import imdlib as imd")
    print("   data = imd.get_data('rain', 2020, 2024, fn_format='yearwise', file_dir=DATA_DIR)")
    print("Refer to IMD Pune Data Supply Portal (imdpune.gov.in) for long-term historical archives.")

if __name__ == "__main__":
    download_imd()

