import os

import requests
from flask import render_template, request, jsonify, send_file
from flask_login import current_user, login_required
from geopy.distance import geodesic
from matplotlib import pyplot as plt
import io
from datetime import timedelta, datetime
import geopandas as gpd

from __init__ import app, db, PNG_PATH
from avalanche_statistics import distance_avalanche, count_avalanches_in_radius
from models import Marker, Route, AvalancheMarker
from routes import plan_route, get_elevation, get_routes_to_json

if not os.path.exists("static/hiking_trails.geojson"):
    get_routes_to_json()

@app.route('/api/markers', methods=['POST'])
@login_required
def add_marker():
    try:
        data = request.json
        new_marker = Marker(
            user_id=current_user.id,
            name=data['name'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            description=data.get('description', '')
        )
        db.session.add(new_marker)
        db.session.commit()
        return jsonify({'message': 'Marker added successfully', 'id': new_marker.id}), 201
    except Exception as e:
        db.session.rollback()
        print("Error adding marker:", str(e))
        return jsonify({'error': 'Server error: ' + str(e)}), 500


@app.route('/api/routes', methods=['POST'])
@login_required
def add_route():
    data = request.get_json()
    new_route = Route(
        user_id=current_user.id,
        name=data['name'],
        description=data.get('description', ''),
        waypoints=data['waypoints']
    )
    db.session.add(new_route)
    db.session.commit()
    return jsonify({'message': 'Route added successfully'}), 201


@app.route('/api/routes/<int:route_id>', methods=['DELETE'])
@login_required
def delete_route(route_id):
    route = Route.query.get(route_id)
    if not route or route.user_id != current_user.id:
        return jsonify({'error': 'Brak dostępu lub trasa nie istnieje'}), 404

    db.session.delete(route)
    db.session.commit()
    return jsonify({'message': 'Trasa usunięta'})


@app.route('/api/markers', methods=['GET'])
@login_required
def get_markers():
    markers = Marker.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'latitude': m.latitude,
        'longitude': m.longitude,
        'description': m.description
    } for m in markers])


@app.route('/api/routes', methods=['GET'])
@login_required
def get_routes():
    routes = Route.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'waypoints': r.waypoints,
        'description': r.description
    } for r in routes])


@app.route('/api/markers/<int:marker_id>', methods=['DELETE'])
@login_required
def delete_marker(marker_id):
    marker = Marker.query.get(marker_id)
    if not marker or marker.user_id != current_user.id:
        return jsonify({'error': 'Marker not found or unauthorized'}), 404
    db.session.delete(marker)
    db.session.commit()
    return jsonify({'message': 'Marker deleted successfully'})


@app.route("/api/szlaki")
def get_trails():
    szlaki = gpd.read_file("static/hiking_trails.geojson")
    return jsonify(szlaki.__geo_interface__)

@app.route("/search_peak", methods=["GET"])
def search_peak():
    peak_name = request.args.get("q")

    if not peak_name:
        return jsonify({"error": "Brak nazwy szczytu"}), 400

    # Nominatium  OpenStreetMap API
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={peak_name}&featuretype=peak"
    headers = {"User-Agent": "Tu mozna wpisac doslownie dowolna rzecz i bedzie dzialac"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "Błąd połączenia z Nominatim API"}), 500

    data = response.json()

    if not data:
        return jsonify({"error": "Nie znaleziono szczytu"}), 404

    result = {
        "name": peak_name,
        "lat": data[0]["lat"],
        "lon": data[0]["lon"]
    }

    return jsonify(result)

@app.route("/api/route/segment", methods=["POST"])
def plan_segment():
    data = request.get_json()
    start = data.get("from")
    end = data.get("to")

    if not start or not end:
        return jsonify({"error": "Brakuje punktów start lub end"}), 400

    route_points, distance, elevation_gain, elevation_loss = plan_route(start, end)

    geojson_coords = [(lon, lat) for lat, lon in route_points]
    geojson_feature = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": geojson_coords
                },
                "properties": {}
            }
        ]
    }

    return jsonify({
        "route_points": route_points,
        "distance": distance,
        "elevation_gain": elevation_gain,
        "elevation_loss": elevation_loss,
        "routeGeoJson": geojson_feature
    })

@app.route("/api/route/trim", methods=["POST"])
def trim_last_segment():
    data = request.get_json()
    points = data.get("points", [])

    points = points[:-1]
    full_features = []
    total_distance = 0
    total_gain = 0
    total_loss = 0

    for i in range(len(points) - 1):
        seg_points, dist, gain, loss = plan_route(points[i], points[i+1])
        total_distance += dist
        total_gain += gain
        total_loss += loss

        coords = [(lon, lat) for lat, lon in seg_points]
        full_features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            },
            "properties": {}
        })

    return jsonify({
        "routeGeoJson": {
            "type": "FeatureCollection",
            "features": full_features
        },
        "points": points,
        "length": total_distance,
        "elevationGain": total_gain,
        "elevationLoss": total_loss
    })

@app.route('/api/route/elevation-profile', methods=['POST'])
def elevation_profile():
    data = request.get_json()
    points = data.get('points', [])

    if len(points) < 2:
        return {"error": "Zbyt mało punktów"}, 400

    elevations = []
    distances = [0]

    total_distance = 0
    prev_lat, prev_lng = points[0]

    ele = get_elevation(prev_lat, prev_lng)
    elevations.append(ele)
    for i in range(len(points) - 1):
        seg_points, dist, gain, loss = plan_route(points[i], points[i + 1])
        prev_lat, prev_lng = seg_points[0]
        for lat, lng in seg_points[1:]:
            ele = get_elevation(lat, lng)
            elevations.append(ele)
            segment_dist = geodesic((lat, lng), (prev_lat, prev_lng)).kilometers
            total_distance += segment_dist
            distances.append(total_distance)
            prev_lat, prev_lng = lat, lng

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(distances, elevations, color='darkgreen', linewidth=2)
    ax.set_title("Profil wysokości trasy")
    ax.set_xlabel("Dystans (km)")
    ax.set_ylabel("Wysokość (m)")
    ax.grid(True)

    img_io = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_io, format='png')
    img_io.seek(0)
    plt.close(fig)

    return send_file(img_io, mimetype='image/png')


@app.route('/api/markers/<int:marker_id>', methods=['PUT'])
@login_required
def update_marker(marker_id):
    data = request.get_json()
    marker = Marker.query.get_or_404(marker_id)

    if marker.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    marker.name = data.get("name", marker.name)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/routes/<int:route_id>', methods=['PUT'])
@login_required
def update_route(route_id):
    data = request.get_json()
    route = Route.query.get_or_404(route_id)

    if route.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    route.name = data.get("name", route.name)
    route.description = data.get("description", route.description)
    route.waypoints = data.get("waypoints", route.waypoints)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/avalanche_markers', methods=['POST'])
@login_required
def add_avalanche_marker():
    data = request.get_json()
    new_marker = AvalancheMarker(
        user_id=current_user.id,
        latitude=data['latitude'],
        longitude=data['longitude'],
        description=data.get('description', ''),
        created_at=datetime.now()
    )
    db.session.add(new_marker)
    db.session.commit()
    return jsonify({'message': 'Avalanche marker added successfully'}), 201


@app.route('/api/avalanche_markers', methods=['GET'])
def get_avalanche_markers():
    markers = AvalancheMarker.query.order_by(AvalancheMarker.created_at.desc()).all()
    return jsonify([{
        'id': m.id,
        'latitude': m.latitude,
        'longitude': m.longitude,
        'description': m.description,
        'created_at': m.created_at.strftime('%Y-%m-%d %H:%M'),
        'username': m.user.username
    } for m in markers])


@app.route("/api/nearest_avalanche", methods=["POST"])
def nearest_avalanche():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:
        return jsonify({"error": "Brak współrzędnych"}), 400

    avalanches = AvalancheMarker.query.all()

    if not avalanches:
        return jsonify({"distance": None})  #Brak lawin

    min_distance = min(
        distance_avalanche(lat, lon, avalanche.latitude, avalanche.longitude)
        for avalanche in avalanches
    )

    return jsonify({"distance": round(min_distance, 2)})

@app.route("/api/avalanches_in_radius", methods=["POST"])
def avalanches_in_radius():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:
        return jsonify({"error": "Brak współrzędnych"}), 400

    avalanches = AvalancheMarker.query.all()
    number_of_avalanches = count_avalanches_in_radius(lat, lon, avalanches)

    return jsonify({"number_of_avalanches": number_of_avalanches})


@app.route('/plot_avalanche_chart', methods=['POST'])
def plot_avalanche_chart():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    radius_km = data.get("radius", 2.0)
    days = data.get("days", 30)

    if lat is None or lon is None:
        return jsonify({"error": "Brak współrzędnych"}), 400

    now = datetime.now()
    start_date = now - timedelta(days=days)

    avalanches = AvalancheMarker.query.filter(AvalancheMarker.created_at >= start_date).all()

    #Dane dzienne
    date_counts = { (start_date + timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(days + 1) }

    for avalanche in avalanches:
        distance = distance_avalanche(lat, lon, avalanche.latitude, avalanche.longitude)
        if distance <= radius_km:
            day = avalanche.created_at.strftime('%Y-%m-%d')
            if day in date_counts:
                date_counts[day] += 1

    labels = list(date_counts.keys())
    values = list(date_counts.values())

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(labels, values, marker='o', color='red')
    ax.fill_between(labels, values, alpha=0.3, color='red')
    ax.set_title("Liczba lawin w okolicy ({} km)".format(radius_km))
    ax.set_xlabel("Data")
    ax.set_ylabel("Liczba lawin")
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png')
