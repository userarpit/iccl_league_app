from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Count, Sum, Q
from .models import Team_Standing, Match, LEAGUE_START, VENUE, Card, Goal, Team, Player
from datetime import timedelta
import pandas as pd  # For the league table
import requests
from django.http import JsonResponse
import os
from datetime import timedelta

from django.http import HttpResponse
from django.db import connection


# Instagram API config (set your env variables securely!)
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")


from django.db.models import Min


def get_week_labels():
    """Generates dropdown labels for weeks by fetching dates from the database."""
    # Fetch all unique week numbers and their corresponding match dates
    # We use Min('match_date') to get the date for each week, assuming all
    # matches in a given week have the same date.
    week_data = (
        Match.objects.values("week_number")
        .annotate(match_date=Min("match_date"))
        .order_by("week_number")
    )

    week_labels = {}
    for data in week_data:
        week_number = data["week_number"]
        match_date = data["match_date"]
        week_labels[week_number] = (
            f"{week_number} - {match_date.strftime('%A, %d %B %Y')}"
        )

    return week_labels


def get_base_context(active_tab):
    """Provides common context for all views."""
    return {
        "venue": VENUE,
        "active_tab": active_tab,
        "week_labels": get_week_labels(),
    }


def fixture_view(request):
    active_tab = "Fixture"
    context = get_base_context(active_tab)

    selected_week_number = int(request.GET.get("week", 1))  # Default to week 1

    fixtures_for_week = Match.objects.filter(week_number=selected_week_number).order_by(
        "match_date", "match_time"
    )

    if fixtures_for_week.exists():
        first_match_of_week = fixtures_for_week.first()
        week_date = first_match_of_week.match_date
        context["week_date_str"] = week_date.strftime("%A, %d %B %Y")
    else:
        context["week_date_str"] = "N/A"

    context["selected_week_number"] = selected_week_number
    context["fixtures_for_week"] = fixtures_for_week
    context["max_week_number"] = (
        Match.objects.order_by("-week_number").first().week_number
        if Match.objects.exists()
        else 0
    )

    return render(request, "league/fixture.html", context)


def result_view(request):
    active_tab = "Result"
    context = get_base_context(active_tab)

    selected_week_number = int(request.GET.get("week", 1))

    # Retrieve match results for the selected week,
    # and use select_related() to pre-fetch the related M.O.M. player
    results_for_week = (
        Match.objects.filter(
            Q(week_number=selected_week_number)
            & (Q(is_played=True) | Q(is_walkover=True))
        )
        .select_related("mom")
        .prefetch_related("goals", "cards")
        .order_by("match_date", "match_time")
    )

    if results_for_week.exists():
        first_match_of_week = results_for_week.first()
        week_date = first_match_of_week.match_date
        context["week_date_str"] = week_date.strftime("%A, %d %B %Y")
    else:
        context["week_date_str"] = "N/A"

    context["selected_week_number"] = selected_week_number
    context["results_for_week"] = results_for_week
    context["max_week_number"] = (
        Match.objects.order_by("-week_number").first().week_number
        if Match.objects.exists()
        else 0
    )

    return render(request, "league/result.html", context)


def table_view(request):
    active_tab = "Table"
    context = get_base_context(active_tab)

    # Get all unique match weeks from the database
    match_weeks = (
        Team_Standing.objects.values_list("matches_played", flat=True)
        .distinct()
        .order_by("matches_played")
    )

    # Get the selected match week from the URL query parameters
    selected_week = request.GET.get("match_week")

    if selected_week and selected_week.isdigit():
        selected_week = int(selected_week)
    else:
        # Default to the latest match week if none is specified
        if match_weeks:
            selected_week = match_weeks.last()
        else:
            selected_week = 1

    # Fetch data for the selected match week
    standings_data = Team_Standing.objects.filter(
        matches_played=selected_week
    ).order_by("-points", "-goal_difference", "-goals_for")

    # Convert queryset to DataFrame
    df = pd.DataFrame(
        list(
            standings_data.values(
                "name",
                "matches_played",
                "wins",
                "draws",
                "losses",
                "goals_for",
                "goals_against",
                "goal_difference",
                "points",
            )
        )
    )

    if not df.empty:
        # Reorder and rename columns
        df = df[
            [
                "name",
                "matches_played",
                "wins",
                "draws",
                "losses",
                "goals_for",
                "goals_against",
                "goal_difference",
                "points",
            ]
        ]
        df = df.rename(
            columns={
                "name": "Team",
                "matches_played": "MP",
                "wins": "W",
                "draws": "D",
                "losses": "L",
                "goals_for": "GF",
                "goals_against": "GA",
                "goal_difference": "GD",
                "points": "Pts",
            }
        )
        points_table_html = df.to_html(index=False, classes="league-table")
    else:
        points_table_html = "<p>No standings available</p>"

    context["points_table_html"] = points_table_html
    context["match_weeks"] = match_weeks
    context["selected_week"] = selected_week

    return render(request, "league/table.html", context)


def team_of_the_week_view(request):
    active_tab = "Team of the Week"
    context = get_base_context(active_tab)
    return render(request, "league/team_of_the_week.html", context)


def update_result_view(request):
    if request.method == "POST":
        match_id = request.POST.get("match_id")
        home_score = request.POST.get("home_score")
        away_score = request.POST.get("away_score")

        try:
            match = Match.objects.get(id=match_id)
            match.home_score = int(home_score)
            match.away_score = int(away_score)
            match.is_played = True
            match.save()

            if match.home_score > match.away_score:
                match.home_team.points += 3
            elif match.away_score > match.home_score:
                match.away_team.points += 3
            else:
                match.home_team.points += 1
                match.away_team.points += 1

            match.home_team.save()
            match.away_team.save()

        except Match.DoesNotExist:
            pass
        except ValueError:
            pass

    return result_view(request)


# -------------------------------
# ✅ New: Post Views
# -------------------------------


def post_view(request):
    """
    Handles both the post.html page and AJAX preview refresh.
    If ?ajax=1 is passed, it returns JSON preview data.
    """
    active_tab = "Post"
    context = get_base_context(active_tab)
    weeks = range(1, 23)

    # Defaults
    selected_type = request.GET.get("post_type", "fixture")
    try:
        selected_week = int(request.GET.get("matches_played", 1))
    except ValueError:
        selected_week = 1

    # Matches for selected week
    matches = (
        Match.objects.filter(week_number=selected_week)
        .select_related("home_team", "away_team")
        .order_by("match_time")
    )

    # Placeholder Team of the Week (replace with real logic later)
    team_of_week = []

    # 🔹 If AJAX call → return JSON data
    if request.GET.get("ajax") == "1":
        data = {
            "post_type": selected_type,
            "week": selected_week,
            "matches": [
                {
                    "home": m.home_team.name,
                    "away": m.away_team.name,
                    "time": m.match_time,
                    "home_score": m.home_score,
                    "away_score": m.away_score,
                }
                for m in matches
            ],
            "team_of_week": [
                {"name": p.name, "team": p.team.name} for p in team_of_week
            ],
        }
        return JsonResponse(data)

    # 🔹 Normal request → render HTML template

    context["weeks"] = weeks
    context["selected_type"] = selected_type
    context["selected_week"] = selected_week
    context["matches"] = matches
    context["team_of_week"] = team_of_week

    return render(request, "league/post.html", context)


def submit_post(request):
    if request.method == "POST":
        post_type = request.POST.get("post_type")
        match_week = request.POST.get("match_week")

        caption = f"{post_type.capitalize()} - Match Week {match_week}"

        # Example placeholder image
        image_url = "https://via.placeholder.com/800x800.png?text=ICCL+Post"

        if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID:
            try:
                post_url = (
                    f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media"
                )
                payload = {
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": INSTAGRAM_ACCESS_TOKEN,
                }
                r = requests.post(post_url, data=payload)
                result = r.json()

                if "id" in result:
                    creation_id = result["id"]
                    publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
                    requests.post(
                        publish_url,
                        data={
                            "creation_id": creation_id,
                            "access_token": INSTAGRAM_ACCESS_TOKEN,
                        },
                    )
                    return HttpResponse("✅ Post submitted successfully to Instagram!")
                else:
                    return HttpResponse(f"❌ Instagram Error: {result}")
            except Exception as e:
                return HttpResponse(f"❌ Exception: {str(e)}")
        else:
            return HttpResponse(
                "⚠️ Instagram API not configured. Please set access token and business ID."
            )

    return redirect("post")


# your_app/views.py


def post_preview(request):
    active_tab = "Preview"
    context = get_base_context(active_tab)

    selected_week = request.GET.get("match_week")

    matches = []
    if selected_week:
        matches = Match.objects.filter(week_number=selected_week).select_related(
            "home_team", "away_team"
        )

    context["selected_week"] = selected_week
    context["matches"] = matches

    return render(request, "league/post_preview.html", context)


def stats_view(request):
    active_tab = "Stats"
    context = get_base_context(active_tab)

    # Top Goal Scorers
    top_scorers = (
        Goal.objects.values("player__name", "player__team__name")
        .annotate(total_goals=Sum("goals"))
        .order_by("-total_goals")
    )

    # Yellow Cards
    yellow_cards = (
        Card.objects.filter(card_type="YELLOW")
        .values("player__name", "player__team__name")
        .annotate(total_yellows=Count("id"))
        .order_by("-total_yellows")
    )

    # Red Cards
    red_cards = (
        Card.objects.filter(card_type="RED")
        .values("player__name", "player__team__name")
        .annotate(total_reds=Count("id"))
        .order_by("-total_reds")
    )

    context["top_scorers"] = top_scorers
    context["yellow_cards"] = yellow_cards
    context["red_cards"] = red_cards

    return render(request, "league/stats.html", context)


def players_view(request):
    active_tab = "Players"
    context = get_base_context(active_tab)

    # Fetch all teams for the dropdown
    all_teams = Team.objects.all().order_by("name")

    # Get the selected team ID from the URL parameter, default to the first team
    selected_team_id = request.GET.get("team_id")
    if not selected_team_id and all_teams.exists():
        selected_team_id = all_teams.first().id

    # Fetch players for the selected team
    players_for_team = []
    if selected_team_id:
        players_for_team = Player.objects.filter(team_id=selected_team_id).order_by(
            "name"
        )

    context["all_teams"] = all_teams
    context["players_for_team"] = players_for_team
    context["selected_team_id"] = int(selected_team_id) if selected_team_id else None

    return render(request, "league/players.html", context)


def player_profile_view(request, player_id):
    active_tab = "Players"

    # Get the common context first
    context = get_base_context(active_tab)

    # Now get the player-specific data
    player = get_object_or_404(Player, id=player_id)

    # Fetch total goals for the player
    total_goals = (
        Goal.objects.filter(player=player).aggregate(Sum("goals"))["goals__sum"] or 0
    )

    # Fetch all goals scored by the player
    goals = Goal.objects.filter(player=player).order_by("match__match_date")

    # Fetch all cards for the player
    cards = Card.objects.filter(player=player).order_by("match__match_date")
    
    # Fetch Man of the Match (MOM) details
    moms = Match.objects.filter(mom=player).order_by("week_number")

    # Add the player-specific data to the context
    context.update(
        {
            "player": player,
            "total_goals": total_goals,
            "goals": goals,
            "cards": cards,
            "moms": moms,  # Add the MOM queryset
        }
    )

    return render(request, "league/player_profile.html", context)


def health_check(request):
    try:
        # Attempt to execute a simple database query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return HttpResponse("OK", status=200)
    except Exception:
        return HttpResponse("Database connection failed", status=500)
