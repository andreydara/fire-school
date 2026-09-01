# Local fallback setup — Python 3.11

The primary student environment is CDSE JupyterLab. This local setup is the supported fallback when CDSE is unavailable or when a participant wants to test the course before travelling.

Use **Python 3.11**. Do not create the environment with an unspecified `python` executable if several Python versions are installed.

## 1. Clone the repository

```bash
git clone https://github.com/andreydara/fire-school.git
cd fire-school
```

## 2. Create the virtual environment

### macOS / Linux

Check that Python 3.11 exists:

```bash
python3.11 --version
```

Create and activate the environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python --version
```

The final command should report Python 3.11.x.

### Windows PowerShell

```powershell
py -3.11 --version
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python --version
```

## 3. Install the course environment

Upgrade packaging tools first:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Preferred installation:

```bash
python -m pip install -r requirements.txt
```

Optional extensions:

```bash
python -m pip install -r requirements-optional.txt
```

## 4. Register the Jupyter kernel

```bash
python -m ipykernel install --user --name geo-adapt-fire-school --display-name "GEO-ADAPT Fire School (Python 3.11)"
```

In JupyterLab, select **GEO-ADAPT Fire School (Python 3.11)**.

## 5. Check the environment

From the repository root:

```bash
python scripts/check_environment.py
```

Then open `00_preflight.ipynb` and run all cells.

## 6. Earth Engine project configuration

If Earth Engine works without an explicit project, no extra setting is needed. If your Earth Engine account requires a registered Google Cloud project, set it before launching Jupyter:

### macOS / Linux

```bash
export GEE_PROJECT_ID="your-google-cloud-project-id"
jupyter lab
```

### Windows PowerShell

```powershell
$env:GEE_PROJECT_ID="your-google-cloud-project-id"
jupyter lab
```

The same variable is used by the preflight and all Earth Engine notebooks.

## 7. Course data

The repository already contains the student-facing static inputs:

- Galičica AOI;
- Galičica EFFIS subset;
- ERA5-Land hourly 2024 subset;
- ERA5-Land 1991–latest fire-season subset.

Students do **not** need CDS credentials and should not run `scripts/download_era5_land.py`.

## 8. Updating before the course

```bash
git pull
python -m pip install -r requirements.txt
python scripts/check_environment.py
```

If `git pull` reports local notebook changes, save a copy of your work before resolving the conflict.
