"""
DDI API Serializers
"""
from rest_framework import serializers


class DrugInputSerializer(serializers.Serializer):
    """약물 입력 시리얼라이저"""
    drugs = serializers.ListField(
        child=serializers.CharField(max_length=200),
        min_length=2,
        help_text="약물 이름 또는 DrugBank ID 리스트 (최소 2개)"
    )


class InteractionSerializer(serializers.Serializer):
    """상호작용 상세 정보"""
    type = serializers.IntegerField()
    sentence = serializers.CharField()
    risk_score = serializers.IntegerField()
    severity = serializers.CharField()
    category = serializers.CharField()
    probability = serializers.FloatField(required=False)


class PairResultSerializer(serializers.Serializer):
    """약물 쌍 결과"""
    drug1_id = serializers.CharField()
    drug2_id = serializers.CharField()
    drug1_name = serializers.CharField()
    drug2_name = serializers.CharField()
    method = serializers.CharField()
    has_interaction = serializers.BooleanField()
    interactions = InteractionSerializer(many=True)
    max_risk_score = serializers.IntegerField()
    max_severity = serializers.CharField()


class DDIAnalysisResultSerializer(serializers.Serializer):
    """DDI 분석 결과"""
    overall_risk_score = serializers.IntegerField()
    overall_severity = serializers.CharField()
    total_interactions = serializers.IntegerField()
    pairwise_results = PairResultSerializer(many=True)
    high_risk_pairs = PairResultSerializer(many=True)


class DrugSearchResultSerializer(serializers.Serializer):
    """약물 검색 결과"""
    drug_id = serializers.CharField()
    drug_name = serializers.CharField()
    similarity_score = serializers.FloatField(required=False)
