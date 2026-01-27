# Django 약물 상호작용 위험도 분석 웹 서비스

## 시스템 상태

✅ **서버 정상 작동 중!**
- 총 약물: 2,214개
- 총 상호작용 데이터: 222,127개
- ML 모델: 미탑재 (Rule-based로 작동)

## 빠른 시작

### 1. 서버 실행

```bash
cd C:\CDSS\ddi_web
python manage.py runserver 0.0.0.0:8000
```

### 2. 웹 브라우저에서 접속

```
http://localhost:8000/
```

### 3. 사용 방법

1. 약물 이름을 검색 (예: `aspirin`, `metformin`)
2. 여러 약물 추가 (최소 2개)
3. "위험도 분석" 버튼 클릭
4. 결과 확인

## API 엔드포인트

### 1. 헬스 체크
```bash
GET http://localhost:8000/api/health/
```

**응답:**
```json
{
  "success": true,
  "system": "DDI Analysis System",
  "status": "healthy",
  "ml_model_loaded": false,
  "total_drugs": 2214,
  "total_interactions": 222127
}
```

### 2. 약물 검색
```bash
GET http://localhost:8000/api/drugs/search/?q=aspirin
```

**응답:**
```json
{
  "success": true,
  "data": [
    {
      "drug_id": "DB00945",
      "drug_name": "Acetylsalicylic acid"
    }
  ]
}
```

### 3. DDI 분석
```bash
POST http://localhost:8000/api/analyze/
Content-Type: application/json

{
  "drugs": ["aspirin", "metformin", "statin"]
}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "overall_risk_score": 60,
    "overall_severity": "MODERATE",
    "total_interactions": 3,
    "pairwise_results": [...],
    "high_risk_pairs": [...]
  }
}
```

## 프로젝트 구조

```
ddi_web/
├── ddi_service/              # Django 프로젝트 설정
│   ├── settings.py
│   └── urls.py
├── ddi_api/                  # DDI API 앱
│   ├── views.py              # API Views
│   ├── serializers.py        # DRF Serializers
│   ├── urls.py               # URL 설정
│   ├── ddi_core/             # DDI 핵심 모듈
│   │   ├── risk_severity_mapping.py
│   │   ├── data_preprocessing.py
│   │   ├── ml_model.py
│   │   └── hybrid_predictor.py
│   └── templates/            # HTML 템플릿
│       └── ddi_api/
│           └── index.html
├── manage.py
└── requirements.txt
```

## 주요 기능

### 웹 UI
- ✅ 약물 검색 자동완성
- ✅ 여러 약물 선택 및 관리
- ✅ 실시간 위험도 분석
- ✅ 시각적 결과 표시
  - 전체 위험도 점수
  - 고위험 조합 강조
  - 개별 조합별 상세 정보

### API
- ✅ RESTful API
- ✅ JSON 형식
- ✅ CORS 지원
- ✅ 오류 처리

### 데이터
- ✅ 222,127개 알려진 상호작용
- ✅ 113개 상호작용 타입
- ✅ 2,214개 약물 정보
- ✅ 위험도 4단계 분류 (HIGH/MODERATE/LOW/SAFE)

## 테스트

### API 테스트

```bash
# 1. 헬스 체크
curl http://localhost:8000/api/health/

# 2. 약물 검색
curl "http://localhost:8000/api/drugs/search/?q=aspirin"

# 3. DDI 분석
curl -X POST http://localhost:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"drugs": ["DB00945", "DB00331"]}'
```

## 설정

### settings.py 주요 설정

```python
# DDI 시스템 설정
DDI_DATA_DIR = r'C:\CDSS\deepddi2\data'
DDI_ML_MODEL_PATH = r'C:\CDSS\ml_ddi_system\models\ddi_random_forest.pkl'

# CORS 설정 (개발용)
CORS_ALLOW_ALL_ORIGINS = True

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}
```

## 성능 최적화

### 싱글톤 패턴
- 데이터 로더 및 예측기를 싱글톤으로 관리
- 서버 시작 시 한 번만 데이터 로딩
- 메모리 효율적

### 캐싱
향후 Redis 캐싱 추가 가능:
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 배포

### 프로덕션 체크리스트

1. **settings.py 수정**
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
]
```

2. **정적 파일 수집**
```bash
python manage.py collectstatic
```

3. **Gunicorn 사용**
```bash
pip install gunicorn
gunicorn ddi_service.wsgi:application --bind 0.0.0.0:8000
```

4. **Nginx 설정**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## ML 모델 추가 (선택사항)

ML 모델을 학습하여 예측력 향상:

```bash
cd C:\CDSS\ml_ddi_system
python ml_model.py
```

모델 학습 후 `settings.py`에 경로가 자동 설정됩니다.

## 문제 해결

### 포트가 이미 사용 중
```bash
# 다른 포트 사용
python manage.py runserver 8001
```

### 데이터 로딩 실패
- `DDI_DATA_DIR` 경로 확인
- 데이터 파일 존재 여부 확인

### CORS 오류
- `CORS_ALLOW_ALL_ORIGINS = True` 확인
- 브라우저 콘솔에서 오류 메시지 확인

## 라이센스

교육 및 연구 목적

## 지원

이슈 또는 질문은 GitHub Issues로 등록해주세요.
