"""
DDI API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.generic import TemplateView
import os

from .serializers import (
    DrugInputSerializer,
    DDIAnalysisResultSerializer,
    DrugSearchResultSerializer
)
from .ddi_core.data_preprocessing import DDIDataLoader
from .ddi_core.hybrid_predictor import HybridDDIPredictor
from .ddi_core.ml_model import DDIPredictor


# 싱글톤 패턴으로 데이터 로더 초기화 (한 번만 로딩)
_data_loader = None
_hybrid_predictor = None


def get_data_loader():
    """데이터 로더 싱글톤 인스턴스"""
    global _data_loader
    if _data_loader is None:
        data_dir = getattr(settings, 'DDI_DATA_DIR', 'C:/CDSS/deepddi2/data')
        _data_loader = DDIDataLoader(data_dir=data_dir)
        _data_loader.load_all_data()
    return _data_loader


def get_hybrid_predictor():
    """Hybrid 예측기 싱글톤 인스턴스"""
    global _hybrid_predictor
    if _hybrid_predictor is None:
        data_loader = get_data_loader()

        # ML 모델 로딩 (있다면)
        ml_predictor = None
        model_path = getattr(settings, 'DDI_ML_MODEL_PATH', None)
        if model_path and os.path.exists(model_path):
            try:
                ml_predictor = DDIPredictor(data_loader=data_loader)
                ml_predictor.load_model(model_path)
                print(f"[INFO] ML model loaded from {model_path}")
            except Exception as e:
                print(f"[WARNING] Could not load ML model: {e}")

        _hybrid_predictor = HybridDDIPredictor(
            data_loader=data_loader,
            ml_predictor=ml_predictor
        )
    return _hybrid_predictor


class HomeView(TemplateView):
    """홈페이지 뷰"""
    template_name = 'ddi_api/index.html'


class DDIAnalysisView(APIView):
    """
    약물 상호작용 분석 API

    POST /api/analyze/
    {
        "drugs": ["aspirin", "metformin", "statin"]
    }
    """

    def post(self, request):
        serializer = DrugInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        drug_inputs = serializer.validated_data['drugs']

        try:
            predictor = get_hybrid_predictor()
            data_loader = get_data_loader()

            # 약물 ID 확인
            drug_ids = []
            not_found = []

            for drug_input in drug_inputs:
                # DrugBank ID로 직접 검색
                if drug_input.startswith('DB') and drug_input in data_loader.drug_name_map:
                    drug_ids.append(drug_input)
                    continue

                # 약물 이름으로 검색
                found = False
                query_lower = drug_input.lower()
                for drug_id, drug_name in data_loader.drug_name_map.items():
                    if query_lower == drug_name.lower() or query_lower in drug_name.lower():
                        drug_ids.append(drug_id)
                        found = True
                        break

                if not found:
                    not_found.append(drug_input)

            if not_found:
                return Response(
                    {
                        "error": f"Drugs not found: {', '.join(not_found)}",
                        "not_found": not_found
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if len(drug_ids) < 2:
                return Response(
                    {"error": "At least 2 valid drugs are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 분석 실행
            result = predictor.predict_multi_drugs(drug_ids)

            # 결과 시리얼라이즈
            result_serializer = DDIAnalysisResultSerializer(result)

            return Response({
                "success": True,
                "data": result_serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DrugSearchView(APIView):
    """
    약물 검색 API

    GET /api/drugs/search/?q=aspirin
    """

    def get(self, request):
        query = request.query_params.get('q', '').strip()

        if not query:
            return Response(
                {"error": "Query parameter 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data_loader = get_data_loader()
            query_lower = query.lower()

            matches = []

            # DrugBank ID로 직접 검색
            if query.startswith("DB") and query in data_loader.drug_name_map:
                drug_name = data_loader.drug_name_map[query]
                matches.append({
                    'drug_id': query,
                    'drug_name': drug_name
                })
                return Response({
                    "success": True,
                    "data": matches
                })

            # 약물 이름으로 검색
            for drug_id, drug_name in data_loader.drug_name_map.items():
                if query_lower in drug_name.lower():
                    matches.append({
                        'drug_id': drug_id,
                        'drug_name': drug_name
                    })

                    # 정확히 일치하면 그것만 반환
                    if query_lower == drug_name.lower():
                        return Response({
                            "success": True,
                            "data": [matches[-1]]
                        })

                    if len(matches) >= 20:  # 최대 20개
                        break

            return Response({
                "success": True,
                "data": matches[:20]
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(APIView):
    """시스템 헬스 체크"""

    def get(self, request):
        try:
            data_loader = get_data_loader()
            predictor = get_hybrid_predictor()

            return Response({
                "success": True,
                "system": "DDI Analysis System",
                "status": "healthy",
                "ml_model_loaded": predictor.ml_predictor is not None if predictor else False,
                "total_drugs": len(data_loader.drug_name_map),
                "total_interactions": len(data_loader.ddi_data) if data_loader.ddi_data is not None else 0
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
