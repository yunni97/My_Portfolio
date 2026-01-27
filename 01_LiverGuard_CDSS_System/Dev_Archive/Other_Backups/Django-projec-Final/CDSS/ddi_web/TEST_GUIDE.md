# 테스트 가이드 - 실제 약물 조합 예시

## 🧪 테스트 시나리오

### ✅ 시나리오 1: 안전한 조합 (LOW 위험도)

**약물 조합:** 고혈압 치료제
- **Lisinopril** (리시노프릴) - ACE 억제제
- **Amlodipine** (암로디핀) - 칼슘채널차단제

#### 웹에서 테스트
```
1. "lisinopril" 입력 → Enter
2. "amlodipine" 입력 → Enter
3. "위험도 분석" 클릭
```

#### 예상 결과
```
✅ 전체 위험도: LOW (40%)
   총 상호작용: 1개
   고위험 조합: 0개

🟡 Lisinopril + Amlodipine
   위험도: 40% (LOW)
   - 저혈압 활동이 증가할 수 있음 (경미)

👍 해석: 함께 복용 가능하지만 혈압 모니터링 권장
```

#### API 테스트
```bash
curl -X POST http://localhost:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"drugs": ["DB00722", "DB00381"]}'
```

---

### ⚠️ 시나리오 2: 중간 위험도 (MODERATE)

**약물 조합:** 항응고제 + 아스피린
- **Aspirin** (아스피린) - 항혈소판제
- **Warfarin** (와파린) - 항응고제

#### 웹에서 테스트
```
1. "aspirin" 또는 "acetylsalicylic" 입력 → Enter
2. "warfarin" 입력 → Enter
3. "위험도 분석" 클릭
```

#### 예상 결과
```
🟠 전체 위험도: MODERATE (70%)
   총 상호작용: 1개
   고위험 조합: 1개

[WARNING] 고위험 조합

🟠 Aspirin + Warfarin
   위험도: 70% (MODERATE)
   - 항응고 활동이 증가하여 출혈 위험 증가

⚠️ 해석: 주의 필요! 함께 복용 시 출혈 위험 증가
          의사와 상담 필수
```

#### API 테스트
```bash
curl -X POST http://localhost:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"drugs": ["DB00945", "DB00682"]}'
```

---

### 🔴 시나리오 3: 고위험 조합 (HIGH)

**약물 조합:** 스타틴 + 피브레이트
- **Simvastatin** (심바스타틴) - 스타틴 (콜레스테롤 약)
- **Gemfibrozil** (젬피브로질) - 피브레이트 (중성지방 약)

#### 웹에서 테스트
```
1. "simvastatin" 입력 → Enter
2. "gemfibrozil" 입력 → Enter
3. "위험도 분석" 클릭
```

#### 예상 결과
```
🔴 전체 위험도: HIGH (95%)
   총 상호작용: 1개
   고위험 조합: 1개

[WARNING] 고위험 조합 (위험도 >= 70%)

🔴 Simvastatin + Gemfibrozil
   위험도: 95% (HIGH)
   - 횡문근융해증, 근육글로불린뇨, CPK 상승 위험

🚨 해석: 매우 위험! 근육 손상 위험
          이 조합은 피해야 합니다
          반드시 의사와 상담
```

#### API 테스트
```bash
curl -X POST http://localhost:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"drugs": ["DB00641", "DB01241"]}'
```

---

## 📊 위험도 등급 설명

### 🟢 SAFE / BENEFICIAL (0-19%)
- 상호작용 없음 또는 유익한 효과
- 안전하게 함께 복용 가능

### 🟡 LOW (20-49%)
- 경미한 상호작용
- 주의하면서 복용 가능
- 증상 모니터링 권장

### 🟠 MODERATE (50-79%)
- 중간 정도 상호작용
- 의사 상담 필요
- 정기적인 검사 필요

### 🔴 HIGH (80-100%)
- 심각한 상호작용
- 생명을 위협할 수 있음
- 이 조합은 피해야 함
- 반드시 의사와 상담

---

## 🎯 실습 과제

### 과제 1: 안전한 조합 찾기
다음 약물 중 2개를 골라 안전한 조합을 만들어보세요:
- Lisinopril
- Amlodipine
- Metoprolol (베타차단제)

**힌트:** 고혈압 약물들은 대부분 함께 사용 가능

### 과제 2: 위험한 조합 찾기
다음 약물들의 위험도를 확인해보세요:
- Aspirin + Warfarin (항응고제 + 항혈소판제)
- Simvastatin + Gemfibrozil (스타틴 + 피브레이트)

**힌트:** 비슷한 작용을 하는 약물은 위험할 수 있음

### 과제 3: 다중 약물 조합
3개 이상의 약물을 입력하여 복잡한 조합을 분석해보세요:
```
예: Aspirin, Metformin, Amlodipine
```

---

## 🧪 추가 테스트 케이스

### 테스트 1: 당뇨병 + 심혈관 질환
```
약물: Metformin, Aspirin, Atorvastatin

검색어:
- "metformin"
- "aspirin"
- "atorvastatin"

예상: MODERATE (저혈당 위험)
```

### 테스트 2: 고혈압 3제 요법
```
약물: Lisinopril, Amlodipine, Hydrochlorothiazide

검색어:
- "lisinopril"
- "amlodipine"
- "hydrochlorothiazide"

예상: LOW (일반적인 조합)
```

### 테스트 3: 통증 관리
```
약물: Ibuprofen, Acetaminophen

검색어:
- "ibuprofen"
- "acetaminophen"

예상: SAFE to LOW
```

---

## 🔍 자동완성 테스트

### 최소 입력 테스트
```
입력: "l"
결과: Lisinopril, Losartan, Levothyroxine, ...

입력: "li"
결과: Lisinopril, Liothyronine, ...

입력: "lis"
결과: Lisinopril

→ 3자만 입력으로 정확한 약물 찾기!
```

### 부분 검색 테스트
```
입력: "metf"
결과: Metformin

입력: "warfa"
결과: Warfarin

입력: "simva"
결과: Simvastatin
```

---

## 📱 사용자 시나리오 테스트

### 시나리오 A: 신규 처방 확인
```
상황: 의사가 새로운 약을 처방했고,
      기존 약과의 상호작용을 확인하고 싶음

절차:
1. 기존 약물 입력 (예: Metformin)
2. 새로운 약물 입력 (예: Aspirin)
3. 위험도 확인
4. 결과를 의사에게 보여주기
```

### 시나리오 B: 약국에서 구매 전 확인
```
상황: 일반의약품 구매 전 상호작용 확인

절차:
1. 현재 복용 중인 처방약 입력
2. 구매하려는 일반의약품 입력
3. 안전성 확인
```

### 시나리오 C: 가족 약물 관리
```
상황: 부모님이 여러 약물을 복용 중

절차:
1. 모든 약물 입력 (3-5개)
2. 전체 위험도 확인
3. 고위험 조합 확인
4. 의사와 상담 일정 잡기
```

---

## ✅ 체크리스트

테스트 완료 시 확인:

- [ ] 안전한 조합 테스트 완료
- [ ] 중간 위험도 조합 테스트 완료
- [ ] 고위험 조합 테스트 완료
- [ ] 자동완성 기능 테스트 완료
- [ ] 키보드 단축키 테스트 완료
- [ ] 3개 이상 약물 조합 테스트 완료
- [ ] API 직접 호출 테스트 완료

---

## 🎓 실제 의학 지식

### Simvastatin + Gemfibrozil이 위험한 이유
- 둘 다 간에서 같은 효소로 대사됨
- 서로의 혈중 농도를 증가시킴
- 근육 손상(횡문근융해증) 위험 증가
- **실제 의료 가이드라인에서도 금지**

### Aspirin + Warfarin이 위험한 이유
- 둘 다 혈액 응고를 방해
- 출혈 위험이 상승적으로 증가
- 특히 위장관 출혈 위험
- **반드시 의사 감독 하에만 사용**

### Lisinopril + Amlodipine이 안전한 이유
- 서로 다른 메커니즘으로 혈압 감소
- 시너지 효과로 더 좋은 혈압 조절
- **실제로 자주 함께 처방됨**

---

## 🚀 빠른 테스트 명령어

### 터미널에서 한 번에 테스트
```bash
# 1. 안전한 조합
curl -X POST http://localhost:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"drugs": ["DB00722", "DB00381"]}' | jq '.data.overall_severity'

# 2. 중간 위험도
curl -X POST http://localhost:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"drugs": ["DB00945", "DB00682"]}' | jq '.data.overall_severity'

# 3. 고위험
curl -X POST http://localhost:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"drugs": ["DB00641", "DB01241"]}' | jq '.data.overall_severity'
```

---

## 📝 테스트 결과 기록

### 내 테스트 결과

| 조합 | 예상 | 실제 | 통과 |
|------|------|------|------|
| Lisinopril + Amlodipine | LOW | ? | [ ] |
| Aspirin + Warfarin | MODERATE | ? | [ ] |
| Simvastatin + Gemfibrozil | HIGH | ? | [ ] |

---

**지금 바로 테스트해보세요!**

```bash
# 서버 실행
cd C:\CDSS\ddi_web
python manage.py runserver

# 브라우저에서 http://localhost:8000/ 접속
```
