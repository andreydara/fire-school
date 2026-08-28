# Course data

Small, stable inputs that are safe and practical to keep in Git belong here, for example boundaries, sample points and compact CSV/GeoJSON files.

Do **not** commit large raw Sentinel/Landsat archives. Larger teaching inputs should be obtained from live services or stored as dedicated fallback assets outside normal Git history.


## Weather subsets

The course uses two compact ERA5-Land subsets under `data/weather/`:

- `era5_land_galicica_hourly_2024.nc` — hourly April–October 2024;
- `era5_land_galicica_fireseason_1991_latest.nc` — April–October daily 12 UTC weather from 1991 through the latest prepared 2026 date, with 1991–2020 used as the climatological baseline.

These are course-ready subsets, not raw global archives. The temporary CDS download cache under `data/weather/_tmp/` should not be committed.
