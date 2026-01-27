# setup_korean_font.py
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform

def setup_korean_font():
    """한글 폰트 자동 설정"""
    
    print("=" * 60)
    print("Matplotlib 한글 폰트 설정")
    print("=" * 60)
    print()
    
    # OS별 한글 폰트
    system = platform.system()
    
    if system == 'Windows':
        # Windows 기본 한글 폰트
        font_list = [
            'Malgun Gothic',      # 맑은 고딕
            'NanumGothic',        # 나눔고딕
            'NanumBarunGothic',   # 나눔바른고딕
            'Gulim',              # 굴림
            'Dotum',              # 돋움
        ]
    elif system == 'Darwin':  # Mac
        font_list = [
            'AppleGothic',
            'NanumGothic',
        ]
    else:  # Linux
        font_list = [
            'NanumGothic',
            'NanumBarunGothic',
        ]
    
    # 사용 가능한 폰트 찾기
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    korean_font = None
    for font in font_list:
        if font in available_fonts:
            korean_font = font
            print(f"✓ 한글 폰트 발견: {font}")
            break
    
    if korean_font:
        # matplotlib 설정
        plt.rcParams['font.family'] = korean_font
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
        
        print(f"✓ 한글 폰트 설정 완료: {korean_font}")
        
        # 테스트
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, '한글 테스트\n가나다라마바사', 
               ha='center', va='center', fontsize=30)
        ax.set_title('한글 폰트 테스트', fontsize=20)
        ax.axis('off')
        
        plt.savefig('font_test.png', dpi=150, bbox_inches='tight')
        print("✓ 테스트 이미지 저장: font_test.png")
        plt.show()
        
        print("\n" + "=" * 60)
        print("✅ 한글 설정 완료!")
        print("=" * 60)
        
        return korean_font
    else:
        print("⚠️ 한글 폰트를 찾을 수 없습니다.")
        print("\n사용 가능한 폰트 목록:")
        
        # 한글 폰트 후보 검색
        korean_fonts = [f for f in available_fonts 
                       if any(k in f.lower() for k in ['gothic', 'gulim', 'dotum', 'malgun', 'nanum'])]
        
        if korean_fonts:
            for font in korean_fonts[:10]:
                print(f"  - {font}")
        else:
            print("  한글 폰트가 없습니다. 나눔폰트 설치가 필요합니다.")
        
        return None

if __name__ == '__main__':
    setup_korean_font()