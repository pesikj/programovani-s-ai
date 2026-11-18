from django.urls import path
from . import case_views

app_name = 'crm'
urlpatterns = [
    path('', case_views.case_list, name='case-list'),
    path('cases/new/', case_views.case_create, name='case-create'),
    path('cases/<int:pk>/', case_views.case_detail, name='case-detail'),
    path('cases/<int:pk>/edit/', case_views.case_update, name='case-update'),
]
