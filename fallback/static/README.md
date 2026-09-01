# Static offline map captures

Interactive Folium/Earth Engine maps embedded in rendered HTML may still request web tiles. For a **true venue-internet outage**, the following views should be captured as static PNG or PDF files after the final successful run.

Filenames:

- `01_true_colour_swir_indices.png`
- `02_effis_fire_history.png`
- `03_dnbr_severity_effis.png`
- `04_recovery_zones.png`
- `05_weather_climatology.png`
- `05_prefire_ndmi.png`
- `06_susceptibility_effis.png`
- `06_weight_sensitivity.png`

The goal is to keep the analytical discussion teachable when map tiles or cloud backends fail.
