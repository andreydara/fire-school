#!/usr/bin/env python3

from __future__ import annotations

import calendar
import shutil
import zipfile
from pathlib import Path

import cdsapi
import numpy as np
import pandas as pd
import xarray as xr


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

OUTDIR = Path("data/weather")
TMPDIR = OUTDIR / "_tmp"

# Canonical Galičica AOI + generous ~0.1–0.2° buffer.
# CDS order: [North, West, South, East]
AREA = [41.60, 20.50, 40.60, 21.30]

HOURS = [f"{h:02d}:00" for h in range(24)]
DAYS = [f"{d:02d}" for d in range(1, 32)]
MONTHS = [f"{m:02d}" for m in range(1, 13)]

HOURLY_VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "total_precipitation",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
]

DAILY_MEAN_VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
]


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def ensure_credentials():
    path = Path.home() / ".cdsapirc"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist.\n"
            "Create it with your CDS URL and personal access token first."
        )
    print(f"✓ CDS credentials found: {path}")


def normalize_time(ds: xr.Dataset) -> xr.Dataset:
    """CDS files may call the time coordinate time or valid_time."""
    if "valid_time" in ds.coords and "time" not in ds.coords:
        ds = ds.rename({"valid_time": "time"})
    return ds


def open_download(path: Path) -> xr.Dataset:
    """
    Open either a NetCDF file or a ZIP containing one or more NetCDF files.
    Load into memory so temporary extracted files can safely disappear.
    """
    if zipfile.is_zipfile(path):
        extract_dir = path.with_suffix("")
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(path) as z:
            z.extractall(extract_dir)

        nc_files = sorted(extract_dir.rglob("*.nc"))
        if not nc_files:
            raise RuntimeError(f"No NetCDF files found inside {path}")

        datasets = [
            normalize_time(xr.open_dataset(p)).load()
            for p in nc_files
        ]

        ds = xr.merge(datasets, compat="override")
        for x in datasets:
            x.close()

        return ds

    return normalize_time(xr.open_dataset(path)).load()


def standardize_names(ds: xr.Dataset) -> xr.Dataset:
    """Normalize common CDS/ECMWF short variable names."""
    aliases = {
        "t2m": "t2m",
        "d2m": "d2m",
        "u10": "u10",
        "v10": "v10",
        "tp": "tp",
        "swvl1": "swvl1",
        "swvl2": "swvl2",
    }

    rename = {}
    for old, new in aliases.items():
        if old in ds and old != new:
            rename[old] = new

    if rename:
        ds = ds.rename(rename)

    return ds


def add_temperature_rh_wind(ds: xr.Dataset) -> xr.Dataset:
    """Add convenient derived variables."""
    ds = ds.copy()

    if "t2m" in ds:
        ds["t2m_c"] = ds["t2m"] - 273.15
        ds["t2m_c"].attrs = {
            "long_name": "2 m air temperature",
            "units": "degC",
        }

    if "d2m" in ds:
        ds["d2m_c"] = ds["d2m"] - 273.15
        ds["d2m_c"].attrs = {
            "long_name": "2 m dewpoint temperature",
            "units": "degC",
        }

    if "t2m_c" in ds and "d2m_c" in ds:
        # Magnus approximation.
        t = ds["t2m_c"]
        td = ds["d2m_c"]

        rh = 100.0 * np.exp(
            (17.625 * td / (243.04 + td))
            - (17.625 * t / (243.04 + t))
        )

        ds["rh_pct"] = rh.clip(0, 100)
        ds["rh_pct"].attrs = {
            "long_name": "Relative humidity derived from T and dewpoint",
            "units": "%",
        }

    if "u10" in ds and "v10" in ds:
        ds["wind_speed_ms"] = np.hypot(ds["u10"], ds["v10"])
        ds["wind_speed_ms"].attrs = {
            "long_name": "10 m wind speed",
            "units": "m s-1",
        }

    return ds


def save_compressed(ds: xr.Dataset, path: Path):
    encoding = {}

    for var in ds.data_vars:
        if np.issubdtype(ds[var].dtype, np.number):
            encoding[var] = {
                "zlib": True,
                "complevel": 4,
            }

    ds.to_netcdf(
        path,
        engine="netcdf4",
        encoding=encoding,
    )

    print(f"✓ Wrote {path} ({path.stat().st_size / 1024**2:.1f} MB)")


# ---------------------------------------------------------------------
# 1. HOURLY APRIL–SEPTEMBER 2024
# ---------------------------------------------------------------------

def download_hourly_2024(client: cdsapi.Client) -> xr.Dataset:
    print("\n=== ERA5-Land hourly April–September 2024 ===")

    datasets = []

    for month in range(4, 10):
        days_in_month = calendar.monthrange(2024, month)[1]

        request = {
            "variable": HOURLY_VARIABLES,
            "year": "2024",
            "month": f"{month:02d}",
            "day": [f"{d:02d}" for d in range(1, days_in_month + 1)],
            "time": HOURS,
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": AREA,
        }

        target = TMPDIR / f"era5land_hourly_2024_{month:02d}.nc"

        if not target.exists():
            print(f"Downloading 2024-{month:02d} ...")
            client.retrieve(
                "reanalysis-era5-land",
                request,
                str(target),
            )
        else:
            print(f"Already downloaded: {target}")

        ds = standardize_names(open_download(target))
        datasets.append(ds)

    ds = xr.concat(
        datasets,
        dim="time",
        data_vars="minimal",
        coords="minimal",
        compat="override",
    ).sortby("time")

    ds = add_temperature_rh_wind(ds)

    ds.attrs.update({
        "title": "ERA5-Land hourly weather for Galičica wildfire course",
        "period": "2024-04-01 to 2024-09-30",
        "source": "Copernicus Climate Data Store / ERA5-Land",
        "course": "GEO-ADAPT Wildfire Summer School 2026",
        "note": (
            "total_precipitation is an ERA5-Land accumulated variable; "
            "interpret accumulation timestamps according to ECMWF conventions."
        ),
    })

    return ds


# ---------------------------------------------------------------------
# 2. DAILY CLIMATOLOGY 1991–2025
# ---------------------------------------------------------------------

def year_blocks(start=1991, end=2025, width=5):
    y = start
    while y <= end:
        y2 = min(y + width - 1, end)
        yield list(range(y, y2 + 1))
        y = y2 + 1


def download_daily_means(client: cdsapi.Client) -> xr.Dataset:
    print("\n=== ERA5-Land daily means 1991–2025 ===")

    datasets = []

    for years in year_blocks():
        label = f"{years[0]}_{years[-1]}"
        target = TMPDIR / f"daily_mean_{label}.zip"

        request = {
            "variable": DAILY_MEAN_VARIABLES,
            "year": [str(y) for y in years],
            "month": MONTHS,
            "day": DAYS,
            "daily_statistic": "daily_mean",
            "time_zone": "utc+00:00",
            "frequency": "1_hourly",
            "area": AREA,
        }

        if not target.exists():
            print(f"Downloading daily means {label} ...")
            client.retrieve(
                "derived-era5-land-daily-statistics",
                request,
                str(target),
            )
        else:
            print(f"Already downloaded: {target}")

        datasets.append(
            standardize_names(open_download(target))
        )

    return xr.concat(
        datasets,
        dim="time",
        data_vars="minimal",
        coords="minimal",
        compat="override",
    ).sortby("time")


def download_daily_tmax(client: cdsapi.Client) -> xr.Dataset:
    print("\n=== ERA5-Land daily Tmax 1991–2025 ===")

    datasets = []

    for years in year_blocks():
        label = f"{years[0]}_{years[-1]}"
        target = TMPDIR / f"daily_tmax_{label}.zip"

        request = {
            "variable": ["2m_temperature"],
            "year": [str(y) for y in years],
            "month": MONTHS,
            "day": DAYS,
            "daily_statistic": "daily_maximum",
            "time_zone": "utc+00:00",
            "frequency": "1_hourly",
            "area": AREA,
        }

        if not target.exists():
            print(f"Downloading daily Tmax {label} ...")
            client.retrieve(
                "derived-era5-land-daily-statistics",
                request,
                str(target),
            )
        else:
            print(f"Already downloaded: {target}")

        ds = standardize_names(open_download(target))

        if "t2m" not in ds:
            raise RuntimeError(
                f"Could not find t2m in {target}: {list(ds.data_vars)}"
            )

        ds = ds[["t2m"]].rename({"t2m": "t2m_max"})
        datasets.append(ds)

    return xr.concat(
        datasets,
        dim="time",
        data_vars="minimal",
        coords="minimal",
        compat="override",
    ).sortby("time")


# ---------------------------------------------------------------------
# DAILY PRECIPITATION
#
# ERA5-Land accumulated variables are NOT offered by the derived daily
# statistics dataset. At 00 UTC, total_precipitation represents the
# 24-hour accumulation ending at that timestamp — i.e. the previous
# UTC day.
# ---------------------------------------------------------------------

def download_daily_precip(client: cdsapi.Client) -> xr.Dataset:
    print("\n=== ERA5-Land daily precipitation 1991–2025 ===")

    datasets = []

    # Need 1991-01-02 through 2026-01-01 timestamps so shifting back
    # one day produces complete 1991-01-01 through 2025-12-31 coverage.
    for year in range(1991, 2027):
        target = TMPDIR / f"daily_precip_00utc_{year}.nc"

        request = {
            "variable": ["total_precipitation"],
            "year": str(year),
            "month": MONTHS,
            "day": DAYS,
            "time": ["00:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": AREA,
        }

        if not target.exists():
            print(f"Downloading precipitation timestamps {year} ...")
            client.retrieve(
                "reanalysis-era5-land",
                request,
                str(target),
            )
        else:
            print(f"Already downloaded: {target}")

        ds = standardize_names(open_download(target))
        datasets.append(ds)

    ds = xr.concat(
        datasets,
        dim="time",
        data_vars="minimal",
        coords="minimal",
        compat="override",
    ).sortby("time")

    if "tp" not in ds:
        raise RuntimeError(
            f"Could not find total precipitation variable: {list(ds.data_vars)}"
        )

    # Timestamp 00 UTC corresponds to precipitation accumulated
    # during the preceding UTC day.
    ds = ds[["tp"]]
    ds = ds.assign_coords(
        time=ds.time - np.timedelta64(1, "D")
    )

    ds = ds.sel(
        time=slice("1991-01-01", "2025-12-31")
    )

    ds["precip_mm"] = ds["tp"] * 1000.0
    ds["precip_mm"].attrs = {
        "long_name": "Daily total precipitation",
        "units": "mm day-1",
        "day_definition": "00:00–24:00 UTC",
    }

    return ds[["precip_mm"]]


def build_daily_dataset(client: cdsapi.Client) -> xr.Dataset:
    means = download_daily_means(client)
    tmax = download_daily_tmax(client)
    precip = download_daily_precip(client)

    daily = xr.merge(
        [means, tmax, precip],
        compat="override",
        join="inner",
    )

    daily = add_temperature_rh_wind(daily)

    if "t2m_max" in daily:
        daily["t2m_max_c"] = daily["t2m_max"] - 273.15
        daily["t2m_max_c"].attrs = {
            "long_name": "Daily maximum 2 m air temperature",
            "units": "degC",
        }

    daily.attrs.update({
        "title": "ERA5-Land daily weather climatology for Galičica",
        "period": "1991-01-01 to 2025-12-31",
        "daily_time_zone": "UTC",
        "source": "Copernicus Climate Data Store / ERA5-Land",
        "course": "GEO-ADAPT Wildfire Summer School 2026",
        "note": (
            "RH is calculated from daily-mean temperature and "
            "daily-mean dewpoint and is therefore an approximate daily-mean RH. "
            "Use the hourly 2024 file for event-time/noon RH."
        ),
    })

    return daily


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    ensure_credentials()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    TMPDIR.mkdir(parents=True, exist_ok=True)

    client = cdsapi.Client()

    hourly = download_hourly_2024(client)
    save_compressed(
        hourly,
        OUTDIR / "era5_land_galicica_hourly_2024.nc",
    )

    daily = build_daily_dataset(client)
    save_compressed(
        daily,
        OUTDIR / "era5_land_galicica_daily_1991_2025.nc",
    )

    print("\n=== VALIDATION ===")
    print(hourly)
    print()
    print(daily)

    print("\nFinal files:")
    for path in sorted(OUTDIR.glob("*.nc")):
        print(
            f"  {path} "
            f"({path.stat().st_size / 1024**2:.1f} MB)"
        )

    print(
        "\nTemporary CDS downloads remain under "
        f"{TMPDIR} so interrupted runs can resume."
    )
    print(
        "After checking the final NetCDF files, you can delete _tmp manually."
    )


if __name__ == "__main__":
    main()