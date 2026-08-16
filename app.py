"""
app.py
-------
Main Flask application. This is the single entry point that ties
Module 1 (bin monitoring), Module 2 (route optimization), and
Module 3 (vehicle/collection management) together behind one set
of REST API endpoints, and serves the dashboard frontend.

Run with:  python app.py
"""

from flask import Flask, jsonify, request, render_template

from database.database import init_db
from modules.bin_monitoring import bin_service
from modules.route_optimization.route_service import generate_optimized_route
from modules.collection import vehicle_service, collection_service

app = Flask(__name__)


# ======================================================================
# PAGE ROUTES (serve the dashboard HTML - built in Phase 10)
# ======================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/bins")
def bins_page():
    return render_template("bins.html")


@app.route("/routes")
def routes_page():
    return render_template("routes.html")


@app.route("/vehicles")
def vehicles_page():
    return render_template("vehicles.html")


# ======================================================================
# MODULE 1 API - Bin Monitoring
# ======================================================================

@app.route("/api/bins", methods=["GET"])
def api_get_bins():
    return jsonify(bin_service.get_all_bins())


@app.route("/api/bins/<bin_id>", methods=["GET"])
def api_get_bin(bin_id):
    bin_data = bin_service.get_bin(bin_id)
    if bin_data is None:
        return jsonify({"error": "Bin not found"}), 404
    return jsonify(bin_data)


@app.route("/api/bins/collection-required", methods=["GET"])
def api_collection_required():
    return jsonify(bin_service.get_bins_requiring_collection())


@app.route("/api/bins/simulate", methods=["POST"])
def api_simulate_sensors():
    summary = bin_service.simulate_all_sensors()
    return jsonify({"updated": summary})


@app.route("/api/bins/detect", methods=["POST"])
def api_detect_full_bins():
    return jsonify(bin_service.detect_full_bins())


@app.route("/api/bins/<bin_id>/threshold", methods=["POST"])
def api_set_threshold(bin_id):
    data = request.get_json()
    if not data or "threshold" not in data:
        return jsonify({"error": "threshold value required"}), 400
    bin_service.set_threshold(bin_id, float(data["threshold"]))
    return jsonify({"bin_id": bin_id, "new_threshold": data["threshold"]})


# ======================================================================
# MODULE 2 API - Route Optimization
# ======================================================================

@app.route("/api/route/generate", methods=["POST"])
def api_generate_route():
    route = generate_optimized_route()
    if route is None:
        return jsonify({"error": "No bins currently require collection"}), 400
    if "error" in route:
        return jsonify(route), 500
    return jsonify(route)


# ======================================================================
# MODULE 3 API - Vehicles & Collection Management
# ======================================================================

@app.route("/api/vehicles", methods=["GET"])
def api_get_vehicles():
    return jsonify(vehicle_service.get_all_vehicles())


@app.route("/api/route/assign", methods=["POST"])
def api_assign_route():
    result = collection_service.assign_route_to_vehicle()
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/route/<int:route_id>/start", methods=["POST"])
def api_start_collection(route_id):
    collection_service.start_collection(route_id)
    return jsonify({"route_id": route_id, "status": "In Progress"})


@app.route("/api/route/<int:route_id>/collect/<bin_id>", methods=["POST"])
def api_mark_bin_collected(route_id, bin_id):
    collection_service.mark_bin_collected(route_id, bin_id)
    return jsonify({"route_id": route_id, "bin_id": bin_id, "status": "Collected"})


@app.route("/api/route/<int:route_id>/complete", methods=["POST"])
def api_complete_route(route_id):
    result = collection_service.complete_route(route_id)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@app.route("/api/route/<int:route_id>", methods=["GET"])
def api_get_route_progress(route_id):
    progress = collection_service.get_route_progress(route_id)
    if progress is None:
        return jsonify({"error": "Route not found"}), 404
    return jsonify(progress)


@app.route("/api/routes/active", methods=["GET"])
def api_get_active_routes():
    return jsonify(collection_service.get_active_routes())


# ======================================================================
# DASHBOARD SUMMARY API
# ======================================================================

@app.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats():
    all_bins = [b for b in bin_service.get_all_bins() if b["bin_id"] not in ("DEPOT", "DUMP")]
    required = [b for b in all_bins if b["status"] == "Collection Required"]
    normal = [b for b in all_bins if b["status"] == "Normal"]

    vehicles = vehicle_service.get_all_vehicles()
    available_vehicles = [v for v in vehicles if v["available"] == 1]

    active_routes = collection_service.get_active_routes()

    total_distance = sum(r["total_distance_km"] or 0 for r in active_routes)
    total_time = sum(r["estimated_time_min"] or 0 for r in active_routes)

    total_bin_count = len(all_bins)
    collected_today = len([b for b in all_bins if b["fill_level"] == 0])
    completion_pct = round((collected_today / total_bin_count) * 100, 1) if total_bin_count else 0

    return jsonify({
        "total_bins": total_bin_count,
        "normal_bins": len(normal),
        "full_bins": len(required),
        "collection_required": len(required),
        "collected_bins": collected_today,
        "available_vehicles": len(available_vehicles),
        "total_vehicles": len(vehicles),
        "active_routes": len(active_routes),
        "total_distance_km": round(total_distance, 2),
        "estimated_time_min": round(total_time, 1),
        "completion_percentage": completion_pct
    })


if __name__ == "__main__":
    init_db()
    print("\nStarting Smart Waste Collection System server...")
    print("Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, port=5000)