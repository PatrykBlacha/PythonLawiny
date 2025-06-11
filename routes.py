import overpy
import json
import rasterio
from collections import defaultdict
from geopy.distance import geodesic
from scipy.spatial import KDTree
from queue import PriorityQueue

COLOR_MAP = {
    "red": "#ff0000",
    "blue": "#0000ff",
    "green": "#00aa00",
    "yellow": "#ffff00",
    "black": "#000000",
}


with open("static/hiking_trails.geojson", encoding="utf-8") as f:
    GEOJSON = json.load(f)

GRAPH = defaultdict(list)
NODES = set()

for feature in GEOJSON["features"]:
    geometry = feature["geometry"]
    coords_list = []

    if geometry["type"] == "LineString":
        coords_list = [geometry["coordinates"]]
    elif geometry["type"] == "MultiLineString":
        coords_list = geometry["coordinates"]

    for coords in coords_list:
        for i in range(len(coords) - 1):
            a = tuple(reversed(coords[i]))
            b = tuple(reversed(coords[i + 1]))
            dist = geodesic(a, b).kilometers
            GRAPH[a].append((b, dist))
            GRAPH[b].append((a, dist))
            NODES.add(a)
            NODES.add(b)

NODES = list(NODES)
NODE_TREE = KDTree(NODES)

DEM = rasterio.open("static/NMT_tatry2.tif")
def extract_color(tags):
    color = tags.get("colour", "")

    if not color and "osmc:symbol" in tags:
        symbol = tags["osmc:symbol"]
        color = symbol.split(":")[0]

    color = color.lower().strip()
    return COLOR_MAP.get(color, "#888888")

def get_elevation(lat,lon):
    with rasterio.open('static/NMT_tatry2.tif') as dem:
        try:
            # rasterio używa (lon, lat) – odwrotna kolejność
            row, col = dem.index(lon, lat)
            elevation = dem.read(1)[row, col]
            return float(elevation)
        except Exception as e:
            print(f"Nie udało się pobrać wysokości dla ({lat}, {lon}): {e}")
            return None

def get_routes_to_json():
    api = overpy.Overpass()
    try:
        result = api.query("""
        [out:json][timeout:25];
        (
          relation["route"="hiking"](49.14, 19.64, 49.30, 20.30);
        );
        out body;
        >;
        out skel qt;
        """)
    except overpy.exception.OverpassTooManyRequests:
        print("Zbyt wiele żądań – spróbuj ponownie później.")
        return
    except Exception as e:
        print(f"Błąd zapytania: {e}")
        return

    features = []

    for rel in result.relations:
        segments = []

        for member in rel.members:
            if isinstance(member, overpy.RelationWay):
                way = member.resolve()
                if way and way.nodes:
                    coords = [[float(node.lon), float(node.lat)] for node in way.nodes]
                    if len(coords) >= 2:
                        segments.append(coords)

        if not segments:
            continue

        if len(segments) == 1:
            geometry = {
                "type": "LineString",
                "coordinates": segments[0]
            }
        else:
            geometry = {
                "type": "MultiLineString",
                "coordinates": segments
            }

        tags = rel.tags
        color = extract_color(tags)

        feature = {
            "type": "Feature",
            "properties": {
                "name": tags.get("name", "Brak nazwy"),
                "tags": tags,
                "color": color
            },
            "geometry": geometry
        }
        features.append(feature)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    with open("static/hiking_trails.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2, sort_keys=True)


def get_elevation(lat, lon):
    try:
        row, col = DEM.index(lon, lat)
        return float(DEM.read(1)[row, col])
    except:
        return None


def heuristic(a, b):
    return geodesic(a, b).kilometers

def astar(graph, start, goal):
    open_set = PriorityQueue()
    open_set.put((0, start))

    came_from = {}
    g_score = {node: float('inf') for node in graph}
    g_score[start] = 0

    f_score = {node: float('inf') for node in graph}
    f_score[start] = heuristic(start, goal)

    while not open_set.empty():
        _, current = open_set.get()

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        for neighbor, cost in graph[current]:
            tentative_g_score = g_score[current] + cost
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                open_set.put((f_score[neighbor], neighbor))

    return []

def find_closest_node(lat, lon):
    distance, idx = NODE_TREE.query((lat, lon))
    return NODES[idx]

def plan_route(start, end):
    start_node = find_closest_node(*start)
    end_node = find_closest_node(*end)

    path = astar(GRAPH, start_node, end_node)

    if not path:
        return [], 0, 0, 0

    route_points = []
    elevations = []

    for lat, lon in path:
        route_points.append([lat, lon])
        elevations.append(get_elevation(lat, lon) or 0)

    total_distance = 0
    elevation_gain = 0
    elevation_loss = 0

    for i in range(len(path) - 1):
        dist = geodesic(path[i], path[i + 1]).kilometers
        total_distance += dist

        delta = elevations[i + 1] - elevations[i]
        if delta > 0:
            elevation_gain += delta
        else:
            elevation_loss -= delta

    return route_points, total_distance, elevation_gain, elevation_loss