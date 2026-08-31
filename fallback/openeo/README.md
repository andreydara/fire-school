# CDSE openEO live backup

These notebooks provide a **secondary live EO backend** for the course when Google Earth Engine is unavailable because of authentication, project/IAM, quota or service problems.

They are not a second version of the course. The six notebooks under `notebooks/` remain canonical.

## When to use this backup

Use openEO when:

- the CDSE Jupyter environment is working;
- the venue has internet access;
- Earth Engine is unavailable or a participant cannot initialize an EE project.

Do **not** use openEO as the offline fallback. openEO still depends on CDSE services and network access. For a venue/network outage, use the committed local data and trainer reference material under `fallback/`.

## Kernel

Run the fallback notebooks in the **same Python 3 kernel used for the canonical GEE notebooks**.

The fallback installs only the lightweight `openeo` Python client if it is missing. This is intentional: the course Python 3 kernel already contains the core stack used here — GeoPandas, NumPy, Matplotlib, xarray and netCDF4.

Do **not** install GeoPandas, Rasterio, rioxarray or other compiled geospatial packages into CDSE's dedicated OpenEO kernel for this course. That environment is useful for the official CDSE samples, but it does not contain the full course stack and ad-hoc geospatial installs can introduce binary-library mismatches.

CDSE documents that pip-installed packages are removed when the JupyterLab instance is restarted, so the small `openeo` client may need to be reinstalled in a new session. The notebook bootstrap cell handles that automatically.

## Sequence

1. `00_openeo_smoke_test.ipynb` — connection, authentication, collections and processes.
2. `01_03_05_s2_core.ipynb` — compact Sentinel-2 replacement for the core EO steps used in Practicals 01, 03 and the Sentinel-2 part of 05.
3. `04_recovery_timeseries.ipynb` — seasonal 2019–2025 NBR/NDVI/NDMI over the EFFIS target polygon.
4. `06_susceptibility_predictors.ipynb` — CDSE-native WorldCover, typical summer NDMI, Copernicus DEM slope and aspect.

Practical 02 does not need an openEO replacement because the EFFIS archive is already committed locally.

## Deliberate differences from the GEE workflow

The openEO backup is optimized for resilience and teaching continuity:

- it uses the EFFIS target area or a small buffered target bounding box rather than the entire course AOI where possible;
- it uses CDSE's standard `to_scl_dilation_mask` process for Sentinel-2 cloud masking;
- exact pixel counts and summary values can therefore differ slightly from the canonical GEE notebooks;
- the interpretation questions and scientific concepts should remain the same.

Do not present differences between GEE and openEO as errors unless the difference changes the scientific conclusion.

## Cost/performance principle

Filter spatial extent, temporal extent and bands as early as possible. The fallback intentionally keeps requests small. If a synchronous request times out, the notebooks switch to or explain how to use a batch job.

Current CDSE documentation used for these workflows:

- openEO Python client / CDSE connection and authentication;
- `SENTINEL2_L2A` with SCL masking;
- `aggregate_temporal` and `aggregate_spatial`;
- `ESA_WORLDCOVER_10M_2021_V2`;
- `COPERNICUS_30` with native `slope` and `aspect` processes.


## Output format

The live backup uses **NetCDF + xarray**, not GeoTIFF + Rasterio.

This is deliberate: xarray and netCDF4 are already part of the canonical course environment, while Rasterio is optional in the current CDSE Python 3 image. CDSE's own openEO examples also use NetCDF downloads with xarray for inspection. This keeps the emergency path smaller and avoids installing compiled geospatial packages during class.
