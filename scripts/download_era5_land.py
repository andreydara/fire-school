#!/usr/bin/env python3

from __future__ import annotations

import argparse
import calendar
from datetime import date, timedelta
from pathlib import Path

import cdsapi
import numpy as np
import xarray as xr


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

OUTDIR = Path("data/weather")
TMPDIR = OUTDIR / "_tmp"

# Canonical Galičica AOI + generous ~0.1–0.2° buffer.
# CDS order: [North, West, South, East]
AREA = [41.60, 20.50, 40.60, 21.30]

# Detailed historical event dataset.
HOURLY_YEAR = 2024
HOURLY_START_MONTH = 4
HOURLY_END_MONTH = 10  # April–October, inclusive
HOURLY_START = f"{HOURLY_YEAR}-04-01"
HOURLY_END = f"{HOURLY_YEAR}-10-31"
HOURLY_OUT = OUTDIR / "era5_land_galicica_hourly_2024.nc"

# Fire-season climatology/current-season dataset.
CLIM_START_YEAR = 1991
CLIM_BASELINE_START_YEAR = 1991
CLIM_BASELINE_END_YEAR = 2020
FIRESEASON_START_MONTH = 4
FIRESEASON_END_MONTH = 10  # April–October, inclusive

# ERA5-Land is normally available close to real time. Use a conservative
# lag so the script does not request the newest, potentially unavailable day.
# We subtract one additional day below because the UTC daily precipitation
# for day D is stored at 00 UTC on day D+1.
CDS_LAG_DAYS = 7

FIRESEASON_OUT = OUTDIR / "era5_land_galicica_fireseason_1991_latest.nc"

HOURS = [f"{h:02d}:00" for h in range(24)]
DAYS = [f"{d:02d}" for d in range(1, 32)]

HOURLY_VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "total_precipitation",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
]

# Same physical variables for the compact fire-season product. We retrieve
# only 00 and 12 UTC rather than all 24 hours.
FIRESEASON_VARIABLES = HOURLY_VARIABLES.copy()
FIRESEASON_TIMES = ["00:00", "12:00"]

RAW_SHORT_NAMES = ["t2m", "d2m", "u10", "v10", "tp", "swvl1", "swvl2"]


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def ensure_credentials() -> None:
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
    """Open a NetCDF download, load it into memory, and close the file."""
    with xr.open_dataset(path) as src:
        ds = normalize_time(src).load()
    return ds


def standardize_names(ds: xr.Dataset) -> xr.Dataset:
    """
    Normalize common CDS/ECMWF variable names.

    Current ERA5-Land NetCDF downloads normally already use the short names
    below, but keeping aliases here makes the script tolerant of long names.
    """
    aliases = {
        "2m_temperature": "t2m",
        "2m_dewpoint_temperature": "d2m",
        "10m_u_component_of_wind": "u10",
        "10m_v_component_of_wind": "v10",
        "total_precipitation": "tp",
        "volumetric_soil_water_layer_1": "swvl1",
        "volumetric_soil_water_layer_2": "swvl2",
    }

    rename = {old: new for old, new in aliases.items() if old in ds and new not in ds}
    if rename:
        ds = ds.rename(rename)

    return ds


def add_temperature_rh_wind(ds: xr.Dataset) -> xr.Dataset:
    """Add convenient derived meteorological variables."""
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


def add_hourly_precip_increment(ds: xr.Dataset) -> xr.Dataset:
    """
    Add approximate hourly precipitation increments in mm.

    In the standard ERA5-Land hourly archive, total precipitation is an
    accumulation from 00 UTC to the valid forecast step. At 00 UTC the value
    represents the 24 h accumulation during the previous UTC day. Therefore:
      * at 01 UTC, the accumulated value itself is the 00–01 UTC increment;
      * at 02–23 UTC, differences give the hourly increment;
      * at 00 UTC, the difference from the previous 23 UTC value gives the
        final hour of the previous day.

    The very first timestamp cannot be differenced and remains NaN.
    """
    if "tp" not in ds or "time" not in ds.coords:
        return ds

    ds = ds.copy()
    accum_mm = ds["tp"] * 1000.0
    diff_mm = accum_mm.diff("time", label="upper").reindex(time=ds.time)
    hour = ds.time.dt.hour

    hourly_mm = xr.where(hour == 1, accum_mm, diff_mm)
    hourly_mm = hourly_mm.where(hourly_mm >= -1e-9).clip(min=0)

    ds["precip_hourly_mm"] = hourly_mm
    ds["precip_hourly_mm"].attrs = {
        "long_name": "Hourly precipitation increment derived from ERA5-Land accumulation",
        "units": "mm h-1",
    }
    return ds


def save_compressed(ds: xr.Dataset, path: Path) -> None:
    """Write atomically as compressed NetCDF4."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")

    encoding = {}
    for var in ds.data_vars:
        if np.issubdtype(ds[var].dtype, np.number):
            encoding[var] = {"zlib": True, "complevel": 4}

    ds.to_netcdf(tmp, engine="netcdf4", encoding=encoding)
    tmp.replace(path)
    print(f"✓ Wrote {path} ({path.stat().st_size / 1024**2:.1f} MB)")


def dataset_time_bounds(path: Path) -> tuple[np.datetime64, np.datetime64] | None:
    if not path.exists():
        return None
    try:
        with xr.open_dataset(path) as ds:
            ds = normalize_time(ds)
            if "time" not in ds.coords or ds.time.size == 0:
                return None
            return np.datetime64(ds.time.min().values), np.datetime64(ds.time.max().values)
    except Exception:
        return None


def covers(path: Path, start: str, end: str) -> bool:
    bounds = dataset_time_bounds(path)
    if bounds is None:
        return False
    lo, hi = bounds
    return lo <= np.datetime64(start) and hi >= np.datetime64(end)


def require_raw_variables(ds: xr.Dataset, context: str) -> xr.Dataset:
    missing = [v for v in RAW_SHORT_NAMES if v not in ds]
    if missing:
        raise RuntimeError(
            f"Missing ERA5-Land variables in {context}: {missing}. "
            f"Available: {list(ds.data_vars)}"
        )
    return ds


def year_blocks(start: int, end: int, width: int = 5):
    y = start
    while y <= end:
        y2 = min(y + width - 1, end)
        yield list(range(y, y2 + 1))
        y = y2 + 1


def fireseason_latest_target(today: date | None = None) -> date:
    """
    Latest day to include in the daily fire-season dataset.

    Use a conservative CDS lag and reserve one extra day because precipitation
    for day D is read from ERA5-Land at 00 UTC on D+1.
    """
    today = today or date.today()
    candidate = today - timedelta(days=CDS_LAG_DAYS + 1)

    season_start = date(candidate.year, FIRESEASON_START_MONTH, 1)
    season_end = date(candidate.year, FIRESEASON_END_MONTH, 31)

    if candidate < season_start:
        return date(candidate.year - 1, FIRESEASON_END_MONTH, 31)
    return min(candidate, season_end)


def make_cds_client() -> cdsapi.Client:
    # Avoid cdsapi's extremely long default retry cycle for genuine network/DNS
    # problems while still tolerating brief service hiccups.
    return cdsapi.Client(retry_max=8, sleep_max=30, timeout=120)


# ---------------------------------------------------------------------
# 1. HOURLY APRIL–OCTOBER 2024
# ---------------------------------------------------------------------

def download_hourly_2024(client: cdsapi.Client, force: bool = False) -> xr.Dataset:
    print("\n=== ERA5-Land hourly April–October 2024 ===")

    if not force and covers(HOURLY_OUT, HOURLY_START, f"{HOURLY_END}T23:00"):
        print(f"✓ Complete hourly file already exists: {HOURLY_OUT}")
        return open_download(HOURLY_OUT)

    datasets: list[xr.Dataset] = []
    months_present: set[int] = set()

    # Reuse an existing partial final file (e.g. the already-downloaded
    # April–September version) instead of redownloading those months.
    if HOURLY_OUT.exists() and not force:
        existing = standardize_names(open_download(HOURLY_OUT))
        existing = require_raw_variables(existing, str(HOURLY_OUT))
        existing = existing[RAW_SHORT_NAMES]
        wanted = existing.sel(time=slice(HOURLY_START, f"{HOURLY_END}T23:59:59"))
        if wanted.time.size:
            datasets.append(wanted)
            months_present = set(int(m) for m in np.unique(wanted.time.dt.month.values))
            print(
                "Reusing existing hourly file for months:",
                ", ".join(f"{m:02d}" for m in sorted(months_present)),
            )

    for month in range(HOURLY_START_MONTH, HOURLY_END_MONTH + 1):
        if month in months_present and not force:
            continue

        days_in_month = calendar.monthrange(HOURLY_YEAR, month)[1]
        target = TMPDIR / f"era5land_hourly_{HOURLY_YEAR}_{month:02d}.nc"

        request = {
            "variable": HOURLY_VARIABLES,
            "year": str(HOURLY_YEAR),
            "month": f"{month:02d}",
            "day": [f"{d:02d}" for d in range(1, days_in_month + 1)],
            "time": HOURS,
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": AREA,
        }

        if target.exists() and not force:
            print(f"Already downloaded monthly chunk: {target}")
        else:
            print(f"Downloading {HOURLY_YEAR}-{month:02d} ...")
            client.retrieve("reanalysis-era5-land", request, str(target))

        ds = standardize_names(open_download(target))
        ds = require_raw_variables(ds, str(target))[RAW_SHORT_NAMES]
        datasets.append(ds)

    if not datasets:
        raise RuntimeError("No hourly ERA5-Land data were available to combine.")

    ds = xr.concat(
        datasets,
        dim="time",
        data_vars="minimal",
        coords="minimal",
        compat="override",
        join="outer",
    ).sortby("time")

    # Remove any duplicated timestamps introduced when reusing a partial file.
    _, unique_idx = np.unique(ds.time.values, return_index=True)
    ds = ds.isel(time=np.sort(unique_idx))
    ds = ds.sel(time=slice(HOURLY_START, f"{HOURLY_END}T23:59:59"))

    ds = add_temperature_rh_wind(ds)
    ds = add_hourly_precip_increment(ds)

    ds.attrs.update({
        "title": "ERA5-Land hourly weather for Galičica wildfire course",
        "period": "2024-04-01 to 2024-10-31",
        "source": "Copernicus Climate Data Store / ERA5-Land",
        "course": "GEO-ADAPT Wildfire Summer School 2026",
        "note": (
            "Includes raw ERA5-Land total precipitation accumulation plus a "
            "derived precip_hourly_mm increment. ERA5-Land accumulation "
            "conventions differ from ERA5; see ECMWF documentation."
        ),
    })

    return ds


# ---------------------------------------------------------------------
# 2. FIRE-SEASON 12 UTC WEATHER + PREVIOUS-24-H PRECIPITATION
#    1991–LATEST AVAILABLE (INCLUDING 2026)
# ---------------------------------------------------------------------

def historical_fireseason_raw(
    client: cdsapi.Client,
    start_year: int,
    end_year: int,
    force: bool = False,
) -> list[xr.Dataset]:
    """Download complete past years in restartable five-year blocks."""
    datasets: list[xr.Dataset] = []
    if end_year < start_year:
        return datasets

    # November is retrieved because 00 UTC on 1 November contains the
    # 24-hour accumulation for 31 October. Extra November data are discarded.
    months = [f"{m:02d}" for m in range(FIRESEASON_START_MONTH, 12)]

    for years in year_blocks(start_year, end_year, width=5):
        label = f"{years[0]}_{years[-1]}"
        target = TMPDIR / f"fireseason_raw_{label}.nc"

        request = {
            "variable": FIRESEASON_VARIABLES,
            "year": [str(y) for y in years],
            "month": months,
            "day": DAYS,
            "time": FIRESEASON_TIMES,
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": AREA,
        }

        if target.exists() and not force:
            print(f"Already downloaded historical block: {target}")
        else:
            print(f"Downloading fire-season raw data {label} ...")
            client.retrieve("reanalysis-era5-land", request, str(target))

        ds = standardize_names(open_download(target))
        datasets.append(require_raw_variables(ds, str(target))[RAW_SHORT_NAMES])

    return datasets


def current_fireseason_raw(
    client: cdsapi.Client,
    target_date: date,
    force: bool = False,
) -> list[xr.Dataset]:
    """
    Download the current year's season only through target_date + 1 day.

    The extra raw day supplies 00 UTC precipitation for target_date.
    """
    year = target_date.year
    season_start = date(year, FIRESEASON_START_MONTH, 1)
    if target_date < season_start:
        return []

    raw_end = target_date + timedelta(days=1)
    datasets: list[xr.Dataset] = []

    # Full past months in the current year can be requested together.
    full_month_end = raw_end.month - 1
    if full_month_end >= FIRESEASON_START_MONTH:
        months = [f"{m:02d}" for m in range(FIRESEASON_START_MONTH, full_month_end + 1)]
        target = TMPDIR / f"fireseason_raw_{year}_fullmonths_through_{full_month_end:02d}.nc"
        request = {
            "variable": FIRESEASON_VARIABLES,
            "year": str(year),
            "month": months,
            "day": DAYS,
            "time": FIRESEASON_TIMES,
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": AREA,
        }
        if target.exists() and not force:
            print(f"Already downloaded current-year full months: {target}")
        else:
            print(f"Downloading {year} full months through {full_month_end:02d} ...")
            client.retrieve("reanalysis-era5-land", request, str(target))
        ds = standardize_names(open_download(target))
        datasets.append(require_raw_variables(ds, str(target))[RAW_SHORT_NAMES])

    # Partial final raw month. If raw_end is 1 November, this deliberately
    # downloads only 1 November, which is enough for 31 October precipitation.
    partial_month = raw_end.month
    partial_days = [f"{d:02d}" for d in range(1, raw_end.day + 1)]
    target = TMPDIR / f"fireseason_raw_{year}_{partial_month:02d}_through_{raw_end.day:02d}.nc"
    request = {
        "variable": FIRESEASON_VARIABLES,
        "year": str(year),
        "month": f"{partial_month:02d}",
        "day": partial_days,
        "time": FIRESEASON_TIMES,
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": AREA,
    }
    if target.exists() and not force:
        print(f"Already downloaded current-year partial month: {target}")
    else:
        print(f"Downloading {year}-{partial_month:02d}-01 through {raw_end.isoformat()} ...")
        client.retrieve("reanalysis-era5-land", request, str(target))
    ds = standardize_names(open_download(target))
    datasets.append(require_raw_variables(ds, str(target))[RAW_SHORT_NAMES])

    return datasets


def build_fireseason_dataset(
    client: cdsapi.Client,
    force: bool = False,
    latest_date: date | None = None,
) -> xr.Dataset:
    target_date = latest_date or fireseason_latest_target()
    print(
        "\n=== ERA5-Land fire-season climatology/current season ===\n"
        f"Target coverage: {CLIM_START_YEAR}-04-01 through {target_date.isoformat()}\n"
        f"Climatological baseline: {CLIM_BASELINE_START_YEAR}–{CLIM_BASELINE_END_YEAR}"
    )

    # If the final file already reaches the expected target date, no CDS work.
    if not force and covers(
        FIRESEASON_OUT,
        f"{CLIM_START_YEAR}-04-01",
        target_date.isoformat(),
    ):
        print(f"✓ Complete fire-season file already exists: {FIRESEASON_OUT}")
        return open_download(FIRESEASON_OUT)

    raw_sets: list[xr.Dataset] = []

    # Complete years before the current target year.
    raw_sets.extend(
        historical_fireseason_raw(
            client,
            CLIM_START_YEAR,
            target_date.year - 1,
            force=force,
        )
    )

    # Current/latest year, possibly partial (e.g. 2026 through August).
    raw_sets.extend(current_fireseason_raw(client, target_date, force=force))

    if not raw_sets:
        raise RuntimeError("No fire-season ERA5-Land data were downloaded.")

    raw = xr.concat(
        raw_sets,
        dim="time",
        data_vars="minimal",
        coords="minimal",
        compat="override",
        join="outer",
    ).sortby("time")

    _, unique_idx = np.unique(raw.time.values, return_index=True)
    raw = raw.isel(time=np.sort(unique_idx))

    # Standardized daily weather snapshot at 12 UTC.
    noon = raw.where(raw.time.dt.hour == 12, drop=True)
    noon = noon[["t2m", "d2m", "u10", "v10", "swvl1", "swvl2"]]
    noon = noon.assign_coords(time=noon.time.dt.floor("D"))
    noon = add_temperature_rh_wind(noon)

    # Previous 24 h UTC precipitation: in ERA5-Land, 00 UTC stores the 24 h
    # accumulation ending at 00 UTC, i.e. precipitation during the previous day.
    precip = raw[["tp"]].where(raw.time.dt.hour == 0, drop=True)
    precip = precip.assign_coords(time=precip.time - np.timedelta64(1, "D"))
    precip["precip_24h_mm"] = precip["tp"] * 1000.0
    precip["precip_24h_mm"].attrs = {
        "long_name": "Previous 24-hour total precipitation",
        "units": "mm day-1",
        "day_definition": "00:00–24:00 UTC",
    }
    precip = precip[["precip_24h_mm"]]

    daily = xr.merge([noon, precip], compat="override", join="inner").sortby("time")

    # Retain April–October only, including the latest available 2026 date.
    daily = daily.sel(
        time=slice(f"{CLIM_START_YEAR}-04-01", target_date.isoformat())
    )
    daily = daily.where(
        (daily.time.dt.month >= FIRESEASON_START_MONTH)
        & (daily.time.dt.month <= FIRESEASON_END_MONTH),
        drop=True,
    )

    daily.attrs.update({
        "title": "ERA5-Land Galičica fire-season weather climatology and current season",
        "period": f"April–October, {CLIM_START_YEAR}–{target_date.year}; latest date {target_date.isoformat()}",
        "climatological_baseline": f"{CLIM_BASELINE_START_YEAR}-{CLIM_BASELINE_END_YEAR}",
        "weather_time": "12:00 UTC",
        "precipitation": "Previous 24 h UTC accumulation",
        "source": "Copernicus Climate Data Store / ERA5-Land",
        "course": "GEO-ADAPT Wildfire Summer School 2026",
        "note": (
            "12 UTC is used as a consistent fire-weather snapshot and is not "
            "claimed to reproduce operational EFFIS/FWI exactly. Relative "
            "humidity is derived from 2 m temperature and dewpoint."
        ),
    })

    return daily


# ---------------------------------------------------------------------
# VALIDATION / CLI
# ---------------------------------------------------------------------

def print_validation(label: str, ds: xr.Dataset) -> None:
    print(f"\n--- {label} ---")
    print("time:", str(ds.time.min().values), "→", str(ds.time.max().values))
    print("dimensions:", dict(ds.sizes))
    print("variables:", ", ".join(ds.data_vars))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download compact ERA5-Land datasets for the GEO-ADAPT wildfire course."
    )
    p.add_argument(
        "--skip-hourly",
        action="store_true",
        help="Do not build/update the detailed April–October 2024 hourly file.",
    )
    p.add_argument(
        "--skip-fireseason",
        action="store_true",
        help="Do not build/update the 1991–latest fire-season file.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Redownload cached chunks and rebuild outputs even if they already exist.",
    )
    p.add_argument(
        "--latest-date",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help=(
            "Override the automatically chosen latest fire-season date. "
            "Useful if CDS availability temporarily lags the conservative default."
        ),
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ensure_credentials()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    TMPDIR.mkdir(parents=True, exist_ok=True)

    client = make_cds_client()
    results: list[tuple[str, xr.Dataset]] = []

    if not args.skip_hourly:
        hourly = download_hourly_2024(client, force=args.force)
        save_compressed(hourly, HOURLY_OUT)
        results.append(("Hourly 2024", hourly))

    if not args.skip_fireseason:
        fireseason = build_fireseason_dataset(
            client,
            force=args.force,
            latest_date=args.latest_date,
        )
        save_compressed(fireseason, FIRESEASON_OUT)
        results.append(("Fire-season 1991–latest", fireseason))

    print("\n=== VALIDATION ===")
    for label, ds in results:
        print_validation(label, ds)

    print("\nFinal files:")
    for path in sorted(OUTDIR.glob("*.nc")):
        print(f"  {path} ({path.stat().st_size / 1024**2:.1f} MB)")

    print(
        "\nTemporary CDS chunks remain under "
        f"{TMPDIR} so interrupted runs can resume."
    )
    print(
        "After the final NetCDF files are validated and no further updates are "
        "needed, _tmp can be deleted manually."
    )


if __name__ == "__main__":
    main()
