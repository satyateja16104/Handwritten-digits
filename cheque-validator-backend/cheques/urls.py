from django.urls import path
from .views import ChequeUploadView, SessionListView,GeneratePDFView
from . import views
urlpatterns = [
    path('cheques/', ChequeUploadView.as_view(), name='cheque-upload'),
    path('sessions/', SessionListView.as_view(), name='session-history'),
    path('sessions/<int:pk>/pdf/', views.GeneratePDFView.as_view(), name='generate-pdf'),
]
