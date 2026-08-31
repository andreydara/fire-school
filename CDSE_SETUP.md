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

## 3. Download the course repository

Do **not** keep the Git repository itself inside `~/mystorage`.

The CDSE persistent storage is S3-backed and Git pack-file operations can fail there. Clone into the temporary local filesystem first:

```bash
cd /tmp
rm -rf fire-school-source
git clone --depth 1 https://github.com/andreydara/fire-school.git fire-school-source
```

Then copy the course files into persistent storage:

```bash
mkdir -p ~/mystorage/fire-school
cp -a /tmp/fire-school-source/. ~/mystorage/fire-school/
rm -rf ~/mystorage/fire-school/.git
```

The last command removes Git metadata from the persistent copy. The notebooks and data remain.

## 4. Open the persistent course folder

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

## 5. Select the Python 3 kernel

The canonical course notebooks use the standard **Python 3** kernel.

When opening a notebook:

1. check the kernel name in the top-right corner;
2. if necessary, choose **Kernel → Change Kernel**;
3. select **Python 3**.

Do not switch the canonical practicals to the dedicated OpenEO kernel.

## 6. Run the preflight

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

## 7. Earth Engine authentication

The first Earth Engine check may ask you to authenticate.

Follow the authentication link and complete the Google sign-in flow.

If Earth Engine requires an explicit Google Cloud project, either:

- set `GEE_PROJECT_ID` in the first configuration cell of `00_preflight.ipynb`; or
- export it in a terminal before starting a new Jupyter session:

```bash
export GEE_PROJECT_ID="your-google-cloud-project-id"
```

If you do not know which project to use, ask the trainer rather than creating an arbitrary project during the practical.

## 8. Start the practicals

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

## 9. openEO live backup

Use the openEO fallback only if the trainer asks the class to switch because Earth Engine is unavailable.

Keep the **Python 3** kernel.

Open:

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

## 10. Updating the course files

Because the persistent copy intentionally contains no `.git` directory, do not run `git pull` inside `~/mystorage/fire-school`.

To refresh from GitHub:

```bash
cd /tmp
rm -rf fire-school-source
git clone --depth 1 https://github.com/andreydara/fire-school.git fire-school-source

cp -a /tmp/fire-school-source/. ~/mystorage/fire-school/
rm -rf ~/mystorage/fire-school/.git
```

This overlays the newest course files while keeping the persistent folder.

If you have made important personal changes to a notebook, save a copy under a different filename before refreshing.

## 11. What is persistent?

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

## 12. If something fails

When asking for help, provide:

- the full error message;
- the notebook and cell number;
- whether you are using the **Python 3** kernel;
- the final preflight summary;
- whether the failure concerns Earth Engine, openEO, local course data or JupyterLab itself.
