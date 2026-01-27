# Horizontal risk bar for blood test indicators (configurable for 4 different metrics).
# Style mimics the sample: rounded gradient bar with soft shadow and a black value bubble with a small pointer.
# Supports both normal direction (higher = more dangerous) and reverse direction (lower = more dangerous).

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server-side rendering

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib as mpl
import io
import base64

# -------------------- Indicator Configurations --------------------
INDICATORS = {
    'afp': {
        'title': 'AFP',
        'unit': 'ng/mL',
        'vmin': 0,
        'vmax': 500,
        'ranges': [(0, 10), (10, 100), (100, 400), (400, 500)],
        'labels': ['정상\n0-10', '주의\n10-100', '위험\n100-400', '매우위험\n400+'],
        'reverse': False,         # 높을수록 위험
        'colors': ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c'],  # 녹색→노랑→주황→빨강
    },
    'ast': {
        'title': 'AST',
        'unit': 'U/L',
        'vmin': 0,
        'vmax': 100,
        'ranges': [(0, 40), (40, 50), (50, 100)],
        'labels': ['정상\n0-40', '경계\n40-50', '위험\n50+'],
        'reverse': False,         
        'gender_specific': True,  # 성별 기준 다름
        'male_threshold': 40,
        'female_threshold': 32,
    },
    'alt': {
        'title': 'ALT',
        'unit': 'U/L',
        'vmin': 0,
        'vmax': 100,
        'ranges': [(0, 40), (40, 50), (50, 100)],
        'labels': ['정상\n0-40', '경계\n40-50', '위험\n50+'],
        'reverse': False,
        'gender_specific': True,
        'male_threshold': 40,
        'female_threshold': 35,
    },
    'albi_grade': {
        'title': 'ALBI Grade',
        'unit': '',
        'vmin': 1,
        'vmax': 3,
        'ranges': [(1, 1.5), (1.5, 2.5), (2.5, 3)],
        'labels': ['Grade 1\n우수', 'Grade 2\n중등도', 'Grade 3\n저하'],
        'reverse': False,         
        'discrete': True,  
        'display_map': {1: 'Grade 1', 2: 'Grade 2', 3: 'Grade 3'},
    },
    'ggt': {
        'title': 'GGT',
        'unit': 'U/L',
        'vmin': 0,
        'vmax': 150,
        'ranges': [(0, 71), (71, 100), (100, 150)],
        'labels': ['정상\n0-71', '경계\n71-100', '위험\n100+'],
        'reverse': False,
        'gender_specific': True,
        'male_threshold': 71,
        'female_threshold': 42
    },
    'r_gtp': {
        'title': 'r-GTP (알코올)',
        'unit': 'U/L',
        'vmin': 0,
        'vmax': 100,
        'ranges': [(0, 63), (63, 77), (77, 100)],
        'labels': ['정상\n0-63', '경계\n63-77', '위험\n77+'],
        'reverse': False,
        'gender_specific': True,
        'male_threshold': 63,
        'female_threshold': 35
    },
    # 부가 지표
    'bilirubin': {
        'title': 'Bilirubin',
        'unit': 'mg/dL',
        'vmin': 0.1,
        'vmax': 3.5,
        'ranges': [(0.1, 1.2), (1.2, 2.5), (2.5, 3.5)],
        'labels': ['정상\n0.1-1.2', '주의\n1.2-2.5', '위험\n2.5+'],
        'reverse': False
    },
    'albumin': {
        'title': 'Albumin',
        'unit': 'g/dL',
        'vmin': 1.5,
        'vmax': 5.5,
        'ranges': [(1.5, 2.0), (2.0, 3.5), (3.5, 5.5)],
        'labels': ['위험\n<2.0', '주의\n2.0-3.5', '정상\n3.5-5.5'],
        'reverse': True  # 낮을수록 위험
    },
    
    'alp': {
        'title': 'ALP',
        'unit': 'U/L',
        'vmin': 0,
        'vmax': 200,
        'ranges': [(40, 120), (120, 160), (160, 200)],
        'labels': ['정상\n40-120', '경계\n120-160', '위험\n160+'],
        'reverse': False,
        'gender_specific': True,
        'male_threshold': 120,
        'female_threshold': 104
    },
    'total_protein': {
        'title': 'Total Protein',
        'unit': 'g/dL',
        'vmin': 4.0,
        'vmax': 9.0,
        'ranges': [(4.0, 6.0), (6.0, 8.0), (8.0, 9.0)],
        'labels': ['낮음\n<6.0', '정상\n6.0-8.0', '높음\n8.0+'],
        'reverse': False
    },
    'platelet': {
        'title': 'Platelet',
        'unit': '×10³/μL',
        'vmin': 50,
        'vmax': 500,
        'ranges': [(50, 150), (150, 400), (400, 500)],
        'labels': ['낮음\n<150', '정상\n150-400', '높음\n400+'],
        'reverse': False
    },
    'pt': {
        'title': 'PT',
        'unit': 'seconds',
        'vmin': 9,
        'vmax': 16,
        'ranges': [(9, 11), (11, 13), (13, 16)],
        'labels': ['낮음\n<11', '정상\n11-13', '높음\n13+'],
        'reverse': False
    },
    'inr': {
        'title': 'INR',
        'unit': '',
        'vmin': 0.5,
        'vmax': 2.5,
        'ranges': [(0.5, 0.8), (0.8, 1.2), (1.2, 2.5)],
        'labels': ['낮음\n<0.8', '정상\n0.8-1.2', '높음\n1.2+'],
        'reverse': False
    },
}

# -------------------- Helpers --------------------
def lerp(a, b, t):
    return a + (b - a) * t

def gradient_colors(n=600, reverse=False, custom_colors=None):
    """Return an (n,1,3) RGB gradient: green → yellow → red (left→right).
    If reverse=True, flip the gradient (red → yellow → green)."""
    
    if custom_colors:
        # 커스텀 컬러 사용
        num_sections = len(custom_colors) - 1
        arr = np.zeros((n, 1, 3), dtype=float)
        section_size = n // num_sections
        
        for i in range(num_sections):
            start_idx = i * section_size
            end_idx = (i + 1) * section_size if i < num_sections - 1 else n
            start_color = np.array(mpl.colors.to_rgb(custom_colors[i]))
            end_color = np.array(mpl.colors.to_rgb(custom_colors[i + 1]))
            
            for j in range(start_idx, end_idx):
                t = (j - start_idx) / max(1, end_idx - start_idx - 1)
                arr[j, 0, :] = lerp(start_color, end_color, t)
        return arr
    
    # 기본: 녹색 → 노랑 → 빨강
    left  = np.array(mpl.colors.to_rgb("#2ecc71"))
    mid   = np.array(mpl.colors.to_rgb("#f1c40f"))
    right = np.array(mpl.colors.to_rgb("#e74c3c"))
    
    if reverse:
        left, right = right, left
    
    arr = np.zeros((n, 1, 3), dtype=float)
    half = n // 2
    for i in range(half):
        t = i / max(1, half - 1)
        arr[i, 0, :] = lerp(left, mid, t)
    for i in range(half, n):
        t = (i - half) / max(1, n - half - 1)
        arr[i, 0, :] = lerp(mid, right, t)
    return arr

def draw_value_bubble(ax, x, y, text, fontsize=14, color="black"):
    """값 표시 버블"""
    w, h = 70, 34
    bubble = FancyBboxPatch(
        (x - w/2, y), w, h, 
        boxstyle="round,pad=0.02,rounding_size=8",
        ec="none", fc=color, zorder=5
    )
    ax.add_patch(bubble)
    
    # 삼각형 포인터
    tri = mpl.patches.Polygon(
        [[x-6, y], [x+6, y], [x, y-8]], 
        closed=True, fc=color, ec="none", zorder=5
    )
    ax.add_patch(tri)
    
    ax.text(
        x, y + h*0.55, text, 
        color="white", fontsize=fontsize, fontweight="bold",
        ha="center", va="center", zorder=6
    )

def generate_risk_bar(indicator, value, gender='male'):
    """
    간 검사 지표 그래프 생성
    
    Args:
        indicator: 'afp', 'ast', 'alt', 'albi_grade', 'ggt', 'r_gtp', etc.
        value: 수치
        gender: 'male' 또는 'female' (성별 기준 적용)
    """
    if indicator not in INDICATORS:
        raise ValueError(f"Invalid indicator: {indicator}")
    
    config = INDICATORS[indicator]
    title = config['title']
    unit = config['unit']
    vmin = config['vmin']
    vmax = config['vmax']
    ranges = config['ranges']
    labels = config['labels']
    reverse = config.get('reverse', False)
    discrete = config.get('discrete', False)
    
    # ALBI Grade 특수 처리
    if indicator == 'albi_grade':
        # Grade 문자열을 숫자로 변환
        if isinstance(value, str):
            if 'Grade 1' in value or value == '1':
                value = 1
            elif 'Grade 2' in value or value == '2':
                value = 2
            elif 'Grade 3' in value or value == '3':
                value = 3
        display_value = config['display_map'].get(int(value), f'Grade {int(value)}')
    else:
        display_value = value
    
    # Figure
    fig = plt.figure(figsize=(8, 2.5))
    ax = plt.axes([0,0,1,1])
    ax.set_xlim(0, 800)
    ax.set_ylim(0, 250)
    ax.axis('off')
    
    # Title (볼드, 크게)
    ax.text(20, 220, title, fontsize=18, fontweight="bold", va="top")
    
    # Bar geometry
    bar_x, bar_y = 40, 90
    bar_w, bar_h = 720, 40
    radius = bar_h / 2
    
    # Shadow
    shadow = FancyBboxPatch(
        (bar_x, bar_y-5), bar_w, bar_h, 
        boxstyle=f"round,pad=0,rounding_size={radius}",
        ec="none", fc="#e6e6e6", zorder=0
    )
    ax.add_patch(shadow)
    
    # White housing
    housing = FancyBboxPatch(
        (bar_x, bar_y), bar_w, bar_h, 
        boxstyle=f"round,pad=0,rounding_size={radius}",
        ec="none", fc="white", zorder=1
    )
    ax.add_patch(housing)
    
    # Gradient
    custom_colors = config.get('colors')
    grad = gradient_colors(1000, reverse=reverse, custom_colors=custom_colors)
    im = ax.imshow(
        grad.transpose(1,0,2), 
        extent=(bar_x, bar_x+bar_w, bar_y, bar_y+bar_h),
        origin="lower", zorder=2, interpolation="bicubic"
    )
    im.set_clip_path(housing)
    
    # Outline
    outline = FancyBboxPatch(
        (bar_x, bar_y), bar_w, bar_h, 
        boxstyle=f"round,pad=0,rounding_size={radius}",
        ec="#cccccc", fc="none", lw=2, zorder=3
    )
    ax.add_patch(outline)
    
    # Value mapping
    v = max(vmin, min(vmax, value))
    t = (v - vmin) / (vmax - vmin + 1e-9)
    px = bar_x + t * bar_w
    
    # 위험도에 따라 버블 색상 변경
    if t < 0.33:
        bubble_color = "#2ecc71"  # 녹색
    elif t < 0.66:
        bubble_color = "#f1c40f"  # 노랑
    else:
        bubble_color = "#e74c3c"  # 빨강
    
    if reverse:
        if t > 0.66:
            bubble_color = "#2ecc71"
        elif t > 0.33:
            bubble_color = "#f1c40f"
        else:
            bubble_color = "#e74c3c"
    
    # Value bubble
    if discrete:
        bubble_text = display_value
    else:
        bubble_text = f"{display_value:.1f}"
    
    draw_value_bubble(ax, px, bar_y + bar_h + 25, bubble_text, fontsize=14, color=bubble_color)
    
    # Unit label
    if unit:
        ax.text(bar_x + bar_w, bar_y - 15, f"{unit}", fontsize=10, ha="right", va="top", color="#666666")
    
    # Range labels
    for (a, b), lab in zip(ranges, labels):
        ta = (a - vmin) / (vmax - vmin)
        tb = (b - vmin) / (vmax - vmin)
        mx = bar_x + (ta + tb)/2 * bar_w
        ax.text(mx, bar_y - 15, lab, fontsize=9, ha="center", va="top", color="#555555")
    
    # Convert to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=True)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    
    return img_base64
#     left  = np.array(mpl.colors.to_rgb("#2ecc71"))  # green
#     mid   = np.array(mpl.colors.to_rgb("#f1c40f"))  # yellow
#     right = np.array(mpl.colors.to_rgb("#e74c3c"))  # red
    
#     if reverse:
#         left, right = right, left  # Swap colors for reverse gradient
    
#     arr = np.zeros((n, 1, 3), dtype=float)
#     half = n // 2
#     for i in range(half):
#         t = i / max(1, half - 1)
#         arr[i, 0, :] = lerp(left, mid, t)
#     for i in range(half, n):
#         t = (i - half) / max(1, n - half - 1)
#         arr[i, 0, :] = lerp(mid, right, t)
#     return arr

# def draw_value_bubble(ax, x, y, text, fontsize=14):
#     """Centered black rounded bubble with a small bottom pointer."""
#     w, h = 70, 34
#     # rounded capsule
#     bubble = FancyBboxPatch((x - w/2, y), w, h, boxstyle="round,pad=0.02,rounding_size=8",
#                             ec="none", fc="black", zorder=5)
#     ax.add_patch(bubble)
#     # small pointer
#     tri = mpl.patches.Polygon([[x-6, y], [x+6, y], [x, y-8]], closed=True, fc="black", ec="none", zorder=5)
#     ax.add_patch(tri)
#     ax.text(x, y + h*0.55, text, color="white", fontsize=fontsize, fontweight="bold",
#             ha="center", va="center", zorder=6)

# def generate_risk_bar(indicator, value):
#     """
#     Generate a risk bar graph for a given indicator and value.
#     Returns base64 encoded PNG image.
    
#     Args:
#         indicator (str): One of 'bilirubin', 'albumin', 'inr', 'platelet'
#         value (float): The value to display on the graph
    
#     Returns:
#         str: Base64 encoded PNG image
#     """
#     if indicator not in INDICATORS:
#         raise ValueError(f"Invalid indicator: {indicator}")
    
#     # Get configuration
#     config = INDICATORS[indicator]
#     title = config['title']
#     unit = config['unit']
#     vmin = config['vmin']
#     vmax = config['vmax']
#     ranges = config['ranges']
#     labels = config['labels']
#     reverse = config['reverse']
    
#     # Handle platelet display multiplier
#     display_value = value
#     if indicator == 'platelet' and 'display_multiplier' in config:
#         display_value = value * config['display_multiplier']
    
#     # -------------------- Figure --------------------
#     fig = plt.figure(figsize=(8, 2.2))
#     ax = plt.axes([0,0,1,1])
#     ax.set_xlim(0, 800)
#     ax.set_ylim(0, 220)
#     ax.axis('off')
    
#     # Title
#     ax.text(20, 200, title, fontsize=16, fontweight="bold", va="top")
    
#     # Bar geometry
#     bar_x, bar_y = 40, 80
#     bar_w, bar_h = 720, 36
#     radius = bar_h / 2
    
#     # Soft shadow (light gray rounded rectangle, slightly offset)
#     shadow = FancyBboxPatch((bar_x, bar_y-5), bar_w, bar_h, boxstyle=f"round,pad=0,rounding_size={radius}",
#                             ec="none", fc="#e6e6e6", zorder=0)
#     ax.add_patch(shadow)
    
#     # White housing
#     housing = FancyBboxPatch((bar_x, bar_y), bar_w, bar_h, boxstyle=f"round,pad=0,rounding_size={radius}",
#                              ec="none", fc="white", zorder=1)
#     ax.add_patch(housing)
    
#     # Gradient fill (imshow clipped to rounded rect)
#     grad = gradient_colors(1000, reverse=reverse)
#     im = ax.imshow(grad.transpose(1,0,2), extent=(bar_x, bar_x+bar_w, bar_y, bar_y+bar_h),
#                    origin="lower", zorder=2, interpolation="bicubic")
#     im.set_clip_path(housing)
    
#     # Outline
#     outline = FancyBboxPatch((bar_x, bar_y), bar_w, bar_h, boxstyle=f"round,pad=0,rounding_size={radius}",
#                              ec="#cccccc", fc="none", lw=2, zorder=3)
#     ax.add_patch(outline)
    
#     # Value mapping
#     v = max(vmin, min(vmax, value))
#     t = (v - vmin) / (vmax - vmin + 1e-9)
#     px = bar_x + t * bar_w
    
#     # Value bubble (display formatted value WITHOUT unit)
#     if indicator == 'platelet':
#         # Divide by 10000 and show 2 decimal places
#         bubble_text = f"{display_value / 10000:.2f}"
#     else:
#         bubble_text = f"{display_value:.1f}"
#     draw_value_bubble(ax, px, bar_y + bar_h + 20, bubble_text, fontsize=14)

#     # Unit label in bottom right corner
#     ax.text(bar_x + bar_w, bar_y - 25, f"{unit}", fontsize=9, ha="right", va="top", color="#666666")

#     # Optional ticks for ranges
#     for (a, b), lab in zip(ranges, labels):
#         ta = (a - vmin) / (vmax - vmin); tb = (b - vmin) / (vmax - vmin)
#         mx = bar_x + (ta + tb)/2 * bar_w
#         ax.text(mx, bar_y - 12, lab, fontsize=8, ha="center", va="top", color="#555555")
    
#     # Convert to base64
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=True)
#     buf.seek(0)
#     img_base64 = base64.b64encode(buf.read()).decode('utf-8')
#     plt.close(fig)

#     return img_base64
