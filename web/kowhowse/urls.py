from django.urls import path, re_path
from django.contrib import admin
from front import views


urlpatterns = [
    path('', views.index, name='index'),
    path('<int:survey_id>', views.survey, name='survey'),
    path('<int:survey_id>/questions', views.question, name='question')
]
