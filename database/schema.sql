-- ============================================================
-- SMART WASTE COLLECTION SYSTEM - DATABASE SCHEMA
-- ============================================================

-- 1. BINS: master record of every waste bin in the city
CREATE TABLE IF NOT EXISTS bins (
    bin_id TEXT PRIMARY KEY,              -- e.g. 'B1', 'B2'
    location_name TEXT NOT NULL,          -- human readable place name
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    waste_type TEXT DEFAULT 'Mixed',      -- Plastic / Organic / E-Waste / Construction / Hazardous / Mixed
    fill_level REAL NOT NULL DEFAULT 0,   -- current fill %, 0-100
    threshold REAL NOT NULL DEFAULT 75,   -- configurable trigger point
    status TEXT NOT NULL DEFAULT 'Normal',            -- Normal / Collection Required
    collection_status TEXT NOT NULL DEFAULT 'Pending', -- Pending / Assigned / Collected
    last_updated TEXT NOT NULL            -- ISO timestamp of last sensor reading
);

-- 2. VEHICLES: waste collection trucks
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY,          -- e.g. 'V1'
    vehicle_name TEXT NOT NULL,
    capacity INTEGER NOT NULL,            -- max bins it can service in one route
    available INTEGER NOT NULL DEFAULT 1  -- 1 = available, 0 = on a route
);

-- 3. ROUTES: one optimized collection run
CREATE TABLE IF NOT EXISTS routes (
    route_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT,
    total_distance_km REAL,
    estimated_time_min REAL,
    bins_count INTEGER,
    status TEXT NOT NULL DEFAULT 'Planned',  -- Planned / In Progress / Completed
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
);

-- 4. ROUTE_BINS: ordered stops within a route (many-to-many, bins <-> routes)
CREATE TABLE IF NOT EXISTS route_bins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    bin_id TEXT NOT NULL,
    sequence_order INTEGER NOT NULL,   -- order of visit: 1, 2, 3...
    collected INTEGER NOT NULL DEFAULT 0,  -- 0 = not yet, 1 = collected
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id)
);

-- 5. SENSOR_READINGS: history log of simulated IoT sensor pings
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bin_id TEXT NOT NULL,
    fill_level REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id)
);