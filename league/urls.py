from django.urls import path
from . import views

urlpatterns = [
    path('', views.fixture_view, name='home'),
    path('fixtures/', views.fixture_view, name='fixtures'),
    path('results/', views.result_view, name='results'),
    path('table/', views.table_view, name='table'),
    path('update-result/', views.update_result_view, name='update_result'),
    path("post/", views.post_view, name="post"),
    path("stats/", views.stats_view, name="stats"),
    path("players/", views.players_view, name="players"),
    path('player/<int:player_id>/', views.player_profile_view, name='player_profile'),
]
