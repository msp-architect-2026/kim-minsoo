import smbus2
import bme280
import time
import sys
from influxdb import InfluxDBClient # [추가] InfluxDB 라이브러리

port = 1
address = 0x76

# [추가] InfluxDB 연결 설정 (K3s 내부 DNS 서비스 이름 사용)
DB_HOST = 'influxdb-svc.monitoring.svc.cluster.local'
DB_PORT = 8086
DB_NAME = 'safe_edge_db'

try:
    # [추가] DB 연결 및 데이터베이스 생성
    client = InfluxDBClient(host=DB_HOST, port=DB_PORT)
    client.create_database(DB_NAME)
    client.switch_database(DB_NAME)
    print(f"[INFO] Connected to InfluxDB ({DB_NAME}) successfully.", flush=True)
except Exception as e:
    print(f"[ERROR] Failed to connect InfluxDB: {e}", flush=True)
    sys.exit(1)

try:
    bus = smbus2.SMBus(port)
    calibration_params = bme280.load_calibration_params(bus, address)
except Exception as e:
    print(f"[ERROR] Failed to initialize BME280 sensor: {e}", flush=True)
    sys.exit(1)

try:
    print("[INFO] BME280 sensor measurement started.", flush=True)
    while True:
        data = bme280.sample(bus, address, calibration_params)
        
        temp = data.temperature
        hum = data.humidity
        press = data.pressure
        
        # 기존 텍스트 출력 유지
        print(f"[INFO] Temp: {temp:.2f}C | Humidity: {hum:.2f}% | Pressure: {press:.2f}hPa", flush=True)
        
        # [추가] InfluxDB 포맷으로 데이터 조립 및 전송
        json_body = [
            {
                "measurement": "environment_data",
                "tags": {
                    "location": "danger_zone",
                    "node": "worker-2"
                },
                "fields": {
                    "temperature": round(temp, 2),
                    "humidity": round(hum, 2),
                    "pressure": round(press, 2)
                }
            }
            
        ]
        client.write_points(json_body)
        
        time.sleep(2)

except KeyboardInterrupt:
    print("\n[INFO] Measurement stopped by user.", flush=True)
except Exception as e:
    print(f"[ERROR] Unexpected error occurred: {e}", flush=True)