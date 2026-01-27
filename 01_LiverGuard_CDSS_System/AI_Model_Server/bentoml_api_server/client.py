import bentoml
import nibabel as nib
import numpy as np
import os

# === [설정] ===
FILE_PATH = "/mnt/c/Users/401-14/Downloads/LITS17/volume-110.nii/volume-110.nii" 
SERVER_URL = "http://localhost:3001"
OUTPUT_FILENAME = "prediction_result3.nii.gz" # 저장할 파일 이름

# 라벨 맵핑 (사용자님이 알려주신 정보)
LABEL_MAP = {
    0: "Background", 1: "Spleen", 2: "Kidneys", 3: "Pancreas",
    4: "Stomach", 5: "Heart", 6: "Duodenum", 7: "Gallbladder?", 
    8: "Liver", 9: "Tumor"
}

def main():
    if not os.path.exists(FILE_PATH):
        print(f"❌ 파일을 찾을 수 없습니다: {FILE_PATH}")
        return

    print(f"📂 원본 데이터 로딩 중... ({FILE_PATH})")
    nii_img = nib.load(FILE_PATH)
    # 원본의 위치 정보(Affine)를 저장해둬야 나중에 겹쳐볼 수 있습니다.
    affine = nii_img.affine 
    data = nii_img.get_fdata().astype(np.float32)

    # 차원 맞추기 (nnU-Net용)
    if data.ndim == 3:
        input_data = data[np.newaxis, ...] 
    else:
        input_data = data

    print("🚀 서버로 전송 및 추론 중... (기다려주세요)")
    try:
        # 타임아웃 넉넉하게 설정
        client = bentoml.SyncHTTPClient(SERVER_URL, timeout=3600)
        result = client.segment(input_data=input_data)

        print("\n✅ 예측 성공!")
        
        # === [핵심] 결과 분석 및 저장 ===
        unique_labels = np.unique(result)
        print("-" * 30)
        print("🔍 [탐색 결과 리포트]")
        
        found_tumor = False
        for label in unique_labels:
            label_int = int(label)
            name = LABEL_MAP.get(label_int, "Unknown")
            count = np.sum(result == label_int)
            print(f"  - 라벨 {label_int} ({name}): {count} voxels")
            
            if label_int == 9:
                found_tumor = True

        if found_tumor:
            print("\n🚨 종양(Tumor)이 검출되었습니다!")
        else:
            print("\n⚠️ 종양이 검출되지 않았습니다. (너무 작거나 미러링을 꺼서 놓쳤을 수 있음)")

        # NIfTI 파일로 저장
        print("-" * 30)
        print(f"💾 결과를 3D 파일로 저장합니다: {OUTPUT_FILENAME}")
        
        # 결과 배율이 (Channel, Z, Y, X) 형태라면 (Z, Y, X)로 바꿔야 함
        if result.ndim == 4:
             result = result[0]
             
        # 결과값은 정수(Integer)여야 하므로 변환
        result = result.astype(np.uint8)
        
        # 원본 이미지의 위치 정보(affine)를 입혀서 저장
        new_img = nib.Nifti1Image(result, affine)
        nib.save(new_img, OUTPUT_FILENAME)
        print("✅ 저장 완료! 이제 시각화 툴에서 열어보세요.")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")

if __name__ == "__main__":
    main()