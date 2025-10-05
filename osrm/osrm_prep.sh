#!/usr/bin/env bash
set -euo pipefail
cd /data

PBF="/data/kanto-latest.osm.pbf"
OSRM="/data/kanto-latest.osrm"

# --- 入力チェック ---
if [ ! -f "$PBF" ]; then
  echo "[ERROR] $PBF が見つかりません。以下のようにホストで配置してください。"
  echo "  curl -L -o ./osrm/files/kanto-latest.osm.pbf \\"
  echo "    https://download.geofabrik.de/asia/japan/kanto-latest.osm.pbf"
  exit 1
fi

# --- 既にビルド済みならスキップ ---
if [ -f "$OSRM" ]; then
  echo "[INFO] OSRM graph already exists ($OSRM). Skipping build."
  exit 0
fi

echo "[1/3] osrm-extract"
osrm-extract -p /opt/car.lua "$PBF"

echo "[2/3] osrm-partition"
osrm-partition "$OSRM"

echo "[3/3] osrm-customize"
osrm-customize "$OSRM"

echo "[✅] OSRM build done: $OSRM"