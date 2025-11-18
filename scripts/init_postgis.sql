-- Enterprise Geospatial Intelligence Platform — PostGIS Initialization
-- Run on first database creation

-- Ensure PostGIS extension is enabled
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema for application (optional isolation)
-- CREATE SCHEMA IF NOT EXISTS geospatial;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE geospatial_db TO geospatial;
GRANT ALL ON SCHEMA public TO geospatial;

-- Enable PostGIS for the database (redundant if already enabled)
SELECT PostGIS_Version();
