"""
modules/route_optimization/route_service.py
-----------------------------------------------
MODULE 2 orchestrator. Ties Module 1's collection-required bins into
A* to produce ONE combined optimized collection route.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.bin_monitoring.bin_service import get_bins_requiring_collection, get_all_bins
from modules.route_optimization.graph import build_graph
from modules.route_optimization.astar import a_star, haversine_distance

DEPOT_ID = "DEPOT"
DUMP_ID = "DUMP"
AVERAGE_SPEED_KMPH = 25


def _order_bins_nearest_neighbour(start_id, bin_ids, coordinates):
    remaining = set(bin_ids)
    order = []
    current = start_id

    while remaining:
        lat1, lon1 = coordinates[current]
        nearest = min(
            remaining,
            key=lambda b: haversine_distance(lat1, lon1, coordinates[b][0], coordinates[b][1])
        )
        order.append(nearest)
        remaining.remove(nearest)
        current = nearest

    return order


def generate_optimized_route():
    required_bins = get_bins_requiring_collection()
    if not required_bins:
        return None

    all_locations = get_all_bins()
    graph, coordinates = build_graph(all_locations)

    bin_ids = [b["bin_id"] for b in required_bins]

    visit_order = _order_bins_nearest_neighbour(DEPOT_ID, bin_ids, coordinates)

    full_stop_sequence = [DEPOT_ID] + visit_order + [DUMP_ID]

    segment_paths = []
    full_path = []
    total_distance = 0.0

    for i in range(len(full_stop_sequence) - 1):
        start = full_stop_sequence[i]
        goal = full_stop_sequence[i + 1]

        path, cost = a_star(graph, coordinates, start, goal)

        if not path:
            return {
                "error": f"No road path found between {start} and {goal}",
                "bin_sequence": visit_order
            }

        segment_paths.append({
            "from": start, "to": goal, "path": path, "distance_km": round(cost, 2)
        })

        total_distance += cost
        if full_path:
            full_path.extend(path[1:])
        else:
            full_path.extend(path)

    estimated_time_min = round((total_distance / AVERAGE_SPEED_KMPH) * 60, 1)
    bins_count = len(visit_order)
    efficiency = round(total_distance / bins_count, 2) if bins_count else 0

    return {
        "bin_sequence": visit_order,
        "full_path": full_path,
        "segment_paths": segment_paths,
        "total_distance_km": round(total_distance, 2),
        "estimated_time_min": estimated_time_min,
        "bins_count": bins_count,
        "efficiency_km_per_bin": efficiency
    }


if __name__ == "__main__":
    result = generate_optimized_route()

    if result is None:
        print("No bins currently require collection. Run sensor simulation first.")
    elif "error" in result:
        print("ERROR:", result["error"])
    else:
        print("=== OPTIMIZED COLLECTION ROUTE ===\n")
        print(f"Visiting order ({result['bins_count']} bins):")
        print("  DEPOT -> " + " -> ".join(result["bin_sequence"]) + " -> DUMP\n")

        print("Segment-by-segment A* paths:")
        for seg in result["segment_paths"]:
            print(f"  {seg['from']} -> {seg['to']}: {' -> '.join(seg['path'])}  ({seg['distance_km']} km)")

        print(f"\nFull combined route ({len(result['full_path'])} road nodes):")
        print("  " + " -> ".join(result["full_path"]))

        print(f"\nTotal distance: {result['total_distance_km']} km")
        print(f"Estimated travel time: {result['estimated_time_min']} min")
        print(f"Bins collected: {result['bins_count']}")
        print(f"Route efficiency: {result['efficiency_km_per_bin']} km/bin")