"""
modules/route_optimization/graph.py
--------------------------------------
MODULE 2 - builds the road network graph used by A*.
Each location connects only to its K nearest neighbours (sparse, realistic),
not a fully-connected graph. Edge cost = Haversine distance x simulated traffic.
"""

import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.route_optimization.astar import haversine_distance

K_NEAREST = 5
TRAFFIC_MIN = 1.0
TRAFFIC_MAX = 1.6


def build_graph(locations):
    coordinates = {loc["bin_id"]: (loc["latitude"], loc["longitude"]) for loc in locations}
    node_ids = list(coordinates.keys())

    graph = {node_id: [] for node_id in node_ids}

    for node in node_ids:
        distances = []
        for other in node_ids:
            if other == node:
                continue
            lat1, lon1 = coordinates[node]
            lat2, lon2 = coordinates[other]
            d = haversine_distance(lat1, lon1, lat2, lon2)
            distances.append((d, other))

        distances.sort(key=lambda x: x[0])
        nearest = distances[:K_NEAREST]

        for real_distance, neighbor in nearest:
            traffic_weight = round(random.uniform(TRAFFIC_MIN, TRAFFIC_MAX), 2)
            cost = round(real_distance * traffic_weight, 3)
            _add_edge(graph, node, neighbor, cost)

    _ensure_connected(graph, coordinates)
    return graph, coordinates


def _add_edge(graph, a, b, cost):
    if not any(n == b for n, _ in graph[a]):
        graph[a].append((b, cost))
    if not any(n == a for n, _ in graph[b]):
        graph[b].append((a, cost))


def _connected_component(graph, start):
    visited = {start}
    queue = [start]
    while queue:
        current = queue.pop(0)
        for neighbor, _ in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited


def _ensure_connected(graph, coordinates):
    all_nodes = set(graph.keys())
    remaining = set(all_nodes)

    components = []
    while remaining:
        start = next(iter(remaining))
        comp = _connected_component(graph, start)
        components.append(comp)
        remaining -= comp

    if len(components) <= 1:
        return

    components.sort(key=len, reverse=True)
    main_component = components[0]

    for comp in components[1:]:
        best_pair = None
        best_dist = float("inf")
        for a in main_component:
            lat1, lon1 = coordinates[a]
            for b in comp:
                lat2, lon2 = coordinates[b]
                d = haversine_distance(lat1, lon1, lat2, lon2)
                if d < best_dist:
                    best_dist = d
                    best_pair = (a, b)

        a, b = best_pair
        _add_edge(graph, a, b, round(best_dist * 1.2, 3))
        main_component |= comp


if __name__ == "__main__":
    sample_locations = [
        {"bin_id": "DEPOT", "latitude": 13.0878, "longitude": 80.2785},
        {"bin_id": "B1", "latitude": 13.0418, "longitude": 80.2341},
        {"bin_id": "B2", "latitude": 13.0850, "longitude": 80.2101},
        {"bin_id": "B3", "latitude": 12.9791, "longitude": 80.2183},
        {"bin_id": "B4", "latitude": 13.0067, "longitude": 80.2570},
        {"bin_id": "DUMP", "latitude": 13.1425, "longitude": 80.2489},
    ]

    graph, coords = build_graph(sample_locations)

    print("Road network built. Adjacency list:")
    for node, edges in graph.items():
        edge_str = ", ".join(f"{n}({c}km)" for n, c in edges)
        print(f"  {node}: {edge_str}")

    print(f"\nTotal nodes: {len(graph)}")
    total_edges = sum(len(edges) for edges in graph.values()) // 2
    print(f"Total unique road connections: {total_edges}")