"""
데이터 전처리 모듈
DDI 데이터와 약물 유사도 데이터를 로딩하고 ML 학습용으로 변환
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path


class DDIDataLoader:
    """DDI 데이터 로더 및 전처리"""

    def __init__(self, data_dir="C:/CDSS/deepddi2/data"):
        self.data_dir = Path(data_dir)

        # 파일 경로 설정
        self.ddi_file = self.data_dir / "DrugBank_known_ddi.txt"
        self.drug_info_file = self.data_dir / "Approved_drug_Information.txt"
        self.drug_list_file = self.data_dir / "DrugList.txt"
        self.similarity_file = self.data_dir / "drug_similarity.csv"
        self.interaction_info_file = self.data_dir / "Type_information" / "Interaction_information_model1.csv"

        # 데이터 저장
        self.ddi_data = None
        self.drug_name_map = {}  # DrugBank ID -> 약물 이름
        self.drug_list = []
        self.similarity_matrix = None
        self.interaction_types = {}

    def load_all_data(self):
        """모든 데이터 로딩"""
        print("Loading DDI data...")
        self.load_ddi_data()

        print("Loading drug information...")
        self.load_drug_info()

        print("Loading interaction types...")
        self.load_interaction_types()

        print("Loading similarity matrix...")
        self.load_similarity_matrix()

        print("Data loading complete!")
        return self

    def load_ddi_data(self):
        """DDI 데이터 로딩"""
        self.ddi_data = pd.read_csv(self.ddi_file, sep='\t')
        print(f"  Loaded {len(self.ddi_data)} known DDI interactions")
        return self.ddi_data

    def load_drug_info(self):
        """약물 정보 로딩 (ID to Name 매핑)"""
        df = pd.read_csv(
            self.drug_info_file,
            sep='\t',
            header=None,
            names=['drug_id', 'drug_name', 'category', 'status',
                   'target', 'target_id', 'target_gene', 'action', 'known']
        )

        # DrugBank ID -> 약물 이름 매핑 (첫 번째 등장만)
        self.drug_name_map = df.drop_duplicates('drug_id').set_index('drug_id')['drug_name'].to_dict()

        # 약물 리스트 로딩
        with open(self.drug_list_file, 'r') as f:
            self.drug_list = [line.strip() for line in f]

        print(f"  Loaded {len(self.drug_name_map)} drug names")
        print(f"  Drug list contains {len(self.drug_list)} drugs")
        return self.drug_name_map

    def load_interaction_types(self):
        """상호작용 타입 정보 로딩"""
        df = pd.read_csv(self.interaction_info_file, sep='\t')
        self.interaction_types = df.set_index('type')['sentence'].to_dict()
        print(f"  Loaded {len(self.interaction_types)} interaction types")
        return self.interaction_types

    def load_similarity_matrix(self):
        """약물 구조 유사도 행렬 로딩"""
        try:
            # CSV 파일이 너무 크므로 샘플링해서 로딩
            # 첫 줄만 읽어서 약물 리스트 확인
            drugs = pd.read_csv(self.similarity_file, nrows=0).columns.tolist()
            drugs = drugs[1:]  # 첫 칼럼은 인덱스

            # 전체 데이터 로딩 (메모리 주의)
            print("  Loading similarity matrix (this may take a while)...")
            self.similarity_matrix = pd.read_csv(self.similarity_file, index_col=0)

            print(f"  Loaded similarity matrix: {self.similarity_matrix.shape}")
            return self.similarity_matrix
        except Exception as e:
            print(f"  Warning: Could not load full similarity matrix: {e}")
            print("  Will use simplified features instead")
            return None

    def get_drug_name(self, drug_id):
        """DrugBank ID로부터 약물 이름 가져오기"""
        return self.drug_name_map.get(drug_id, drug_id)

    def get_drugbank_id(self, drug_name):
        """약물 이름으로부터 DrugBank ID 찾기"""
        # 역방향 검색
        for drug_id, name in self.drug_name_map.items():
            if name.lower() == drug_name.lower():
                return drug_id
        return None

    def check_known_ddi(self, drug1_id, drug2_id):
        """
        두 약물 간 알려진 DDI가 있는지 확인

        Returns:
            list: 상호작용 타입 리스트 (없으면 빈 리스트)
        """
        if self.ddi_data is None:
            self.load_ddi_data()

        # 양방향 확인
        mask1 = (self.ddi_data['drug1'] == drug1_id) & (self.ddi_data['drug2'] == drug2_id)
        mask2 = (self.ddi_data['drug1'] == drug2_id) & (self.ddi_data['drug2'] == drug1_id)

        results = self.ddi_data[mask1 | mask2]

        if len(results) > 0:
            return results['Label'].tolist()
        return []

    def get_drug_similarity(self, drug1_id, drug2_id):
        """두 약물 간 구조적 유사도 가져오기"""
        if self.similarity_matrix is None:
            return 0.0

        try:
            if drug1_id in self.similarity_matrix.index and drug2_id in self.similarity_matrix.columns:
                return self.similarity_matrix.loc[drug1_id, drug2_id]
        except:
            pass

        return 0.0

    def prepare_ml_features(self, drug1_id, drug2_id):
        """
        두 약물에 대한 ML 특징 벡터 생성

        Returns:
            np.array: 특징 벡터
        """
        features = []

        # 1. 구조 유사도
        similarity = self.get_drug_similarity(drug1_id, drug2_id)
        features.append(similarity)

        # 2. 약물 1의 전체 DDI 개수
        drug1_ddi_count = len(self.ddi_data[
            (self.ddi_data['drug1'] == drug1_id) | (self.ddi_data['drug2'] == drug1_id)
        ])
        features.append(drug1_ddi_count)

        # 3. 약물 2의 전체 DDI 개수
        drug2_ddi_count = len(self.ddi_data[
            (self.ddi_data['drug1'] == drug2_id) | (self.ddi_data['drug2'] == drug2_id)
        ])
        features.append(drug2_ddi_count)

        # 4. 두 약물의 공통 상호작용 파트너 수
        drug1_partners = set(
            self.ddi_data[self.ddi_data['drug1'] == drug1_id]['drug2'].tolist() +
            self.ddi_data[self.ddi_data['drug2'] == drug1_id]['drug1'].tolist()
        )
        drug2_partners = set(
            self.ddi_data[self.ddi_data['drug1'] == drug2_id]['drug2'].tolist() +
            self.ddi_data[self.ddi_data['drug2'] == drug2_id]['drug1'].tolist()
        )
        common_partners = len(drug1_partners & drug2_partners)
        features.append(common_partners)

        return np.array(features)

    def prepare_training_data(self, sample_size=None):
        """
        ML 모델 학습용 데이터 준비

        Args:
            sample_size: 샘플링할 데이터 개수 (None이면 전체)

        Returns:
            X: 특징 행렬
            y: 레이블 (상호작용 타입)
            pairs: 약물 쌍 리스트
        """
        if self.ddi_data is None:
            self.load_ddi_data()

        # 샘플링 (선택적)
        if sample_size:
            ddi_sample = self.ddi_data.sample(min(sample_size, len(self.ddi_data)))
        else:
            ddi_sample = self.ddi_data

        X = []
        y = []
        pairs = []

        print(f"Preparing {len(ddi_sample)} training samples...")

        for idx, row in ddi_sample.iterrows():
            drug1 = row['drug1']
            drug2 = row['drug2']
            label = row['Label']

            # 특징 벡터 생성
            features = self.prepare_ml_features(drug1, drug2)
            X.append(features)
            y.append(label)
            pairs.append((drug1, drug2))

            if (idx + 1) % 10000 == 0:
                print(f"  Processed {idx + 1}/{len(ddi_sample)} samples")

        X = np.array(X)
        y = np.array(y)

        print(f"Training data prepared: X shape = {X.shape}, y shape = {y.shape}")

        return X, y, pairs

    def save_preprocessed_data(self, X, y, pairs, output_file):
        """전처리된 데이터 저장"""
        data = {
            'X': X,
            'y': y,
            'pairs': pairs
        }
        with open(output_file, 'wb') as f:
            pickle.dump(data, f)
        print(f"Saved preprocessed data to {output_file}")

    def load_preprocessed_data(self, input_file):
        """전처리된 데이터 로딩"""
        with open(input_file, 'rb') as f:
            data = pickle.load(f)
        print(f"Loaded preprocessed data from {input_file}")
        return data['X'], data['y'], data['pairs']


def main():
    """테스트용 메인 함수"""
    loader = DDIDataLoader()
    loader.load_all_data()

    # 예시: 두 약물 간 DDI 확인
    print("\n=== Example: Check DDI ===")
    drug1 = "DB01115"  # 예시 약물
    drug2 = "DB08807"  # 예시 약물

    drug1_name = loader.get_drug_name(drug1)
    drug2_name = loader.get_drug_name(drug2)

    print(f"Drug 1: {drug1} ({drug1_name})")
    print(f"Drug 2: {drug2} ({drug2_name})")

    interactions = loader.check_known_ddi(drug1, drug2)
    print(f"Known interactions: {interactions}")

    if interactions:
        for interaction_type in interactions:
            sentence = loader.interaction_types.get(interaction_type, "Unknown")
            print(f"  Type {interaction_type}: {sentence}")

    # 특징 벡터 생성
    features = loader.prepare_ml_features(drug1, drug2)
    print(f"Feature vector: {features}")


if __name__ == "__main__":
    main()
