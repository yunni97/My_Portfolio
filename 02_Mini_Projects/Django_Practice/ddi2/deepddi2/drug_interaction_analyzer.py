"""
약물 상호작용 분석 엔진
여러 약물의 조합을 분석하여 위험도를 계산
"""
import pandas as pd
from itertools import combinations
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from interaction_risk_scorer import get_risk_score, get_risk_level, get_risk_color


@dataclass
class DrugInteraction:
    """약물 상호작용 정보"""
    drug1: str
    drug2: str
    drug1_id: str
    drug2_id: str
    interaction_type: int
    risk_score: int
    risk_level: str
    description: str


@dataclass
class AnalysisResult:
    """분석 결과"""
    total_combinations: int
    interactions_found: int
    overall_risk_score: float
    overall_risk_level: str
    interactions: List[DrugInteraction]
    safe_combinations: List[Tuple[str, str]]


class DrugInteractionAnalyzer:
    """약물 상호작용 분석기"""

    def __init__(self, data_dir: str = './data'):
        """
        초기화

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir

        # 데이터 로드
        self._load_drug_names()
        self._load_interactions()
        self._load_interaction_descriptions()

    def _load_drug_names(self):
        """약물 이름 → DrugBank ID 매핑 로드"""
        self.drug_name_to_id = {}
        self.drug_id_to_name = {}

        with open(f'{self.data_dir}/Approved_drug_Information.txt', 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    drug_id = parts[0]
                    drug_name = parts[1].lower()  # 소문자로 변환

                    # 중복 방지 (첫 번째 것만 저장)
                    if drug_name not in self.drug_name_to_id:
                        self.drug_name_to_id[drug_name] = drug_id

                    if drug_id not in self.drug_id_to_name:
                        self.drug_id_to_name[drug_id] = parts[1]  # 원래 대소문자 유지

        print(f"Loaded {len(self.drug_id_to_name)} drugs")

    def _load_interactions(self):
        """약물 상호작용 데이터 로드"""
        df = pd.read_csv(f'{self.data_dir}/DrugBank_known_ddi.txt', sep='\t')

        # 양방향 검색을 위한 딕셔너리 생성
        self.interactions = {}
        for _, row in df.iterrows():
            drug1 = row['drug1']
            drug2 = row['drug2']
            label = int(row['Label'])

            # 양방향으로 저장
            key1 = (drug1, drug2)
            key2 = (drug2, drug1)

            if key1 not in self.interactions:
                self.interactions[key1] = []
            if key2 not in self.interactions:
                self.interactions[key2] = []

            self.interactions[key1].append(label)
            self.interactions[key2].append(label)

        print(f"Loaded {len(df)} interactions")

    def _load_interaction_descriptions(self):
        """상호작용 타입별 설명 로드"""
        self.interaction_descriptions = {}

        with open(f'{self.data_dir}/Type_information/Interaction_information_model1.csv', 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # 헤더 제외

            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    try:
                        itype = int(parts[0])
                        sentence = parts[1]
                        self.interaction_descriptions[itype] = sentence
                    except ValueError:
                        continue

        print(f"Loaded {len(self.interaction_descriptions)} interaction type descriptions")

    def get_drug_id(self, drug_name: str) -> Optional[str]:
        """
        약물 이름으로 DrugBank ID 검색

        Args:
            drug_name: 약물 이름

        Returns:
            DrugBank ID 또는 None
        """
        # 정확한 매칭
        drug_name_lower = drug_name.lower().strip()
        if drug_name_lower in self.drug_name_to_id:
            return self.drug_name_to_id[drug_name_lower]

        # 부분 매칭 (첫 번째 단어만)
        for name, drug_id in self.drug_name_to_id.items():
            if drug_name_lower in name or name in drug_name_lower:
                return drug_id

        return None

    def analyze_drug_combination(self, drug_names: List[str]) -> AnalysisResult:
        """
        약물 조합 분석

        Args:
            drug_names: 약물 이름 리스트

        Returns:
            분석 결과
        """
        # 약물 이름 → DrugBank ID 변환
        drug_mapping = {}
        unknown_drugs = []

        for name in drug_names:
            drug_id = self.get_drug_id(name)
            if drug_id:
                drug_mapping[name] = drug_id
            else:
                unknown_drugs.append(name)

        if unknown_drugs:
            print(f"Warning: Unknown drugs: {unknown_drugs}")

        # 모든 조합 생성
        valid_drugs = list(drug_mapping.keys())
        all_combinations = list(combinations(valid_drugs, 2))

        # 상호작용 검색
        interactions_found = []
        safe_combinations = []

        for drug1_name, drug2_name in all_combinations:
            drug1_id = drug_mapping[drug1_name]
            drug2_id = drug_mapping[drug2_name]

            # 상호작용 조회
            key = (drug1_id, drug2_id)
            if key in self.interactions:
                interaction_types = self.interactions[key]

                # 가장 위험한 상호작용 선택
                max_risk_type = max(interaction_types, key=lambda t: get_risk_score(t))
                risk_score = get_risk_score(max_risk_type)
                risk_level = get_risk_level(risk_score)

                # 설명 생성
                description = self.interaction_descriptions.get(
                    max_risk_type,
                    "상호작용이 있습니다."
                )
                description = description.replace('#Drug1', drug1_name).replace('#Drug2', drug2_name)

                interaction = DrugInteraction(
                    drug1=drug1_name,
                    drug2=drug2_name,
                    drug1_id=drug1_id,
                    drug2_id=drug2_id,
                    interaction_type=max_risk_type,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    description=description
                )
                interactions_found.append(interaction)
            else:
                safe_combinations.append((drug1_name, drug2_name))

        # 전체 위험도 계산
        if interactions_found:
            # 가장 높은 위험도와 평균 위험도의 가중 평균
            max_risk = max(i.risk_score for i in interactions_found)
            avg_risk = sum(i.risk_score for i in interactions_found) / len(interactions_found)
            overall_risk_score = max_risk * 0.6 + avg_risk * 0.4
        else:
            overall_risk_score = 0

        overall_risk_level = get_risk_level(int(overall_risk_score))

        return AnalysisResult(
            total_combinations=len(all_combinations),
            interactions_found=len(interactions_found),
            overall_risk_score=overall_risk_score,
            overall_risk_level=overall_risk_level,
            interactions=sorted(interactions_found, key=lambda x: x.risk_score, reverse=True),
            safe_combinations=safe_combinations
        )

    def print_analysis_result(self, result: AnalysisResult):
        """
        분석 결과 출력

        Args:
            result: 분석 결과
        """
        # 위험도 레벨 텍스트 표시
        level_symbols = {
            'CRITICAL': '[CRITICAL]',
            'HIGH': '[HIGH]',
            'MEDIUM': '[MEDIUM]',
            'LOW': '[LOW]',
            'MINIMAL': '[MINIMAL]'
        }

        print("\n" + "=" * 80)
        print("Drug Interaction Analysis Result")
        print("=" * 80)

        # 전체 위험도
        symbol = level_symbols.get(result.overall_risk_level, '[MEDIUM]')
        print(f"\n{symbol} Overall Risk: {result.overall_risk_level} ({result.overall_risk_score:.1f}%)")
        print(f"   Total combinations: {result.total_combinations}")
        print(f"   Interactions found: {result.interactions_found}")
        print(f"   Safe combinations: {len(result.safe_combinations)}")

        # 상호작용 발견된 조합
        if result.interactions:
            print(f"\n{'='*80}")
            print(f"Interactions Found ({len(result.interactions)})")
            print(f"{'='*80}\n")

            for i, interaction in enumerate(result.interactions, 1):
                symbol = level_symbols.get(interaction.risk_level, '[MEDIUM]')
                print(f"{i}. {symbol} {interaction.drug1} + {interaction.drug2}")
                print(f"   Risk: {interaction.risk_level} ({interaction.risk_score}%)")
                print(f"   Type: {interaction.interaction_type}")
                print(f"   Description: {interaction.description}")
                print()

        # 안전한 조합
        if result.safe_combinations:
            print(f"{'='*80}")
            print(f"Safe Combinations ({len(result.safe_combinations)})")
            print(f"{'='*80}\n")

            for drug1, drug2 in result.safe_combinations:
                print(f"   [SAFE] {drug1} + {drug2}: No known interactions")

        print("\n" + "=" * 80)


if __name__ == '__main__':
    # 테스트
    analyzer = DrugInteractionAnalyzer()

    # 예제 1: 상호작용이 있는 약물 조합
    print("\nTest 1: Drugs with known interactions")
    drugs = ["Nifedipine", "Sotalol", "Carvedilol", "Nebivolol"]
    result = analyzer.analyze_drug_combination(drugs)
    analyzer.print_analysis_result(result)

    # 예제 2: 간단한 2개 약물 조합
    print("\n\nTest 2: Simple two-drug combination")
    drugs = ["Nifedipine", "Esmolol"]
    result = analyzer.analyze_drug_combination(drugs)
    analyzer.print_analysis_result(result)
