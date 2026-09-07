from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

import geopandas as gpd
import pandas as pd
import requests
from bs4 import BeautifulSoup
from shapely.geometry import Polygon
from shapely.ops import unary_union


ACQUISITION_PLANS_URL = (
    "https://sentinels.copernicus.eu/copernicus/sentinel-2/acquisition-plans"
)
USER_AGENT = "sentinel2-acquisition-aoi/1.0"
KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


@dataclass(frozen=True)
class Plan:
    satellite: str
    start: datetime
    end: datetime
    url: str


@dataclass
class Acquisition:
    satellite: str
    acquisition_id: str
    start: datetime
    end: datetime | None
    geometry: object
    plan: Plan


def _parse_iso_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _parse_plan_stamp(value: str) -> datetime:
    return datetime.strptime(
        value.upper(), "%Y%m%dT%H%M%S"
    ).replace(tzinfo=timezone.utc)


def _format_dt(dt: datetime | None) -> str:
    if dt is None:
        return ""

    return (
        dt.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def load_aoi(path: str | Path):
    """
    Load an AOI from GeoJSON or ESRI Shapefile.

    Supported:
        .geojson
        .json
        .shp

    The AOI is automatically reprojected to EPSG:4326.
    All features are merged into a single geometry.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"AOI file not found: {path}")

    supported = {".geojson", ".json", ".shp"}
    if path.suffix.lower() not in supported:
        raise ValueError(
            "Unsupported AOI format. "
            "Use GeoJSON (.geojson/.json) or Shapefile (.shp)."
        )

    gdf = gpd.read_file(path)

    if gdf.empty:
        raise ValueError("AOI file contains no features.")

    gdf = gdf[
        gdf.geometry.notna() & ~gdf.geometry.is_empty
    ].copy()

    if gdf.empty:
        raise ValueError("AOI contains no valid geometries.")

    if gdf.crs is None:
        raise ValueError(
            "AOI has no CRS information. "
            "Assign the correct CRS before running."
        )

    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    try:
        geom = gdf.geometry.union_all()
    except AttributeError:
        # Compatibility with older GeoPandas versions
        geom = unary_union(gdf.geometry.values)

    if not geom.is_valid:
        geom = geom.buffer(0)

    if geom.is_empty or not geom.is_valid:
        raise ValueError("AOI geometry is empty or invalid.")

    return geom


def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def _discover_plans(session: requests.Session) -> dict[str, list[Plan]]:
    response = session.get(ACQUISITION_PLANS_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    plans = {
        "S2A": [],
        "S2B": [],
        "S2C": [],
    }

    pattern = re.compile(
        r"(s2[abc])_mp_acq__kml_(\d{8}t\d{6})_(\d{8}t\d{6})",
        re.IGNORECASE,
    )

    seen = set()

    for anchor in soup.find_all("a", href=True):
        full_url = urljoin(ACQUISITION_PLANS_URL, anchor["href"])
        match = pattern.search(full_url)

        if not match or full_url in seen:
            continue

        seen.add(full_url)

        satellite = match.group(1).upper()

        plans[satellite].append(
            Plan(
                satellite=satellite,
                start=_parse_plan_stamp(match.group(2)),
                end=_parse_plan_stamp(match.group(3)),
                url=full_url,
            )
        )

    for satellite in plans:
        plans[satellite].sort(
            key=lambda p: p.start,
            reverse=True,
        )

    return plans


def _plans_overlapping_window(
    plans: list[Plan],
    window_start: datetime,
    window_end: datetime,
) -> list[Plan]:
    return [
        p
        for p in plans
        if p.end >= window_start and p.start <= window_end
    ]


def _latest_plan_for_time(
    plans: list[Plan],
    when: datetime,
) -> Plan | None:
    candidates = [
        p
        for p in plans
        if p.start <= when <= p.end
    ]

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.start)


def _parse_coordinate_text(
    text: str | None,
) -> list[tuple[float, float]]:
    if not text:
        return []

    coords = []

    for token in text.split():
        parts = token.split(",")

        if len(parts) >= 2:
            coords.append(
                (float(parts[0]), float(parts[1]))
            )

    return coords


def _polygon_from_kml_element(poly_elem: ET.Element):
    outer_elem = poly_elem.find(
        "kml:outerBoundaryIs/kml:LinearRing/kml:coordinates",
        KML_NS,
    )

    outer = _parse_coordinate_text(
        outer_elem.text if outer_elem is not None else None
    )

    if len(outer) < 4:
        return None

    holes = []

    for inner_elem in poly_elem.findall(
        "kml:innerBoundaryIs/kml:LinearRing/kml:coordinates",
        KML_NS,
    ):
        ring = _parse_coordinate_text(inner_elem.text)

        if len(ring) >= 4:
            holes.append(ring)

    geom = Polygon(outer, holes)

    if not geom.is_valid:
        geom = geom.buffer(0)

    return None if geom.is_empty else geom


def _placemark_geometry(placemark: ET.Element):
    polygons = []

    for poly_elem in placemark.findall(
        ".//kml:Polygon",
        KML_NS,
    ):
        polygon = _polygon_from_kml_element(poly_elem)

        if polygon is not None:
            polygons.append(polygon)

    if not polygons:
        return None

    geom = unary_union(polygons)

    if not geom.is_valid:
        geom = geom.buffer(0)

    return None if geom.is_empty else geom


def _nominal_placemarks(root: ET.Element) -> list[ET.Element]:
    placemarks = []

    for folder in root.findall(".//kml:Folder", KML_NS):
        name_elem = folder.find("kml:name", KML_NS)

        folder_name = (
            (name_elem.text or "").strip()
            if name_elem is not None
            else ""
        )

        if folder_name.upper().startswith("NOMINAL"):
            placemarks.extend(
                folder.findall(
                    ".//kml:Placemark",
                    KML_NS,
                )
            )

    return placemarks


def _parse_kml_plan(
    content: bytes,
    plan: Plan,
) -> list[Acquisition]:
    root = ET.fromstring(content)
    placemarks = _nominal_placemarks(root)

    if not placemarks:
        raise RuntimeError(
            f"No NOMINAL placemarks found in {plan.url}. "
            "The Copernicus KML structure may have changed."
        )

    acquisitions = []

    for placemark in placemarks:
        name_elem = placemark.find("kml:name", KML_NS)

        acquisition_id = (
            (name_elem.text or "").strip()
            if name_elem is not None
            else "<unnamed>"
        )

        begin_elem = placemark.find(
            "kml:TimeSpan/kml:begin",
            KML_NS,
        )

        end_elem = placemark.find(
            "kml:TimeSpan/kml:end",
            KML_NS,
        )

        if begin_elem is None or not begin_elem.text:
            continue

        start = _parse_iso_utc(begin_elem.text)

        end = (
            _parse_iso_utc(end_elem.text)
            if end_elem is not None and end_elem.text
            else None
        )

        geometry = _placemark_geometry(placemark)

        if geometry is None:
            continue

        acquisitions.append(
            Acquisition(
                satellite=plan.satellite,
                acquisition_id=acquisition_id,
                start=start,
                end=end,
                geometry=geometry,
                plan=plan,
            )
        )

    return acquisitions


def _download_plan(
    session: requests.Session,
    plan: Plan,
) -> bytes:
    response = session.get(plan.url, timeout=60)
    response.raise_for_status()
    return response.content


def find_sentinel2_acquisitions(
    aoi_path: str | Path,
    days: int = 7,
    start: datetime | None = None,
    satellites: tuple[str, ...] = ("S2A", "S2B", "S2C"),
    verbose: bool = True,
    include_geometry: bool = False,
) -> pd.DataFrame:
    """
    Find planned Sentinel-2 NOMINAL acquisitions intersecting an AOI.

    Parameters
    ----------
    aoi_path:
        Path to a .geojson, .json, or .shp AOI.
    days:
        Number of days to search forward.
    start:
        UTC start datetime. Defaults to current UTC time.
    satellites:
        Satellites to include. Defaults to S2A, S2B and S2C.
    verbose:
        Print progress information.
    include_geometry:
        If True, return a GeoDataFrame containing each planned acquisition
        footprint in the ``geometry`` column.

    Returns
    -------
    pandas.DataFrame
        Planned acquisitions sorted by start time.
    """
    if days <= 0:
        raise ValueError("days must be greater than 0.")

    if start is None:
        window_start = datetime.now(timezone.utc)
    else:
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        window_start = start.astimezone(timezone.utc)

    window_end = window_start + timedelta(days=days)

    if verbose:
        print(f"AOI: {aoi_path}")
        print(
            "Search window:",
            _format_dt(window_start),
            "to",
            _format_dt(window_end),
        )

    aoi = load_aoi(aoi_path)
    session = _get_session()
    plans_by_satellite = _discover_plans(session)

    matches = []

    for satellite in satellites:
        satellite = satellite.upper()

        if satellite not in plans_by_satellite:
            raise ValueError(
                f"Unknown satellite: {satellite}"
            )

        all_plans = plans_by_satellite[satellite]

        selected_plans = _plans_overlapping_window(
            all_plans,
            window_start,
            window_end,
        )

        if not selected_plans:
            if verbose:
                print(
                    f"Warning: no published {satellite} plan "
                    "covers this search window."
                )
            continue

        for plan in selected_plans:
            if verbose:
                print(
                    f"Reading {satellite} plan: "
                    f"{_format_dt(plan.start)} → "
                    f"{_format_dt(plan.end)}"
                )

            content = _download_plan(session, plan)
            acquisitions = _parse_kml_plan(content, plan)

            for acq in acquisitions:
                acq_end = acq.end or acq.start

                if acq_end < window_start:
                    continue

                if acq.start > window_end:
                    continue

                # Copernicus plans may overlap. Prefer the newest
                # published plan valid at the acquisition time.
                preferred_plan = _latest_plan_for_time(
                    selected_plans,
                    acq.start,
                )

                if (
                    preferred_plan is None
                    or preferred_plan.url != plan.url
                ):
                    continue

                if aoi.intersects(acq.geometry):
                    matches.append(acq)

    unique = {
        (
            a.satellite,
            a.acquisition_id,
            a.start,
        ): a
        for a in matches
    }

    acquisitions = sorted(
        unique.values(),
        key=lambda a: (
            a.start,
            a.satellite,
        ),
    )

    results = pd.DataFrame(
        [
            {
                "satellite": acq.satellite,
                "acquisition_id": acq.acquisition_id,
                "start_utc": _format_dt(acq.start),
                "end_utc": _format_dt(acq.end),
                "plan_start_utc": _format_dt(acq.plan.start),
                "plan_end_utc": _format_dt(acq.plan.end),
                "plan_url": acq.plan.url,
                **({"geometry": acq.geometry} if include_geometry else {}),
            }
            for acq in acquisitions
        ],
        columns=[
            "satellite",
            "acquisition_id",
            "start_utc",
            "end_utc",
            "plan_start_utc",
            "plan_end_utc",
            "plan_url",
            *(["geometry"] if include_geometry else []),
        ],
    )

    if include_geometry:
        results = gpd.GeoDataFrame(
            results, geometry="geometry", crs="EPSG:4326"
        )

    if verbose:
        print(f"Found {len(results)} acquisition(s).")

    return results


def plot_sentinel2_overpasses(
    aoi_path: str | Path,
    days: int = 7,
    start: datetime | None = None,
    satellites: tuple[str, ...] = ("S2A", "S2B", "S2C"),
    timezone_name: str = "UTC",
    figsize: tuple[float, float] = (8, 8),
    padding_fraction: float = 0.20,
    save_dir: str | Path | None = None,
    show: bool = True,
    verbose: bool = True,
):
    """
    Plot one figure for each planned Sentinel-2 acquisition intersecting an AOI.

    Each plot shows the AOI and the planned acquisition footprint, with the
    satellite and acquisition time in the title.

    Returns
    -------
    (acquisitions, figures)
        acquisitions is a GeoDataFrame and figures is a list of Matplotlib
        Figure objects.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "Plotting requires matplotlib. Install it with: pip install matplotlib"
        ) from exc

    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(timezone_name)
    except Exception as exc:
        raise ValueError(
            f"Unknown timezone {timezone_name!r}. "
            "Use an IANA timezone such as 'UTC' or 'Europe/Copenhagen'."
        ) from exc

    aoi = load_aoi(aoi_path)
    aoi_gdf = gpd.GeoDataFrame(
        {"name": ["AOI"]}, geometry=[aoi], crs="EPSG:4326"
    )

    acquisitions = find_sentinel2_acquisitions(
        aoi_path=aoi_path,
        days=days,
        start=start,
        satellites=satellites,
        verbose=verbose,
        include_geometry=True,
    )

    if acquisitions.empty:
        if verbose:
            print("No planned overpasses to plot.")
        return acquisitions, []

    save_path = None
    if save_dir is not None:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

    minx, miny, maxx, maxy = aoi.bounds
    width = maxx - minx
    height = maxy - miny
    pad_x = max(width * padding_fraction, 0.01)
    pad_y = max(height * padding_fraction, 0.01)

    figures = []

    for _, row in acquisitions.iterrows():
        fig, ax = plt.subplots(figsize=figsize)

        footprint = gpd.GeoDataFrame(
            {"satellite": [row["satellite"]]},
            geometry=[row.geometry],
            crs="EPSG:4326",
        )

        footprint.plot(ax=ax, alpha=0.30)
        footprint.boundary.plot(ax=ax, linewidth=1.2)
        aoi_gdf.boundary.plot(ax=ax, linewidth=2.5)

        start_utc = _parse_iso_utc(row["start_utc"])
        local_time = start_utc.astimezone(tz)
        time_label = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")

        ax.set_title(f"{row['satellite']} planned overpass\n{time_label}")
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True, alpha=0.25)
        fig.tight_layout()

        figures.append(fig)

        if save_path is not None:
            stamp = start_utc.strftime("%Y%m%dT%H%M%SZ")
            filename = save_path / f"{row['satellite']}_{stamp}.png"
            fig.savefig(filename, dpi=150, bbox_inches="tight")

        if show:
            plt.show()
        else:
            plt.close(fig)

    return acquisitions, figures


def next_sentinel2_acquisition(
    aoi_path: str | Path,
    days: int = 7,
    **kwargs,
) -> pd.Series | None:
    """
    Return the first planned Sentinel-2 acquisition
    intersecting the AOI, or None if none are found.
    """
    results = find_sentinel2_acquisitions(
        aoi_path=aoi_path,
        days=days,
        **kwargs,
    )

    if results.empty:
        return None

    return results.iloc[0]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Find planned Sentinel-2 acquisitions "
            "intersecting a GeoJSON or Shapefile AOI."
        )
    )

    parser.add_argument(
        "aoi",
        help="Path to AOI (.geojson, .json, or .shp)",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to search forward (default: 7)",
    )

    parser.add_argument(
        "--output",
        default="sentinel2_acquisitions.csv",
        help="Output CSV path",
    )

    args = parser.parse_args()

    df = find_sentinel2_acquisitions(
        aoi_path=args.aoi,
        days=args.days,
    )

    print()
    if df.empty:
        print("No matching acquisitions found.")
    else:
        print(df.to_string(index=False))

    df.to_csv(args.output, index=False)
    print(f"\nSaved results to: {args.output}")
