import orthanc
import requests
import json

# Docker Compose 내부망 주소 사용 ("http://서비스명:포트")
DJANGO_WEBHOOK_URL = "https://sylphy-unprolongable-mirta.ngrok-free.dev/api/pacs/webhook/"

def OnStoredInstance(instanceId, tags, metadata):
    # 1. 로그 출력 (Orthanc 로그창에서 확인 가능)
    print(f"[Orthanc] New DICOM received! ID: {instanceId}")

    # 2. Django에게 알림 전송
    try:
        payload = {
            "instance_id": instanceId,
            "patient_id": tags.get("PatientID", "Unknown"),
            "study_instance_uid": tags.get("StudyInstanceUID", "Unknown")
        }
        
        # 3초 타임아웃 (Django가 바빠도 Orthanc는 멈추면 안 되니까)
        requests.post(DJANGO_WEBHOOK_URL, json=payload, timeout=3)
        print(f"[Orthanc] Trigger sent to Django for {instanceId}")

    except Exception as e:
        print(f"[Orthanc] Failed to trigger Django: {e}")

# Orthanc에 이벤트 등록
orthanc.RegisterOnStoredInstanceCallback(OnStoredInstance)