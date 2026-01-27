from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('patient/add/', views.patient_add_view, name='patient_add'),
    path('patient/<str:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('patient/<str:patient_id>/delete/', views.patient_delete_view, name='patient_delete'),
]