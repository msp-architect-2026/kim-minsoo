import cv2
import sys
import os
import time
import math
import numpy as np
from datetime import datetime # 👈 추가: 파일명에 시간 기록용
from ultralytics import YOLO
from picamera2 import Picamera2
from influxdb import InfluxDBClient
from datetime import datetime, timedelta  # 👈 timedelta 추가

# 설정값
CLASS_MAP = {0: "FIRE", 1: "SMOKE"}
DB_HOST = 'influxdb-svc.monitoring.svc.cluster.local'
DB_PORT = 8086
DB_NAME = 'safe_edge_db'

# 📸 사진 저장 설정
SNAPSHOT_DIR = '/app/snapshots' # 파드 내부에 저장될 임시 폴더
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
COOLDOWN_SEC = 5               # 연속 촬영 방지 (10초에 1장만)
last_snapshot_time = 0          # 마지막 촬영 시간 기록

def calculate_angle(p1, p2):
    # ... (기존 로직과 완전히 동일하므로 생략) ...
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    rad = math.atan2(dy, dx)
    deg = math.degrees(rad)
    return abs(90 - abs(deg))

def main():
    # 1. InfluxDB 연결 (기존 동일)
    try:
        client = InfluxDBClient(host=DB_HOST, port=DB_PORT)
        client.switch_database(DB_NAME)
        print(f"[INFO] InfluxDB ({DB_NAME}) 연결 성공!", flush=True)
    except Exception as e:
        print(f"[ERROR] InfluxDB 연결 실패: {e}", flush=True)
        sys.exit(1)

    # 2. YOLO 모델 로드 (기존 동일)
    fire_model_path = 'fire.pt'
    pose_model_path = 'pose.pt'
    if not os.path.exists(fire_model_path) or not os.path.exists(pose_model_path):
        print(f"[ERROR] 모델 파일을 찾을 수 없습니다.", flush=True)
        sys.exit(1)
        
    print("[INFO] YOLO 화재 및 Pose 모델 로딩 중...", flush=True)
    fire_model = YOLO(fire_model_path)
    pose_model = YOLO(pose_model_path)

    # 3. Picamera2 초기화 (기존 동일)
    print("[INFO] Picamera2 연결 시도 중...", flush=True)
    try:
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"size": (640, 480)})
        picam2.configure(config)
        picam2.start()
        print("[INFO] ✅ 카메라 연결 및 설정 완료!", flush=True)
        time.sleep(2)
    except Exception as e:
        print(f"[ERROR] 카메라 초기화 실패: {e}", flush=True)
        sys.exit(1)

    print("[INFO] 📷 실시간 통합 감시 시작... (종료: Ctrl+C)", flush=True)
    
    global last_snapshot_time # 전역 변수 참조

    try:
        while True:
            # 4. 프레임 캡처 (기존 동일)
            try:
                frame = picam2.capture_array()
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"[WARN] 프레임 읽기 실패: {e}", flush=True)
                time.sleep(1)
                continue

            fire_detected, fallen_detected, bending_detected = 0, 0, 0

            # 5-A. 화재 추론 (기존 동일)
            fire_results = fire_model(frame_bgr, imgsz=320, verbose=False)
            if fire_results[0].boxes is not None and len(fire_results[0].boxes) > 0:
                for box in fire_results[0].boxes:
                    if int(box.cls[0]) in CLASS_MAP and float(box.conf[0]) > 0.4:
                        fire_detected = 1
                        break
            
            # 5-B. Pose 추론 (기존 동일)
            pose_results = pose_model(frame_bgr, imgsz=320, verbose=False)
            if pose_results[0].boxes is not None and pose_results[0].keypoints is not None:
                boxes = pose_results[0].boxes
                keypoints = pose_results[0].keypoints.data.cpu().numpy()
                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    width, height = x2 - x1, y2 - y1
                    kps = keypoints[i]
                    shoulder, hip = kps[5][:2], kps[11][:2]
                    conf_s, conf_h = kps[5][2], kps[11][2]

                    if width > height * 1.1: 
                        fallen_detected = 1
                    elif conf_s > 0.5 and conf_h > 0.5:
                        if calculate_angle(shoulder, hip) > 35:
                            bending_detected = 1
                        
            status_text = f"🔥Fire: {fire_detected} | 🔴Fallen: {fallen_detected} | 🟠Bending: {bending_detected}"
            print(f"[AI STATUS] {status_text}", flush=True)

            # ==================================================
            # 📸 6. [신규] 이벤트 감지 시 스냅샷 저장 (쿨다운 적용)
            # ==================================================
            if fire_detected or fallen_detected or bending_detected:
                current_time = time.time()
                # 마지막 촬영으로부터 10초(COOLDOWN_SEC)가 지났을 때만 저장
                if current_time - last_snapshot_time > COOLDOWN_SEC:
                    
                    # 어떤 이벤트인지 파악 (파일명용)
                    event_name = "FIRE" if fire_detected else "FALLEN" if fallen_detected else "BENDING"

                    # 1. UTC 시간에 9시간을 더해 한국 시간(KST)으로 변환
                    kst_now = datetime.utcnow() + timedelta(hours=9)

                    # 2. YYMMDDHHMMSS 형식 (예: 260306144027) - 초 단위까지 넣어 덮어쓰기 방어!
                    time_str = kst_now.strftime('%y%m%d%H%M%S')

                    # 3. 원하시는 포맷으로 조립 (예: 260306144027_event_FIRE.jpg)
                    filename = os.path.join(SNAPSHOT_DIR, f"{time_str}_event_{event_name}.jpg")
                    
                    # 디스크에 사진 저장 (0.05초 소요)
                    cv2.imwrite(filename, frame_bgr)
                    print(f"  👉 [📸 SNAPSHOT] 현장 증거 사진 저장 완료: {filename}", flush=True)
                    
                    # 타이머 리셋
                    last_snapshot_time = current_time

            # 7. InfluxDB 전송 및 대기 (기존 동일)
            json_body = [{
                "measurement": "ai_detection",
                "tags": {"location": "danger_zone", "node": "worker-2"},
                "fields": {
                    "fire_detected": fire_detected,
                    "fallen_detected": fallen_detected,
                    "bending_detected": bending_detected
                }
            }]
            client.write_points(json_body)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] 종료.", flush=True)
    finally:
        picam2.stop()

if __name__ == "__main__":
    main()