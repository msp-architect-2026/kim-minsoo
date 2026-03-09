# 라즈베리파이 5(Bookworm)의 기본 파이썬과 동일한 버전인 3.11 사용!
FROM arm64v8/python:3.11-slim-bookworm

# 1. 라즈베리파이 공식 저장소 인증키 및 주소 추가
RUN apt-get update && apt-get install -y wget gnupg2 \
    && wget -qO - http://archive.raspberrypi.com/debian/raspberrypi.gpg.key | gpg --dearmor -o /usr/share/keyrings/raspberrypi-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.gpg] http://archive.raspberrypi.com/debian/ bookworm main" > /etc/apt/sources.list.d/raspi.list

# 2. 필수 시스템 라이브러리 및 Picamera2, libcamera 설치
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libgl1 libxcb1 libxext6 libsm6 libxrender1 \
    python3-picamera2 \
    && rm -rf /var/lib/apt/lists/*

# 3. 껍데기 PIL 폴더 강제 삭제 (pip로 설치될 ultralytics 패키지와 충돌 방지)
RUN rm -rf /usr/lib/python3/dist-packages/PIL /usr/lib/python3/dist-packages/Pillow*

# 작업 폴더 설정
WORKDIR /app

# 4. apt로 설치한 Picamera2(3.11 호환)를 도커의 Python 3.11이 찾을 수 있도록 경로 연결
ENV PYTHONPATH=/usr/lib/python3/dist-packages

# 5. 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 코드와 모델 파일 복사
COPY . .

# 7. 컨테이너 시작 명령어
ENTRYPOINT ["python", "app.py"]