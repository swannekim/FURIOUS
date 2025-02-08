from flask import Flask, jsonify, request, make_response
from flask_cors import CORS

import pandas as pd
from datetime import datetime, timedelta
import json
from functools import lru_cache

from calculation_cri import ship_ids, load_geojson_selected, ownship_ellipses, find_three_closest_ships, compute_vo_region, compute_v_region, compute_tcr, compute_tcpa, compute_vo_cri

# app instance
app = Flask(__name__)
CORS(app) # allows port 8080 in use


file_mapping = {
    'passenger': 'passenger_resample10T_ver03',
    'cargo': 'cargo_resample10T_ver04',
}
    
@app.route('/load_geojson_data_selected', methods=['GET'])
def load_geojson_data_selected():
    ship_type = request.args.get('shipType')
    datetime_str = request.args.get('datetime')
    print(f"Received ship_type: {ship_type}")
    print(f"Received datetime: {datetime_str}")
    
    if not ship_type:
        return jsonify({"error": "shipType parameter is missing"}), 400

    file_name = file_mapping.get(ship_type)
    if not file_name:
        return jsonify({"error": f"No file mapping found for ship_type: {ship_type}"}), 400

    try:
        print(f"Loading file for getting data: {file_name}")
        result = load_geojson_selected(file_name, datetime_str)
        print(f"Filtered data loaded successfully!")
        return make_response(json.dumps(result, indent=2), 200, {'Content-Type': 'application/json'})
    
    except ValueError as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@lru_cache(maxsize=128)
def cached_ship_ids(file_name):
    return ship_ids(file_name)

@app.route('/get_ship_ids', methods=['GET'])
def get_ship_ids():
    ship_type = request.args.get('shipType')
    print(f"Received ship_type: {ship_type}")
    
    if not ship_type:
        return jsonify({"error": "shipType parameter is missing"}), 400

    file_name = file_mapping.get(ship_type)
    if not file_name:
        return jsonify({"error": f"No file mapping found for ship_type: {ship_type}"}), 400

    try:
        print(f"Loading file for getting ship ids: {file_name}")
        result = cached_ship_ids(file_name)
        print(f"Getting ship ids Success!")
        return jsonify(result)
    
    except ValueError as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@lru_cache(maxsize=256)
def cached_compute_vo_region(file_name, target_ship_ids, date_time, time_length):
    return compute_vo_region(file_name, target_ship_ids, date_time, time_length)

@lru_cache(maxsize=256)
def cached_compute_v_region(file_name, ship_id, date_time, time_length):
    return compute_v_region(file_name, ship_id, date_time, time_length)

@app.route("/os_domain", methods=['POST'])
def os_domain():
    try:
        data = request.json
        print("Received data:", data)

        ship_type = data.get('shipType')
        file_name = file_mapping.get(ship_type)

        ship_id = data.get('shipId')
        date_time = data.get('datetime')
        time_length = int(data.get('timeLength', 30))
        print(file_name, ship_id, date_time, time_length)
        
        result = ownship_ellipses(file_name, ship_id, date_time, time_length)
        return make_response(json.dumps(result, indent=2), 200, {'Content-Type': 'application/json'})
    
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400

@app.route("/computation", methods=['POST'])
def computation():

    data = request.json
    print("Received data:", data)

    ship_type = data.get('shipType')
    file_name = file_mapping.get(ship_type)

    ship_id = data.get('shipId')
    date_time = data.get('datetime')
    time_length = int(data.get('timeLength', 30))

    target_ship_ids = data.get('selectedTsIds')

    # If no target ships are selected, find the 3 closest ships
    if not target_ship_ids:
        print("No target ships selected. Finding the three closest ships...")
        closest_ships = find_three_closest_ships(file_name, ship_id, date_time)
        target_ship_ids = [ship['properties']['SHIP_ID'] for ship in closest_ships]
        print("Closest ships selected as targets:", target_ship_ids)
    target_ship_ids = tuple(target_ship_ids)

    print("==== computing vo region =====")
    vo_region, vo_geojson = cached_compute_vo_region(file_name, target_ship_ids, date_time, time_length)
    print("===== computing v region =====")
    v_region, v_geojson = cached_compute_v_region(file_name, ship_id, date_time, time_length)

    print("===== computing tcr =====")
    tcr, vo_area, v_area = compute_tcr(vo_region, v_region, vo_geojson, v_geojson)
    print("===== computing tcpa =====")
    tcpa = compute_tcpa(file_name, ship_id, date_time, target_ship_ids)

    print("===== computing cri =====")
    cri = compute_vo_cri(tcr, tcpa, date_time, time_length)

    result = [round(vo_area, 5), round(v_area, 5), round(cri, 5), round(tcr, 7), round(tcpa, 5)]
    print("computation result: ", result)

    return jsonify(result)

@app.route("/computation_vo", methods=['POST'])
def computation_vo():
    try:
        data = request.json
        print("Received data:", data) 
        ship_id = data.get('shipId')
        ship_type = data.get('shipType')
        file_name = file_mapping.get(ship_type)

        date_time = data.get('datetime')
        time_length = int(data.get('timeLength', 30))

        target_ship_ids = data.get('selectedTsIds')
        # If no target ships are selected, find the 3 closest ships
        if not target_ship_ids:
            print("No target ships selected. Finding the three closest ships...")
            closest_ships = find_three_closest_ships(file_name, ship_id, date_time)
            target_ship_ids = [ship['properties']['SHIP_ID'] for ship in closest_ships]
            print("Closest ships selected as targets:", target_ship_ids)
        target_ship_ids = tuple(target_ship_ids)

        vo_region, vo_geojson = cached_compute_vo_region(file_name, target_ship_ids, date_time, time_length)
        print("Velocity Obstacle region Geojson calculated", vo_geojson)

        return make_response(json.dumps(vo_geojson, indent=2), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400

@app.route("/computation_v", methods=['POST'])
def computation_v():
    try:
        data = request.json
        print("Received data:", data)

        ship_type = data.get('shipType')
        file_name = file_mapping.get(ship_type)

        ship_id = data.get('shipId')
        date_time = data.get('datetime')
        time_length = int(data.get('timeLength', 30))

        v_region, v_geojson = cached_compute_v_region(file_name, ship_id, date_time, time_length)
        print("Velocity region Geojson calculated", v_geojson)

        return make_response(json.dumps(v_geojson, indent=2), 200, {'Content-Type': 'application/json'})
    
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400


# app running
if __name__ == "__main__":
    app.run(debug=True, port=8080) # dev mode
    # app.run() # deploy production mode