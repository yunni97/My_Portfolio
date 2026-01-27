from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import base64
import requests
import json
import random

@csrf_exempt
def lasso_cox_multimodal(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        # static/test.jpg 파일 읽기
        image_path = os.path.join(settings.BASE_DIR.parent, 'static', 'test.jpg')

        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')

        # 10개의 랜덤 tabular features 생성
        table_features = [round(random.uniform(0, 100), 2) for _ in range(10)]
        table_features_str = json.dumps(table_features)

        # AI API 요청
        api_url = 'http://34.67.62.238:3000/predict'
        payload = {
            'image_base64': image_base64,
            'table_features': table_features_str
        }

        response = requests.post(api_url, json=payload, timeout=30)
        response.raise_for_status()

        # AI API 응답 반환
        result = response.json()

        return JsonResponse({
            'success': True,
            'prediction': result,
            'input_features': table_features
        })

    except FileNotFoundError:
        return JsonResponse({'error': 'test.jpg not found in static directory'}, status=404)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'AI API request failed: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
