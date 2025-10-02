from django.urls import path
from . import views

urlpatterns = [
    path("", views.sponsors_view, name="home"),
    path("fixtures/", views.fixture_view, name="fixtures"),
    path("results/", views.result_view, name="results"),
    path("table/", views.table_view, name="table"),
    path("stats/", views.stats_view, name="stats"),
    path("players/", views.players_view, name="players"),
    path("player/<int:player_id>/", views.player_profile_view, name="player_profile"),
    path("players/", views.players_view, name="players"),
    path("healthz", views.health_check),
    # New URL for image upload
    path("posts/", views.posts_view, name="posts"),
    path("team-of-the-week/", views.team_of_the_week, name="team_of_the_week"),
    path("sponsors/", views.sponsors_view, name="sponsors"),
]
