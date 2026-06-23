# ===== SECTION 1: IMPORT & CONFIG =====
from shapely.geometry import LineString, MultiLineString, MultiPoint, mapping
import gpxpy 
import folium
from math import radians, cos, sin, asin, sqrt
from haversine import haversine
from datetime import datetime

file_path = '/Users/fluxboi/Safe-Cycle/data/blue_hills.gpx'
output_file = "path_map.html"

# ===== SECTION 2: UTILITY FUNCTIONS =====

def haversine_dist(lat1, lon1, lat2, lon2):
    """Calculate distance between two coords in meters."""
    coord1 = [lat1, lon1]
    coord2 = [lat2, lon2]
    distance = haversine(coord1, coord2) * 1000
    return distance

def nonduplicate_intersections(intrsec_pts, precision=5):
    """Remove near-duplicate intersection points (GPS noise)."""
    seen = set()
    unique = []
    for pt in intrsec_pts:
        rounded = (round(pt[0], precision), round(pt[1], precision))
        if rounded not in seen:
            seen.add(rounded)
            unique.append(rounded)
    return unique

# ===== SECTION 3: DATA PARSING =====

def parse_gpx(file_path):
    """Open GPX file and return parsed data."""
    with open(file_path, 'r') as gf:
        gpx = gpxpy.parse(gf)
    return gpx

def extract_points_from_gpx(gpx):
    """
    Pull all points from GPX tracks and return structured data.
    
    Returns:
        dict with keys: 'points', 'coordinates', 'timestamps', 'elevations', 'gpx_obj'
    """
    point_objs = []
    coordinates = []
    timestamps = []
    elevations = []

    for track in gpx.tracks:
        for segment in track.segments:
            for idx, point in enumerate(segment.points):
                point_objs.append({
                    'point_num': idx,
                    'coord': [point.latitude, point.longitude],
                    'timestamp': point.time.strftime("%I:%M:%S"),
                    'elevation': point.elevation
                })
                coordinates.append((point.latitude, point.longitude))
                timestamps.append(point.time)
                elevations.append(point.elevation)
    
    return {
        'points': point_objs,
        'coordinates': coordinates,
        'timestamps': timestamps,
        'elevations': elevations,
        'gpx': gpx
    }

# ===== SECTION 4: VALIDATION FUNCTIONS =====
# Check data for anomalies

def calculate_segment_data(coordinates, timestamps):
    """
    For each segment between consecutive points, calculate distance, time, and speed.
    
    Returns:
        dict with keys: 'distances', 'speeds', 'timedeltas'
    """
    segment_distances = []
    segment_speeds = []
    timedeltas = []
    
    for i in range(len(coordinates) - 1):
        dist = haversine_dist(coordinates[i][0], coordinates[i][1], coordinates[i+1][0], coordinates[i+1][1])
        segment_distances.append(dist)
        
        dt = (timestamps[i+1] - timestamps[i]).total_seconds()
        timedeltas.append(dt)
        
        speed = dist / dt if dt > 0 else 0
        segment_speeds.append(speed)
    
    return {
        'distances': segment_distances,
        'speeds': segment_speeds,
        'timedeltas': timedeltas
    }

def check_speed_anomalies(segment_speeds, threshold_mps=22):
    """
    Flag segments where speed exceeds threshold (default 22 m/s ≈ 79 km/h).
    
    Args:
        segment_speeds: list of speeds in m/s
        threshold_mps: max plausible speed in meters per second
    
    Returns:
        list of dicts with keys: 'segment_idx', 'speed_mps', 'speed_kmh'
    """
    anomalies = []
    for idx, speed in enumerate(segment_speeds):
        if speed >= threshold_mps:
            anomalies.append({
                'segment_idx': idx,
                'speed_mps': speed,
                'speed_kmh': speed * 3.6
            })
    return anomalies

def check_self_intersections(line):
    """Find points where the track crosses itself."""
    if line.is_simple:
        print("Clean path!")
        return []

    print("Intersection detected!")
    intrsec_pts = []
    coords = list(line.coords)

    for i in range(len(coords) - 1):
        seg1 = LineString([coords[i], coords[i+1]])
        for j in range(i + 2, len(coords) - 1):
            seg2 = LineString([coords[j], coords[j+1]])
            if seg1.intersects(seg2):
                inter = seg1.intersection(seg2)
                if inter.geom_type == 'Point':
                    intrsec_pts.append(inter.coords[0])
                elif inter.geom_type == 'MultiPoint':
                    for pt in inter.geoms:
                        intrsec_pts.append(pt.coords[0])
                else:
                    xs, ys = inter.xy
                    for x, y in zip(xs, ys):
                        intrsec_pts.append((x, y))

    print(f"Found {len(intrsec_pts)} intersection(s):", intrsec_pts)
    return intrsec_pts

# ===== SECTION 5: VISUALIZATION =====
# Create the map and add markers

def create_base_map(coordinates):
    """Create a folium map centered on the track."""
    center_lat = sum([c[0] for c in coordinates]) / len(coordinates)
    center_lon = sum([c[1] for c in coordinates]) / len(coordinates)
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
    return m

def add_track_to_map(m, coordinates):
    """Draw the bike track as a polyline."""
    folium.PolyLine(
        locations=coordinates,
        color="#1FC5B7",
        weight=5,
        tooltip="Blue Hills Bike Track",
        smooth_factor=8
    ).add_to(m)

def add_checkpoints_to_map(m, coordinates, interval=10):
    """Add numbered markers every N points."""
    custom_icon = folium.CustomIcon(
    icon_image="assets/person-biking-solid.png",
    icon_size=[25, 25]                 
    )
    for idx in range(0, len(coordinates), interval):
        if idx < len(coordinates):
            folium.Marker(
                coordinates[idx],
                icon=custom_icon,
                popup=f"Checkpoint: {idx}",
            ).add_to(m)

def add_intersections_to_map(m, intrsec_pts):
    """Mark intersection points with red circles."""
    for idx, pt in enumerate(intrsec_pts):
        folium.CircleMarker(
            location=pt,
            popup="Intersection!",
            color="#ED0808",
            fill=True,
            fill_color="red",
            opacity=4,
            radius=8
        ).add_to(m)

def add_speed_anomalies_to_map(m, coordinates, anomaly_indices):
    """Mark segments with speed anomalies in orange."""
    for idx in anomaly_indices:
        if idx < len(coordinates):
            folium.CircleMarker(
                location=coordinates[idx],
                popup=f"Speed anomaly at segment {idx}",
                color="#FFA500",
                fill=True,
                fill_color="orange",
                opacity=4,
                radius=8
            ).add_to(m)

def save_map(m, output_file):
    """Save map to HTML file."""
    m.save(output_file)

# ===== SECTION 6: MAIN WORKFLOW =====

if __name__ == "__main__":
    # Parse and extract
    gpx = parse_gpx(file_path)
    data = extract_points_from_gpx(gpx)
    
    coordinates = data['coordinates']
    timestamps = data['timestamps']
    
    # Calculate segment metrics
    segment_data = calculate_segment_data(coordinates, timestamps)
    
    # Validate
    speed_anomalies = check_speed_anomalies(segment_data['speeds'], threshold_mps=22)
    speed_indices = [a['segment_idx'] for a in speed_anomalies]
    
    # Intersections
    path_line = LineString([(lat, lon) for lat, lon in coordinates])
    intrsec_pts = check_self_intersections(path_line)
    intrsec_pts = nonduplicate_intersections(intrsec_pts, precision=5)
    
    # Visualize
    m = create_base_map(coordinates)
    add_track_to_map(m, coordinates)
    add_checkpoints_to_map(m, coordinates, interval=100)
    add_intersections_to_map(m, intrsec_pts)
    add_speed_anomalies_to_map(m, coordinates, speed_indices)
    save_map(m, output_file)
    
    # Print results
    print(f"Track analysis complete.")
    print(f"Speed anomalies: {len(speed_anomalies)}")
    print(f"Self-intersections: {len(intrsec_pts)}")