# EFFIS reference layer

The burned-area practical is wired to compare the student dNBR result with a small EFFIS reference layer at:

`data/effis/galicica_effis.gpkg`

For the course, keep only a clipped Galičica/Ohrid-area reference file here rather than the full EFFIS dataset.

The trainer-provided Google Drive folder currently exposes the shapefile sidecars `.dbf`, `.shx`, and `.prj`; the `.shp` geometry file was not visible through the connected Drive listing when the notebook was prepared. Once the complete source layer is available, clip it to the course AOI and save it as `galicica_effis.gpkg`.

The notebook `notebooks/03_burned_area_severity.ipynb` detects this file automatically and skips the EFFIS comparison gracefully if it is absent.
