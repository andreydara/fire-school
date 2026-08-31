#!/usr/bin/env python3
"""Render trainer reference HTML from the student notebooks.

Run this only from a trainer environment that has already passed the preflight
and has working Earth Engine credentials.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
OUTDIR = ROOT / "fallback" / "reference_html"

NOTEBOOKS = [
    "01_python_eo_intro.ipynb",
    "02_historical_fires.ipynb",
    "03_burned_area_severity.ipynb",
    "04_recovery.ipynb",
    "05_fire_weather_fuels.ipynb",
    "06_fire_susceptibility.ipynb",
]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "notebooks",
        nargs="*",
        help="Notebook filenames to render; default is all six.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Per-cell execution timeout in seconds.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    selected = args.notebooks or NOTEBOOKS

    unknown = [name for name in selected if name not in NOTEBOOKS]
    if unknown:
        raise SystemExit("Unknown notebook(s): " + ", ".join(unknown))

    OUTDIR.mkdir(parents=True, exist_ok=True)

    print("Trainer reference export")
    print("Repository:", ROOT)
    print("Output:", OUTDIR)
    print(
        "Use an activated course environment with working Earth Engine "
        "credentials before running this script."
    )

    for name in selected:
        path = NOTEBOOK_DIR / name
        print(f"\n=== Rendering {name} ===")

        cmd = [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "html",
            "--execute",
            str(path),
            "--output-dir",
            str(OUTDIR),
            f"--ExecutePreprocessor.timeout={args.timeout}",
        ]
        subprocess.run(cmd, cwd=ROOT, check=True)

    print("\nReference HTML complete.")\n    print(\n        "Important: interactive Folium/Earth Engine tiles in HTML may still "\n        "require network access. Capture the key maps listed in "\n        "fallback/static/README.md before travel."\n    )
    print(
        "Open every exported file before travel. If the files are to be used "
        "as offline student fallback material, commit the reviewed HTML files "
        "under fallback/reference_html/."
    )

if __name__ == "__main__":
    main()
