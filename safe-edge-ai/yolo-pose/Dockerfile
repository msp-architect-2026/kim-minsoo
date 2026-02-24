FROM python:3.10-slim

# 이전에 겪었던 OpenCV 에러 방지용 라이브러리 일괄 설치!
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libxcb1 libxext6 libsm6 libxrender1 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "app.py"]