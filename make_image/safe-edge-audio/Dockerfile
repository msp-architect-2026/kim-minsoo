# 1. 이전 AI 파드들과 동일하게 라즈베리파이 5 호환성이 검증된 3.11-bookworm 사용
FROM python:3.11-slim-bookworm

# 2. 마이크 제어 및 파이썬 라이브러리 빌드에 필수적인 시스템 패키지 설치
# (💡 gcc와 python3-dev가 있어야 pyaudio가 에러 없이 설치됩니다)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    portaudio19-dev \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# 3. requirements.txt 설치
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 모델 다운로드 캐시 폴더 생성
RUN mkdir -p /app/tfhub_cache

ENTRYPOINT ["python", "app.py"]