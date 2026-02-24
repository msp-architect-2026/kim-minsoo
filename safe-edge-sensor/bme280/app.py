import smbus2
import bme280
import time
import sys

port = 1
address = 0x76

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
        
        # 한 줄로 깔끔하게 출력하여 로그 수집에 최적화
        print(f"[INFO] Temp: {temp:.2f}C | Humidity: {hum:.2f}% | Pressure: {press:.2f}hPa", flush=True)
        
        time.sleep(2)

except KeyboardInterrupt:
    print("\n[INFO] Measurement stopped by user.", flush=True)
except Exception as e:
    print(f"[ERROR] Unexpected error occurred: {e}", flush=True)