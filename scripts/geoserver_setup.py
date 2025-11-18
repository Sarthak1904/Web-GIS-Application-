#!/usr/bin/env python3
"""
GeoServer REST API setup script.
Creates workspace and PostGIS data store for the platform.
Run after GeoServer is up and migrations are applied.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from config import get_settings

settings = get_settings()
GEOSERVER_URL = settings.geoserver_url.rstrip("/")
USER = settings.geoserver_user
PASSWORD = settings.geoserver_password
WORKSPACE = "geospatial"
DATASTORE = "postgis"
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_NAME = "geospatial_db"
DB_USER = "geospatial"
DB_PASS = "geospatial"


def wait_for_geoserver(max_attempts=30):
    """Wait for GeoServer to be ready."""
    for i in range(max_attempts):
        try:
            r = httpx.get(f"{GEOSERVER_URL}/geoserver/web/", timeout=5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def create_workspace(client):
    """Create workspace if not exists."""
    r = client.get(f"{GEOSERVER_URL}/geoserver/rest/workspaces/{WORKSPACE}.json")
    if r.status_code == 200:
        print(f"Workspace '{WORKSPACE}' already exists")
        return
    r = client.post(
        f"{GEOSERVER_URL}/geoserver/rest/workspaces",
        json={"workspace": {"name": WORKSPACE}},
    )
    if r.status_code in (200, 201):
        print(f"Created workspace '{WORKSPACE}'")
    else:
        print(f"Failed to create workspace: {r.status_code} {r.text}")


def create_datastore(client):
    """Create PostGIS data store if not exists."""
    r = client.get(
        f"{GEOSERVER_URL}/geoserver/rest/workspaces/{WORKSPACE}/datastores/{DATASTORE}.json"
    )
    if r.status_code == 200:
        print(f"Datastore '{DATASTORE}' already exists")
        return
    payload = {
        "dataStore": {
            "name": DATASTORE,
            "type": "PostGIS",
            "enabled": True,
            "connectionParameters": {
                "entry": [
                    {"@key": "host", "$": DB_HOST},
                    {"@key": "port", "$": "5432"},
                    {"@key": "database", "$": DB_NAME},
                    {"@key": "user", "$": DB_USER},
                    {"@key": "passwd", "$": DB_PASS},
                    {"@key": "dbtype", "$": "postgis"},
                ]
            },
        }
    }
    r = client.post(
        f"{GEOSERVER_URL}/geoserver/rest/workspaces/{WORKSPACE}/datastores",
        params={"configure": "all"},
        json=payload,
    )
    if r.status_code in (200, 201):
        print(f"Created datastore '{DATASTORE}'")
    else:
        print(f"Failed to create datastore: {r.status_code} {r.text}")


def main():
    if not wait_for_geoserver():
        print("GeoServer not available. Is it running?")
        sys.exit(1)

    with httpx.Client(auth=(USER, PASSWORD), timeout=30) as client:
        create_workspace(client)
        create_datastore(client)
    print("GeoServer setup complete.")


if __name__ == "__main__":
    main()
