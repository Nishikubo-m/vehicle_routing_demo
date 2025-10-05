import requests
import folium
import polyline
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# --- OSRM のエンドポイント（compose内からはサービス名で到達） ---
BASE = "http://osrm:5000"

# --- 入力データ------------------------
# 倉庫（デポ）
DEPOT = ("OptHub倉庫", 35.638633, 139.759828)  # Depot

# 20拠点
STOPS = [
    ("ダイバーシティ東京 プラザ店", 35.62595982, 139.7762261),
    ("エキュート品川店", 35.63134041, 139.7445551),
    ("アトレ大井町店", 35.6085819, 139.7382601),
    ("ディラ大崎駅店", 35.62170512, 139.7374029),
    ("大森北店", 35.59058432, 139.7719922),
    ("渋谷道玄坂店", 35.66624823, 139.6949094),
    ("新宿本店", 35.69669898, 139.7184976),
    ("世田谷千歳台店", 35.66186402, 139.6380329),
    ("マルイファミリー溝口店", 35.61163903, 139.6462727),
    ("東京ソラマチ店", 35.71274464, 139.8250213),
    ("ヨドバシAkiba店", 35.69979371, 139.7801535),
    ("東京ドームシティラクーア店", 35.70865235, 139.7572892),
    ("駒沢自由通り店", 35.63418314, 139.6667103),
    ("笹塚店", 35.67626116, 139.6775296),
    ("自由が丘店", 35.61171667, 139.6871683),
    ("南砂町SUNAMO店", 35.66943552, 139.805676),
    ("中延駅前店", 35.60727856, 139.7182348),
    ("東京ミッドタウン店", 35.66763003, 139.7358906),
    ("武蔵小杉東急スクエア店", 35.57742498, 139.663075),
    ("ビーンズ阿佐ヶ谷店", 35.70894241, 139.6266649),
]

NUM_VEHICLES = 5
STOPS_PER_VEHICLE = 4
assert len(STOPS) == NUM_VEHICLES * STOPS_PER_VEHICLE, "拠点は20件（5×4）にしてください。"

points = [DEPOT] + STOPS
names = [p[0] for p in points]
lats  = [p[1] for p in points]
lons  = [p[2] for p in points]

# --- OSRM /table で距離行列（m）を取得 --------------------------------
def osrm_table(lats, lons, metric="distance"):
    coords = ";".join([f"{lon},{lat}" for lat, lon in zip(lats, lons)])
    url = f"{BASE}/table/v1/driving/{coords}?annotations=distance,duration"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()
    key = "distances" if metric == "distance" else "durations"
    mat = data.get(key)
    if mat is None:
        raise RuntimeError(f"OSRM table error: {data}")
    BIG = 10**9
    # 到達不能時は大値に
    return [[(c if c is not None and c >= 0 else BIG) for c in row] for row in mat]

dist_matrix_m = osrm_table(lats, lons, metric="distance")

# --- OR-Tools: 「各車ちょうど4件」訪問 & 総距離最小 -------------------
manager = pywrapcp.RoutingIndexManager(len(points), NUM_VEHICLES, 0)  # depot=0
routing = pywrapcp.RoutingModel(manager)

def cost_cb(fi, ti):
    i = manager.IndexToNode(fi); j = manager.IndexToNode(ti)
    return int(dist_matrix_m[i][j])

tid = routing.RegisterTransitCallback(cost_cb)
routing.SetArcCostEvaluatorOfAllVehicles(tid)

# 訪問数ディメンション（拠点=1、デポ=0）で各車 End の累積 = 4 を強制
def demand_cb(i):
    node = manager.IndexToNode(i)
    return 0 if node == 0 else 1
did = routing.RegisterUnaryTransitCallback(demand_cb)
routing.AddDimensionWithVehicleCapacity(did, 0, [STOPS_PER_VEHICLE]*NUM_VEHICLES, True, "Stops")
stops_dim = routing.GetDimensionOrDie("Stops")
solver = routing.solver()
for v in range(NUM_VEHICLES):
    solver.Add(stops_dim.CumulVar(routing.End(v)) == STOPS_PER_VEHICLE)

# 探索パラメータ
params = pywrapcp.DefaultRoutingSearchParameters()
params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
params.time_limit.FromSeconds(30)

solution = routing.SolveWithParameters(params)
if not solution:
    raise SystemExit("解が見つかりませんでした。time_limitを延ばすなど調整してください。")

# --- 解の取り出し -------------------------------------------------------
routes = []   # [(veh_id, [node_ids...])]
total_m = 0
for v in range(NUM_VEHICLES):
    idx = routing.Start(v)
    path = []
    while not routing.IsEnd(idx):
        path.append(manager.IndexToNode(idx))
        nxt = solution.Value(routing.NextVar(idx))
        total_m += routing.GetArcCostForVehicle(idx, nxt, v)
        idx = nxt
    path.append(manager.IndexToNode(idx))
    routes.append((v, path))

per_vehicle_m = []
per_vehicle_names = []  # ★ 各トラックの訪問順（店名）

for v, path in routes:
    # 距離集計
    d = 0
    for i, j in zip(path, path[1:]):
        d += dist_matrix_m[i][j]
    per_vehicle_m.append(d)

    # 店名の並び（デポ→...→デポ）
    per_vehicle_names.append([names[n] for n in path])

print(f"[VRP] total distance = {total_m/1000:.3f} km")
for v, (d, seq_names) in enumerate(zip(per_vehicle_m, per_vehicle_names), start=1):
    print(f"  - Truck{v}: {d/1000:.3f} km")
    print("    " + " → ".join(seq_names))

import csv, os
os.makedirs("./output", exist_ok=True)
with open("./output/vrp_routes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["truck", "distance_km", "sequence"])
    for v, (d, seq_names) in enumerate(zip(per_vehicle_m, per_vehicle_names), start=1):
        w.writerow([f"Truck{v}", f"{d/1000:.3f}", " -> ".join(seq_names)])
print("saved: ./output/vrp_routes.csv")

# --- Folium: 白黒タイルでマーカー＆ルート描画 --------------------------
m = folium.Map(location=[lats[0], lons[0]], zoom_start=12, tiles="cartodb positron", control_scale=True)
folium.Marker([lats[0], lons[0]], tooltip=names[0], icon=folium.Icon(color="green")).add_to(m)

colors = ["red","blue","purple","orange","darkgreen"]

def osrm_route_polyline(seq_nodes):
    """VRPで得た訪問順に従って、OSRM /route で道路沿いポリラインを取得"""
    coords = ";".join([f"{lons[n]},{lats[n]}" for n in seq_nodes])
    url = f"{BASE}/route/v1/driving/{coords}"
    params = {"overview": "full", "geometries": "polyline", "steps": "false"}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM route error: {data}")
    geom = data["routes"][0]["geometry"]
    return polyline.decode(geom)

for v, path in routes:
    # path は [depot, s?, s?, s?, s?, depot] のノードID列
    color = colors[v % len(colors)]
    # 道路にスナップしたルート
    snapped = osrm_route_polyline(path)
    folium.PolyLine(snapped, color=color, weight=4, opacity=0.9, tooltip=f"Truck{v+1}").add_to(m)

    # 拠点マーカー（訪問順の番号付き）
    step = 0
    for n in path:
        if n == 0:   # depot はスキップ
            continue
        step += 1
        folium.CircleMarker(
            [lats[n], lons[n]],
            radius=5, color=color, fill=True, fill_opacity=1.0,
            tooltip=f"{names[n]} (Truck{v+1} #{step})"
        ).add_to(m)

m.save("./output/vrp_solution_map.html")
print("saved: ./output/vrp_solution_map.html")