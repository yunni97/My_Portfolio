# C:\Users\401-14\Desktop\ddi-model\api_v2.py
# (최종본: DB연동, KFDA(dur_items) 최적화, 비동기(Async) 검색 적용)

import sys
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pickle
import joblib
import json
from itertools import combinations
from flask import Flask, request, jsonify
from flask_cors import CORS
import platform
import subprocess
import pandas as pd
import re
import io, base64
import os
from dotenv import load_dotenv

# --- 환경 변수 로드 ---
load_dotenv()

# --- DB 연동을 위한 라이브러리 추가 ---
from sqlalchemy import create_engine,text
import pymysql
# (터미널에서 pip install sqlalchemy pymysql pandas numpy joblib flask flask-cors waitress python-dotenv)
from ddi_map import get_ddi_info
# 모델 import
from services.cox_model_service import get_cox_model

print("--- 1. AI 서버 (Flask, DB연동 v2) 시작 중 ---")

# --- DB 연결 설정 (.env에서 불러오기) ---
db_user = os.getenv("MYSQL_USER")
db_password = os.getenv("MYSQL_PASSWORD")
db_host = os.getenv("MYSQL_HOST")
db_port = os.getenv("MYSQL_PORT")
db_name = os.getenv("MYSQL_DATABASE")

db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# --- 전역 변수 선언 ---
GLOBAL_DB_ENGINE = None
# GLOBAL_DRUG_LIST_FOR_SEARCH = [] # <-- [삭제] 비동기 검색으로 변경
GLOBAL_MODEL = None
GLOBAL_THRESHOLDS = {}
GLOBAL_NAME_TO_SMILES = {}
GLOBAL_MLB_CLASSES_STR = []
GLOBAL_EMBEDDING_MAP = {}
# GLOBAL_AI_NAME_MAP = {} # <-- [삭제] (AI_NAME_MAP은 ENG_TO_KOR_MAP으로 통합)
GLOBAL_ENG_TO_KOR_MAP = {}
GLOBAL_DB_LOOKUP = {}
GLOBAL_DB_NAME_TO_ID = {}
GLOBAL_DB_ID_TO_NAME = {}
GLOBAL_DB_NAME_LIST = []
GLOBAL_ENG_TO_CLASS = {}
GLOBAL_CLASS_TO_ENG_LIST = {}

# ----------------------------------------------------------------------
# 1. DB 엔진 생성 및 자산 로드
# ----------------------------------------------------------------------
try:
    # --- [수정] DB 엔진 생성 ---
    try:
        GLOBAL_DB_ENGINE = create_engine(db_url)
        print("--- 0. DB 엔진 생성 완료 ---")
    except Exception as e:
        print(f"❌ 치명적 오류: DB 엔진 생성 실패: {e}")
        sys.exit(1) # DB 연결 실패 시 서버 종료

    PROJECT_ROOT = pathlib.Path(__file__).parent 

    # --- [유지] AI 모델 자산 경로 (PKL, JOBLIB) ---
    SMILES_MAP_PATH = PROJECT_ROOT / 'data' / 'drug_name_to_smiles.pkl'
    MLB_CLASSES_PATH = PROJECT_ROOT / 'data' / 'mlb_classes_v2.pkl'
    EMBEDDING_MAP_PATH = PROJECT_ROOT / 'data' / 'embedding_map_v2.pkl'
    MODEL_PATH = PROJECT_ROOT / 'models' / 'ovr_xgb_model_v4_clinical.joblib'
    THRESHOLDS_PATH = PROJECT_ROOT / 'models' / 'optimal_thresholds_v4_clinical.json'

    print("--- 2. AI 자산 (PKL/Model) 로드 시작 ---")
    
    # [유지] AI 모델 및 PKL 파일은 메모리에 로드
    GLOBAL_MODEL = joblib.load(MODEL_PATH)
    with open(THRESHOLDS_PATH, 'r') as f: GLOBAL_THRESHOLDS = json.load(f)
    with open(SMILES_MAP_PATH, 'rb') as f: GLOBAL_NAME_TO_SMILES = pickle.load(f)
    with open(MLB_CLASSES_PATH, 'rb') as f:
        mlb_classes_raw = pickle.load(f)
        GLOBAL_MLB_CLASSES_STR = [str(c) for c in mlb_classes_raw]
    with open(EMBEDDING_MAP_PATH, 'rb') as f: GLOBAL_EMBEDDING_MAP = pickle.load(f)
    print("--- 3. AI 자산 (PKL/Model) 로드 완료 ---")

    print("--- 4. DB 기반 맵 로드 시작 (서버 메모리 캐싱) ---")

    # --- [수정] 맵핑 정보 로드 (한/영 변환용) ---
    def load_ai_name_map():
        # (AI 예측 및 한글명 반환에 필요한 GLOBAL_ENG_TO_KOR_MAP만 로드)
        global GLOBAL_ENG_TO_KOR_MAP
        try:
            map_df = pd.read_sql("SELECT KoreanName, EnglishName FROM dur_drug_mapping", GLOBAL_DB_ENGINE)
            map_df = map_df.dropna(subset=['EnglishName', 'KoreanName'])
            # (AI 예측에 필요한 ENG -> KOR 맵만 유지)
            map_df_unique_eng = map_df.drop_duplicates(subset=['EnglishName'])
            GLOBAL_ENG_TO_KOR_MAP = pd.Series(map_df_unique_eng.KoreanName.values, index=map_df_unique_eng.EnglishName).to_dict()
            print("✅ [1/3] 한/영 맵핑 사전 로드 완료 (from DB: dur_drug_mapping)")
        except Exception as e:
            print(f"❌ 오류 [1/3]: 한/영 맵핑 (DB) 로드 실패: {e}")

    # --- [수정] DrugBank DB 로드 (from dur_ddi_drugbank, dur_drug_info) ---
    def load_drugbank_database():
        global GLOBAL_DB_LOOKUP, GLOBAL_DB_NAME_TO_ID, GLOBAL_DB_ID_TO_NAME, GLOBAL_DB_NAME_LIST
        try:
            # 1. DDI 관계 로드
            db_ddi_df = pd.read_sql("SELECT drug1_id, drug2_id, interaction_type FROM dur_ddi_drugbank", GLOBAL_DB_ENGINE)
            
            # 2. 약물 ID/Name 로드
            df_drugs = pd.read_sql("SELECT drugbank_id, name FROM dur_drug_info", GLOBAL_DB_ENGINE)
            
            # 3. 기존 api.py 로직을 DB 데이터로 수행
            ddi_related_ids = set(db_ddi_df['drug1_id'].unique()) | set(db_ddi_df['drug2_id'].unique())
            df_drugs_filtered = df_drugs[df_drugs['drugbank_id'].isin(ddi_related_ids)]

            GLOBAL_DB_NAME_TO_ID = pd.Series(df_drugs_filtered['drugbank_id'].values, index=df_drugs_filtered['name'].str.lower()).to_dict()
            GLOBAL_DB_ID_TO_NAME = pd.Series(df_drugs_filtered['name'].apply(lambda x: x.capitalize() if isinstance(x, str) else x).values, index=df_drugs_filtered['drugbank_id']).to_dict()
            
            db_ddi_df['pair_key'] = db_ddi_df.apply(lambda row: frozenset([row['drug1_id'], row['drug2_id']]), axis=1)
            GLOBAL_DB_LOOKUP = db_ddi_df.drop_duplicates(subset=['pair_key', 'interaction_type']).groupby('pair_key')['interaction_type'].apply(list).to_dict()
            
            GLOBAL_DB_NAME_LIST = list(df_drugs_filtered['name'].apply(lambda x: x.capitalize() if isinstance(x, str) else x).unique())
            print("✅ [2/3] DrugBank DB (1차) 로드 완료 (from DB: dur_ddi_drugbank, dur_drug_info)")
        except Exception as e:
            print(f"❌ 오류 [2/3]: DrugBank DB (DB) 로드 실패: {e}")
            
    # --- [수정] 약물 마스터 DB 로드 (from dur_drug_info) ---
    def load_drug_master_info():
        global GLOBAL_ENG_TO_CLASS, GLOBAL_CLASS_TO_ENG_LIST
        try:
            # '대체약물용 계열(clean_category)'을 DB에서 로드
            master_df = pd.read_sql("SELECT name, clean_category FROM dur_drug_info", GLOBAL_DB_ENGINE)
            master_df = master_df.dropna(subset=['name', 'clean_category'])
            master_df = master_df.drop_duplicates(subset=['name', 'clean_category'])
            
            # (api.py의 drug_name 대신 DB의 name 사용)
            GLOBAL_ENG_TO_CLASS = pd.Series(
                master_df.drop_duplicates(subset=['name']).clean_category.values, 
                index=master_df.drop_duplicates(subset=['name']).name
            ).to_dict()
            GLOBAL_CLASS_TO_ENG_LIST = master_df.groupby('clean_category')['name'].apply(list).to_dict()
            print("✅ [3/3] 약물 계열(대체약물) DB 로드 완료 (from DB: dur_drug_info)")
        except Exception as e:
            print(f"❌ 오류 [3/3]: 약물 계열 DB (DB) 로드 실패: {e}")

    # --- 서버 시작 시 로딩 실행 ---
    load_ai_name_map()
    load_drugbank_database()
    load_drug_master_info()

    # --- [삭제] create_searchable_drug_list() 함수 및 호출 ---
    
    print("--- 5. 모든 자산 로드 완료. 서버가 준비되었습니다. ---")

except Exception as e:
    print(f"❌ 치명적 오류: 자산 로드 실패: {e}")
    sys.exit(1)

# ----------------------------------------------------------------------
# 2. 헬퍼 함수 (AI/DB 검사, ddi_map 등)
# ----------------------------------------------------------------------

def get_ddi_info_from_map(ddi_id_int: int):
    try: return get_ddi_info(ddi_id_int)
    except Exception: return None

def get_korean_name(eng_name):
    # .capitalize() 추가: 'warfarin' -> 'Warfarin' (DB에 저장된 이름)
    kor_name = GLOBAL_ENG_TO_KOR_MAP.get(eng_name.capitalize())
    if kor_name:
        return f"{kor_name} ({eng_name})"
    return eng_name

# --- AI 예측 함수 (로직 유지) ---
def get_drug_vector(drug_name):
    if drug_name not in GLOBAL_NAME_TO_SMILES: return None 
    smiles = GLOBAL_NAME_TO_SMILES[drug_name]
    if smiles not in GLOBAL_EMBEDDING_MAP: return None 
    try: return np.array(GLOBAL_EMBEDDING_MAP[smiles]).reshape(1, -1)
    except Exception: return None

def run_ai_prediction_for_pair(drug_a_name, drug_b_name):
    if GLOBAL_MODEL is None or not isinstance(GLOBAL_MODEL, list): return None
    vec_a, vec_b = get_drug_vector(drug_a_name), get_drug_vector(drug_b_name)
    if vec_a is None or vec_b is None: return None 
    X_input = np.concatenate([vec_a, vec_b], axis=1)
    try:
        X_input_cpu = np.ascontiguousarray(X_input, dtype=np.float32)
        probs_list = [model.predict_proba(X_input_cpu)[0, 1] for model in GLOBAL_MODEL]
        y_proba = np.array(probs_list)
    except Exception as e:
        print(f"❌ 모델 예측 실패: {e}")
        return None

    results_high, results_medium, results_low = [], [], []
    for i, ddi_id_str in enumerate(GLOBAL_MLB_CLASSES_STR):
        if i >= len(y_proba): break
        prob = float(y_proba[i])
        threshold = GLOBAL_THRESHOLDS.get(ddi_id_str)
        if threshold is None: continue

        if prob > float(threshold):
            try:
                ddi_id_int = int(float(ddi_id_str))
                ddi_info = get_ddi_info(ddi_id_int)
                if ddi_info is None: continue
                name, desc = ddi_info['title'], ddi_info['description']
                desc = desc.replace("#Drug1", drug_a_name).replace("#Drug2", drug_b_name)
                prob_percent = float(round(prob * 100, 2))
                event_data = {"event": name, "probability": prob_percent, "description": desc}

                if prob_percent > 50: results_high.append(event_data)
                elif prob_percent >= 20: results_medium.append(event_data)
                elif prob_percent > 0: results_low.append(event_data)
            except Exception as e:
                print(f"❌ DDI ID {ddi_id_str} 처리 중 오류: {e}")

    final_result = {
        "pair_name": f"'{drug_a_name}' + '{drug_b_name}'",
        "high_risk": sorted(results_high, key=lambda x: x["probability"], reverse=True),
        "medium_risk": sorted(results_medium, key=lambda x: x["probability"], reverse=True),
        "low_risk": sorted(results_low, key=lambda x: x["probability"], reverse=True)
    }
    if results_high or results_medium or results_low:
        return final_result
    else:
        return None

# --- DB 검사 함수 (check_drugbank_ddi, check_kfda_ddi) ---
def check_drugbank_ddi(drug_list_english):
    found_contraindications = []
    drug_ids = {}
    for eng_name in drug_list_english:
        drug_id = GLOBAL_DB_NAME_TO_ID.get(eng_name.lower())
        if drug_id: drug_ids[eng_name] = drug_id
    drug_names = list(drug_ids.keys())
    if len(drug_ids) < 2: return []

    for name_a, name_b in combinations(drug_names, 2):
        id_a, id_b = drug_ids[name_a], drug_ids[name_b]
        pair_key = frozenset([id_a, id_b])
        if pair_key in GLOBAL_DB_LOOKUP:
            ddi_type_ids = GLOBAL_DB_LOOKUP[pair_key]
            for ddi_id_str in ddi_type_ids:
                try:
                    ddi_id_int = int(ddi_id_str)
                    ddi_info = get_ddi_info_from_map(ddi_id_int)
                    if ddi_info is None: continue
                    name, desc = ddi_info['title'], ddi_info['description']
                    desc_replaced = desc.replace("#Drug1", name_a).replace("#Drug2", name_b)
                    found_contraindications.append({"drug_a": name_a, "drug_b": name_b, "ddi_id": ddi_id_int, "event": name, "description": desc_replaced})
                except Exception: pass
    return found_contraindications

# --- [수정] KFDA 검사 (from dur_items, v4 - FULLTEXT 최적화) ---
def check_kfda_ddi_from_db(drug_list_korean):
    """
    KFDA 2차 방어선 검사 (최적화 v4)
    DB(dur_items)를 FULLTEXT 인덱스(MATCH...AGAINST)로 실시간 조회합니다.
    """
    found_contraindications = []
    if len(drug_list_korean) < 2: 
        return found_contraindications
    
    col_a = '주성분' 
    col_b = '병용금기DUR성분명'
    col_reason = '금기내용'
    
    try:
        with GLOBAL_DB_ENGINE.connect() as conn:
            for drug_a_kor, drug_b_kor in combinations(drug_list_korean, 2):
                
                # FULLTEXT 인덱스를 사용하는 MATCH ... AGAINST (BOOLEAN MODE)
                query_sql = text(f"""
                SELECT DISTINCT `{col_reason}` 
                FROM dur_items 
                WHERE 
                    (MATCH(`{col_a}`) AGAINST(:a IN BOOLEAN MODE) AND MATCH(`{col_b}`) AGAINST(:b IN BOOLEAN MODE))
                    OR 
                    (MATCH(`{col_a}`) AGAINST(:b IN BOOLEAN MODE) AND MATCH(`{col_b}`) AGAINST(:a IN BOOLEAN MODE))
                LIMIT 1
                """)
                
                # 파라미터를 딕셔너리로 전달 (예: '아미오다론')
                result = conn.execute(query_sql, {"a": drug_a_kor, "b": drug_b_kor})
                row = result.fetchone()
                
                if row:
                    found_contraindications.append({
                        "drug_a": drug_a_kor, 
                        "drug_b": drug_b_kor, 
                        "reason": row[0]
                    })
        
        if not found_contraindications: 
            return []
        
        result_df = pd.DataFrame(found_contraindications).drop_duplicates()
        return result_df.to_dict('records')
        
    except Exception as e:
        print(f"❌ KFDA DB (dur_items) 조회 오류: {e}")
        return [] 

# --- 대체 약물 헬퍼 함수 (모든 capitalize 수정 적용) ---
def get_problematic_drugs(drugbank_ddi_results, ai_ddi_results):
    problematic_drugs = {} 
    
    for item in drugbank_ddi_results:
        ddi_info = get_ddi_info_from_map(item['ddi_id'])
        if ddi_info and ddi_info['risk_level'] in ["HIGH", "MODERATE"]: 
            problematic_drugs[item['drug_a']] = get_korean_name(item['drug_a'])
            problematic_drugs[item['drug_b']] = get_korean_name(item['drug_b'])
            
    if ai_ddi_results:
        for result in ai_ddi_results:
            if result.get('high_risk') or result.get('medium_risk'):
                try:
                    pair_drugs_raw = result['pair_name'].replace("'", "").split(' + ')
                    if len(pair_drugs_raw) == 2:
                        drug_a, drug_b = pair_drugs_raw
                        problematic_drugs[drug_a] = get_korean_name(drug_a)
                        problematic_drugs[drug_b] = get_korean_name(drug_b)
                except Exception: pass 
    return problematic_drugs 


# ----------------------------------------------------------------------
# 3. Flask 앱 정의 및 API 엔드포인트
# ----------------------------------------------------------------------
app = Flask(__name__)
CORS(app) # CORS 허용


# -- 간수치 생존여부 예측 모델 api --
# 전역 cox 모델 객체
cph = get_cox_model()
@app.route("/api/v2/predict_survival", methods=["POST"])
def predict_survival():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data"}), 400

    X = pd.DataFrame([{
        "sex": 1 if data["sex"].lower() == "male" else 0,
        "age_at_index": data["age_at_index"],
        "bmi": data["bmi"],
        "AFP": data["afp"],
        "albumin": data["albumin"],
        "PT": data["pt"]
    }])
    
    target_day = data.get("target_days", 1825)
    surv_func = cph.predict_survival_function(X)

    closest_day = surv_func.index[
        surv_func.index.get_indexer([target_day], method="nearest")
    ][0]
    # surv_func is a DataFrame with one column, get the value properly
    surv_prob = float(surv_func.iloc[:, 0].loc[closest_day])

    # 시각화 - surv_func의 첫 번째 컬럼 값들을 가져오기
    fig, ax = plt.subplots(figsize=(7,5))
    surv_values = surv_func.iloc[:, 0].values  # 첫 번째 컬럼의 모든 값
    ax.plot(surv_func.index, surv_values, label="Survival Curve", color="blue")
    ax.axvline(closest_day, color="red", linestyle="--", label=f"Target Day: {closest_day}")
    ax.axhline(surv_prob, color="green", linestyle="--", label=f"Probability: {surv_prob:.2f}")
    ax.set_xlabel("Days")
    ax.set_ylabel("Survival Probability")
    ax.set_title("Predicted Survival Curve")
    ax.legend()
    ax.grid(True, alpha=0.3)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close(fig)
    img_base64 = base64.b64encode(buf.getvalue()).decode()

    print(f"Prediction success: survival_probability={surv_prob:.4f}, target_day={closest_day}")

    return jsonify({
        "target_day": int(closest_day),
        "survival_probability": round(surv_prob, 4),
        "plot_base64": img_base64
    })


@app.route('/api/v2/search_drugs', methods=['GET'])
def search_drugs():
    """React-select가 타이핑할 때마다 호출하는 비동기 API"""
    
    query = request.args.get('query', '') # React-select가 보낸 검색어
    if len(query) < 1: # 너무 짧은 검색어는 무시
        return jsonify([])

    try:
        # --- [수정] ---
        # 한글/영문 검색 모두 BOOLEAN MODE를 사용하도록 쿼리 변경
        sql_query = text("""
            SELECT KoreanName, EnglishName 
            FROM dur_drug_mapping
            WHERE 
                MATCH(KoreanName) AGAINST(:query_bool IN BOOLEAN MODE)
                OR
                MATCH(EnglishName) AGAINST(:query_bool IN BOOLEAN MODE)
            LIMIT 20
        """)
        
        # --- [수정] ---
        # '아미' -> '+아미*', 'wa' -> '+wa*'
        # 한글/영문 모두 BOOLEAN MODE용 파라미터를 생성
        query_bool = f"+{query}*" 
        
        with GLOBAL_DB_ENGINE.connect() as conn:
            # [수정] query_bool 파라미터를 하나만 전달
            result = conn.execute(sql_query, {"query_bool": query_bool})
            rows = result.fetchall()

        # React-select가 원하는 { value, label } 형태로 가공
        options = []
        seen_eng_names = set() # 중복 방지
        for row in rows:
            eng_name = row[1]
            kor_name = row[0]
            
            if eng_name in seen_eng_names:
                continue
            seen_eng_names.add(eng_name)

            if kor_name and eng_name:
                options.append({
                    "value": eng_name,
                    "label": f"{kor_name} ({eng_name})"
                })
            elif eng_name:
                options.append({
                    "value": eng_name,
                    "label": eng_name
                })

        return jsonify(options)

    except Exception as e:
        print(f"❌ /api/search_drugs 엔드포인트 오류: {e}")
        return jsonify({"error": str(e)}), 500

# --- API 2: 통합 검사 (모든 capitalize 수정 적용) ---
@app.route('/api/v2/check_all', methods=['POST'])
def check_all_ddi():
    """AI, DrugBank, KFDA 검사를 모두 수행하는 통합 엔드포인트"""
    try:
        data = request.json
        selected_drugs_english = data['drugs']
        if len(selected_drugs_english) < 2:
            return jsonify({"error": "At least two drugs are required"}), 400

        # React에서 'warfarin'(소문자)을 받아도, 한글명 '와파린'을 찾을 수 있도록 .capitalize()
        selected_drugs_korean = [GLOBAL_ENG_TO_KOR_MAP.get(eng.capitalize()) for eng in selected_drugs_english if GLOBAL_ENG_TO_KOR_MAP.get(eng.capitalize())]

        # --- 1. AI 예측 (3차) ---
        ai_results = []
        for drug_a_name, drug_b_name in combinations(selected_drugs_english, 2):
            # --- [수정] AI가 인식할 수 있도록 첫 글자 대문자화 ---
            drug_a_ai = drug_a_name.capitalize()
            drug_b_ai = drug_b_name.capitalize()
            
            prediction_result = run_ai_prediction_for_pair(drug_a_ai, drug_b_ai)
            
            # [수정] AI가 "Warfarin"으로 예측했어도, UI에는 "warfarin"으로 표시
            if prediction_result:
                prediction_result['pair_name'] = f"'{drug_a_name}' + '{drug_b_name}'"
                ai_results.append(prediction_result)

        # --- 2. DrugBank 검사 (1차) ---
        db_results = check_drugbank_ddi(selected_drugs_english)
        
        # --- 3. KFDA 검사 (2차) ---
        kfda_results = check_kfda_ddi_from_db(selected_drugs_korean)
        
        # --- 4. 위험 약물 식별 ---
        problematic_drugs_map = get_problematic_drugs(db_results, ai_results)

        return jsonify({
            "ai_predictions": ai_results,
            "drugbank_checks": db_results,
            "kfda_checks": kfda_results,
            "problematic_drugs": problematic_drugs_map 
        })
    except Exception as e:
        print(f"❌ /check_all 엔드포인트 오류: {e}")
        return jsonify({"error": str(e)}), 500

# --- API 3: 대체 약물 추천 (모든 capitalize 수정 적용) ---
@app.route('/api/v2/get_alternatives', methods=['POST'])
def get_alternatives():
    """대체 약물 후보를 검증하여 안전/위험 목록을 반환합니다."""
    try:
        data = request.json
        target_drug_to_replace_eng = data['drug_to_replace'] # 'amiodarone' (소문자)
        opponent_drugs = data['opponent_drugs'] # ['warfarin'] (소문자)

        # 1. 교체할 약물의 계열(Category) 찾기
        # --- [수정] .capitalize()로 키(key)를 대문자화하여 조회 ---
        target_class = GLOBAL_ENG_TO_CLASS.get(target_drug_to_replace_eng.capitalize())
        if not target_class:
            return jsonify({"error": f"'{target_drug_to_replace_eng}'의 약물 계열 정보가 마스터 DB에 없습니다."}), 404

        # 2. 같은 계열의 대체 후보 약물 목록 준비
        candidate_drugs_raw = GLOBAL_CLASS_TO_ENG_LIST.get(target_class, [])
        
        # --- [수정] 대소문자 구분 없이 필터링 ---
        opponent_drugs_lower = set(o.lower() for o in opponent_drugs)
        target_drug_lower = target_drug_to_replace_eng.lower()
        
        candidate_drugs = [
            c for c in candidate_drugs_raw
            if c.lower() != target_drug_lower and c.lower() not in opponent_drugs_lower
        ]

        if not candidate_drugs:
            return jsonify({"error": f"'{target_class}' 계열에 등록된 다른 약물이 없어, 동일 계열 대체가 불가능합니다."}), 404
        
        # 3. 대체 약물 안전성 자동 검증
        safe_alternatives = []
        risky_alternatives = []
        
        for candidate_eng in candidate_drugs: # 예: 'Dronedarone' (DB에서 가져온 대문자)
            
            # React가 보낸 소문자 opponent_drugs + DB의 대문자 candidate_eng
            # 예: ['warfarin'] + ['Dronedarone']
            hypothetical_list = opponent_drugs + [candidate_eng]
            
            # 1차(DrugBank) + 3차(AI) 검사
            db_check = check_drugbank_ddi(hypothetical_list)
            ai_check_json = []
            for d1, d2 in combinations(hypothetical_list, 2):
                # --- [수정] AI가 인식할 수 있도록 첫 글자 대문자화 ---
                # 'warfarin' -> 'Warfarin', 'Dronedarone' -> 'Dronedarone'
                d1_ai = d1.capitalize()
                d2_ai = d2.capitalize()
                prediction_result = run_ai_prediction_for_pair(d1_ai, d2_ai)
            
                # [수정] UI에는 원본(소문자/대문자) 이름으로 표시
                if prediction_result:
                    prediction_result['pair_name'] = f"'{d1}' + '{d2}'"
                    ai_check_json.append(prediction_result)

            # 위험도 평가
            problem_drugs_in_check = get_problematic_drugs(db_check, ai_check_json)
            
            candidate_kor_eng = get_korean_name(candidate_eng) # 'Dronedarone' -> '드로네다론 (Dronedarone)'
            
            if not problem_drugs_in_check:
                safe_alternatives.append({
                    "name": candidate_kor_eng,
                    "eng_name": candidate_eng,
                    "category": target_class
                })
            else:
                risky_alternatives.append({
                    "name": candidate_kor_eng,
                    "reason": f"다음 약물과 상호작용 감지: {', '.join(problem_drugs_in_check.values())}"
                })
        
        return jsonify({
            "safe_alternatives": safe_alternatives,
            "risky_alternatives": risky_alternatives
        })

    except Exception as e:
        print(f"❌ /api/get_alternatives 엔드포인트 오류: {e}")
        return jsonify({"error": str(e)}), 500
    
# --- API 4: 경량화된 우선순위 검사 (홈페이지 요약본용) ---
@app.route('/api/v2/check_priority', methods=['POST'])
def check_priority_ddi():
    """AI, DrugBank, KFDA 검사를 모두 수행하고, 우선순위에 따라 가장 높은 순위 결과 하나만 반환합니다."""
    try:
        data = request.json
        selected_drugs_english = data['drugs']
        if len(selected_drugs_english) < 2:
            return jsonify({"tier_found": 0, "message": "최소 두 가지 약물이 필요합니다."}), 400

        selected_drugs_korean = [GLOBAL_ENG_TO_KOR_MAP.get(eng.capitalize()) for eng in selected_drugs_english if GLOBAL_ENG_TO_KOR_MAP.get(eng.capitalize())]

        # --- 1. AI 예측 (3차) ---
        ai_results = []
        for drug_a_name, drug_b_name in combinations(selected_drugs_english, 2):
            drug_a_ai = drug_a_name.capitalize()
            drug_b_ai = drug_b_name.capitalize()
            
            prediction_result = run_ai_prediction_for_pair(drug_a_ai, drug_b_ai)
            
            if prediction_result:
                prediction_result['pair_name'] = f"'{drug_a_name}' + '{drug_b_name}'"
                ai_results.append(prediction_result)

        # --- 2. DrugBank 검사 (1차) ---
        db_results = check_drugbank_ddi(selected_drugs_english)
        
        # --- 3. KFDA 검사 (2차) ---
        kfda_results = check_kfda_ddi_from_db(selected_drugs_korean)
        
        # --- 4. 최종 결과 출력 순서 결정 (Sequential Priority Logic) ---
        
        # 🥇 1순위: DrugBank (Tier 1) 검사
        if db_results:
            # ==========================================================
            # ✍️ 여기를 수정합니다 (1/2)
            # ==========================================================
            first_conflict = db_results[0]
            
            # 'event' 키에 이미 DDI_KOREAN_MAP의 요약(제목)이 들어 있습니다.
            detailed_message = first_conflict.get('event', 'DrugBank 상호작용 감지') 
            
            # 사용자 요청: 조합 + 상세 요약 (첫 문단)
            final_message = f"'{first_conflict.get('drug_a')}' + '{first_conflict.get('drug_b')}': {detailed_message}"

            return jsonify({
                "tier_found": 1,
                "message": final_message, # 👈 상세 메시지로 변경
                "results": db_results
            })

        # 🥈 2순위: KFDA (Tier 2) 검사
        if kfda_results:
            # ==========================================================
            # ✍️ 여기를 수정합니다 (2/2)
            # ==========================================================
            first_kfda = kfda_results[0]
            
            # 'reason' 키에 KFDA 금기 사유가 들어 있습니다.
            kfda_message = f"'{first_kfda.get('drug_a')}' + '{first_kfda.get('drug_b')}': {first_kfda.get('reason', 'KFDA 병용 금기')}"
            
            return jsonify({
                "tier_found": 2,
                "message": kfda_message, # 👈 KFDA 상세 메시지로 변경
                "results": kfda_results
            })

        # 🥉 3순위: AI 예측 (Tier 3) 검사 (High/Medium Risk만 유효)
        # AI 결과 중 High 또는 Medium Risk가 하나라도 있는지 확인
        ai_high_medium_risk = [result for result in ai_results if result.get('high_risk') or result.get('medium_risk')]

        if ai_high_medium_risk:
            # (AI 결과는 이미 상세하므로 그대로 사용)
            return jsonify({
                "tier_found": 3,
                "message": f"3차 (AI) 예측 위험({len(ai_high_medium_risk)}건)이 감지되었습니다.",
                "results": ai_results
            })

        # 0순위: 안전함
        return jsonify({
            "tier_found": 0,
            "message": "상호작용 위험이 발견되지 않았습니다. 안전합니다."
        })

    except Exception as e:
        print(f"❌ /check_priority 엔드포인트 오류: {e}")
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------------
# 4. 서버 실행
# ----------------------------------------------------------------------
if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5000
    app_module = 'api_v2:app' # <-- 파일명 수정
    system = platform.system()
    if system == 'Windows':
        print(f"--- Windows OS 감지: 'waitress'로 서버를 시작합니다 (http://{host}:{port}) ---")
        command = ['waitress-serve', f'--host={host}', f'--port={port}', app_module]
    else:
        print(f"--- {system} OS 감지: 로컬 Flask 개발 서버를 시작합니다.")
        command = None
        app.run(host=host, port=port, debug=False)
    if command:
        try: subprocess.run(command)
        except FileNotFoundError: print(f"\n[오류] '{command[0]}'를 찾을 수 없습니다.")
        except Exception as e: print(f"\n[오류] 서버 실행 중 예외가 발생했습니다: {e}")