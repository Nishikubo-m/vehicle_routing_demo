# vehicle_routing_demo


## 🚀 実行方法

1. **OSMデータのダウンロード** 

   まず、関東エリアの地図データ（PBF形式）を取得します：

   ```bash
   curl -L -o ./osrm/files/kanto-latest.osm.pbf \
   https://download.geofabrik.de/asia/japan/kanto-latest.osm.pbf
   ```

2. **Docker環境の起動**

    既存のコンテナがあれば停止・削除してから、再起動します：

    ```bash
    docker compose down --remove-orphans
    docker compose up -d
    ```

3. **OSRM の起動確認**

    OSRM コンテナのログを確認し、次のようなメッセージが出ていれば起動成功：

    ```bash
    docker compose logs -f osrm
    ```

    出力例：

    ```
    [info] Listening on: 0.0.0.0:5000
    [info] running and waiting for requests
    ```
    - ✅ running and waiting for requests と表示されれば、OSRM が正常に稼働しています。
    - 以下のファイルが生成されます。（2GB近くあるので注意！）
        - kanto-latest.osm.pbf  
        - kanto-latest.osrm  
        - kanto-latest.osrm.cell_metrics  
        - kanto-latest.osrm.cells  
        - kanto-latest.osrm.cnbg  
        - kanto-latest.osrm.cnbg_to_ebg  
        - kanto-latest.osrm.datasource_names  
        - kanto-latest.osrm.ebg  
        - kanto-latest.osrm.ebg_nodes  
        - kanto-latest.osrm.edges  
        - kanto-latest.osrm.env  
        - kanto-latest.osrm.fileIndex  
        - kanto-latest.osrm.geometry  
        - kanto-latest.osrm.icd  
        - kanto-latest.osrm.maneuver_overrides  
        - kanto-latest.osrm.mldgr  
        - kanto-latest.osrm.names  
        - kanto-latest.osrm.nbg_nodes  
        - kanto-latest.osrm.partition  
        - kanto-latest.osrm.properties  
        - kanto-latest.osrm.ramIndex  
        - kanto-latest.osrm.restrictions  
        - kanto-latest.osrm.timestamp  
        - kanto-latest.osrm.tld  
        - kanto-latest.osrm.tls  
        - kanto-latest.osrm.turn_duration_penalties  
        - kanto-latest.osrm.turn_penalties_index  
        - kanto-latest.osrm.turn_weight_penalties  
        - osrm_prep.sh




4. **ルート最適化スクリプトの実行**
    開発用コンテナ（vrp-dev）に入って、Pythonスクリプトを実行します：
    （vscodeであれば、dev-containerでも可）

    ```bash
    docker compose exec dev bash
    python app/map_point.py
    python app/vrp_optimize_and_map.py
    ```

    実行が完了すると、最適化されたルートマップと経路情報が以下に出力されます：

    ```
    ./output/points_only_map.html
    ./output/vrp_routes.csv
    ./output/vrp_solution_map.html
    ```
