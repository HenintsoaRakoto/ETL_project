from django.urls import path
from . import views

app_name = 'etl'

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_file, name='upload'),
    path('tables/', views.list_tables, name='tables'),
    path('tables/<str:table_name>/', views.view_table, name='view_table'),
    path('tables/<str:table_name>/delete/', views.delete_table, name='delete_table'),
    path("execute_query/", views.execute_query, name="execute_query"),
]