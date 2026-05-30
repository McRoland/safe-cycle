import shapely 
from shapely.geometry import LineString, MultiLineString, MultiPoint, mapping
import pandas as pd
import geopandas as gpd
import gpxpy
import pytest 
import json
import folium
from math import radians, cos, sin, asin, sqrt
from haversine import haversine
from datetime import datetime


# ------- Haversine distance func ------

def haversine_dist(lat1, lon1, lat2, lon2):

    coord1 = [lat1, lon1]
    coord2 = [lat2, lon2]
    distance = haversine(coord1, coord2) * 1000
    
    
    return distance

# ------ Parsing and gathering info ------

file_path = '/Users/fluxboi/Safe-Cycle/blue_hills.gpx'
# print(file_path)
output_file = "path_map.html"

def parse_and_map(): 
    
    with open(file_path, 'r') as gf:
        gpx = gpxpy.parse(gf)
    # print(gpx)

    
    # Collect all points
    point_objs = []
    coordinates = []
    timestamps = []
    elevations = []

    for track in gpx.tracks:
        for segment in track.segments:
            for idx, point in enumerate(segment.points):
                point_objs.append({
                    'point_num': str(idx),
                    'coord': str([point.latitude, point.longitude]),
                    'timestamp': point.time.strftime("%I:%M:%S"),
                    'elevation': str(point.elevation)

                })
                coordinates.append((point.latitude, point.longitude))
                timestamps.append(point.time)  # datetime obj so i can subtract another and create a timedelta (time difference and quotient)
                elevations.append(point.elevation)
    
    # Calculate segments
    segment_distances = []
    segment_speeds = []
    timedeltas = []
    
    for i in range(len(coordinates)-1):
        # Distance
        dist = haversine_dist(coordinates[i][0], coordinates[i][1],
                             coordinates[i+1][0], coordinates[i+1][1])
        segment_distances.append(dist)
        
        # Time difference
        dt = (timestamps[i+1] - timestamps[i]).total_seconds()
        timedeltas.append(dt)
        
        # Speed (meters per second, convert to km/h if desired)
        speed = dist / dt if dt > 0 else 0
        segment_speeds.append(speed)
    
    # print(segment_distances, segment_speeds, point_objs)
    # print(f"The total distance is {total_dist:.2f} meters.")


# ------ Mapping out the coordinates ------
    center_lat = sum([c[0] for c in coordinates]) / len(coordinates) #formula for center of polyline for map
    center_lon = sum([c[1] for c in coordinates]) / len(coordinates)
    path_line = LineString([(lat, lon) for lat, lon in coordinates])
    # print(path_line)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    folium.PolyLine(
        locations=coordinates,
        color="#1FC5B7",
        weight=5,
        tooltip="Blue Hills Bike Track",
        smooth_factor=8
        ).add_to(m)
    

    for track in gpx.tracks:
        for segment in track.segments:
            for idx, point in enumerate(segment.points):
                if (idx + 1) % 10 == 0:
                    folium.Marker(
                        coordinates[idx],
                        popup= f"Checkpoint: {idx}",
                    ).add_to(m)
    


    return [path_line, coordinates, timestamps, segment_speeds, timedeltas, point_objs, gpx, m]

[path_line, coordinates, timestamps, segment_speeds, timedeltas, point_objs, gpx, m] = parse_and_map()

# print(coordinates)
# Check for self intersections
def check_self_intersections(line):
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

intrsec_pts = check_self_intersections(path_line)
# test_line = LineString([(0,0),(2,2),(2,0),(0,2),(0,0)])
# assert len(check_self_intersections(None, path_line)) > 0
# print("test passed")
def nonduplicate_intersections(intrsec_pts, precision=5):
    seen = set()
    unique = []
    for pt in intrsec_pts:
        rounded = (round(pt[0], precision), round(pt[1], precision))
        if rounded not in seen:
            seen.add(rounded)
            unique.append(rounded)
    return unique
intrsec_pts = nonduplicate_intersections(intrsec_pts, precision=5)

def map_validations(intrsec_pts):
    for idx, pt in enumerate(intrsec_pts):
        folium.CircleMarker(
            location= intrsec_pts[idx],
            popup="Intersection!",
            color="#ED0808"
        ).add_to(m)

    m.save(output_file)
map_validations(intrsec_pts)











# Check for speed plausibility
# def check_for_speed():
    # for speed in segment_speeds:
        # for dt in timedeltas:
# 
    # return


    




