import nibabel as nib
import numpy as np
import os

# === [설정] 경로 확인 ===
# 1. 정답 파일 (Ground Truth)
GT_PATH = "/mnt/c/Users/401-14/Downloads/LITS17/segmentation-20.nii/segmentation-20.nii"

# 2. 예측 파일 (Prediction)
PRED_PATH = "/mnt/c/flutter_liverguard/django-dashboard-apiserver/reactproject/media/ct_scans/volume-20_seg.nii.gz"

def calculate_dice_robust():
    print("🔄 강력 보정 채점 시작...")
    
    if not os.path.exists(GT_PATH) or not os.path.exists(PRED_PATH):
        print("❌ 파일을 찾을 수 없습니다.")
        return

    # 1. 파일 로드
    gt_img = nib.load(GT_PATH)
    pred_img = nib.load(PRED_PATH)

    # 2. [핵심] 둘 다 표준 방향(RAS)으로 강제 정렬
    # 이렇게 해야 뒤집히거나 돌아간 것들이 딱 맞게 겹칩니다.
    print("📏 방향 보정 중 (Reorientation)...")
    gt_canonical = nib.as_closest_canonical(gt_img)
    pred_canonical = nib.as_closest_canonical(pred_img)
    
    gt_data = gt_canonical.get_fdata().astype(np.uint8)
    pred_data = pred_canonical.get_fdata().astype(np.uint8)

    # 크기 확인 (다르면 비교 불가)
    if gt_data.shape != pred_data.shape:
        print(f"⚠️ 크기 불일치! GT:{gt_data.shape} vs Pred:{pred_data.shape}")
        print("   (크기가 다르면 점수 계산이 불가능합니다. 전처리를 확인하세요.)")
        return

    print(f"📊 [정답 라벨] {np.unique(gt_data)}")
    print(f"📊 [예측 라벨] {np.unique(pred_data)}")

    # === 3. 정밀 비교 (Boolean Masking) ===
    # 섞이지 않게 딱 그것만 뽑아서 비교합니다.
    
    # --- 간 (Liver) ---
    # 정답: 1번이 간
    gt_liver_mask = (gt_data == 1)
    # 예측: 8번이 간 (나머지 1,3,5...는 다 무시)
    pred_liver_mask = (pred_data == 8)
    
    score_liver = dice_coefficient(gt_liver_mask, pred_liver_mask)

    # --- 종양 (Tumor) ---
    # 정답: 2번이 종양
    gt_tumor_mask = (gt_data == 2)
    # 예측: 9번이 종양
    pred_tumor_mask = (pred_data == 9)
    
    score_tumor = dice_coefficient(gt_tumor_mask, pred_tumor_mask)

    print("-" * 30)
    print(f"🏆 최종 성적표")
    print(f"🫁 간(Liver) 정확도:   {score_liver:.4f} ({score_liver*100:.1f}%)")
    print(f"🦠 종양(Tumor) 정확도:  {score_tumor:.4f} ({score_tumor*100:.1f}%)")
    
    if score_liver < 0.8:
        print("\n⚠️ 점수가 여전히 낮다면, MRIcron에서 두 파일을 겹쳐보세요.")
        print("   여전히 위치가 어긋나 있을 수 있습니다.")

def dice_coefficient(mask1, mask2):
    # Boolean 마스크끼리 비교 (True/False)
    intersection = np.logical_and(mask1, mask2).sum()
    total = mask1.sum() + mask2.sum()
    
    if total == 0:
        return 1.0 # 둘 다 없으면 100점
    
    return (2. * intersection) / (total + 0.00001)

if __name__ == "__main__":
    calculate_dice_robust()