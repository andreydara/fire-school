#!/usr/bin/env python3
"""Build or verify compact local fallback/reference tables.

The outputs mirror the local-data logic used in Practicals 02 and 05.
They are intentionally small and committed to the repository so the class can
continue when a live EO backend is unavailable.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "fallback" / "tables"

AOI_PATH = ROOT / "data" / "aoi" / "galicica_aoi.geojson"
EFFIS_PATH = ROOT / "data" / "effis" / "Galicica.gpkg"
FIRESEASON_PATH = (
    ROOT / "data" / "weather" / "era5_land_galicica_fireseason_1991_latest.nc"
)

TARGET_EFFIS_ID = "240575"
BASELINE_START = 1991
BASELINE_END = 2020

FILES = {
    "effis_annual_summary.csv",
    "weather_fire_start_reference.csv",
    "weather_compound_top_2024.csv",
    "weather_recent_2026.csv",
}


def spatial_mean(ds: xr.Dataset, geometry) -> xr.Dataset:
    lat_name = "latitude" if "latitude" in ds.coords else "lat"
    lon_name = "longitude" if "longitude" in ds.coords else "lon"

    lats = ds[lat_name].values
    lons = ds[lon_name].values

    mask = np.array(
        [
            [geometry.covers(Point(float(lon), float(lat))) for lon in lons]
            for lat in lats
        ]
    )

    weights = np.cos(np.deg2rad(ds[lat_name]))
    return ds.where(
        xr.DataArray(
            mask,
            coords={lat_name: lats, lon_name: lons},
            dims=(lat_name, lon_name),
        )
    ).weighted(weights).mean((lat_name, lon_name))


def empirical_percentile(value: float, reference: pd.Series) -> float:
    reference = pd.Series(reference).dropna()
    if reference.empty or pd.isna(value):
        return np.nan
    return 100.0 * (reference <= value).mean()


def build_tables() -> dict[str, pd.DataFrame]:
    aoi = gpd.read_file(AOI_PATH).to_crs("EPSG:4326").geometry.iloc[0]

    effis = gpd.read_file(EFFIS_PATH).to_crs("EPSG:4326").copy()
    effis["FIREDATE"] = pd.to_datetime(effis["FIREDATE"], errors="coerce")
    effis["AREA_HA"] = pd.to_numeric(effis["AREA_HA"], errors="coerce")

    year_min = int(effis["FIREDATE"].dt.year.min())
    year_max = int(effis["FIREDATE"].dt.year.max())

    annual = (
        effis.assign(year=effis["FIREDATE"].dt.year)
        .groupby("year")
        .agg(
            fire_polygons=("id", "size"),
            mapped_area_ha=("AREA_HA", "sum"),
        )
        .reindex(range(year_min, year_max + 1), fill_value=0)
        .reset_index()
    )
    annual["mapped_area_ha"] = annual["mapped_area_ha"].round(3)

    target = effis[effis["id"].astype(str) == TARGET_EFFIS_ID]
    if target.empty:
        raise RuntimeError(f"EFFIS target {TARGET_EFFIS_ID} not found.")

    fire_start = pd.Timestamp(target.iloc[0]["FIREDATE"]).normalize()

    with xr.open_dataset(FIRESEASON_PATH, engine="netcdf4") as source:
        fireseason = source.load()

    fireseason_mean = spatial_mean(fireseason, aoi)
    fire_df = fireseason_mean.to_dataframe().reset_index()
    fire_df["time"] = pd.to_datetime(fire_df["time"])
    fire_df["year"] = fire_df["time"].dt.year
    fire_df["month"] = fire_df["time"].dt.month
    fire_df = fire_df.sort_values("time").copy()

    fire_df["precip_30d_mm"] = (
        fire_df.groupby("year")["precip_24h_mm"]
        .transform(lambda series: series.rolling(30, min_periods=25).sum())
    )

    baseline = fire_df[
        fire_df["year"].between(BASELINE_START, BASELINE_END)
    ].copy()
    baseline_aug = baseline[baseline["month"] == 8].copy()

    obs_2024 = fire_df[fire_df["year"] == 2024].copy()
    fire_row = obs_2024.loc[obs_2024["time"] == fire_start]
    if fire_row.empty:
        raise RuntimeError(f"No 2024 weather row for EFFIS date {fire_start.date()}.")
    row = fire_row.iloc[0]

    metric_specs = [
        (
            "12 UTC temperature",
            "t2m_c",
            "degC",
            "high = more fire-conducive",
        ),
        (
            "12 UTC relative humidity",
            "rh_pct",
            "%",
            "low = more fire-conducive",
        ),
        (
            "12 UTC wind speed",
            "wind_speed_ms",
            "m/s",
            "high = more fire-conducive",
        ),
        (
            "Shallow soil moisture",
            "swvl1",
            "m3/m3",
            "low = drier surface",
        ),
        (
            "Previous 30-day precipitation",
            "precip_30d_mm",
            "mm",
            "low = drier antecedent period",
        ),
    ]

    fire_start_rows = []
    for label, variable, unit, interpretation in metric_specs:
        fire_start_rows.append(
            {
                "date": fire_start.date().isoformat(),
                "metric": label,
                "value": round(float(row[variable]), 3),
                "unit": unit,
                "august_1991_2020_percentile": round(
                    empirical_percentile(row[variable], baseline_aug[variable]),
                    1,
                ),
                "interpretation": interpretation,
            }
        )
    fire_start_reference = pd.DataFrame(fire_start_rows)

    thresholds = (
        baseline.groupby("month")
        .agg(
            t90=("t2m_c", lambda s: s.quantile(0.90)),
            rh10=("rh_pct", lambda s: s.quantile(0.10)),
            wind90=("wind_speed_ms", lambda s: s.quantile(0.90)),
            sm10=("swvl1", lambda s: s.quantile(0.10)),
            p30_10=("precip_30d_mm", lambda s: s.quantile(0.10)),
        )
        .reset_index()
    )

    def add_flags(df: pd.DataFrame) -> pd.DataFrame:
        x = df.merge(thresholds, on="month", how="left").copy()
        x["compound_flags"] = (
            (x["t2m_c"] >= x["t90"]).astype(int)
            + (x["rh_pct"] <= x["rh10"]).astype(int)
            + (x["wind_speed_ms"] >= x["wind90"]).astype(int)
            + (x["swvl1"] <= x["sm10"]).astype(int)
            + (x["precip_30d_mm"] <= x["p30_10"]).astype(int)
        )
        return x

    keep = [
        "time",
        "t2m_c",
        "rh_pct",
        "wind_speed_ms",
        "swvl1",
        "precip_30d_mm",
        "compound_flags",
    ]

    top_2024 = (
        add_flags(obs_2024)
        .sort_values(["compound_flags", "time"], ascending=[False, True])
        .loc[:, keep]
        .head(15)
        .copy()
    )

    latest_year = int(fire_df["year"].max())
    recent = (
        add_flags(fire_df[fire_df["year"] == latest_year].copy())
        .sort_values(["compound_flags", "time"], ascending=[False, False])
        .loc[:, keep]
        .head(15)
        .copy()
    )

    for frame in (top_2024, recent):
        frame["time"] = pd.to_datetime(frame["time"]).dt.strftime("%Y-%m-%d")
        for column in [
            "t2m_c",
            "rh_pct",
            "wind_speed_ms",
            "swvl1",
            "precip_30d_mm",
        ]:
            frame[column] = frame[column].round(3)

    return {
        "effis_annual_summary.csv": annual,
        "weather_fire_start_reference.csv": fire_start_reference,
        "weather_compound_top_2024.csv": top_2024,
        "weather_recent_2026.csv": recent,
    }


def check_tables(expected: dict[str, pd.DataFrame]) -> None:
    failures: list[str] = []

    for name, expected_frame in expected.items():
        path = OUTDIR / name
        if not path.exists():
            failures.append(f"Missing {path.relative_to(ROOT)}")
            continue

        actual = pd.read_csv(path)
        expected_for_compare = expected_frame.copy()

        try:
            pd.testing.assert_frame_equal(
                actual,
                expected_for_compare,
                check_dtype=False,
                check_exact=False,
                rtol=1e-7,
                atol=1e-7,
            )
            print(f"✓ {name}")
        except AssertionError as exc:
            failures.append(f"{name} differs from regenerated values: {exc}")

    if failures:
        print("\nFallback table verification failed:")
        for failure in failures:
            print("  ✗", failure)
        raise SystemExit(1)

    print("\nAll committed local fallback tables match the course data.")


def write_tables(tables: dict[str, pd.DataFrame]) -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    for name, frame in tables.items():
        path = OUTDIR / name
        frame.to_csv(path, index=False)
        print(f"✓ wrote {path.relative_to(ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify committed tables instead of rewriting them.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tables = build_tables()

    unknown = set(tables) ^ FILES
    if unknown:
        raise RuntimeError(f"Unexpected fallback table set: {sorted(unknown)}")

    if args.check:
        check_tables(tables)
    else:
        write_tables(tables)


if __name__ == "__main__":
    main()
