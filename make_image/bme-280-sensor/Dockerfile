FROM python:3.10-slim

# I2C 통신을 위한 필수 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "app.py"]