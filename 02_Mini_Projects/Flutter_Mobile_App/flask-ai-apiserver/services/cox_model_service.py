import joblib

# Flask 서버 시작 시 한 번만 실행됨
print("🚀 Loading Cox survival model...")

MODEL_PATH = "models/cox_model.pkl"
cox_model = joblib.load(MODEL_PATH)

print("✅ Cox model loaded successfully!")

# 필요시 함수로 래핑도 가능
def get_cox_model():
    """다른 파일에서 모델을 import해서 가져갈 때 사용"""
    return cox_model
