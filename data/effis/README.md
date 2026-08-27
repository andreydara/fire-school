# EFFIS reference data

The course uses one canonical EFFIS burned-area dataset:

`data/effis/Galicica.gpkg`

It is committed directly to this repository, so students do **not** need access to Google Drive or any separate download.

## Dataset

- Area: Galičica / Ohrid / Prespa surroundings
- Format: GeoPackage
- CRS: WGS 84 / CRS84 (longitude, latitude)
- Features: 46 burned-area polygons
- Years represented: 2017–2025
- Size: ~0.3 MB
- Key attributes: `FIREDATE`, `FINALDATE`, `COUNTRY`, `PROVINCE`, `COMMUNE`, `AREA_HA`, land-cover fractions, `PERCNA2K`, and `CLASS`

The much larger Balkans-wide EFFIS subset is intentionally **not** part of the student repository.

For the August 2024 case study, notebooks 02 and 03 filter this archive to the relevant event period and use EFFIS polygon `240575` as the main Ohrid-side reference polygon.
