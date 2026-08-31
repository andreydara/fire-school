# Trainer pre-travel checklist

Use this checklist after the analytical notebooks are stable and before distributing the final course release.

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
python -m pip install -r requirements-lock.txt
python scripts/check_environment.py
```

On Windows, repeat at least once with the PowerShell setup from `SETUP_LOCAL.md` if a Windows trainer/participant machine is available.

- [ ] Notebook 05 opens both NetCDF files with the `netcdf4` engine.
- [ ] `00_preflight.ipynb` passes in the local fallback.

## 3. CDSE JupyterLab

Test from a participant-like CDSE account:

- [ ] repository clones under `~/mystorage`;
- [ ] `git pull` works;
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

## 5. Execute every student notebook

From a trainer account:

- [ ] 01 runs top to bottom;
- [ ] 02 runs top to bottom;
- [ ] 03 runs top to bottom;
- [ ] 04 runs top to bottom;
- [ ] 05 runs top to bottom;
- [ ] 06 runs top to bottom.

Compare with `solutions/reference_checks.md`.

## 6. Offline/reference pack

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

## 7. Capstone

- [ ] five team tasks are understandable without trainer explanation;
- [ ] presentation template is available;
- [ ] trainer rubric is available;
- [ ] presentation timing fits the final schedule;
- [ ] team sizes are assigned or easy to assign on the day.

## 8. Final release

After the final successful test:

- [ ] create a dated Git tag/release;
- [ ] avoid changing notebook logic after the release except for critical fixes;
- [ ] tell participants which tag/commit is the canonical course version;
- [ ] keep the trainer's working branch separate from the released student version if further experiments continue.
