import imp
from django.urls import path,re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('<int:filename>/', views.download_csv_file, name='download_csv_file'),
]