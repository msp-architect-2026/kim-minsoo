FROM python:3.10-slim

# OpenCV 구동에 필요한 최소한의 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 작업 폴더 설정
WORKDIR /app

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드와 모델 파일 복사
COPY . .

# 🚀 추가된 부분: 11분 재설치를 피하기 위해 맨 마지막에 라이브러리 덧붙임
# 🚀 추가된 부분: libgl1 을 패키지 목록에 추가합니다.
RUN apt-get update && apt-get install -y \
    libxcb1 libxext6 libsm6 libxrender1 libgl1 \
    && rm -rf /var/lib/apt/lists/*


# 컨테이너가 켜질 때 실행할 기본 명령어
ENTRYPOINT ["python", "app.py"]