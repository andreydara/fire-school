# CDSE JupyterLab setup

This is the recommended setup for the GEO-ADAPT wildfire practicals.

The course uses **CDSE JupyterLab** as the primary environment. The canonical notebooks run in the standard **Python 3** kernel.

## 1. Open CDSE JupyterLab

1. Sign in to the Copernicus Data Space Ecosystem.
2. Open JupyterLab.
3. Wait for the JupyterLab interface to start.
4. In the left file browser, confirm that `mystorage/` is available.

`~/mystorage` is persistent storage. Files placed there survive JupyterLab restarts.

## 2. Open a terminal

In JupyterLab:

**File → New → Terminal**

The terminal prompt should look similar to:

```text
jovyan@jupyter-...:~$
```

## 3. Clone the course repository

Use the normal Git workflow directly in persistent storage:

```bash
cd ~/mystorage
git clone https://github.com/andreydara/fire-school.git
cd fire-school
```

If the repository already exists:

```bash
cd ~/mystorage/fire-school
git status
git pull --ff-only
```

Before updating, save or commit any notebook changes you want to keep.

## 4. Install the course packages

From the repository root, install the CDSE package set:

```bash
cd ~/mystorage/fire-school
python -m pip install -r requirements-cdse.txt
```

This file contains the analysis packages needed by the course but does not reinstall JupyterLab or the kernel itself.

After installation, restart the notebook kernel before running the preflight:

**Kernel → Restart Kernel**

Runtime pip installations may need to be repeated after a fresh/recreated CDSE JupyterLab session. If the preflight later reports missing core packages, rerun the command above.

## 5. Open the course folder

In the JupyterLab file browser, navigate to:

```text
mystorage/
  fire-school/
```

You should see:

```text
00_preflight.ipynb
notebooks/
data/
fallback/
group_project/
README.md
```

## 6. Select the Python 3 kernel

The canonical course notebooks use the standard **Python 3** kernel.

When opening a notebook:

1. check the kernel name in the top-right corner;
2. if necessary, choose **Kernel → Change Kernel**;
3. select **Python 3**.

Do not switch the canonical practicals to the dedicated OpenEO kernel.

## 7. Run the preflight

Open:

```text
00_preflight.ipynb
```

Then choose:

**Run → Run All Cells**

The target result is:

```text
YOUR COURSE ENVIRONMENT IS READY
```

Optional packages may be absent without blocking the course.

## 8. Earth Engine authentication

The first Earth Engine check may ask you to authenticate.

Follow the authentication link and complete the Google sign-in flow.

If Earth Engine requires an explicit Google Cloud project, either:

- set `GEE_PROJECT_ID` in the first configuration cell of `00_preflight.ipynb`; or
- export it in a terminal before starting a new Jupyter session:

```bash
export GEE_PROJECT_ID="your-google-cloud-project-id"
```

If you do not know which project to use, ask the trainer rather than creating an arbitrary project during the practical.

## 9. Start the practicals

Run the notebooks in order:

```text
notebooks/01_python_eo_intro.ipynb
notebooks/02_historical_fires.ipynb
notebooks/03_burned_area_severity.ipynb
notebooks/04_recovery.ipynb
notebooks/05_fire_weather_fuels.ipynb
notebooks/06_fire_susceptibility.ipynb
```

Run the core cells from top to bottom.

## 10. openEO live backup

Use the openEO fallback only if the class switches because Earth Engine is unavailable.

Keep the **Python 3** kernel and open:

```text
fallback/openeo/
```

The fallback notebooks install only the lightweight `openeo` Python client when it is missing.

Do **not** manually install GeoPandas, Rasterio, rioxarray or other compiled geospatial packages into the dedicated OpenEO kernel.

The first live openEO request can take several minutes. Results are cached in:

```text
~/mystorage/geo_adapt_openeo_cache/
```

so repeated runs are much faster.

## 11. Updating the course files

Use normal Git commands:

```bash
cd ~/mystorage/fire-school
git status
git pull --ff-only
```

If `git status` shows local notebook changes, save, commit or copy them before pulling.

After an update, rerun:

```bash
python -m pip install -r requirements-cdse.txt
```

if the dependency file changed or the preflight reports missing packages.

## 12. Temporary weather files

The two final ERA5-Land NetCDF files are committed to the repository. Intermediate CDS chunks are not.

Temporary preparation files belong under:

```text
data/weather/_tmp/
```

and partial writes use:

```text
*.part
```

Both are ignored by Git. Do not force-add them to the repository.

Students do not need to run `scripts/download_era5_land.py`.

## 13. If Git reports a pack-file error

Normal clone/fetch/pull in `~/mystorage` has been tested successfully. If Git nevertheless reports an error such as:

```text
Failed to checksum '.git/objects/pack/tmp_pack_...'
fetch-pack: invalid index-pack output
```

first check the repository state:

```bash
git status
git fsck --full
git ls-files data/weather/_tmp
git ls-files '*.part'
```

The last two commands should return nothing.

If the repository is clean, retry:

```bash
rm -f .git/objects/pack/tmp_pack_*
git fetch origin
git pull --ff-only
```

If the same error persists, use a fresh clone as a recovery step rather than as the normal course workflow.

## 14. What is persistent?

Persistent:

```text
~/mystorage/...
```

Not guaranteed to persist:

```text
/tmp/...
runtime pip installations
the current Jupyter session
```

Therefore keep notebooks, outputs and personal work under `~/mystorage`.

## 15. If something else fails

When asking for help, provide:

- the full error message;
- the notebook and cell number;
- whether you are using the **Python 3** kernel;
- the final preflight summary;
- whether the failure concerns package installation, Earth Engine, openEO, local course data, Git or JupyterLab itself.
