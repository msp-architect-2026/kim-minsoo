import cv2
from ultralytics import YOLO
import math
import sys
import os
import numpy as np

def calculate_angle(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    rad = math.atan2(dy, dx)
    deg = math.degrees(rad)
    return abs(90 - abs(deg))

def classify_pose(image_path):
    # 📌 사용하실 모델 파일 이름 (필요시 수정)
    model_path = 'pose.pt' 
    
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found: {model_path}")
        sys.exit(1)
        
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        sys.exit(1)

    print(f"[INFO] Starting pose analysis on: {image_path}")
    
    model = YOLO(model_path)
    img = cv2.imread(image_path)
    
    target_width = 640
    ratio = target_width / img.shape[1]
    target_height = int(img.shape[0] * ratio)
    img = cv2.resize(img, (target_width, target_height))

    results = model(img)

    if results[0].boxes is not None and results[0].keypoints is not None:
        boxes = results[0].boxes
        keypoints = results[0].keypoints.data.cpu().numpy()

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            width = x2 - x1
            height = y2 - y1
            
            kps = keypoints[i]
            shoulder = kps[5][:2]
            hip = kps[11][:2]
            conf_s = kps[5][2]
            conf_h = kps[11][2]

            status = "Unknown"
            color = (200, 200, 200)

            if width > height * 1.1: 
                status = "FALLEN (Lying)"
                color = (0, 0, 255)
            elif conf_s > 0.5 and conf_h > 0.5:
                angle = calculate_angle(shoulder, hip)
                if angle > 35:
                    status = f"BENDING ({int(angle)}deg)"
                    color = (0, 165, 255)
                else:
                    status = "STANDING"
                    color = (0, 255, 0)
            else:
                status = "STANDING (Low Conf)"
                color = (0, 255, 0)

            # 그리기 로직
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            if conf_s > 0.5 and conf_h > 0.5:
                cv2.line(img, (int(shoulder[0]), int(shoulder[1])), (int(hip[0]), int(hip[1])), color, 4)

            label = f"{status}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (int(x1), int(y1)-25), (int(x1)+w, int(y1)), color, -1)
            cv2.putText(img, label, (int(x1), int(y1)-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            print(f"[DETECTED] {status}")

    output_filename = "result_" + os.path.basename(image_path)
    cv2.imwrite(output_filename, img)
    print(f"[INFO] Result saved to: {output_filename}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "lying.jpg"
    classify_pose(target_file)