# Trainer pre-travel checklist

Checklist for after the analytical notebooks are stable and before distributing the final course release.

## 1. Repository state

- [ ] `git status` is clean.
- [ ] `git pull` completes without conflicts.
- [ ] `python scripts/validate_course.py` passes.
- [ ] Student notebooks contain no saved execution outputs.
- [ ] No trainer credentials, API keys or trainer-specific Earth Engine project IDs are committed.

## 2. Local Python fallback

Test from a **fresh Python 3.11 virtual environment**, not the development environment:

```bash
python3.11 -m venv .venv-test
source .venv-test/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/check_environment.py
```

On Windows, repeat at least once with the PowerShell setup from `SETUP_LOCAL.md` if a Windows trainer/participant machine is available.

- [ ] Notebook 05 opens both NetCDF files with the `netcdf4` engine.
- [ ] `00_preflight.ipynb` passes in the local fallback.

## 3. CDSE JupyterLab

Test from a participant-like CDSE account:

- [ ] the repository clones directly under `~/mystorage/fire-school`;
- [ ] normal `git fetch` / `git pull --ff-only` work there;
- [ ] `git ls-files data/weather/_tmp` returns nothing;
- [ ] `git ls-files '*.part'` returns nothing;
- [ ] `python -m pip install -r requirements-cdse.txt` succeeds in a fresh standard Python environment;
- [ ] the Python 3 kernel is restarted after installation;
- [ ] the update procedure in `CDSE_SETUP.md` works;
- [ ] preflight identifies writable persistent storage;
- [ ] core packages import;
- [ ] local weather datasets open;
- [ ] Jupyter kernel restarts cleanly.

## 4. Earth Engine access — critical

The public notebooks do not use a trainer-specific project.

Before the course:

- [ ] test Earth Engine with at least **two non-trainer participant-like accounts**;
- [ ] confirm whether participants can initialize without an explicit project;
- [ ] if a shared course Google Cloud project is used, grant the required IAM access before arrival;
- [ ] if individual projects are required, send setup instructions early enough for participants to test them;
- [ ] verify all six notebooks after the final Earth Engine access decision.

Do not discover the project/IAM model during the first practical.

## 5. CDSE openEO live backup

In the same **Python 3 course kernel** used for the canonical GEE notebooks:

- [ ] run `fallback/openeo/00_openeo_smoke_test.ipynb`;
- [ ] confirm Sentinel-2, WorldCover and Copernicus DEM collections are available;
- [ ] confirm `to_scl_dilation_mask`, `slope` and `aspect` processes are available;
- [ ] run `01_03_05_s2_core.ipynb` once;
- [ ] run `04_recovery_timeseries.ipynb` once;
- [ ] run `06_susceptibility_predictors.ipynb` once;
- [ ] record typical runtime and whether any job-credit limits are encountered.

Allow the fallback bootstrap cell to install only `openeo` when it is missing. Do not install the full compiled geospatial stack into the dedicated OpenEO environment.

## 6. Execute every student notebook

From a trainer account:

- [ ] 01 runs top to bottom;
- [ ] 02 runs top to bottom;
- [ ] 03 runs top to bottom;
- [ ] 04 runs top to bottom;
- [ ] 05 runs top to bottom;
- [ ] 06 runs top to bottom.

Compare with `solutions/reference_checks.md`.

## 7. Offline/reference pack

Generate rendered references:

```bash
python scripts/build_trainer_references.py
```

Then:

- [ ] open every file under `fallback/reference_html/`;
- [ ] confirm tables and static figures render;
- [ ] remember that interactive web-map tiles may still need internet;
- [ ] capture the key maps listed in `fallback/static/README.md` as static PNG/PDF files;
- [ ] review all references for accidental credentials or personal paths;
- [ ] keep a second copy outside the venue internet connection (trainer laptop / USB / shared offline folder).

The committed EFFIS and weather tables under `fallback/tables/` are already available without APIs.

## 8. Capstone

- [ ] five team tasks are understandable without trainer explanation;
- [ ] presentation template is available;
- [ ] presentation timing fits the final schedule;
- [ ] team sizes are assigned or easy to assign on the day.

## 9. Final release

After the final successful test:

- [ ] create a dated Git tag/release;
- [ ] avoid changing notebook logic after the release except for critical fixes;
- [ ] tell participants which tag/commit is the canonical course version;
- [ ] keep the trainer's working branch separate from the released student version if further experiments continue.
