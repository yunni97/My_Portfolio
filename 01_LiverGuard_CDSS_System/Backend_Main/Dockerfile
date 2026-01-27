# 1. Python 3.10 기반 이미지
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# 4. OS 패키지 설치 (MySQL-client + C 빌드 툴)
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 5. Python 라이브러리 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# 6. Django 프로젝트 복사
COPY . /app/

# 7. Gunicorn 실행 (프로덕션 권장)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "1", "--chdir", "/app/config"]
