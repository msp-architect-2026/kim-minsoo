import cv2
from ultralytics import YOLO
import sys
import os

CLASS_MAP = {0: "FIRE", 1: "SMOKE"}
COLORS = {0: (0, 0, 255), 1: (200, 200, 200)}

def test_fire_smoke_detection(image_path):
    model_path = 'fire.pt'
    
    # 1. 파일 존재 여부 검증
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found: {model_path}")
        sys.exit(1)
        
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        sys.exit(1)

    print(f"[INFO] Starting inference on: {image_path}")
    
    # 2. 모델 로드 및 이미지 읽기
    model = YOLO(model_path)
    img = cv2.imread(image_path)
    img = cv2.resize(img, (640, int(640 * img.shape[0] / img.shape[1])))

    # 3. 추론 실행
    results = model(img)
    detected_count = 0
    
    # 4. 결과 분석
    if results[0].boxes is not None:
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            if cls_id in CLASS_MAP and conf > 0.4:
                detected_count += 1
                label_text = CLASS_MAP[cls_id]
                color = COLORS.get(cls_id, (0, 255, 0))
                
                # 좌표 계산 및 박스 그리기
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                
                label_display = f"{label_text} ({conf*100:.0f}%)"
                cv2.putText(img, label_display, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                print(f"[DETECTED] {label_text} - Confidence: {conf:.2f}")

    if detected_count == 0:
        print("[INFO] No fire or smoke detected.")

    # 5. 결과 저장
    output_filename = "result_" + os.path.basename(image_path)
    cv2.imwrite(output_filename, img)
    print(f"[INFO] Result saved to: {output_filename}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "mini_fire.jpg"
    test_fire_smoke_detection(target_file)