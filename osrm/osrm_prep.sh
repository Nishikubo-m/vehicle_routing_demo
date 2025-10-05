#!/usr/bin/env bash
set -euo pipefail

cd /data

if [ ! -f "/data/tokyo.osm.pbf" ]; then
  echo "ERROR: /data/tokyo.osm.pbf が見つかりません。vehicle_routing_demo/osrm/files に置いてください。"
  exit 1
fi

if [ -f "/data/tokyo.osrm" ]; then
  echo "OSRM graph already exists. Skipping build."
  exit 0
fi

echo "[1/3] osrm-extract"
osrm-extract -p /opt/car.lua /data/tokyo.osm.pbf

echo "[2/3] osrm-partition"
osrm-partition /data/tokyo.osrm

echo "[3/3] osrm-customize"
osrm-customize /data/tokyo.osrm

echo "OSRM build done."