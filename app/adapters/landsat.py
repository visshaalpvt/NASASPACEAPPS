"""
NASA/USGS Landsat 8 & 9 Collection 2 Tier 1 Level-2 Adapter (GEE).
Resolves 30-meter field parcel NDVI and thermal canopy Land Surface Temperature.
Applies QA_PIXEL cloud and shadow bitmask filtering.
Reports the exact acquisition date of the newest clear image, NOT query end date.
"""
import time
import datetime as dt
from typing import Optional, Dict, Any, List

from app.adapters.base import SourceResult
from app.adapters.gee_auth import init_ee

COLLECTION_L8 = "LANDSAT/LC08/C02/T1_L2"
COLLECTION_L9 = "LANDSAT/LC09/C02/T1_L2"


def fetch_landsat(
    lat: float,
    lon: float,
    polygon_coords: Optional[List[List[float]]] = None,
    buffer_meters: float = 300.0,
    days_back: int = 45
) -> SourceResult:
    """
    Fetch high-resolution (30m) field NDVI and thermal LST from Landsat-8/9 over user polygon or 300m point buffer.
    """
    t0 = time.time()
    success, err_msg = init_ee()
    if not success:
        return SourceResult(
            source="Landsat 8 & 9 (30m GEE)",
            dataset_id=f"{COLLECTION_L8} / {COLLECTION_L9}",
            status="SKIPPED-no-credentials",
            latency_ms=int((time.time() - t0) * 1000),
            error=err_msg
        )

    try:
        import ee
        if polygon_coords and len(polygon_coords) >= 3:
            roi = ee.Geometry.Polygon(polygon_coords)
        else:
            roi = ee.Geometry.Point([lon, lat]).buffer(buffer_meters)

        end_date = dt.date.today()
        start_date = end_date - dt.timedelta(days=days_back)

        def mask_and_index(image):
            qa = image.select("QA_PIXEL")
            cloud_shadow = qa.bitwiseAnd(1 << 4).neq(0)
            clouds = qa.bitwiseAnd(1 << 3).neq(0)
            clear_mask = cloud_shadow.Or(clouds).Not()

            nir = image.select("SR_B5").multiply(0.0000275).add(-0.2)
            red = image.select("SR_B4").multiply(0.0000275).add(-0.2)
            ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")

            # Thermal band ST_B10: scale x 0.00341802 + 149.0 Kelvin -> - 273.15 -> °C
            lst_c = image.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST_C")

            return (image
                    .updateMask(clear_mask)
                    .addBands(ndvi)
                    .addBands(lst_c)
                    .addBands(ee.Image.constant(1).rename("clear_pixel").updateMask(clear_mask)))

        col8 = ee.ImageCollection(COLLECTION_L8).filterBounds(roi).filterDate(start_date.isoformat(), end_date.isoformat())
        col9 = ee.ImageCollection(COLLECTION_L9).filterBounds(roi).filterDate(start_date.isoformat(), end_date.isoformat())
        combined = col8.merge(col9).map(mask_and_index)

        size = combined.size().getInfo()
        if size == 0:
            return SourceResult(
                source="Landsat 8 & 9 (30m GEE)",
                dataset_id=f"{COLLECTION_L8} / {COLLECTION_L9}",
                status="unavailable",
                latency_ms=int((time.time() - t0) * 1000),
                error=f"No Landsat-8/9 scenes acquired over field within past {days_back} days"
            )

        # Get exact newest acquisition timestamp
        newest_img = combined.sort("system:time_start", False).first()
        newest_time = newest_img.get("system:time_start").getInfo()
        newest_date = dt.datetime.utcfromtimestamp(newest_time / 1000.0).strftime("%Y-%m-%d")

        median_img = combined.median()
        stats = median_img.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.count(), "", True),
            geometry=roi,
            scale=30
        ).getInfo()

        clear_pixels = int(stats.get("clear_pixel_count", 0) or 0)
        if clear_pixels < 3:
            return SourceResult(
                source="Landsat 8 & 9 (30m GEE)",
                dataset_id=f"{COLLECTION_L8} / {COLLECTION_L9}",
                status="unavailable",
                latency_ms=int((time.time() - t0) * 1000),
                error="Insufficient clear observations (<3 cloud-free 30m pixels)"
            )

        ndvi_val = stats.get("NDVI_mean")
        lst_val = stats.get("LST_C_mean")

        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="Landsat 8 & 9 (30m GEE)",
            dataset_id=f"{COLLECTION_L8} / {COLLECTION_L9}",
            status="live",
            observed_through=newest_date,
            freshness_note=f"Acquisition date of newest overpass: {newest_date} (16-day constellation revisit interval)",
            latency_ms=latency,
            n_obs=clear_pixels,
            units="NDVI: index (-1 to 1), Canopy LST: °C",
            data={
                "field_ndvi_30m": round(float(ndvi_val), 3) if ndvi_val is not None else None,
                "canopy_lst_c": round(float(lst_val), 1) if lst_val is not None else None,
                "clear_pixel_count": clear_pixels,
                "spatial_resolution_m": 30,
                "latest_scene_date": newest_date
            }
        )

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return SourceResult(
            source="Landsat 8 & 9 (30m GEE)",
            dataset_id=f"{COLLECTION_L8} / {COLLECTION_L9}",
            status="unavailable",
            latency_ms=latency,
            error=f"GEE Landsat execution exception: {str(e)}"
        )
