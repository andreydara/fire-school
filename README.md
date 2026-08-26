# GEO-ADAPT Wildfire Summer School 2026

Hands-on materials for the GEO-ADAPT Summer School **Geospatial Information for Wildfire Monitoring and Risk Assessment**, Lake Ohrid, North Macedonia, September 2026.

## Course environment

The primary hands-on environment is **Copernicus Data Space Ecosystem (CDSE) JupyterLab**. Python is the common analysis interface; exercises may use CDSE/openEO/STAC, Google Earth Engine, and other public services as backends. Near-real-time wildfire monitoring is taught separately by Kenneth using browser tools, Python, and QGIS.

## Repository structure

```text
00_preflight.ipynb        # environment and account checks
notebooks/                # student hands-on exercises
data/                     # small shared/static inputs only
fallback/                 # cached inputs for API/service outages
group_project/            # Galičica capstone instructions/templates
solutions/                # trainer/reference material
```

Planned student notebooks:

1. `01_python_eo_intro.ipynb`
2. `02_historical_fires.ipynb`
3. `03_burned_area_severity.ipynb`
4. `04_recovery.ipynb`
5. `05_fire_weather_fuels.ipynb`
6. `06_fire_susceptibility.ipynb`

## Before the course

1. Create/verify your CDSE account and request JupyterLab access.
2. Verify Google Earth Engine access.
3. Install QGIS LTR if requested by the trainers.
4. Download this repository into persistent CDSE `~/mystorage`.
5. Open `00_preflight.ipynb` and run all cells.
6. Send the trainers the error text or a screenshot if the final summary contains any **FAIL** items.

## Working in CDSE JupyterLab

Clone into persistent storage:

```bash
cd ~/mystorage
git clone https://github.com/andreydara/fire-school.git
cd fire-school
```

To get updates later:

```bash
cd ~/mystorage/fire-school
git pull
```

## Resilience principle

Each core practical should eventually support three levels:

1. live cloud/API workflow;
2. cached-data fallback;
3. trainer reference output.

The course should remain teachable even if a remote service or venue internet connection is temporarily unavailable.
