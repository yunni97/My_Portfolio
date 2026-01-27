# -----------------------------
# 1️⃣ Python base image
# -----------------------------
FROM python:3.11-slim

# 필수 패키지 설치 (gcc, libssl 등)
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 2️⃣ 작업 디렉토리 설정
# -----------------------------
WORKDIR /app

# -----------------------------
# 3️⃣ Python dependencies 설치
# -----------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# 4️⃣ 소스 코드 복사
# -----------------------------
COPY . .

# -----------------------------
# 5️⃣ Django collectstatic (선택)
# -----------------------------
# 환경 변수에 따라 비활성화 가능
RUN python reactproject/manage.py collectstatic --noinput || true

# -----------------------------
# 6️⃣ Gunicorn으로 실행
# -----------------------------
WORKDIR /app/reactproject
CMD ["gunicorn", "reactproject.wsgi:application", "--bind", "0.0.0.0:8000"]

# -----------------------------
# 7️⃣ Expose Port
# -----------------------------
EXPOSE 8000