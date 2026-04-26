from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reader-status/', views.reader_status, name='reader_status'),
    path('card-status/', views.card_status, name='card_status'),
    path('dump/', views.dump_card, name='dump_card'),
    path('read/', views.read_block, name='read_block'),
    path('read/action/', views.read_block_action, name='read_block_action'),
    path('write/', views.write_block, name='write_block'),
    path('change-key/', views.change_key, name='change_key'),
    path('logs/', views.logs, name='logs'),
    path('logs/clear/', views.logs_clear, name='logs_clear'),
    path('keys/', views.keys, name='keys'),
    path('keys/add/', views.keys_add, name='keys_add'),
    path('keys/<int:pk>/delete/', views.keys_delete, name='keys_delete'),
    path('change-key/action/', views.change_key_action, name='change_key_action'),
]