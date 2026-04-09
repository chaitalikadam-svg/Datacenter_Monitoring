from django.urls import path
from . import views

urlpatterns = [
    path('', views.signup_view, name='signup_view'),
    path('login/', views.login_view, name='login_view'),
    path('sensor-data/', views.receive_sensor_data, name='sensor-data'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/rack-data/', views.rack_data_api, name='rack-data'),
]