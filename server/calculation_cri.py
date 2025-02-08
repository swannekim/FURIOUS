import json
from geojson import Feature, FeatureCollection
from datetime import datetime, timedelta
from geopy.distance import geodesic
import numpy as np
from shapely.geometry import Point, mapping, shape, Polygon, GeometryCollection
from shapely.ops import unary_union
from shapely.affinity import rotate
from shapely.ops import transform
from pyproj import Transformer

def ship_ids(filename):
    geojson_data_path = './testdata/' + filename + '.geojson'
    try:
        with open(geojson_data_path, 'r') as file:
            data = json.load(file)
            ship_ids = sorted({feature['properties']['SHIP_ID'] for feature in data['features']})
        return ship_ids
    except Exception as e:
        raise ValueError(f"An error occurred while loading the GeoJSON data and retrieving ids: {e}")
    
def load_geojson_selected(filename, recptn_dt_str):
    geojson_data_path = './testdata/' + filename + '.geojson'
    try:
        with open(geojson_data_path, 'r') as file:
            data = json.load(file)
            if recptn_dt_str:
                try:
                    if recptn_dt_str.endswith('Z'):
                        recptn_dt_str = recptn_dt_str[:-5]
                    recptn_dt = datetime.fromisoformat(recptn_dt_str)
                    time_filtered_features = [
                        feature for feature in data['features']
                        if datetime.fromisoformat(feature['properties']['RECPTN_DT']) == recptn_dt
                    ]
                    data['features'] = time_filtered_features
                    print(f"Filtered features count: {len(time_filtered_features)}")
                except ValueError as e:
                    raise ValueError(f"Invalid datetime format: {e}")
        return data
    except ValueError as e:
        raise ValueError(f"An error occurred while loading the GeoJSON data: {e}")

def load_geojson_timewindow(filename, ship_id, recptn_dt_str, time_length):
    geojson_data_path = './testdata/' + filename + '.geojson'
    try:
        with open(geojson_data_path, 'r') as file:
            geojson_data = json.load(file)
        print("GeoJSON file loaded!")

        if recptn_dt_str.endswith('Z'):
            recptn_dt_str = recptn_dt_str[:-5]
        recptn_dt = datetime.fromisoformat(recptn_dt_str)
        end_time = recptn_dt + timedelta(minutes=time_length)
        print("time window: ", recptn_dt, " ~ ", end_time)

        time_window_features = [
            feature for feature in geojson_data['features']
            if str(feature['properties']['SHIP_ID']) == str(ship_id)
            and recptn_dt <= datetime.fromisoformat(feature['properties']['RECPTN_DT']) <= end_time
        ]
        print(f"Filtered features count: {len(time_window_features)}")

        if not time_window_features:
            return {"error": f"No data found for Ship ID {ship_id} within the time window {recptn_dt} to {end_time}."}
        
        return time_window_features

    except Exception as e:
        raise ValueError(f"An error occurred while loading the GeoJSON data: {e}")
    
def load_geojson_selected_time(filename, ship_id, recptn_dt_str, time_length):
    geojson_data_path = '../server/testdata/' + filename + '.geojson'
    try:
        with open(geojson_data_path, 'r') as file:
            data = json.load(file)
            if recptn_dt_str:
                try:
                    if recptn_dt_str.endswith('Z'):
                        recptn_dt_str = recptn_dt_str[:-5]
                    recptn_dt = datetime.fromisoformat(recptn_dt_str)
                    end_time = recptn_dt + timedelta(minutes=time_length)
                    time_filtered_features = [
                        feature for feature in data['features']
                        if str(feature['properties']['SHIP_ID']) == str(ship_id)
                        and datetime.fromisoformat(feature['properties']['RECPTN_DT']) == end_time
                    ]
                    data['features'] = time_filtered_features
                    print(f"Filtered features count: {len(time_filtered_features)}")
                except ValueError as e:
                    raise ValueError(f"Invalid datetime format: {e}")
        return data
    except ValueError as e:
        raise ValueError(f"An error occurred while loading the GeoJSON data: {e}")

def find_closest_ship(filename, own_ship_id, recptn_dt, target_ship_ids=None):
    geojson_data = load_geojson_selected(filename, recptn_dt)
    print("GeoJSON data loaded!")

    own_ship = None
    target_ships = []

    recptn_dt = datetime.strptime(recptn_dt, '%Y-%m-%dT%H:%M:%S')

    for feature in geojson_data['features']:
        ship_id = feature['properties']['SHIP_ID']
        timestamp = datetime.strptime(feature['properties']['RECPTN_DT'], '%Y-%m-%dT%H:%M:%S')

        if str(ship_id) == str(own_ship_id) and timestamp == recptn_dt:
            own_ship = feature
        elif not target_ship_ids or str(ship_id) in map(str, target_ship_ids):
            target_ships.append(feature)

    if not own_ship:
        raise ValueError("Own ship not found at the given datetime")

    own_ship_coords = (own_ship['geometry']['coordinates'][1], own_ship['geometry']['coordinates'][0])  # (latitude, longitude)
    print("Own ship coordinates:", own_ship_coords)

    closest_ship = None

    # Case 1: No target ship IDs provided, find the closest ship among all target_ships
    if not target_ship_ids:
        if target_ships:
            closest_ship = min(
                target_ships,
                key=lambda s: geodesic(own_ship_coords, (s['geometry']['coordinates'][1], s['geometry']['coordinates'][0])).meters
            )
        else:
            print("Error: No target ships found in the dataset.")
            raise ValueError("No target ships found.")

    # Case 2: Exactly one target ship ID provided, retrieve its feature
    elif len(target_ship_ids) == 1:
        target_ship_id = str(target_ship_ids[0])
        closest_ship = next(
            (ship for ship in target_ships if str(ship['properties']['SHIP_ID']) == target_ship_id),
            None
        )
        if closest_ship is None:
            print(f"Error: Target ship with ID {target_ship_id} not found in the dataset.")
            raise ValueError(f"Target ship with ID {target_ship_id} not found.")

    # Case 3: Multiple target ship IDs provided, find the closest one
    else:
        filtered_ships = [ship for ship in target_ships if str(ship['properties']['SHIP_ID']) in map(str, target_ship_ids)]
        
        if not filtered_ships:
            print("Error: None of the provided target ship IDs exist in the dataset.")
            raise ValueError("No matching target ships found for the given target_ship_ids.")

        closest_ship = min(
            filtered_ships,
            key=lambda s: geodesic(own_ship_coords, (s['geometry']['coordinates'][1], s['geometry']['coordinates'][0])).meters
        )

    print("Selected target ship coordinates:", closest_ship['geometry']['coordinates'])
    return own_ship, closest_ship

def find_three_closest_ships(filename, own_ship_id, recptn_dt_str):
    if recptn_dt_str.endswith('Z'):
        recptn_dt_str = recptn_dt_str[:-5]

    geojson_data = load_geojson_selected(filename, recptn_dt_str)
    print("GeoJSON data loaded!")

    own_ship = None
    target_ships = []

    recptn_dt = datetime.strptime(recptn_dt_str, '%Y-%m-%dT%H:%M:%S')

    for feature in geojson_data['features']:
        ship_id = feature['properties']['SHIP_ID']
        timestamp = datetime.strptime(feature['properties']['RECPTN_DT'], '%Y-%m-%dT%H:%M:%S')
        
        if str(ship_id) == str(own_ship_id) and timestamp == recptn_dt:
            own_ship = feature
        else:
            target_ships.append(feature)

    if not own_ship:
        raise ValueError("Own ship not found at the given datetime")

    own_ship_coords = (own_ship['geometry']['coordinates'][1], own_ship['geometry']['coordinates'][0])  # (latitude, longitude)
    print("Own ship coordinates:", own_ship_coords)

    sorted_ships = sorted(
        target_ships,
        key=lambda s: geodesic(
            own_ship_coords,
            (s['geometry']['coordinates'][1], s['geometry']['coordinates'][0])
        ).meters
    )

    three_closest_ships = sorted_ships[:3]
    print("Three closest ships found.")

    return three_closest_ships

def determine_encounter_mode(own_ship, target_ship):
    own_cog = own_ship['properties']['COG']
    relative_bearing = (own_cog - target_ship['properties']['COG']) % 360
    
    if 112.5 <= relative_bearing < 247.5:
        return 'overtaking'
    elif 5 <= relative_bearing < 112.5 or 247.5 <= relative_bearing < 355:
        return 'crossing'
    else:
        return 'head_on'

def compute_k_factors(L, v):
    k_AD = L * np.exp(0.3591 * np.log(v) + 0.0952)
    k_DT = L * np.exp(0.5441 * np.log(v) - 0.0795)
    return k_AD, k_DT

def compute_R_factors(L, k_AD, k_DT, s):
    R_fore = (L + (1 + s) * 0.67 * np.sqrt(k_AD**2 + (k_DT / 2)**2))
    R_aft = (L + 0.67 * np.sqrt(k_AD**2 + (k_DT / 2)**2))
    R_starb = (0.2 + k_DT) * L
    R_port = (0.2 + 0.75 * k_DT) * L
    return R_fore, R_aft, R_starb, R_port

def calculate_alpha(own_ship_position, target_ship_position, own_ship_cog):
    dx = target_ship_position[0] - own_ship_position[0]
    dy = target_ship_position[1] - own_ship_position[1]
    relative_bearing = np.arctan2(dy, dx)
    
    own_ship_cog_rad = np.deg2rad(own_ship_cog)
    alpha = relative_bearing - own_ship_cog_rad
    return alpha

def create_ellipse(filename, own_ship_id, recptn_dt, target_ship_ids=None, mode=None):
    KNOTS_TO_MPS = 0.514444
    METER_TO_DEGREES = 1 / 111320

    target_ship_ids = target_ship_ids
    own_ship_feature, target_ship_feature = find_closest_ship(filename, own_ship_id, recptn_dt, target_ship_ids)

    own_ship_position = own_ship_feature['geometry']['coordinates']
    own_ship_cog = own_ship_feature['properties']['COG']
    target_ship_position = target_ship_feature['geometry']['coordinates']

    L = own_ship_feature['properties']['LEN_PRED']
    v = own_ship_feature['properties']['SOG'] * KNOTS_TO_MPS
    vt = target_ship_feature['properties']['SOG'] * KNOTS_TO_MPS
    
    k_AD, k_DT = compute_k_factors(L, v)
    
    alpha = calculate_alpha(own_ship_position, target_ship_position, own_ship_cog)
    
    mode = determine_encounter_mode(own_ship_feature, target_ship_feature)
    print(mode)
    
    if mode == 'head_on':
        s = 2 - (v - vt) / v
    elif mode == 'crossing':
        s = 2 - alpha / np.pi
    elif mode == 'overtaking':
        s = 1
    else:
        raise ValueError("Invalid mode. Choose from 'head_on', 'crossing', or 'overtaking'.")
    
    R_fore, R_aft, R_starb, R_port = compute_R_factors(L, k_AD, k_DT, s)
    print("fore: ", R_fore, ", aft: ", R_aft, ", starb: ", R_starb, ", port: ", R_port)

    a = (abs(R_fore) + abs(R_aft)) / 2
    b = (abs(R_starb) + abs(R_port)) / 2
    
    delta_a = abs(R_fore) - a
    delta_b = abs(R_starb) - b
    
    lat = own_ship_position[1]
    a_deg = a * METER_TO_DEGREES / np.cos(np.radians(lat))
    b_deg = b * METER_TO_DEGREES / np.cos(np.radians(lat))
    delta_a_deg = delta_a * METER_TO_DEGREES / np.cos(np.radians(lat))
    delta_b_deg = delta_b * METER_TO_DEGREES / np.cos(np.radians(lat))

    v_deg = v * METER_TO_DEGREES / np.cos(np.radians(lat))
    vt_deg = vt * METER_TO_DEGREES / np.cos(np.radians(lat))

    ellipse = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[]]
        },
        "properties": {
            "angle": own_ship_cog,
            "mode": mode
        }
    }
    
    num_points = 100
    cog_rad = np.radians(own_ship_cog)


    for i in range(num_points):
        theta = 2.0 * np.pi * float(i) / float(num_points)
        x = a_deg * np.cos(theta)
        y = b_deg * np.sin(theta)
        
        x_rot = x * np.cos(cog_rad) - y * np.sin(cog_rad)
        y_rot = x * np.sin(cog_rad) + y * np.cos(cog_rad)

        ellipse["geometry"]["coordinates"][0].append([
            own_ship_position[0] + x_rot - delta_a_deg,
            own_ship_position[1] + y_rot - delta_b_deg
        ])
    
    ellipse["geometry"]["coordinates"][0].append(ellipse["geometry"]["coordinates"][0][0])
    
    return ellipse


def ownship_ellipses(filename, ship_id, recptn_dt_str, time_length=30):
    timewindow_features = load_geojson_timewindow(filename, ship_id, recptn_dt_str, time_length)

    features = []
    own_ship_id = ship_id

    for feature in timewindow_features:
        recptn_dt = feature['properties']['RECPTN_DT']
        ship_position = Point(feature['geometry']['coordinates'])
        cog = feature['properties']['COG']

        ellipse = create_ellipse(filename, own_ship_id, recptn_dt, target_ship_ids=None, mode=None)
        features.append(ellipse)

        encounter_mode = ellipse['properties']['mode']

        features.append({
            "type": "Feature",
            "geometry": mapping(ship_position),
            "properties": {
                "SHIP_ID": ship_id,
                "COG": cog,
                "MODE": encounter_mode
            }
        })

    output = {
        "type": "FeatureCollection",
        "features": features
    }

    print(output)

    return output

def compute_vo_region(filename, ship_ids, recptn_dt_str, time_length=30):
    vo_regions = []
    features = []

    if recptn_dt_str.endswith('Z'):
        recptn_dt_str = recptn_dt_str[:-5]

    for ship_id in ship_ids:
        timewindow_features = load_geojson_timewindow(filename, ship_id, recptn_dt_str, time_length)

        ellipses = []

        for feature in timewindow_features:
            print(f"Feature: {feature}")
            print(f"Feature Type: {type(feature)}")

            recptn_dt = feature['properties']['RECPTN_DT']
            ellipse_data = create_ellipse(filename, ship_id, recptn_dt, target_ship_ids=None, mode=None)
            ellipse = shape(ellipse_data['geometry'])
            ellipses.append(ellipse)

        merged_shape = unary_union(ellipses)

        if merged_shape.geom_type == 'MultiPolygon':
            merged_shape = merged_shape.convex_hull
            print("Convex Hull: Make single ship VO region")

        vo_region_single = merged_shape.buffer(0.005).buffer(-0.001)
        vo_regions.append(vo_region_single)

        feature_with_id = Feature(geometry=mapping(vo_region_single), properties={"ship_id": ship_id})
        print("Single VO region feature: ", feature_with_id)
        features.append(feature_with_id)

    if vo_regions:
        vo_region = unary_union(vo_regions)
        print("Convex Hull: Make multiple ships VO region")
    else:
        vo_region = None
    
    vo_geojson = FeatureCollection(features)
        
    return vo_region, vo_geojson

def compute_v_region(filename, own_ship_id, recptn_dt_str, time_length=30):
    geojson_data = load_geojson_selected_time(filename, own_ship_id, recptn_dt_str, 0)
    print("geojson data loaded!")

    METER_TO_DEGREES = 1 / 111320
    
    feature = geojson_data['features'][0]
    v = feature['properties']['SOG']
    own_ship_cog = feature['properties']['COG']
    own_ship_position = feature['geometry']['coordinates']

    # 1 knot = 0.51444 meters per second
    v_mps = np.log(v) * 0.51444
    
    distance_m = time_length * 60 * v_mps
    distance_deg_lon = distance_m / 111319.9
    distance_deg_lat = distance_m / 110574.0

    x_center = own_ship_position[0]
    y_center = own_ship_position[1]

    angles = np.linspace(0, np.pi, 100)
    x = x_center + distance_deg_lon * np.cos(angles)
    y = y_center + distance_deg_lat * np.sin(angles)
    
    coordinates = list(zip(x, y))
    
    coordinates.append(own_ship_position)
    
    v_region = Polygon(coordinates)
    v_region = rotate(v_region, own_ship_cog - 90, origin=(x_center, y_center))

    v_geojson = Feature(geometry=mapping(v_region), properties={"ship_id": own_ship_id})
    
    return v_region, v_geojson

def compute_tcr(vo_region, v_region, vo_geojson, v_geojson):
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    
    def transform_to_meters(geometry):
        return transform(transformer.transform, geometry)
    
    def calculate_area_km2(geojson_obj):
        if geojson_obj['type'] == 'FeatureCollection':
            geometries = [shape(feature['geometry']) for feature in geojson_obj['features']]
            geometry = GeometryCollection(geometries)
        elif geojson_obj['type'] == 'Feature':
            geometry = shape(geojson_obj['geometry'])
        else:
            geometry = shape(geojson_obj)

        geometry_meters = transform_to_meters(geometry)
        area_m2 = geometry_meters.area
        return area_m2 / 1e6
    
    vo_area = calculate_area_km2(vo_geojson)
    v_area = calculate_area_km2(v_geojson)
    
    intersection_geometry = vo_region.intersection(v_region)
    intersection_geometry_meters = transform_to_meters(intersection_geometry)
    intersection_area = intersection_geometry_meters.area / 1e6
    
    if intersection_area > v_area:
        print("Warning: Intersection area is greater than V area, which indicates a precision issue.")
        intersection_area = min(intersection_area, v_area)
    
    tcr = intersection_area / v_area
    return tcr, vo_area, v_area

def compute_tcpa(filename, own_ship_id, recptn_dt_str, target_ship_ids=None):
    KNOTS_TO_MPS = 0.514444
    DEGREES_TO_METERS = 111139

    if recptn_dt_str.endswith('Z'):
        recptn_dt_str = recptn_dt_str[:-5]
    
    target_ship_ids = target_ship_ids
    own_ship_feature, target_ship_feature = find_closest_ship(filename, own_ship_id, recptn_dt_str, target_ship_ids)

    own_ship_position = own_ship_feature['geometry']['coordinates']
    own_ship_cog = own_ship_feature['properties']['COG']
    target_ship_position = target_ship_feature['geometry']['coordinates']
    target_ship_cog = target_ship_feature['properties']['COG']

    v = own_ship_feature['properties']['SOG'] * KNOTS_TO_MPS
    vt = target_ship_feature['properties']['SOG'] * KNOTS_TO_MPS

    dx = target_ship_position[0] - own_ship_position[0]
    dy = target_ship_position[1] - own_ship_position[1]
    distance = np.sqrt(dx**2 + dy**2)

    distance_m = distance * DEGREES_TO_METERS

    v_x = v * np.cos(np.deg2rad(own_ship_cog))
    v_y = v * np.sin(np.deg2rad(own_ship_cog))
    vt_x = vt * np.cos(np.deg2rad(target_ship_cog))
    vt_y = vt * np.sin(np.deg2rad(target_ship_cog))

    relative_velocity_x = v_x - vt_x
    relative_velocity_y = v_y - vt_y
    relative_velocity = np.sqrt(relative_velocity_x**2 + relative_velocity_y**2)

    alpha = calculate_alpha(own_ship_position, target_ship_position, own_ship_cog)
    tcpa_sec = distance_m * np.cos(alpha - np.pi) / relative_velocity

    tcpa = tcpa_sec / 60

    return tcpa

def compute_vo_cri(tcr, tcpa, t1, time_length=30):
    if t1.endswith('Z'):
        t1 = t1[:-5]
    t1 = datetime.fromisoformat(t1)
    t2 = t1 + timedelta(minutes=time_length)
    
    tcpa_seconds = tcpa * 60
    
    if tcpa_seconds < 0:
        tcpa_prime = 1
    elif tcpa_seconds > (t2 - t1).total_seconds():
        tcpa_prime = 0
    else:
        tcpa_prime = (t2 - t1 - timedelta(seconds=tcpa_seconds)) / (t2 - t1)
    
    return tcr * tcpa_prime
