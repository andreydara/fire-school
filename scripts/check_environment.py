#!/usr/bin/env python3
"""Fast local/CDSE environment check for the student course setup."""

from __future__ import annotations

import importlib
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE_IMPORTS = {
    "numpy": "NumPy",
    "pandas": "Pandas",
    "matplotlib": "Matplotlib",
    "geopandas": "GeoPandas",
    "shapely": "Shapely",
    "folium": "Folium",
    "xarray": "xarray",
    "netCDF4": "netCDF4",
    "ee": "Earth Engine Python API",
    "requests": "Requests",
    "IPython": "IPython",
    "ipykernel": "ipykernel",
}

OPTIONAL_IMPORTS = {
    "pystac_client": "pystac-client",
    "openeo": "openEO client",
}

REQUIRED_FILES = [
    Path("data/aoi/galicica_aoi.geojson"),
    Path("data/effis/Galicica.gpkg"),
    Path("data/weather/era5_land_galicica_hourly_2024.nc"),
    Path("data/weather/era5_land_galicica_fireseason_1991_latest.nc"),
]

errors: list[str] = []

print("GEO-ADAPT course environment check")
print("=" * 72)
print("Python:", sys.version.split()[0])
print("Executable:", sys.executable)
print("OS:", platform.platform())

if sys.version_info[:2] != (3, 11):
    errors.append(
        f"Python 3.11 is required; this interpreter is {sys.version.split()[0]}."
    )
else:
    print("✓ Python 3.11")

for import_name, display_name in CORE_IMPORTS.items():
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "version unavailable")
        print(f"✓ {display_name}: {version}")
    except Exception as exc:
        errors.append(f"{display_name}: {type(exc).__name__}: {exc}")
        print(f"✗ {display_name}: {exc}")

for import_name, display_name in OPTIONAL_IMPORTS.items():
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "version unavailable")
        print(f"! Optional {display_name}: {version}")
    except Exception:
        print(f"! Optional {display_name}: not installed")

print("\nCourse files")
for relative in REQUIRED_FILES:
    path = ROOT / relative
    if path.exists() and path.stat().st_size > 0:
        print(f"✓ {relative} ({path.stat().st_size / 1024**2:.1f} MB)")
    else:
        errors.append(f"Missing course file: {relative}")
        print(f"✗ {relative}")

# Check the two NetCDF files using the backend standardized for the course.
try:
    from netCDF4 import Dataset

    for relative in REQUIRED_FILES[-2:]:
        path = ROOT / relative
        with Dataset(path) as ds:
            if "time" not in ds.dimensions or len(ds.dimensions["time"]) == 0:
                raise RuntimeError(f"{relative} has no usable time dimension")
            print(
                f"✓ NetCDF4 read: {relative} "
                f"({len(ds.dimensions['time'])} time steps)"
            )
except Exception as exc:
    errors.append(f"NetCDF4 course-data check: {type(exc).__name__}: {exc}")
    print(f"✗ NetCDF4 course-data check: {exc}")

gee_project = os.environ.get("GEE_PROJECT_ID", "").strip()
if gee_project:
    print(f"✓ GEE_PROJECT_ID configured: {gee_project}")
else:
    print(
        "! GEE_PROJECT_ID is not set. This is fine if Earth Engine can infer "
        "your project; otherwise set it before running the EE notebooks."
    )

print("\n" + "=" * 72)
if errors:
    print("ENVIRONMENT CHECK FAILED")
    for error in errors:
        print("  ✗", error)
    raise SystemExit(1)

print("ENVIRONMENT CHECK PASSED")
