#!/usr/bin/env python3
"""Static/portable QA checks for the public student course repository."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NOTEBOOKS = [
    Path("00_preflight.ipynb"),
    *[Path(f"notebooks/{i:02d}_{name}.ipynb") for i, name in [
        (1, "python_eo_intro"),
        (2, "historical_fires"),
        (3, "burned_area_severity"),
        (4, "recovery"),
        (5, "fire_weather_fuels"),
        (6, "fire_susceptibility"),
    ]],
]

OPENEO_NOTEBOOKS = [
    Path("fallback/openeo/00_openeo_smoke_test.ipynb"),
    Path("fallback/openeo/01_03_05_s2_core.ipynb"),
    Path("fallback/openeo/04_recovery_timeseries.ipynb"),
    Path("fallback/openeo/06_susceptibility_predictors.ipynb"),
]

REQUIRED_FILES = [
    Path("README.md"),
    Path("CDSE_SETUP.md"),
    Path("SETUP_LOCAL.md"),
    Path("requirements.txt"),
    Path("requirements-cdse.txt"),
    Path("requirements-lock.txt"),
    Path("requirements-optional.txt"),
    Path("requirements-trainer.txt"),
    Path("data/aoi/galicica_aoi.geojson"),
    Path("data/effis/Galicica.gpkg"),
    Path("data/weather/era5_land_galicica_hourly_2024.nc"),
    Path("data/weather/era5_land_galicica_fireseason_1991_latest.nc"),
    Path("group_project/README.md"),
    Path("group_project/presentation_template.md"),
]

errors: list[str] = []

for relative in REQUIRED_FILES:
    path = ROOT / relative
    if not path.exists() or path.stat().st_size == 0:
        errors.append(f"Missing required file: {relative}")

for relative in NOTEBOOKS + OPENEO_NOTEBOOKS:
    path = ROOT / relative
    if not path.exists():
        errors.append(f"Missing notebook: {relative}")
        continue

    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid notebook JSON {relative}: {exc}")
        continue

    cells = notebook.get("cells", [])
    if not cells:
        errors.append(f"Notebook has no cells: {relative}")
        continue

    text = "\n".join(
        "".join(cell.get("source", []))
        if isinstance(cell.get("source", []), list)
        else str(cell.get("source", ""))
        for cell in cells
    )

    # Student notebooks should be distributed without stale execution state.
    for idx, cell in enumerate(cells):
        if cell.get("cell_type") == "code":
            if cell.get("execution_count") not in (None,):
                errors.append(
                    f"{relative}: code cell {idx} has a saved execution count"
                )
            if cell.get("outputs"):
                errors.append(f"{relative}: code cell {idx} has saved outputs")

            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)

            # Core notebooks currently use plain Python rather than cell magics.
            # Parse each code cell to catch syntax damage introduced by edits.
            try:
                ast.parse(source or "")
            except SyntaxError as exc:
                errors.append(
                    f"{relative}: syntax error in code cell {idx}: "
                    f"{exc.msg} (line {exc.lineno})"
                )

    if relative.parent.name == "notebooks":
        has_working_method = any(
            "How to work with this notebook" in (
                "".join(cell.get("source", []))
                if isinstance(cell.get("source", []), list)
                else str(cell.get("source", ""))
            )
            for cell in cells
            if cell.get("cell_type") == "markdown"
        )
        if not has_working_method:
            errors.append(
                f"{relative}: missing student-facing 'How to work with this notebook' guidance"
            )

# Prevent accidental reintroduction of a trainer-specific EE project.
for relative in NOTEBOOKS + OPENEO_NOTEBOOKS:
    path = ROOT / relative
    if path.exists() and "ee-andreydara" in path.read_text(encoding="utf-8"):
        errors.append(f"{relative}: hard-coded trainer Earth Engine project")

# Notebook 05 depends on NetCDF4 and should declare the backend explicitly.
nb5 = ROOT / "notebooks/05_fire_weather_fuels.ipynb"
if nb5.exists():
    text = nb5.read_text(encoding="utf-8")
    if text.count('engine=\\"netcdf4\\"') < 2:
        errors.append(
            "Notebook 05 should open both course NetCDF datasets with engine='netcdf4'."
        )

gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
for entry in [".venv/", ".cdsapirc", "data/weather/_tmp/", "*.part"]:
    if entry not in gitignore:
        errors.append(f".gitignore should include {entry}")

# Intermediate weather downloads must never be tracked. They previously
# caused unnecessary repository churn and can make Git updates much heavier.
if (ROOT / ".git").exists():
    tracked_tmp = subprocess.run(
        ["git", "ls-files", "data/weather/_tmp", "*.part"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if tracked_tmp:
        errors.append(
            "Temporary weather files are tracked by Git: "
            + ", ".join(tracked_tmp.splitlines())
        )

# The CDSE openEO live fallback must stay compatible with the canonical
# Python 3 kernel and should not require Rasterio/rioxarray.
for relative in OPENEO_NOTEBOOKS:
    path = ROOT / relative
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if "import rasterio" in text or '"rasterio"' in text:
            errors.append(
                f"{relative}: openEO fallback should not require Rasterio; "
                "use NetCDF + xarray instead."
            )
        if ".tif" in text or ".tiff" in text:
            errors.append(
                f"{relative}: openEO fallback should prefer NetCDF outputs "
                "for compatibility with the canonical course kernel."
            )


print("Course repository validation")
print("=" * 72)

if errors:
    for error in errors:
        print("✗", error)
    print(f"\nFAILED: {len(errors)} issue(s)")
    raise SystemExit(1)

print("✓ Required files present")
print("✓ Core and openEO fallback notebook JSON/Python syntax valid")
print("✓ Student notebooks contain no saved outputs")
print("✓ No hard-coded trainer Earth Engine project")
print("✓ Notebook 05 uses the NetCDF4 backend explicitly")
print("✓ Sensitive/local and temporary weather files are ignored")
print("\nCOURSE REPOSITORY VALIDATION PASSED")
