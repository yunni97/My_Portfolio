"""
약물 상호작용 위험도 분석기 - 메인 애플리케이션
사용자가 약물 리스트를 입력하면 위험도를 분석하여 출력
"""

import argparse
import json
from pathlib import Path

from data_preprocessing import DDIDataLoader
from ml_model import DDIPredictor
from hybrid_predictor import HybridDDIPredictor


class DDIAnalyzer:
    """약물 상호작용 분석 메인 클래스"""

    def __init__(self, model_path=None):
        """
        초기화

        Args:
            model_path: ML 모델 경로 (None이면 Rule-based만 사용)
        """
        print("🔄 시스템 초기화 중...")

        # 데이터 로더
        self.data_loader = DDIDataLoader()
        self.data_loader.load_all_data()

        # ML 모델 (있다면 로딩)
        self.ml_predictor = None
        if model_path and Path(model_path).exists():
            print(f"🤖 ML 모델 로딩: {model_path}")
            self.ml_predictor = DDIPredictor(data_loader=self.data_loader)
            self.ml_predictor.load_model(model_path)
        else:
            print("⚠️  ML 모델 없음 - Rule-based만 사용합니다")

        # Hybrid 예측기
        self.predictor = HybridDDIPredictor(
            data_loader=self.data_loader,
            ml_predictor=self.ml_predictor
        )

        print("✅ 초기화 완료!\n")

    def search_drug(self, query):
        """
        약물 검색 (이름 또는 ID)

        Args:
            query: 약물 이름 또는 DrugBank ID

        Returns:
            list: 매칭되는 (drug_id, drug_name) 리스트
        """
        query_lower = query.lower().strip()

        matches = []

        # DrugBank ID로 직접 검색
        if query.startswith("DB") and query in self.data_loader.drug_name_map:
            drug_name = self.data_loader.drug_name_map[query]
            matches.append((query, drug_name))
            return matches

        # 약물 이름으로 검색
        for drug_id, drug_name in self.data_loader.drug_name_map.items():
            if query_lower in drug_name.lower():
                matches.append((drug_id, drug_name))

                # 정확히 일치하면 그것만 반환
                if query_lower == drug_name.lower():
                    return [(drug_id, drug_name)]

        return matches[:10]  # 최대 10개까지

    def analyze_drugs(self, drug_inputs):
        """
        여러 약물에 대한 상호작용 분석

        Args:
            drug_inputs: 약물 이름 또는 ID 리스트

        Returns:
            dict: 분석 결과
        """
        # 1. 약물 ID 확인
        drug_ids = []
        drug_names = []

        print("🔍 약물 검색 중...\n")

        for drug_input in drug_inputs:
            matches = self.search_drug(drug_input)

            if not matches:
                print(f"❌ '{drug_input}' - 찾을 수 없습니다")
                continue

            if len(matches) > 1:
                print(f"⚠️  '{drug_input}' - 여러 약물이 검색되었습니다:")
                for i, (drug_id, drug_name) in enumerate(matches[:5], 1):
                    print(f"   {i}. {drug_name} ({drug_id})")
                print(f"   첫 번째 약물을 사용합니다: {matches[0][1]}\n")

            drug_id, drug_name = matches[0]
            drug_ids.append(drug_id)
            drug_names.append(drug_name)
            print(f"✓ {drug_name} ({drug_id})")

        if len(drug_ids) < 2:
            print("\n❌ 분석하려면 최소 2개의 약물이 필요합니다")
            return None

        print(f"\n📊 {len(drug_ids)}개 약물에 대한 상호작용 분석 시작...\n")

        # 2. 예측 실행
        result = self.predictor.predict_multi_drugs(drug_ids)

        # 3. 결과 포맷팅
        formatted = self.predictor.format_output(result)

        return {
            'drug_ids': drug_ids,
            'drug_names': drug_names,
            'result': result,
            'formatted_output': formatted
        }

    def interactive_mode(self):
        """대화형 모드"""
        print("=" * 70)
        print("💊 약물 상호작용 위험도 분석기")
        print("=" * 70)
        print("\n사용법:")
        print("  - 약물 이름 또는 DrugBank ID를 입력하세요")
        print("  - 쉼표(,)로 구분하여 여러 약물 입력")
        print("  - 'quit' 입력 시 종료\n")
        print("=" * 70)

        while True:
            try:
                user_input = input("\n약물 입력 (예: aspirin, metformin, statin): ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 종료합니다")
                    break

                if not user_input:
                    continue

                # 쉼표로 분리
                drug_inputs = [d.strip() for d in user_input.split(',')]

                # 분석 실행
                result = self.analyze_drugs(drug_inputs)

                if result:
                    print("\n" + result['formatted_output'])

            except KeyboardInterrupt:
                print("\n\n👋 종료합니다")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")

    def batch_mode(self, input_file, output_file=None):
        """
        배치 모드 - 파일에서 약물 리스트를 읽어서 분석

        Args:
            input_file: 입력 파일 (한 줄에 하나의 약물 리스트, 쉼표로 구분)
            output_file: 출력 파일 (None이면 화면 출력)
        """
        print(f"📂 파일에서 읽기: {input_file}\n")

        results = []

        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                print(f"\n{'=' * 70}")
                print(f"처리 중: 라인 {line_num}")
                print(f"{'=' * 70}")

                drug_inputs = [d.strip() for d in line.split(',')]
                result = self.analyze_drugs(drug_inputs)

                if result:
                    results.append(result)
                    print("\n" + result['formatted_output'])

        # 출력 파일에 저장
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(result['formatted_output'])
                    f.write("\n\n")
            print(f"\n💾 결과 저장: {output_file}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="약물 상호작용 위험도 분석기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 대화형 모드
  python ddi_analyzer.py

  # 직접 약물 입력
  python ddi_analyzer.py --drugs "aspirin,metformin,statin"

  # 배치 모드 (파일에서 읽기)
  python ddi_analyzer.py --input drugs.txt --output results.txt

  # ML 모델 사용
  python ddi_analyzer.py --model models/ddi_random_forest.pkl --drugs "DB00945,DB00188"
        """
    )

    parser.add_argument(
        '--drugs',
        type=str,
        help='약물 리스트 (쉼표로 구분)'
    )

    parser.add_argument(
        '--input',
        type=str,
        help='입력 파일 (배치 모드)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='출력 파일 (배치 모드)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='ML 모델 경로'
    )

    args = parser.parse_args()

    # 분석기 초기화
    analyzer = DDIAnalyzer(model_path=args.model)

    # 실행 모드 결정
    if args.drugs:
        # 직접 약물 입력
        drug_inputs = [d.strip() for d in args.drugs.split(',')]
        result = analyzer.analyze_drugs(drug_inputs)
        if result:
            print("\n" + result['formatted_output'])

    elif args.input:
        # 배치 모드
        analyzer.batch_mode(args.input, args.output)

    else:
        # 대화형 모드
        analyzer.interactive_mode()


if __name__ == "__main__":
    main()
