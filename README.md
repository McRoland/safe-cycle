# safe-cycle 🚴

A GIS pipeline for validating GPS track data. Built around transportation route integrity checks and spatial QA/QC.

![Route Map](map_preview.png)

## Problem

GPS data is messy. Bike tracks from consumer devices have noise, dropouts, and timestamp corruption. This project validates that a GPX file is actually usable. It catches bad segments before analysis or visualization.

## What It Does

Given a GPX file, safe-cycle checks for:
- **Speed anomalies** — Flags segments where speed exceeds bike physics (e.g., 180 km/h = bad data)
- **Self-intersections** — Detects where a path crosses itself (usually indicates GPS dropout or duplicate tracks)
- **Timestamp issues** — (Coming soon) Validates monotonic time and reasonable segment gaps

Returns a clean HTML map with validation results highlighted.

## Stack

- **Parsing:** GPXpy, Shapely
- **Geospatial:** GeoPandas, Folium
- **Testing:** Pytest
- **Analysis:** Haversine distance, geometric intersection detection

## How to Use

```bash
git clone https://github.com/McRoland/safe-cycle.git
cd safe-cycle
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Example

```python
from safe_cycle import parse_gpx, extract_points_from_gpx, check_speed_anomalies

gpx = parse_gpx("my_ride.gpx")
data = extract_points_from_gpx(gpx)
anomalies = check_speed_anomalies(data['speeds'], threshold_mps=22)

print(f"Found {len(anomalies)} speed anomalies")
```

## What I Learned

- **GPS data validation is foundational.** Before you can analyze or visualize track data, you need to know it's valid. This project taught me to think defensively about inputs.
- **Geometry comes first.** Using Shapely for intersection detection taught me to think in terms of spatial relationships, not just lat/lon arrays.
- **Testing uncovers edge cases.** Writing pytest tests forced me to think about what breaks (zero-time segments, duplicate points, GPS noise) instead of the happy path.

## Next Steps

- Add timestamp validation (monotonic, no huge gaps)
- Detect duplicate/near-duplicate points
- Export cleaned data to GeoJSON
- Add elevation profile validation
