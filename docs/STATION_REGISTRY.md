# Station registry validation

`configs/station_registry_template.csv` is intentionally blank. Do not populate coordinates from map guesses.
Each row should identify the station, coordinate source, coordinate quality, site type and validity period.
`validate_station_registry` checks identifiers, coordinate ranges and date order. Missing coordinates are
warnings, not fabricated values; a registry with missing coordinates must not be used for geographic distance,
upwind/downwind, interpolation or spatial mapping. Keep source URLs or document identifiers in `metadata_source`.
