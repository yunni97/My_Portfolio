"""
빠른 테스트 스크립트
ML 모델 없이 Rule-based만으로 즉시 테스트 가능
"""

from data_preprocessing import DDIDataLoader
from hybrid_predictor import HybridDDIPredictor


def test_single_pair():
    """단일 약물 쌍 테스트"""
    print("=" * 70)
    print("테스트 1: 단일 약물 쌍 상호작용 확인")
    print("=" * 70)

    loader = DDIDataLoader()
    loader.load_all_data()

    predictor = HybridDDIPredictor(data_loader=loader, ml_predictor=None)

    # 예시 약물 쌍
    drug1 = "DB01115"  # 니페디핀 (칼슘채널차단제)
    drug2 = "DB08807"  # 암로디핀 (칼슘채널차단제)

    print(f"\n약물 1: {drug1} ({loader.get_drug_name(drug1)})")
    print(f"약물 2: {drug2} ({loader.get_drug_name(drug2)})")

    result = predictor.predict_pair(drug1, drug2)

    print(f"\n예측 방법: {result['method']}")
    print(f"상호작용 여부: {result['has_interaction']}")

    if result['has_interaction']:
        print(f"위험도: {result['max_risk_score']}% ({result['max_severity']})")
        print(f"\n상호작용 상세:")
        for interaction in result['interactions']:
            print(f"  - {interaction['sentence']}")


def test_multiple_drugs():
    """여러 약물 조합 테스트"""
    print("\n\n" + "=" * 70)
    print("테스트 2: 여러 약물 조합 분석")
    print("=" * 70)

    loader = DDIDataLoader()
    loader.load_all_data()

    predictor = HybridDDIPredictor(data_loader=loader, ml_predictor=None)

    # 고혈압 약물 조합 예시
    test_cases = [
        {
            'name': '고혈압 치료제 조합',
            'drugs': [
                "DB01115",  # 니페디핀 (칼슘채널차단제)
                "DB00594",  # 아테놀롤 (베타차단제)
                "DB00492"   # 포시노프릴 (ACE 억제제)
            ]
        },
        {
            'name': '당뇨병 + 심혈관 약물',
            'drugs': [
                "DB00945",  # 아스피린
                "DB00331",  # 메트포르민
                "DB00381",  # 아토르바스타틴 (스타틴)
                "DB00945"   # 클로피도그렐
            ]
        }
    ]

    for test_case in test_cases:
        print(f"\n{'=' * 70}")
        print(f"케이스: {test_case['name']}")
        print(f"{'=' * 70}")

        # 약물 이름 출력
        print("\n입력 약물:")
        for drug_id in test_case['drugs']:
            drug_name = loader.get_drug_name(drug_id)
            print(f"  - {drug_name} ({drug_id})")

        # 분석
        result = predictor.predict_multi_drugs(test_case['drugs'])

        # 포맷팅된 출력
        formatted = predictor.format_output(result)
        print("\n" + formatted)


def test_drug_search():
    """약물 검색 테스트"""
    print("\n\n" + "=" * 70)
    print("테스트 3: 약물 검색 기능")
    print("=" * 70)

    loader = DDIDataLoader()
    loader.load_all_data()

    # 검색 테스트 케이스
    search_queries = [
        "aspirin",
        "metformin",
        "statin",
        "amlodipine",
        "DB00945"
    ]

    for query in search_queries:
        print(f"\n검색어: '{query}'")

        # 이름으로 검색
        matches = []
        query_lower = query.lower()

        if query.startswith("DB"):
            # DrugBank ID
            if query in loader.drug_name_map:
                matches.append((query, loader.drug_name_map[query]))
        else:
            # 약물 이름
            for drug_id, drug_name in loader.drug_name_map.items():
                if query_lower in drug_name.lower():
                    matches.append((drug_id, drug_name))
                    if len(matches) >= 5:
                        break

        if matches:
            print(f"  찾은 약물: {len(matches)}개")
            for drug_id, drug_name in matches[:5]:
                print(f"    - {drug_name} ({drug_id})")
        else:
            print("  결과 없음")


def test_risk_categories():
    """위험도 카테고리별 예시"""
    print("\n\n" + "=" * 70)
    print("테스트 4: 위험도 등급별 상호작용 예시")
    print("=" * 70)

    from risk_severity_mapping import get_risk_score, get_severity_emoji

    categories = {
        'HIGH': [7, 8, 9, 28, 30],
        'MODERATE': [4, 12, 31, 36, 58],
        'LOW': [2, 3, 38, 48, 87],
        'BENEFICIAL': [10, 11, 29]
    }

    loader = DDIDataLoader()
    loader.load_interaction_types()

    for severity, types in categories.items():
        print(f"\n[{severity}] 위험도 예시:")

        for interaction_type in types[:3]:  # 각 카테고리에서 3개씩만
            risk_info = get_risk_score(interaction_type)
            sentence = loader.interaction_types.get(interaction_type, "Unknown")
            print(f"  [{risk_info['score']}%] {sentence[:80]}...")


def main():
    """메인 함수"""
    print("\n" + "=" * 70)
    print("[DDI] 약물 상호작용 시스템 - 빠른 테스트")
    print("=" * 70)
    print("\nRule-based 방식만 사용 (ML 모델 불필요)")
    print("약 222,000개의 알려진 약물 상호작용 데이터 활용\n")

    try:
        # 테스트 실행
        test_single_pair()
        test_multiple_drugs()
        test_drug_search()
        test_risk_categories()

        print("\n\n" + "=" * 70)
        print("[OK] 모든 테스트 완료!")
        print("=" * 70)
        print("\n다음 단계:")
        print("  1. ML 모델 학습: python ml_model.py")
        print("  2. 대화형 모드: python ddi_analyzer.py")
        print("  3. 직접 입력: python ddi_analyzer.py --drugs 'aspirin,metformin'\n")

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
