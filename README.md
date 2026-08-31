# GEO-ADAPT Wildfire Summer School 2026

Hands-on materials for the GEO-ADAPT Summer School **Geospatial Information for Wildfire Monitoring and Risk Assessment**, Lake Ohrid, North Macedonia, September 2026.

## Course environment

The primary hands-on environment is **Copernicus Data Space Ecosystem (CDSE) JupyterLab**.

The supported local fallback is **Python 3.11 + `venv` + pip**. See `SETUP_LOCAL.md`.

Python is the common analysis interface. The core practicals use Google Earth Engine for cloud EO processing and local course files for EFFIS and ERA5-Land analysis. Near-real-time wildfire monitoring can be taught separately with browser tools, Python and QGIS.

## Student workflow

1. Set up CDSE JupyterLab using `CDSE_SETUP.md`.
2. Open `00_preflight.ipynb`.
3. Run all cells.
4. Resolve any **FAIL** items before the course.
5. Work through `notebooks/01_...` to `06_...` in order.

## Repository structure

```text
00_preflight.ipynb        # CDSE/local environment and account checks
CDSE_SETUP.md             # step-by-step CDSE JupyterLab setup
SETUP_LOCAL.md            # Python 3.11 local fallback setup
requirements.txt          # compatible top-level student dependencies
requirements-lock.txt     # tested Python 3.11 lock
requirements-optional.txt # non-core extensions
notebooks/                # student practicals 01–06
data/                     # committed static student inputs
fallback/                 # outage/reference material
group_project/            # Galičica capstone
solutions/                # trainer-facing reference checks
scripts/                  # setup, validation and data-preparation utilities
```

## Student notebooks

1. `01_python_eo_intro.ipynb` — Python/Jupyter + EO orientation
2. `02_historical_fires.ipynb` — EFFIS fire history + annual NBR trajectory
3. `03_burned_area_severity.ipynb` — Sentinel-2 dNBR burned area and severity
4. `04_recovery.ipynb` — post-fire spectral recovery
5. `05_fire_weather_fuels.ipynb` — ERA5-Land fire weather + vegetation/fuel-condition proxies
6. `06_fire_susceptibility.ipynb` — interpretable landscape susceptibility

## Before the course

### CDSE JupyterLab

Follow `CDSE_SETUP.md`.

Important: the CDSE `~/mystorage` filesystem is S3-backed. The tested course setup clones GitHub into `/tmp` first and copies the course files into persistent storage rather than keeping Git metadata inside `~/mystorage`.

Then run `00_preflight.ipynb` in the **Python 3** kernel.

### Local fallback

Follow `SETUP_LOCAL.md`. The short version is:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-lock.txt
python scripts/check_environment.py
```

Windows PowerShell commands are documented in `SETUP_LOCAL.md`.

## Earth Engine

The notebooks do not use a trainer's private Google Cloud project.

If Earth Engine requires an explicit registered project for a participant, set:

```bash
export GEE_PROJECT_ID="your-google-cloud-project-id"
```

before launching Jupyter. The preflight and all Earth Engine practicals use the same variable.

## Course data

The repository already includes the student-facing inputs needed for the core course:

- canonical Galičica AOI;
- Galičica EFFIS subset;
- ERA5-Land hourly April–October 2024;
- ERA5-Land April–October 1991–latest-2026 fire-season subset.

Students do **not** need CDS credentials and should not run the ERA5-Land download script.

## Resilience / fallback architecture

The course uses three levels:

1. **GEE live** — canonical cloud-EO backend;
2. **CDSE openEO live** — independent backup when Earth Engine is unavailable but CDSE and internet access still work;
3. **local/offline fallback** — committed datasets, reference tables, rendered outputs and static map captures.

The openEO backup is under `fallback/openeo/`. It is intentionally compact rather than a second copy of all six practicals.

See `fallback/README.md`.

Before travel, trainers should render reference HTML with:

```bash
python scripts/build_trainer_references.py
```

## Capstone

The final Galičica group project reuses outputs from the six practicals rather than introducing a separate large analysis.

See:

- `group_project/README.md`;
- `group_project/presentation_template.md`;
- `group_project/trainer_rubric.md`.

## Trainer / repository QA

From a tested trainer environment:

```bash
python scripts/check_environment.py
python scripts/validate_course.py
```

The repository validator checks notebook JSON, Python cell syntax, clean execution state, trainer/student separation, Earth Engine configuration, NetCDF4 use and required files.

See `TRAINER_CHECKLIST.md` for the final pre-travel checklist.
