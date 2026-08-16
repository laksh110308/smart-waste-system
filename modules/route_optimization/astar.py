"""
modules/route_optimization/astar.py
--------------------------------------
MODULE 2 core - A* search algorithm, implemented FROM SCRATCH (no library).

f(n) = g(n) + h(n)
g(n) = actual cost travelled from start to node n
h(n) = Haversine straight-line distance from n to goal (admissible heuristic)
f(n) = estimated total cost of a path through n
"""

import heapq
import math


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def a_star(graph, coordinates, start, goal):
    if start not in graph or goal not in graph:
        return [], float("inf")

    def h(node):
        lat1, lon1 = coordinates[node]
        lat2, lon2 = coordinates[goal]
        return haversine_distance(lat1, lon1, lat2, lon2)

    open_list = [(h(start), start)]
    open_set = {start}
    closed_set = set()

    g_score = {start: 0.0}
    f_score = {start: h(start)}
    parent = {start: None}

    while open_list:
        current_f, current = heapq.heappop(open_list)
        open_set.discard(current)

        if current == goal:
            return _reconstruct_path(parent, goal), g_score[goal]

        closed_set.add(current)

        for neighbor, edge_cost in graph.get(current, []):
            if neighbor in closed_set:
                continue

            tentative_g = g_score[current] + edge_cost

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                parent[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + h(neighbor)

                if neighbor not in open_set:
                    heapq.heappush(open_list, (f_score[neighbor], neighbor))
                    open_set.add(neighbor)

    return [], float("inf")


def _reconstruct_path(parent, goal):
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


if __name__ == "__main__":
    test_graph = {
        "A": [("B", 2), ("D", 4)],
        "B": [("A", 2), ("C", 3), ("E", 1)],
        "C": [("B", 3), ("F", 2)],
        "D": [("A", 4), ("E", 3)],
        "E": [("B", 1), ("D", 3), ("F", 4)],
        "F": [("C", 2), ("E", 4)],
    }

    test_coords = {
        "A": (13.00, 80.20),
        "B": (13.01, 80.21),
        "C": (13.02, 80.22),
        "D": (13.00, 80.22),
        "E": (13.01, 80.23),
        "F": (13.02, 80.24),
    }

    print("Testing A* on a small 6-node road network...")
    path, cost = a_star(test_graph, test_coords, "A", "F")
    print(f"  Path A -> F: {' -> '.join(path)}")
    print(f"  Total cost: {cost}")

    print("\nTesting A* on a path with no connection...")
    test_graph["G"] = []
    test_coords["G"] = (13.05, 80.30)
    path2, cost2 = a_star(test_graph, test_coords, "A", "G")
    print(f"  Path A -> G: {path2 if path2 else 'NO PATH FOUND'} (cost={cost2})")

    print("\nTesting Haversine distance (Chennai landmarks, roughly)...")
    d = haversine_distance(13.0827, 80.2707, 13.0067, 80.2570)
    print(f"  Approx distance: {d:.2f} km")