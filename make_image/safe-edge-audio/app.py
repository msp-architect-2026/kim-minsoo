import os
# 컨테이너 환경을 위해 캐시 경로를 /app 하위로 설정
os.environ['TFHUB_CACHE_DIR'] = '/app/tfhub_cache'

import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import pyaudio
import csv
import scipy.signal
import sys
import time
from influxdb import InfluxDBClient

# ==========================================
# 1. InfluxDB 설정 및 연결
# ==========================================
DB_HOST = 'influxdb-svc.monitoring.svc.cluster.local'
DB_PORT = 8086
DB_NAME = 'safe_edge_db'

try:
    client = InfluxDBClient(host=DB_HOST, port=DB_PORT)
    client.switch_database(DB_NAME)
    print(f"[INFO] InfluxDB ({DB_NAME}) 연결 성공!", flush=True)
except Exception as e:
    print(f"[ERROR] InfluxDB 연결 실패: {e}", flush=True)
    sys.exit(1)

# ==========================================
# 2. 위험 상황으로 간주할 타겟 소리 (DANGER_LABELS)
# ==========================================
DANGER_LABELS = [
    'Gunshot, gunfire', 
    'Splash, splatter', 
    'Fireworks', 
    'Ratchet, pawl', 
    'Explosion'
]

# ==========================================
# 3. YAMNet 모델 로드
# ==========================================
print("[INFO] Loading YAMNet model...", flush=True)
model = hub.load('https://tfhub.dev/google/yamnet/1')

class_map_path = model.class_map_path().numpy()
class_names = []
with tf.io.gfile.GFile(class_map_path) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        class_names.append(row['display_name'])

# ==========================================
# 4. 오디오 및 마이크 설정
# ==========================================
MIC_RATE = 44100
MODEL_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = MIC_RATE
DIGITAL_GAIN = 7.0 

p = pyaudio.PyAudio()
mic_index = None
target_name = "AB13X" 

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if target_name in info['name'] or 'USB' in info['name']:
        mic_index = i
        print(f"[INFO] Monitoring device connected: {info['name']} (Index: {mic_index})", flush=True)
        break

if mic_index is None:
    print("[WARN] USB microphone not found. Using default device.", flush=True)

try:
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=MIC_RATE,
                    input=True, input_device_index=mic_index,
                    frames_per_buffer=CHUNK)
except OSError:
    MIC_RATE = 48000
    CHUNK = 48000
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=MIC_RATE,
                    input=True, input_device_index=mic_index,
                    frames_per_buffer=CHUNK)

print(f"\n[INFO] Abnormal noise monitoring system running (Gain: x{DIGITAL_GAIN})", flush=True)
print("[INFO] Waiting for acoustic events...\n", flush=True)

# ==========================================
# 5. 실시간 오디오 분석 및 InfluxDB 전송 루프
# ==========================================
try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        waveform = np.frombuffer(data, dtype=np.int16) / 32768.0
        
        waveform = waveform * DIGITAL_GAIN
        waveform = np.clip(waveform, -1.0, 1.0) 

        number_of_samples = round(len(waveform) * float(MODEL_RATE) / MIC_RATE)
        waveform_resampled = scipy.signal.resample(waveform, number_of_samples)
        
        scores, embeddings, spectrogram = model(waveform_resampled)
        prediction = np.mean(scores, axis=0)
        
        top_index = np.argmax(prediction)
        top_name = class_names[top_index]
        confidence = float(prediction[top_index]) # InfluxDB 전송을 위해 float 변환

        is_danger = 0
        detected_event = "None"

        # 위험 소리 판별 로직
        if top_name in DANGER_LABELS and confidence > 0.2:
            is_danger = 1
            detected_event = top_name
            print(f"\n[🚨 DANGER] Event: {top_name} | Confidence: {confidence*100:.1f}%", flush=True)
        else:
            sys.stdout.write(".")
            sys.stdout.flush()

        # InfluxDB로 전송할 데이터 구조 포맷팅
        json_body = [
            {
                "measurement": "acoustic_detection",
                "tags": {
                    "location": "danger_zone", 
                    "node": "worker-2",
                    "event_type": detected_event
                },
                "fields": {
                    "is_danger": is_danger,
                    "confidence": confidence
                }
            }
        ]
        
        # InfluxDB 전송 (에러 발생 시 파드 다운 방지)
        try:
            client.write_points(json_body)
        except Exception as db_err:
            print(f"\n[ERROR] InfluxDB 전송 실패: {db_err}", flush=True)

except KeyboardInterrupt:
    print("\n[INFO] System shutdown.", flush=True)
    stream.stop_stream()
    stream.close()
    p.terminate()