"""
Drug Interaction Analyzer 사용 예제
"""
from drug_interaction_analyzer import DrugInteractionAnalyzer

def main():
    print("=" * 80)
    print("Drug Interaction Analyzer - Example Usage")
    print("=" * 80)

    # 분석기 초기화
    print("\nInitializing analyzer...")
    analyzer = DrugInteractionAnalyzer()

    # 예제 1: 고위험 조합
    print("\n" + "=" * 80)
    print("Example 1: High Risk Combination")
    print("=" * 80)
    drugs = ["Nifedipine", "Sotalol", "Carvedilol"]
    print(f"\nAnalyzing drugs: {', '.join(drugs)}")
    result = analyzer.analyze_drug_combination(drugs)
    analyzer.print_analysis_result(result)

    # 예제 2: 안전한 조합
    print("\n" + "=" * 80)
    print("Example 2: Safe Combination")
    print("=" * 80)
    drugs = ["Leuprolide", "Erythropoietin"]
    print(f"\nAnalyzing drugs: {', '.join(drugs)}")
    result = analyzer.analyze_drug_combination(drugs)
    analyzer.print_analysis_result(result)

    # 예제 3: 사용자 입력
    print("\n" + "=" * 80)
    print("Example 3: Custom Input")
    print("=" * 80)

    # 사용 가능한 약물 샘플 표시
    sample_drugs = list(analyzer.drug_id_to_name.values())[:20]
    print("\nSample available drugs:")
    for i, drug in enumerate(sample_drugs, 1):
        print(f"  {i}. {drug}")

    print("\nEnter drug names separated by commas (or press Enter to skip):")
    user_input = input("> ").strip()

    if user_input:
        drugs = [d.strip() for d in user_input.split(",")]
        print(f"\nAnalyzing drugs: {', '.join(drugs)}")
        result = analyzer.analyze_drug_combination(drugs)
        analyzer.print_analysis_result(result)
    else:
        print("Skipped custom input.")

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
    print("\nTip: Run 'streamlit run app_streamlit.py' for a web interface!")


if __name__ == '__main__':
    main()
