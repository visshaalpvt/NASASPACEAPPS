"""
KisanRadar Data Adapters Package.
"""
from app.adapters.base import SourceResult
from app.adapters.power import fetch_power
from app.adapters.forecast import fetch_forecast
from app.adapters.gibs import validate_gibs_layers
from app.adapters.gee_auth import init_ee
from app.adapters.smap import fetch_smap
from app.adapters.gpm import fetch_gpm_imerg
from app.adapters.modis import fetch_modis
from app.adapters.landsat import fetch_landsat
from app.adapters.grace import fetch_grace
from app.adapters.imd import fetch_imd_gridded
from app.adapters.icrisat import fetch_icrisat_records

__all__ = [
    "SourceResult",
    "fetch_power",
    "fetch_forecast",
    "validate_gibs_layers",
    "init_ee",
    "fetch_smap",
    "fetch_gpm_imerg",
    "fetch_modis",
    "fetch_landsat",
    "fetch_grace",
    "fetch_imd_gridded",
    "fetch_icrisat_records",
]

