#!/usr/bin/env python3
"""Static/portable QA checks for the public student course repository."""

from __future__ import annotations

import json
import re
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

REQUIRED_FILES = [
    Path("README.md"),
    Path("SETUP_LOCAL.md"),
    Path("requirements.txt"),
    Path("requirements-lock.txt"),
    Path("requirements-optional.txt"),
    Path("requirements-trainer.txt"),
    Path("data/aoi/galicica_aoi.geojson"),
    Path("data/effis/Galicica.gpkg"),
    Path("data/weather/era5_land_galicica_hourly_2024.nc"),
    Path("data/weather/era5_land_galicica_fireseason_1991_latest.nc"),
    Path("group_project/README.md"),
    Path("group_project/presentation_template.md"),
    Path("group_project/trainer_rubric.md"),
]

# These phrases indicate assistant/user conversation leakage or trainer-specific
# configuration that should never appear in student notebooks.
BANNED_NOTEBOOK_PATTERNS = [
    r"ChatGPT",
    r"\bAndrey\b",
    r"ee-andreydara",
    r"we decided",
    r"we agreed",
    r"I suggest",
    r"I recommend",
    r"send me",
    r"your Mac",
    r"pull it",
]

errors: list[str] = []

for relative in REQUIRED_FILES:
    path = ROOT / relative
    if not path.exists() or path.stat().st_size == 0:
        errors.append(f"Missing required file: {relative}")

for relative in NOTEBOOKS:
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

    for pattern in BANNED_NOTEBOOK_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(
                f"{relative}: student notebook contains banned/meta pattern {pattern!r}"
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

# Prevent accidental reintroduction of a trainer-specific EE project.
for relative in NOTEBOOKS:
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
for entry in [".venv/", ".cdsapirc", "data/weather/_tmp/"]:
    if entry not in gitignore:
        errors.append(f".gitignore should include {entry}")

print("Course repository validation")
print("=" * 72)

if errors:
    for error in errors:
        print("✗", error)
    print(f"\nFAILED: {len(errors)} issue(s)")
    raise SystemExit(1)

print("✓ Required files present")
print("✓ Notebook JSON valid")
print("✓ Student notebooks contain no saved outputs")
print("✓ No trainer/private assistant conversation leakage detected")
print("✓ No hard-coded trainer Earth Engine project")
print("✓ Notebook 05 uses the NetCDF4 backend explicitly")
print("✓ Sensitive/local files are ignored")
print("\nCOURSE REPOSITORY VALIDATION PASSED")
