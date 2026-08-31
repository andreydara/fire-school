# Fallback assets

This folder supports the course when a live backend, API, or venue internet connection is temporarily unavailable.

The fallback strategy is deliberately simple:

1. **Use committed local inputs first.**
2. **Use compact reference tables for interpretation tasks.**
3. For Earth-Engine-dependent maps, use trainer-generated reference HTML created before the course.

Students should switch to fallback material only when instructed by a trainer.

## What already works without a live EO backend

The repository itself contains:

- `data/aoi/galicica_aoi.geojson`;
- `data/effis/Galicica.gpkg`;
- `data/weather/era5_land_galicica_hourly_2024.nc`;
- `data/weather/era5_land_galicica_fireseason_1991_latest.nc`.

Therefore:

- Practical 02 can still use the EFFIS history even if Earth Engine is unavailable;
- the weather/climatology part of Practical 05 is fully local;
- capstone Teams A and D retain substantial evidence even during an EO-service outage.

## Compact reference tables

`fallback/tables/` contains small derived tables that can be used for checking or discussion:

- `effis_annual_summary.csv`;
- `weather_fire_start_reference.csv`;
- `weather_compound_top_2024.csv`;
- `weather_recent_2026.csv`.

These tables reproduce the local-data logic used in the student notebooks. They are not separate scientific products.

## Earth Engine outage

Practicals 01, 03, 04 and 06, and the Sentinel-2 section of Practical 05, require a live Earth Engine session for the full workflow.

Before travel, a trainer should create reference HTML outputs with:

```bash
python scripts/build_trainer_references.py
```

The script writes rendered notebooks under `fallback/reference_html/`.

Those files allow the class to continue with interpretation, uncertainty and management exercises even if the live EO backend is temporarily unavailable.

## Fallback teaching rule

If a live service fails during class:

- allow a short retry;
- do not spend the practical debugging infrastructure;
- move to the corresponding local/reference output;
- keep the same interpretation questions and conceptual learning objective.

Fallback mode should change the **data-delivery mechanism**, not the analytical logic.
