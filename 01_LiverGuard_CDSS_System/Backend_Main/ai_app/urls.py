from django.urls import path
from . import views

urlpatterns = [
    # lasso_cox_multimodal
    path('lasso_cox_multimodal/', views.lasso_cox_multimodal, name='lasso_cox_multimodal'),
]
