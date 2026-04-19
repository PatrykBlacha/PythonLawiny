from math import radians, sin, cos, sqrt, atan2
from constants import EARTH_RADIUS_KM, AVALANCHE_SEARCH_RADIUS_KM

def distance_avalanche(lat1, lon1, lat2, lon2):
    R = EARTH_RADIUS_KM
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = sin(delta_phi / 2) ** 2 + \
        cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def count_avalanches_in_radius(lat, lon, avalanche_markers):
    radius = AVALANCHE_SEARCH_RADIUS_KM
    number_of_avalanches = 0
    for marker in avalanche_markers:
        if distance_avalanche(lat, lon, marker.latitude, marker.longitude) <= radius:
            number_of_avalanches += 1
    return number_of_avalanches
