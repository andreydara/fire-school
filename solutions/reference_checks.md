# Trainer reference checks

These checks are intended to catch broken course runs. They are **not** answer keys that students must reproduce exactly unless an exact value is explicitly listed.

## Repository-level checks

- Galičica AOI file loads in EPSG:4326.
- EFFIS teaching subset contains **46 polygons**.
- EFFIS years span **2017–2025**.
- ERA5-Land hourly file contains **5,136 hourly records**.
- ERA5-Land fire-season file contains **7,632 daily records**.
- The ERA5-Land grid contains 11 × 9 cells in the downloaded rectangle.
- The current AOI-centre mask used in Practical 05 retains **13 grid-cell centres**.

## Practical 01 — Python + EO orientation

Structural checks:

- Earth Engine initializes.
- The canonical AOI loads.
- Sentinel-2 collection size is greater than zero.
- NDVI and NBR outputs have plausible index ranges within approximately -1 to 1.
- True-colour and SWIR false-colour layers render.

If the AOI falls back to a rectangle during the course, the repository is not being read from the expected location and should be fixed before continuing.

## Practical 02 — Historical fires

Exact EFFIS checks:

- 46 polygons total.
- 2024 contains **12 EFFIS polygons** in the course subset.
- Summed mapped area for 2024 is **6,075 ha**.
- Target polygon **240575** is dated **6 August 2024** in EFFIS and has `AREA_HA = 1598`.

The annual summary is reproduced in `fallback/tables/effis_annual_summary.csv`.

The Sentinel-2 NBR trajectory should show a clear 2024 disturbance over the target polygon. If it does not, first check date windows, cloud masking and the selected geometry.

## Practical 03 — Burned area and severity

Do not require an exact AOI-wide severity area because generic dNBR thresholds can respond to non-fire change.

Check instead that:

- pre- and post-fire Sentinel-2 collections are non-empty;
- the strongest coherent dNBR change overlaps the known 2024 fire area;
- water and built-up masking works;
- the EFFIS overlay is visible;
- students can identify at least one plausible disagreement or false positive.

The EFFIS target polygon is dated 6 August 2024. Avoid presenting the EFFIS date as proof of the exact ignition time.

## Practical 04 — Recovery

Structural checks:

- strong, moderate/lower and reference masks all contain usable pixels;
- annual 2019–2025 statistics complete without concurrent-aggregation errors;
- the stronger-impact zone shows a marked 2024 disturbance;
- 2025 should be interpreted as **spectral** recovery only.

If an index suggests recovery while another does not, keep the disagreement as a teaching result rather than forcing a single story.

## Practical 05 — Fire weather and fuel condition

Exact local-data check for EFFIS date **2024-08-06**:

| Metric | AOI mean | August 1991–2020 percentile |
|---|---:|---:|
| 12 UTC temperature | 26.539 °C | 71.4 |
| 12 UTC RH | 32.876 % | 29.0 |
| 12 UTC wind speed | 1.478 m/s | 52.7 |
| shallow soil moisture | 0.181 m³/m³ | 22.7 |
| previous 30-day precipitation | 14.365 mm | 20.4 |

This is a useful teaching point: the EFFIS start date is **not** the single most extreme compound-weather day in the 2024 season.

The transparent flag count reaches 4 on several June 2024 days and reaches 3 on several mid-August days. Treat this as a diagnostic, not FWI or fire probability.

Reference CSVs are under `fallback/tables/`.

## Practical 06 — Fire susceptibility

Structural checks:

- all four factor images render;
- baseline weights sum to 1;
- percentile thresholds are ordered p20 < p40 < p60 < p80;
- class-area shares are approximately quintile-like over the **unmasked burnable area**, because classes are defined from AOI percentiles;
- alternative weight sets visibly change at least some locations.

Do not require the EFFIS footprints to fall predominantly in the highest class. That comparison is a plausibility test, not a fitted validation target.

## Capstone

The trainer should challenge any statement that upgrades:

- dNBR class → ecological truth;
- NDMI/NDVI → direct fuel load;
- weather stress → ignition cause or probability;
- susceptibility → risk;
- spectral greening → complete ecological recovery.
