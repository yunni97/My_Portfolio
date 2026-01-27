# visualize_liver_full.py
import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage

# 한글 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def visualize_liver_full():
    """간 전체 이미지 - 잘림 없이 크게"""
    
    lits_path = r'C:\project\liver_cancer_project\data\LiTS'
    
    print("=" * 60)
    print("간 전체 이미지 시각화 (잘림 없음)")
    print("=" * 60)
    print()
    
    # 데이터 로드
    vol_path = os.path.join(lits_path, 'volume-0.nii')
    seg_path = os.path.join(lits_path, 'segmentation-0.nii')
    
    img = nib.load(vol_path)
    seg = nib.load(seg_path)
    
    img_data = img.get_fdata()
    seg_data = seg.get_fdata()
    
    print(f"✓ Shape: {img_data.shape}\n")
    
    # 최적 슬라이스
    liver_per_slice = np.sum(seg_data == 1, axis=(1, 2))
    best_slice = np.argmax(liver_per_slice)
    
    print(f"✓ 슬라이스: {best_slice}\n")
    
    # 데이터 추출
    img_slice = img_data[best_slice]
    seg_slice = seg_data[best_slice]
    
    # CT 윈도우
    img_windowed = window_ct(img_slice)
    
    # 마스크
    liver_mask = (seg_slice == 1)
    tumor_mask = (seg_slice == 2)
    
    # 통계
    liver_area = np.sum(liver_mask)
    tumor_area = np.sum(tumor_mask)
    
    print(f"간: {liver_area:,} 픽셀")
    print(f"종양: {tumor_area:,} 픽셀\n")
    
    # ========================================
    # 1. 원본 CT만 크게 (A4 가로)
    # ========================================
    
    print("🖼️  [1] 원본 CT 이미지 생성 중...\n")
    
    fig1 = plt.figure(figsize=(16, 16))  # 정사각형, 매우 크게
    ax1 = fig1.add_subplot(111)
    
    im1 = ax1.imshow(img_windowed, cmap='gray', aspect='auto')
    ax1.set_title(f'원본 CT 이미지 (슬라이스 {best_slice})', 
                 fontsize=24, fontweight='bold', pad=20)
    ax1.axis('off')
    
    # 컬러바
    cbar = plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=14)
    
    plt.tight_layout()
    plt.savefig('1_원본_CT.png', dpi=200, bbox_inches='tight')
    print("✓ 저장: 1_원본_CT.png\n")
    plt.show()
    
    # ========================================
    # 2. 세그먼트 마스크만 크게
    # ========================================
    
    print("🖼️  [2] 세그먼트 마스크 생성 중...\n")
    
    fig2 = plt.figure(figsize=(16, 16))
    ax2 = fig2.add_subplot(111)
    
    # 색상 지정
    seg_colored = np.zeros((*seg_slice.shape, 3))
    seg_colored[seg_slice == 0] = [0, 0, 0]      # 배경: 검정
    seg_colored[seg_slice == 1] = [0, 1, 0]      # 간: 초록
    seg_colored[seg_slice == 2] = [1, 0, 0]      # 종양: 빨강
    
    ax2.imshow(seg_colored, aspect='auto')
    ax2.set_title(f'세그먼트 레이블\n검정:배경 / 초록:간 / 빨강:종양', 
                 fontsize=24, fontweight='bold', pad=20)
    ax2.axis('off')
    
    plt.tight_layout()
    plt.savefig('2_세그먼트_마스크.png', dpi=200, bbox_inches='tight')
    print("✓ 저장: 2_세그먼트_마스크.png\n")
    plt.show()
    
    # ========================================
    # 3. CT + 오버레이 크게
    # ========================================
    
    print("🖼️  [3] 오버레이 이미지 생성 중...\n")
    
    fig3 = plt.figure(figsize=(16, 16))
    ax3 = fig3.add_subplot(111)
    
    # CT 배경
    ax3.imshow(img_windowed, cmap='gray', aspect='auto')
    
    # 간 오버레이
    liver_overlay = np.ma.masked_where(~liver_mask, liver_mask)
    ax3.imshow(liver_overlay, cmap='Greens', alpha=0.4, aspect='auto')
    
    # 종양 오버레이
    tumor_overlay = np.ma.masked_where(~tumor_mask, tumor_mask)
    ax3.imshow(tumor_overlay, cmap='Reds', alpha=0.6, aspect='auto')
    
    ax3.set_title(f'CT + 세그먼트 오버레이\n간: {liver_area:,}px / 종양: {tumor_area:,}px', 
                 fontsize=24, fontweight='bold', pad=20)
    ax3.axis('off')
    
    plt.tight_layout()
    plt.savefig('3_오버레이.png', dpi=200, bbox_inches='tight')
    print("✓ 저장: 3_오버레이.png\n")
    plt.show()
    
    # ========================================
    # 4. 경계선만 표시
    # ========================================
    
    print("🖼️  [4] 경계선 이미지 생성 중...\n")
    
    fig4 = plt.figure(figsize=(16, 16))
    ax4 = fig4.add_subplot(111)
    
    ax4.imshow(img_windowed, cmap='gray', aspect='auto')
    
    # 간 경계
    liver_boundary = liver_mask ^ ndimage.binary_erosion(liver_mask, iterations=2)
    ax4.contour(liver_boundary, colors='lime', linewidths=3)
    
    # 종양 경계
    if tumor_area > 0:
        tumor_boundary = tumor_mask ^ ndimage.binary_erosion(tumor_mask, iterations=1)
        ax4.contour(tumor_boundary, colors='red', linewidths=4)
    
    ax4.set_title('경계선 표시\n초록선: 간 경계 / 빨강선: 종양 경계', 
                 fontsize=24, fontweight='bold', pad=20)
    ax4.axis('off')
    
    plt.tight_layout()
    plt.savefig('4_경계선.png', dpi=200, bbox_inches='tight')
    print("✓ 저장: 4_경계선.png\n")
    plt.show()
    
    # ========================================
    # 5. 비교 이미지 (가로 배치)
    # ========================================
    
    print("🖼️  [5] 비교 이미지 생성 중...\n")
    
    fig5 = plt.figure(figsize=(24, 8))  # 가로로 길게
    
    # 원본
    ax1 = fig5.add_subplot(141)
    ax1.imshow(img_windowed, cmap='gray', aspect='auto')
    ax1.set_title('원본 CT', fontsize=18, fontweight='bold')
    ax1.axis('off')
    
    # 세그먼트
    ax2 = fig5.add_subplot(142)
    ax2.imshow(seg_colored, aspect='auto')
    ax2.set_title('세그먼트\n(초록:간/빨강:종양)', fontsize=18, fontweight='bold')
    ax2.axis('off')
    
    # 오버레이
    ax3 = fig5.add_subplot(143)
    ax3.imshow(img_windowed, cmap='gray', aspect='auto')
    ax3.imshow(liver_overlay, cmap='Greens', alpha=0.4, aspect='auto')
    ax3.imshow(tumor_overlay, cmap='Reds', alpha=0.6, aspect='auto')
    ax3.set_title('오버레이', fontsize=18, fontweight='bold')
    ax3.axis('off')
    
    # 경계선
    ax4 = fig5.add_subplot(144)
    ax4.imshow(img_windowed, cmap='gray', aspect='auto')
    ax4.contour(liver_boundary, colors='lime', linewidths=2)
    if tumor_area > 0:
        ax4.contour(tumor_boundary, colors='red', linewidths=3)
    ax4.set_title('경계선', fontsize=18, fontweight='bold')
    ax4.axis('off')
    
    plt.suptitle(f'간암 CT 분석 비교 (케이스 0, 슬라이스 {best_slice})', 
                fontsize=22, fontweight='bold')
    plt.tight_layout()
    plt.savefig('5_비교.png', dpi=200, bbox_inches='tight')
    print("✓ 저장: 5_비교.png\n")
    plt.show()
    
    # ========================================
    # 완료
    # ========================================
    
    print("=" * 60)
    print("✅ 모든 이미지 생성 완료!")
    print("=" * 60)
    
    print("\n📁 생성된 파일 (크고 선명하게):")
    print("  1. 1_원본_CT.png          - 원본 CT만 (16x16 inch)")
    print("  2. 2_세그먼트_마스크.png  - 세그먼트만")
    print("  3. 3_오버레이.png         - CT + 세그먼트")
    print("  4. 4_경계선.png           - 경계선 표시")
    print("  5. 5_비교.png             - 4개 한번에 비교 (가로)")
    
    print("\n💡 각 이미지는:")
    print("  - 잘림 없이 전체 표시")
    print("  - 200 DPI 고해상도")
    print("  - 큰 폰트 (24pt)")

def window_ct(image, window_center=40, window_width=400):
    """CT Windowing"""
    min_value = window_center - window_width / 2
    max_value = window_center + window_width / 2
    windowed = np.clip(image, min_value, max_value)
    windowed = (windowed - min_value) / (max_value - min_value)
    return windowed

if __name__ == '__main__':
    visualize_liver_full()