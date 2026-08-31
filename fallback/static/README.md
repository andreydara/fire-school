# Static offline map captures

Interactive Folium/Earth Engine maps embedded in rendered HTML may still request web tiles. For a **true venue-internet outage**, capture the following views as static PNG or PDF files after the final successful trainer run.

Recommended filenames:

- `01_true_colour_swir_indices.png`
- `02_effis_fire_history.png`
- `03_dnbr_severity_effis.png`
- `04_recovery_zones.png`
- `05_weather_climatology.png`
- `05_prefire_ndmi.png`
- `06_susceptibility_effis.png`
- `06_weight_sensitivity.png`

Also keep the important non-map plots/tables either in the rendered HTML or as screenshots.

## Capture rule

A good fallback image must include enough context for the original interpretation questions:

- legend or clear visual scale;
- AOI/reference boundary where relevant;
- readable title;
- no personal browser/UI clutter;
- no credentials, tokens or private file paths.

The goal is not to create a second polished slide deck. The goal is to keep the analytical discussion teachable when map tiles or cloud backends fail.
