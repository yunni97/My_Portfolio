"""
약물 상호작용 분석 웹 인터페이스 (Streamlit)
"""
import streamlit as st
import pandas as pd
from drug_interaction_analyzer import DrugInteractionAnalyzer
from interaction_risk_scorer import get_risk_color, get_risk_level

# 페이지 설정
st.set_page_config(
    page_title="Drug Interaction Analyzer",
    page_icon="💊",
    layout="wide"
)

# 스타일 설정
st.markdown("""
<style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .risk-critical {
        background-color: #ff4444;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .risk-high {
        background-color: #ff8800;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .risk-medium {
        background-color: #ffbb33;
        color: black;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .risk-low {
        background-color: #00cc44;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .risk-minimal {
        background-color: #0099ff;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# 앱 제목
st.title("💊 Drug Interaction Analyzer")
st.markdown("### Analyze drug combinations for potential interactions")

# 세션 상태 초기화
if 'analyzer' not in st.session_state:
    with st.spinner("Loading drug database..."):
        st.session_state.analyzer = DrugInteractionAnalyzer()
        st.success("✅ Drug database loaded successfully!")

analyzer = st.session_state.analyzer

# 사이드바 - 약물 선택
st.sidebar.header("Select Drugs")
st.sidebar.markdown("Choose drugs to analyze for potential interactions")

# 사용 가능한 약물 리스트 (알파벳 순)
available_drugs = sorted(list(analyzer.drug_id_to_name.values()))

# 약물 검색 및 선택
search_term = st.sidebar.text_input("🔍 Search drug name", "")

if search_term:
    filtered_drugs = [d for d in available_drugs if search_term.lower() in d.lower()]
else:
    filtered_drugs = available_drugs[:100]  # 처음 100개만 표시

st.sidebar.markdown(f"*Showing {len(filtered_drugs)} drugs*")

# 멀티셀렉트로 약물 선택
selected_drugs = st.sidebar.multiselect(
    "Select drugs (2 or more)",
    options=filtered_drugs,
    default=[]
)

# 인기 조합 예제
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Example Combinations")

if st.sidebar.button("High Risk Example"):
    selected_drugs = ["Nifedipine", "Sotalol", "Carvedilol"]

if st.sidebar.button("Medium Risk Example"):
    selected_drugs = ["Leuprolide", "Goserelin"]

# 메인 화면
if len(selected_drugs) < 2:
    st.info("👈 Please select at least 2 drugs from the sidebar to start analysis")

    # 사용법 안내
    st.markdown("---")
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. **Search** for drugs using the search box in the sidebar
    2. **Select** 2 or more drugs from the list
    3. Click **Analyze Interactions** to see results
    4. View **risk scores** and **recommendations**
    """)

    # 통계 정보
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Drugs", f"{len(available_drugs):,}")
    with col2:
        st.metric("Interactions", "222,127")
    with col3:
        st.metric("Interaction Types", "113")

else:
    # 분석 버튼
    if st.button("🔬 Analyze Interactions", type="primary"):
        with st.spinner("Analyzing drug interactions..."):
            result = analyzer.analyze_drug_combination(selected_drugs)

            # 결과 저장
            st.session_state.result = result

    # 결과 표시
    if 'result' in st.session_state and st.session_state.result:
        result = st.session_state.result

        # 전체 위험도 표시
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")

        # 위험도 색상 및 이모지
        risk_emoji = get_risk_color(result.overall_risk_level)
        risk_class = f"risk-{result.overall_risk_level.lower()}"

        st.markdown(f"""
        <div class="{risk_class}">
            <h2>{risk_emoji} Overall Risk: {result.overall_risk_level} ({result.overall_risk_score:.1f}%)</h2>
        </div>
        """, unsafe_allow_html=True)

        # 통계 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Combinations", result.total_combinations)
        with col2:
            st.metric("Interactions Found", result.interactions_found)
        with col3:
            st.metric("Safe Combinations", len(result.safe_combinations))

        # 상호작용 발견된 조합
        if result.interactions:
            st.markdown("---")
            st.markdown("### ⚠️ Interactions Found")

            for i, interaction in enumerate(result.interactions, 1):
                with st.expander(
                    f"{get_risk_color(interaction.risk_level)} {interaction.drug1} + {interaction.drug2} "
                    f"({interaction.risk_level} - {interaction.risk_score}%)",
                    expanded=(i <= 3)  # 처음 3개만 자동 확장
                ):
                    st.markdown(f"**Risk Level:** {interaction.risk_level} ({interaction.risk_score}%)")
                    st.markdown(f"**Interaction Type:** {interaction.interaction_type}")
                    st.markdown(f"**Description:** {interaction.description}")

                    # 권고사항
                    if interaction.risk_level in ['CRITICAL', 'HIGH']:
                        st.warning("⚠️ **Recommendation:** Consult with a healthcare professional before using this combination.")
                    elif interaction.risk_level == 'MEDIUM':
                        st.info("ℹ️ **Recommendation:** Monitor for adverse effects when using this combination.")

        # 안전한 조합
        if result.safe_combinations:
            st.markdown("---")
            st.markdown("### ✅ Safe Combinations")

            safe_df = pd.DataFrame(result.safe_combinations, columns=["Drug 1", "Drug 2"])
            st.dataframe(safe_df, use_container_width=True)
            st.success(f"✅ {len(result.safe_combinations)} drug combinations appear to be safe based on available data.")

        # 다운로드 버튼
        st.markdown("---")
        st.markdown("### 💾 Export Results")

        # 결과를 텍스트로 변환
        export_text = f"""Drug Interaction Analysis Report
{'='*80}

Selected Drugs: {', '.join(selected_drugs)}

Overall Risk: {result.overall_risk_level} ({result.overall_risk_score:.1f}%)
Total Combinations: {result.total_combinations}
Interactions Found: {result.interactions_found}
Safe Combinations: {len(result.safe_combinations)}

{'='*80}
INTERACTIONS FOUND
{'='*80}

"""
        for i, interaction in enumerate(result.interactions, 1):
            export_text += f"""
{i}. {interaction.drug1} + {interaction.drug2}
   Risk: {interaction.risk_level} ({interaction.risk_score}%)
   Type: {interaction.interaction_type}
   Description: {interaction.description}
"""

        if result.safe_combinations:
            export_text += f"\n{'='*80}\nSAFE COMBINATIONS\n{'='*80}\n\n"
            for drug1, drug2 in result.safe_combinations:
                export_text += f"✓ {drug1} + {drug2}\n"

        st.download_button(
            label="📥 Download Report",
            data=export_text,
            file_name="drug_interaction_report.txt",
            mime="text/plain"
        )

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>⚠️ <strong>Disclaimer:</strong> This tool is for educational purposes only.
    Always consult with a qualified healthcare professional before making any medical decisions.</p>
    <p>Data source: DrugBank 5.0</p>
</div>
""", unsafe_allow_html=True)
