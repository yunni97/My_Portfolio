"""
머신러닝 모델 학습 및 예측
Random Forest 기반 DDI 예측
"""

import numpy as np
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score
from collections import Counter

from data_preprocessing import DDIDataLoader
from risk_severity_mapping import get_risk_score


class DDIPredictor:
    """DDI 예측 모델 (Random Forest 기반)"""

    def __init__(self, data_loader=None):
        self.data_loader = data_loader or DDIDataLoader()
        self.model = None
        self.is_trained = False

    def train(self, X, y, n_estimators=100, max_depth=20, random_state=42):
        """
        Random Forest 모델 학습

        Args:
            X: 특징 행렬
            y: 레이블 (상호작용 타입)
            n_estimators: 트리 개수
            max_depth: 최대 깊이
            random_state: 랜덤 시드
        """
        print("Training Random Forest model...")
        print(f"  Training samples: {len(X)}")
        print(f"  Unique interaction types: {len(np.unique(y))}")

        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state, stratify=y
        )

        # Random Forest 학습
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
            verbose=1
        )

        print("  Fitting model...")
        self.model.fit(X_train, y_train)

        # 성능 평가
        print("\n=== Training Performance ===")
        train_pred = self.model.predict(X_train)
        train_acc = accuracy_score(y_train, train_pred)
        print(f"Training Accuracy: {train_acc:.4f}")

        print("\n=== Test Performance ===")
        test_pred = self.model.predict(X_test)
        test_acc = accuracy_score(y_test, test_pred)
        test_f1 = f1_score(y_test, test_pred, average='weighted')
        print(f"Test Accuracy: {test_acc:.4f}")
        print(f"Test F1 Score: {test_f1:.4f}")

        # 주요 클래스에 대한 상세 리포트
        top_classes = Counter(y_train).most_common(10)
        print("\n=== Top 10 Interaction Types ===")
        for interaction_type, count in top_classes:
            print(f"  Type {interaction_type}: {count} samples")

        self.is_trained = True
        print("\nModel training complete!")

        return {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'test_f1': test_f1
        }

    def predict(self, drug1_id, drug2_id):
        """
        두 약물 간 상호작용 예측

        Args:
            drug1_id: 약물 1 DrugBank ID
            drug2_id: 약물 2 DrugBank ID

        Returns:
            dict: {
                'interaction_type': 예측된 상호작용 타입,
                'probability': 예측 확률,
                'risk_score': 위험도 점수,
                'severity': 위험도 등급
            }
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet!")

        # 특징 벡터 생성
        features = self.data_loader.prepare_ml_features(drug1_id, drug2_id)
        features = features.reshape(1, -1)

        # 예측
        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]

        # 예측된 클래스의 확률
        predicted_class_idx = list(self.model.classes_).index(prediction)
        probability = probabilities[predicted_class_idx]

        # 위험도 정보
        risk_info = get_risk_score(prediction)

        return {
            'interaction_type': int(prediction),
            'probability': float(probability),
            'risk_score': risk_info['score'],
            'severity': risk_info['severity'],
            'category': risk_info['category']
        }

    def predict_top_k(self, drug1_id, drug2_id, k=3):
        """
        상위 k개의 가능한 상호작용 예측

        Returns:
            list: 상위 k개의 예측 결과
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet!")

        # 특징 벡터 생성
        features = self.data_loader.prepare_ml_features(drug1_id, drug2_id)
        features = features.reshape(1, -1)

        # 예측 확률
        probabilities = self.model.predict_proba(features)[0]

        # 상위 k개 인덱스
        top_k_indices = np.argsort(probabilities)[-k:][::-1]

        results = []
        for idx in top_k_indices:
            interaction_type = self.model.classes_[idx]
            probability = probabilities[idx]
            risk_info = get_risk_score(interaction_type)

            results.append({
                'interaction_type': int(interaction_type),
                'probability': float(probability),
                'risk_score': risk_info['score'],
                'severity': risk_info['severity'],
                'category': risk_info['category']
            })

        return results

    def save_model(self, model_path):
        """모델 저장"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model!")

        model_data = {
            'model': self.model,
            'is_trained': self.is_trained
        }

        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"Model saved to {model_path}")

    def load_model(self, model_path):
        """모델 로딩"""
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.is_trained = model_data['is_trained']

        print(f"Model loaded from {model_path}")


def train_ddi_model(sample_size=50000, output_dir="C:/CDSS/ml_ddi_system/models"):
    """
    DDI 예측 모델 학습 메인 함수

    Args:
        sample_size: 학습에 사용할 샘플 수
        output_dir: 모델 저장 디렉토리
    """
    # 출력 디렉토리 생성
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 데이터 로딩
    print("=" * 60)
    print("DDI Prediction Model Training")
    print("=" * 60)

    loader = DDIDataLoader()
    loader.load_all_data()

    # 학습 데이터 준비
    print("\n" + "=" * 60)
    print("Preparing training data...")
    print("=" * 60)

    X, y, pairs = loader.prepare_training_data(sample_size=sample_size)

    # 전처리 데이터 저장
    preprocessed_file = output_dir / "preprocessed_data.pkl"
    loader.save_preprocessed_data(X, y, pairs, preprocessed_file)

    # 모델 학습
    print("\n" + "=" * 60)
    print("Training model...")
    print("=" * 60)

    predictor = DDIPredictor(data_loader=loader)
    metrics = predictor.train(X, y, n_estimators=100, max_depth=20)

    # 모델 저장
    model_file = output_dir / "ddi_random_forest.pkl"
    predictor.save_model(model_file)

    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Model saved to: {model_file}")
    print(f"Test Accuracy: {metrics['test_accuracy']:.4f}")
    print(f"Test F1 Score: {metrics['test_f1']:.4f}")

    return predictor, metrics


def main():
    """테스트용 메인 함수"""
    # 소규모 샘플로 빠른 테스트
    print("Training model with sample data...")
    predictor, metrics = train_ddi_model(sample_size=10000)

    # 예측 테스트
    print("\n" + "=" * 60)
    print("Testing prediction...")
    print("=" * 60)

    loader = predictor.data_loader
    test_drug1 = "DB01115"
    test_drug2 = "DB08807"

    print(f"Drug 1: {test_drug1} ({loader.get_drug_name(test_drug1)})")
    print(f"Drug 2: {test_drug2} ({loader.get_drug_name(test_drug2)})")

    # Top-3 예측
    predictions = predictor.predict_top_k(test_drug1, test_drug2, k=3)
    print("\nTop 3 Predictions:")
    for i, pred in enumerate(predictions, 1):
        print(f"  {i}. Type {pred['interaction_type']}: "
              f"{pred['severity']} (score: {pred['risk_score']}, prob: {pred['probability']:.3f})")


if __name__ == "__main__":
    main()
