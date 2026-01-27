"""
Hybrid DDI 예측 시스템
Rule-based (알려진 DDI) + ML 예측 (새로운 조합)
"""

from itertools import combinations
from data_preprocessing import DDIDataLoader
from ml_model import DDIPredictor
from risk_severity_mapping import (
    get_risk_score,
    get_severity_emoji,
    calculate_overall_risk
)


class HybridDDIPredictor:
    """
    Hybrid DDI 예측기
    - 알려진 조합: Rule-based (직접 조회)
    - 새로운 조합: ML 모델 예측
    """

    def __init__(self, data_loader=None, ml_predictor=None):
        self.data_loader = data_loader or DDIDataLoader()
        self.ml_predictor = ml_predictor

    def predict_pair(self, drug1_id, drug2_id):
        """
        두 약물 간 상호작용 예측

        Returns:
            dict: {
                'method': 'rule-based' or 'ml-predicted',
                'has_interaction': bool,
                'interactions': list of interaction info,
                'max_risk_score': int,
                'max_severity': str
            }
        """
        # 1. Rule-based: 알려진 DDI 조회
        known_interactions = self.data_loader.check_known_ddi(drug1_id, drug2_id)

        if known_interactions:
            # 알려진 상호작용이 있음
            interaction_details = []
            risk_scores = []

            for interaction_type in known_interactions:
                risk_info = get_risk_score(interaction_type)
                sentence = self.data_loader.interaction_types.get(
                    interaction_type,
                    "Unknown interaction"
                )

                interaction_details.append({
                    'type': interaction_type,
                    'sentence': sentence,
                    'risk_score': risk_info['score'],
                    'severity': risk_info['severity'],
                    'category': risk_info['category']
                })
                risk_scores.append(risk_info['score'])

            max_risk = max(risk_scores)
            max_severity_idx = risk_scores.index(max_risk)
            max_severity = interaction_details[max_severity_idx]['severity']

            return {
                'method': 'rule-based',
                'has_interaction': True,
                'interactions': interaction_details,
                'max_risk_score': max_risk,
                'max_severity': max_severity
            }

        # 2. ML-based: 모델로 예측
        elif self.ml_predictor and self.ml_predictor.is_trained:
            prediction = self.ml_predictor.predict(drug1_id, drug2_id)

            # 확률이 낮으면 상호작용 없음으로 간주
            if prediction['probability'] < 0.3:
                return {
                    'method': 'ml-predicted',
                    'has_interaction': False,
                    'interactions': [],
                    'max_risk_score': 0,
                    'max_severity': 'SAFE'
                }

            # 예측된 상호작용
            sentence = self.data_loader.interaction_types.get(
                prediction['interaction_type'],
                "Predicted interaction"
            )

            interaction_detail = {
                'type': prediction['interaction_type'],
                'sentence': sentence,
                'risk_score': prediction['risk_score'],
                'severity': prediction['severity'],
                'category': prediction['category'],
                'probability': prediction['probability']
            }

            return {
                'method': 'ml-predicted',
                'has_interaction': True,
                'interactions': [interaction_detail],
                'max_risk_score': prediction['risk_score'],
                'max_severity': prediction['severity']
            }

        # 3. 알 수 없음
        else:
            return {
                'method': 'unknown',
                'has_interaction': False,
                'interactions': [],
                'max_risk_score': 0,
                'max_severity': 'UNKNOWN'
            }

    def predict_multi_drugs(self, drug_ids):
        """
        여러 약물 간의 모든 쌍별 상호작용 예측

        Args:
            drug_ids: list of DrugBank IDs

        Returns:
            dict: {
                'overall_risk_score': int,
                'overall_severity': str,
                'total_interactions': int,
                'pairwise_results': list of interaction results,
                'high_risk_pairs': list of high-risk pairs
            }
        """
        if len(drug_ids) < 2:
            return {
                'overall_risk_score': 0,
                'overall_severity': 'SAFE',
                'total_interactions': 0,
                'pairwise_results': [],
                'high_risk_pairs': []
            }

        # 모든 쌍 생성 (조합)
        pairs = list(combinations(drug_ids, 2))

        pairwise_results = []
        all_risk_scores = []
        high_risk_pairs = []

        for drug1, drug2 in pairs:
            result = self.predict_pair(drug1, drug2)

            # 약물 이름 추가
            result['drug1_id'] = drug1
            result['drug2_id'] = drug2
            result['drug1_name'] = self.data_loader.get_drug_name(drug1)
            result['drug2_name'] = self.data_loader.get_drug_name(drug2)

            pairwise_results.append(result)

            if result['has_interaction']:
                all_risk_scores.append(result['max_risk_score'])

                # 고위험 조합 (위험도 >= 70)
                if result['max_risk_score'] >= 70:
                    high_risk_pairs.append(result)

        # 전체 위험도 계산
        if all_risk_scores:
            overall_score, overall_severity = calculate_overall_risk(all_risk_scores)
        else:
            overall_score = 0
            overall_severity = 'SAFE'

        return {
            'overall_risk_score': overall_score,
            'overall_severity': overall_severity,
            'total_interactions': len([r for r in pairwise_results if r['has_interaction']]),
            'pairwise_results': pairwise_results,
            'high_risk_pairs': high_risk_pairs
        }

    def format_output(self, result):
        """
        사용자 친화적 출력 포맷

        Args:
            result: predict_multi_drugs()의 결과
        """
        output = []

        # 헤더
        output.append("=" * 70)
        output.append("[DDI] 약물 상호작용 위험도 분석")
        output.append("=" * 70)

        # 전체 위험도
        severity_label = result['overall_severity']
        output.append(f"\n[{severity_label}] 전체 위험도: {result['overall_severity']} ({result['overall_risk_score']}%)")
        output.append(f"   총 상호작용: {result['total_interactions']}개")
        output.append(f"   고위험 조합: {len(result['high_risk_pairs'])}개")

        # 고위험 조합 강조
        if result['high_risk_pairs']:
            output.append("\n" + "=" * 70)
            output.append("[WARNING] 고위험 조합 (위험도 >= 70%)")
            output.append("=" * 70)

            for pair in result['high_risk_pairs']:
                output.append(f"\n[HIGH] {pair['drug1_name']} + {pair['drug2_name']}")
                output.append(f"   위험도: {pair['max_risk_score']}% ({pair['max_severity']})")
                output.append(f"   예측 방법: {pair['method']}")

                for interaction in pair['interactions']:
                    severity_tag = f"[{interaction['severity']}]"
                    output.append(f"\n   {severity_tag} {interaction['sentence']}")
                    if 'probability' in interaction:
                        output.append(f"      (예측 확률: {interaction['probability']:.2%})")

        # 모든 조합 상세
        output.append("\n" + "=" * 70)
        output.append("[SUMMARY] 모든 약물 조합 분석")
        output.append("=" * 70)

        for pair in result['pairwise_results']:
            severity_tag = f"[{pair['max_severity']}]"
            output.append(f"\n{severity_tag} {pair['drug1_name']} + {pair['drug2_name']}")

            if not pair['has_interaction']:
                output.append("   [SAFE] 알려진 상호작용 없음")
            else:
                output.append(f"   위험도: {pair['max_risk_score']}% ({pair['max_severity']})")
                output.append(f"   예측 방법: {pair['method']}")

                for interaction in pair['interactions'][:2]:  # 최대 2개만 표시
                    output.append(f"   - {interaction['sentence'][:100]}...")

        output.append("\n" + "=" * 70)

        return "\n".join(output)


def main():
    """테스트용 메인 함수"""
    print("Initializing Hybrid DDI Predictor...")

    # 데이터 로더 초기화
    loader = DDIDataLoader()
    loader.load_all_data()

    # ML 모델 로딩 (이미 학습된 모델이 있다면)
    ml_predictor = None
    # ml_predictor = DDIPredictor(data_loader=loader)
    # ml_predictor.load_model("C:/CDSS/ml_ddi_system/models/ddi_random_forest.pkl")

    # Hybrid 예측기 생성
    predictor = HybridDDIPredictor(data_loader=loader, ml_predictor=ml_predictor)

    # 테스트: 여러 약물 조합
    print("\n" + "=" * 70)
    print("Testing with multiple drugs...")
    print("=" * 70)

    # 예시 약물 (실제 DrugBank ID)
    test_drugs = [
        "DB01115",  # 니페디핀
        "DB08807",  # 암로디핀
        "DB00187",  # 에날라프릴
        "DB00871"   # 메토프롤롤
    ]

    print("\n입력 약물:")
    for drug_id in test_drugs:
        print(f"  - {drug_id}: {loader.get_drug_name(drug_id)}")

    # 예측 실행
    result = predictor.predict_multi_drugs(test_drugs)

    # 결과 출력
    formatted_output = predictor.format_output(result)
    print("\n" + formatted_output)


if __name__ == "__main__":
    main()
