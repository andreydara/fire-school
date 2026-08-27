# Galičica course AOI

Canonical study-area polygon for the wildfire summer-school practicals.

- Repository file: `galicica_aoi.geojson`
- CRS: EPSG:4326
- Source: user-prepared `aoi.gpkg` (27 Aug 2026)
- Approximate extent: 20.720–21.054 E, 40.806–41.361 N
- Approximate area: 1,250 km²

GeoJSON is used in Git because it is tiny, transparent and easy to clone. The original GeoPackage can be retained separately if needed.

The notebooks use this polygon when available and fall back to the earlier training rectangle only if the file is missing.
