import nibabel as nib
import numpy as np
from pathlib import Path

# === [설정] 데이터 폴더 경로 ===
DATA_ROOT = r"C:\Users\401-14\Downloads\LITS17"

def auto_align_recursive():
    root_path = Path(DATA_ROOT)
    if not root_path.exists():
        print("❌ 폴더를 찾을 수 없습니다.")
        return

    # 1. volume-*.nii 이름을 가진 '것'들을 다 찾습니다 (폴더일 수도, 파일일 수도 있음)
    vol_candidates = list(root_path.glob("volume-*.nii"))
    print(f"📂 총 {len(vol_candidates)}개의 후보를 찾았습니다.")

    for item in vol_candidates:
        # === [핵심 수정] 폴더인지 파일인지 확인 ===
        if item.is_dir():
            # 폴더인 경우: volume-51.nii/volume-51.nii
            vol_path = item / item.name
        else:
            # 파일인 경우: volume-51.nii
            vol_path = item

        # 실제 파일이 있는지 확인
        if not vol_path.exists():
            print(f"⚠️ 실제 파일이 없습니다: {vol_path}")
            continue

        # 2. 짝꿍 Segmentation 찾기
        # 폴더 구조에 맞춰서 짝꿍 이름 추론
        # item.name이 'volume-51.nii'라면 -> 'segmentation-51.nii'
        seg_folder_name = item.name.replace("volume", "segmentation")
        seg_candidate = item.parent / seg_folder_name

        if seg_candidate.is_dir():
            # 짝꿍도 폴더인 경우
            seg_path = seg_candidate / seg_candidate.name
        else:
            # 짝꿍이 파일인 경우
            seg_path = seg_candidate

        if not seg_path.exists():
            print(f"⚠️ 짝꿍 Segmentation 파일 없음: {seg_path}")
            continue

        print(f"\n🔄 처리 중: {vol_path.name}")
        
        try:
            # 3. 로드 및 정렬 (이전과 동일)
            vol_img = nib.load(str(vol_path))
            seg_img = nib.load(str(seg_path))

            # 표준 방향(RAS) 변환
            vol_canonical = nib.as_closest_canonical(vol_img)
            seg_canonical = nib.as_closest_canonical(seg_img)

            # 헤더 동기화
            if vol_canonical.shape == seg_canonical.shape:
                final_seg_img = nib.Nifti1Image(
                    seg_canonical.get_fdata(), 
                    vol_canonical.affine, 
                    vol_canonical.header 
                )
                print("   ✅ 헤더 동기화 완료")
            else:
                print("   ⚠️ 크기 불일치 (정렬만 수행)")
                final_seg_img = seg_canonical

            # 4. 저장 (파일이 있던 그 폴더 안에 저장)
            # 예: .../segmentation-51.nii/segmentation-51_aligned.nii.gz
            save_name = seg_path.name.replace(".nii", "_aligned.nii.gz")
            save_path = seg_path.parent / save_name
            
            nib.save(final_seg_img, str(save_path))
            print(f"   💾 저장 완료: {save_path.name}")

        except Exception as e:
            print(f"   ❌ 에러: {e}")

    print("\n🎉 모든 작업 완료!")

if __name__ == "__main__":
    auto_align_recursive()