# ERA5-Land course weather data

This folder contains compact weather inputs for Practical 05.

## Final course files

- `era5_land_galicica_hourly_2024.nc`
  - April–October 2024
  - hourly ERA5-Land over the buffered Galičica course area
  - includes derived temperature in °C, relative humidity, wind speed and hourly precipitation increments

- `era5_land_galicica_fireseason_1991_latest.nc`
  - April–October from 1991 through the latest prepared 2026 date
  - standardized 12 UTC weather snapshot
  - previous-24-hour precipitation
  - 1991–2020 is the course climatological baseline

## Variables used in Practical 05

- 2 m temperature
- 2 m dewpoint temperature
- derived relative humidity
- 10 m U/V wind and derived wind speed
- total / derived precipitation
- volumetric soil water, layers 1 and 2

## Interpretation

ERA5-Land provides regional meteorological context at roughly 0.1° grid spacing. It does not resolve slope-scale wind or microclimate across Galičica.

The course uses 12 UTC as a consistent daily comparison time. This is not claimed to reproduce operational EFFIS or Canadian FWI calculations exactly.

## Source

Copernicus Climate Change Service / ECMWF ERA5-Land.

The preparation script is `scripts/download_era5_land.py`.


## Temporary preparation files

The ERA5-Land preparation script uses `data/weather/_tmp/` for restartable intermediate CDS downloads and `*.part` for atomic writes.

These files are intentionally excluded by `.gitignore` and must not be committed. Only the final course NetCDF files listed above belong in Git.
