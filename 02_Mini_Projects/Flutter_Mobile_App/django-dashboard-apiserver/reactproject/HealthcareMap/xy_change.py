# 좌표변환 후 csv
# EPSG5174 좌표를 WGS84(경도, 위도)로 변환

import pandas as pd
from pyproj import Transformer
import os

# EPSG5174 -> WGS84 변환기 생성
transformer = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True)


def convert_coordinates(x, y):
    """
    EPSG5174 좌표를 WGS84(경도, 위도)로 변환

    Args:
        x: EPSG5174 X 좌표
        y: EPSG5174 Y 좌표

    Returns:
        tuple: (경도, 위도)
    """
    try:
        if pd.isna(x) or pd.isna(y):
            return None, None
        lon, lat = transformer.transform(x, y)
        return lon, lat
    except Exception as e:
        print(f"좌표 변환 오류: {e}")
        return None, None


def convert_csv_coordinates(input_file, output_file, x_col, y_col):
    """
    CSV 파일의 좌표를 변환

    Args:
        input_file: 입력 CSV 파일 경로
        output_file: 출력 CSV 파일 경로
        x_col: X 좌표 컬럼명
        y_col: Y 좌표 컬럼명
    """
    print(f"파일 읽기: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')

    print(f"좌표 변환 중... (총 {len(df)}개 행)")

    # 좌표 변환
    coords = df.apply(lambda row: convert_coordinates(row[x_col], row[y_col]), axis=1)
    df['좌표(x)'] = coords.apply(lambda x: x[0])
    df['좌표(y)'] = coords.apply(lambda x: x[1])

    # 기존 EPSG5174 좌표 컬럼 제거
    df = df.drop(columns=[x_col, y_col])

    print(f"파일 저장: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"완료! 변환된 좌표 수: {df['좌표(x)'].notna().sum()}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # hospital.csv 변환
    print("\n=== hospital.csv 좌표 변환 ===")
    hospital_input = os.path.join(base_dir, "hospital.csv")
    hospital_output = os.path.join(base_dir, "hospital_converted.csv")
    convert_csv_coordinates(
        hospital_input,
        hospital_output,
        "좌표정보X(EPSG5174)",
        "좌표정보Y(EPSG5174)"
    )

    # host2.csv 변환
    print("\n=== host2.csv 좌표 변환 ===")
    host2_input = os.path.join(base_dir, "host2.csv")
    host2_output = os.path.join(base_dir, "host2_converted.csv")
    convert_csv_coordinates(
        host2_input,
        host2_output,
        "좌표정보X(EPSG5174)",
        "좌표정보Y(EPSG5174)"
    )

    print("\n=== 모든 변환 완료 ===")