FROM python:3.10-slim

# 마이크 제어(PyAudio)에 필수적인 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    portaudio19-dev \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 모델 다운로드 캐시 폴더 생성
RUN mkdir -p /app/tfhub_cache

ENTRYPOINT ["python", "app.py"]