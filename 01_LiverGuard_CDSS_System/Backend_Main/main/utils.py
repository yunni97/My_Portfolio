import requests
from django.conf import settings

def upload_dicom_to_orthanc(file_obj):
    """
    Django의 UploadedFile 객체를 받아 Orthanc로 전송
    """
    # settings.py에서 URL과 인증 정보 가져오기
    base_url = getattr(settings, 'ORTHANC_URL', 'http://localhost:8042')
    upload_url = f"{base_url}/instances"
    
    auth = (
        getattr(settings, 'ORTHANC_USER', 'orthanc'),
        getattr(settings, 'ORTHANC_PASSWORD', 'orthanc')
    )
    
    try:
        # 파일 포인터를 처음으로 초기화
        file_obj.seek(0)
        
        # 바이너리 데이터 읽기
        file_content = file_obj.read()
        
        headers = {
            'Content-Type': 'application/dicom' 
        }

        # Orthanc로 POST 요청 전송
        response = requests.post(
            upload_url, 
            data=file_content, 
            headers=headers, 
            auth=auth,
            timeout=30 # 대용량 파일 고려하여 타임아웃 넉넉히 설정
        )

        response.raise_for_status() # 200 OK가 아니면 예외 발생

        # 성공 시 Orthanc가 반환하는 JSON (ID, Status 등 포함)
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[Utils] Orthanc Upload Error: {e}")
        return None