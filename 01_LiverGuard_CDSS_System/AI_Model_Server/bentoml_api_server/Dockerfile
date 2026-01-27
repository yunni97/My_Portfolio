# 1. 베이스 이미지 (가장 무거운 부분 - 변경 거의 없음)
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 시스템 패키지 설치 (자주 안 바뀜 -> 캐시됨)
RUN apt-get update && apt-get install -y git libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

# 4. [핵심] 라이브러리 설치 (requirements.txt가 있다면 그걸 먼저 복사)
# 지금은 직접 설치하시니까, 이 부분은 그대로 둡니다.
# 이 줄은 한 번 빌드되면, 다음부터는 '캐시(Cache)'를 써서 0초 만에 통과합니다!
RUN pip install --no-cache-dir bentoml numpy nibabel pydicom dicom2nifti nnunetv2 requests

# -----------------------------------------------------------
# 5. [여기서부터 바뀝니다] 소스 코드 복사
# 위쪽(1~4번)은 그대로 두고, 오직 이 밑에 있는 파일이 바뀔 때만
# Docker가 "여기서부터만 다시 하자!"라고 동작합니다.
COPY . /app

# 6. 실행 설정
EXPOSE 3000
CMD ["bentoml", "serve", "service:NNUNetService", "--host", "0.0.0.0", "--port", "3000"]