from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Count, Sum, Q
from .models import Team_Standing, Match, Tournament
from .models import VENUE, Card, Goal, Team, Player, TeamOfTheWeek
import pandas as pd  # For the league table
import requests
from django.http import JsonResponse
import os
from collections import defaultdict
from django.contrib import messages
from .forms import PlayerImageForm
import cloudinary.uploader
from django.db import connection
from django.db.models import Min
from django.utils import timezone
from django.db.models import Max

# Instagram API config (set your env variables securely!)
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")


def get_week_labels(tournament_id):
    """Generates dropdown labels for weeks for a specific tournament."""
    if not tournament_id:
        return {}

    week_data = (
        Match.objects.filter(tournament_id=tournament_id)
        .values("week_number")
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


def get_tournament_details(request):
    # Get the selected tournament from the request, default to the first one if none is specified.
    tournament_id = request.GET.get("tournament")
    tournaments = Tournament.objects.all().order_by("id")
    selected_tournament = None

    if tournament_id:
        try:
            selected_tournament = tournaments.get(id=tournament_id)
        except Tournament.DoesNotExist:
            # Handle case where the tournament_id is invalid, default to the first tournament.
            if tournaments.exists():
                selected_tournament = tournaments.first()
    else:
        # If no tournament_id is in the URL, select the first one by default.
        if tournaments.exists():
            selected_tournament = tournaments.first()

    return selected_tournament, tournaments


def get_base_context(active_tab, request):
    """Provides common context for all views."""
    context = {}
    context["selected_tournament"], context["tournaments"] = get_tournament_details(
        request
    )
    context["venue"] = VENUE
    context["active_tab"] = (active_tab,)
    context["week_labels"] = get_week_labels(context["selected_tournament"])

    return context


def fixture_view(request):
    active_tab = "Fixture"
    context = get_base_context(active_tab, request)

    if context["selected_tournament"]:
        # Determine the default week number if not specified in the URL.
        today = timezone.now().date()
        upcoming_matches = Match.objects.filter(
            tournament=context["selected_tournament"],
            match_date__gte=today,
            is_played=False,
        ).order_by("week_number", "match_date")

        next_match_week_number = None
        if upcoming_matches.exists():
            next_match_week_number = upcoming_matches.first().week_number
        else:
            # If no upcoming matches, default to the latest played week.
            last_played_match = (
                Match.objects.filter(
                    tournament=context["selected_tournament"],
                    is_played=True,
                )
                .order_by("-week_number")
                .first()
            )
            if last_played_match:
                next_match_week_number = last_played_match.week_number
            else:
                next_match_week_number = (
                    1  # Fallback to week 1 if no matches exist at all.
                )

        # Get the selected week from the URL, defaulting to the determined week number.
        selected_week_number = int(
            request.GET.get("week_number", next_match_week_number)
        )

        fixtures_for_week = Match.objects.filter(
            tournament=context["selected_tournament"], week_number=selected_week_number
        ).order_by("match_date", "match_time")

        if fixtures_for_week.exists():
            first_match_of_week = fixtures_for_week.first()
            week_date = first_match_of_week.match_date
            context["week_date_str"] = week_date.strftime("%A, %d %B %Y")
        else:
            context["week_date_str"] = "N/A"

        context["selected_week_number"] = selected_week_number
        context["fixtures_for_week"] = fixtures_for_week

        # Filter the max_week_number query by the selected tournament
        max_week_number_match = (
            Match.objects.filter(tournament=context["selected_tournament"])
            .order_by("-week_number")
            .first()
        )

        context["max_week_number"] = (
            max_week_number_match.week_number if max_week_number_match else 0
        )
    else:
        # No tournament selected, so no data to display
        context["fixtures_for_week"] = []
        context["week_date_str"] = "N/A"
        context["selected_week_number"] = 1
        context["max_week_number"] = 0

    return render(request, "league/fixture.html", context)


def result_view(request):
    active_tab = "Result"
    context = get_base_context(active_tab, request)

    results_for_week = None
    if context["selected_tournament"]:
        # Find the latest week number with played matches
        last_played_match = (
            Match.objects.filter(
                Q(tournament=context["selected_tournament"])
                & (Q(is_played=True) | Q(is_walkover=True))
            )
            .order_by("-week_number")
            .first()
        )

        # Set the default week number to the latest played week or 1 if no matches exist
        default_week_number = last_played_match.week_number if last_played_match else 1

        # Get the selected week from the URL, defaulting to the determined week number
        selected_week_number = int(request.GET.get("week_number", default_week_number))

        # Retrieve match results for the selected week,
        # and use select_related() to pre-fetch the related M.O.M. player
        results_for_week = (
            Match.objects.filter(
                Q(tournament=context["selected_tournament"])
                & Q(week_number=selected_week_number)
                & (Q(is_played=True) | Q(is_walkover=True))
            )
            .select_related("mom")
            .prefetch_related("goals", "cards")
            .order_by("match_date", "match_time")
        )

        if results_for_week and results_for_week.exists():
            first_match_of_week = results_for_week.first()
            week_date = first_match_of_week.match_date
            context["week_date_str"] = week_date.strftime("%A, %d %B %Y")
        else:
            context["week_date_str"] = "N/A"

        context["selected_week_number"] = selected_week_number
        context["results_for_week"] = results_for_week if results_for_week else []

        # Get the maximum overall week number for the tournament
        max_week_number_match = (
            Match.objects.filter(tournament=context["selected_tournament"])
            .order_by("-week_number")
            .first()
        )

        context["max_week_number"] = (
            max_week_number_match.week_number if max_week_number_match else 0
        )
    else:
        # No tournament selected
        context["results_for_week"] = []
        context["week_date_str"] = "N/A"
        context["selected_week_number"] = 1
        context["max_week_number"] = 0

    return render(request, "league/result.html", context)


def table_view(request):
    active_tab = "Table"
    context = get_base_context(active_tab, request)

    selected_tournament = context["selected_tournament"]
    if not selected_tournament:
        context["points_table_html"] = "<p>Please select a tournament.</p>"
        context["match_weeks"] = []
        context["selected_week"] = 1
        return render(request, "league/table.html", context)

    # Get all unique match weeks
    match_weeks = (
        Team_Standing.objects.filter(tournament=selected_tournament)
        .values_list("matches_played", flat=True)
        .distinct()
        .order_by("matches_played")
    )

    # Selected week
    selected_week = request.GET.get("match_week")
    if selected_week and str(selected_week).isdigit():
        selected_week = int(selected_week)
    else:
        selected_week = match_weeks.last() if match_weeks else 1

    # Current standings (ordered)
    standings_data = Team_Standing.objects.filter(
        tournament=selected_tournament, matches_played=selected_week
    ).order_by("-points", "-goal_difference", "-goals_for")

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
        # numeric positions for calculation
        df["Position"] = range(1, len(df) + 1)

        # Compare with previous week (if not the first recorded week)
        if match_weeks and selected_week > min(match_weeks):
            prev_week_qs = Team_Standing.objects.filter(
                tournament=selected_tournament, matches_played=selected_week - 1
            ).order_by("-points", "-goal_difference", "-goals_for")

            prev_df = pd.DataFrame(list(prev_week_qs.values("name")))
            if not prev_df.empty:
                prev_df["Prev_Position"] = range(1, len(prev_df) + 1)
                # merge prev position into current df
                df = df.merge(prev_df[["name", "Prev_Position"]], on="name", how="left")
                df["Change"] = df["Prev_Position"] - df["Position"]

                def decorated_position(row):
                    pos = int(row["Position"])
                    change = row.get("Change")
                    # base wrapper with two spans: number and arrow area
                    base = (
                        f'<span class="pos-cell"><span class="pos-number">{pos}</span>'
                    )
                    if pd.isna(change) or change == 0:
                        arrow_html = '<span class="pos-arrow"></span>'
                    elif change > 0:
                        arrow_html = (
                            f'<span class="pos-arrow up">&#9650;{int(change)}</span>'
                        )
                    else:
                        arrow_html = f'<span class="pos-arrow down">&#9660;{abs(int(change))}</span>'
                    return base + arrow_html + "</span>"

                df["Position"] = df.apply(decorated_position, axis=1)
            else:
                # previous week empty — still render wrapped position to keep spacing
                df["Position"] = df["Position"].apply(
                    lambda x: f'<span class="pos-cell"><span class="pos-number">{int(x)}</span><span class="pos-arrow"></span></span>'
                )
        else:
            # first week (or only one week) — wrap with empty arrow span for alignment
            df["Position"] = df["Position"].apply(
                lambda x: f'<span class="pos-cell"><span class="pos-number">{int(x)}</span><span class="pos-arrow"></span></span>'
            )

        # Reorder columns (no separate Indicator column)
        df = df[
            [
                "Position",
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

        # keep escape=False so our HTML spans remain
        points_table_html = df.to_html(
            index=False, escape=False, classes="league-table"
        )
    else:
        points_table_html = "<p>No standings available</p>"

    context["points_table_html"] = points_table_html
    context["match_weeks"] = match_weeks
    context["selected_week"] = selected_week

    return render(request, "league/table.html", context)


def team_of_the_week_view(request):
    active_tab = "Team of the Week"
    context = get_base_context(active_tab, request)
    return render(request, "league/team_of_the_week.html", context)


# -------------------------------
# ✅ New: Post Views
# -------------------------------


def post_view(request):
    """
    Handles both the post.html page and AJAX preview refresh.
    If ?ajax=1 is passed, it returns JSON preview data.
    """
    active_tab = "Post"
    context = get_base_context(active_tab, request)
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
    context = get_base_context(active_tab, request)

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
    context = get_base_context(active_tab, request)
    selected_tournament = context["selected_tournament"]

    if selected_tournament:
        # Top Goal Scorers
        top_scorers = (
            Goal.objects.filter(match__tournament=selected_tournament)
            .values("player__name", "player__team__name")
            .annotate(total_goals=Sum("goals"))
            .order_by("-total_goals")
        )

        # Yellow Cards
        yellow_cards = (
            Card.objects.filter(
                card_type="YELLOW", match__tournament=selected_tournament
            )
            .values("player__name", "player__team__name")
            .annotate(total_yellows=Count("id"))
            .order_by("-total_yellows")
        )

        # Red Cards
        red_cards = (
            Card.objects.filter(card_type="RED", match__tournament=selected_tournament)
            .values("player__name", "player__team__name")
            .annotate(total_reds=Count("id"))
            .order_by("-total_reds")
        )

        # Man of the Match
        motm_by_week = defaultdict(list)

        matches_with_motm = Match.objects.filter(
            Q(tournament=selected_tournament)
            & (Q(is_played=True) | Q(is_walkover=True))
        ).order_by("week_number", "match_date", "match_time")

        for match in matches_with_motm:
            motm_by_week[match.week_number].append(
                {
                    "home_team__name": match.home_team.name,
                    "away_team__name": match.away_team.name,
                    "mom__name": match.mom.name if match.mom else "N/A",
                    "mom_team__name": match.mom.team.name if match.mom else "N/A",
                    "is_walkover": match.is_walkover,  # Add this line
                }
            )
        # Convert defaultdict to a list of dictionaries for easier iteration in the template
        motm_list = [
            {"week_number": week, "matches": matches}
            for week, matches in sorted(motm_by_week.items(), reverse=True)
        ]

    else:
        top_scorers = []
        yellow_cards = []
        red_cards = []
        motm_list = []

    context["top_scorers"] = top_scorers
    context["yellow_cards"] = yellow_cards
    context["red_cards"] = red_cards
    context["motm_by_week"] = motm_list

    return render(request, "league/stats.html", context)


def players_view(request):
    active_tab = "Players"
    context = get_base_context(active_tab, request)
    selected_tournament = context["selected_tournament"]

    if selected_tournament:
        all_teams = Team.objects.filter(tournament=selected_tournament).order_by("name")
        selected_team_id_str = request.GET.get("team_id")

        # Determine the selected team ID
        selected_team_id = None
        if selected_team_id_str:
            try:
                selected_team_id = int(selected_team_id_str)
            except (ValueError, TypeError):
                # If the provided value is not a valid integer, we treat it as if no ID was provided.
                pass

        # If no valid ID was provided (or the ID was invalid), default to the first team.
        # This will be None if there are no teams for the selected tournament.
        if selected_team_id is None and all_teams.exists():
            selected_team_id = all_teams.first().id

        # We explicitly set selected_team_id to 0 if it's still None to avoid TypeError in templates.
        # The template filter must handle 0 as a valid "no team" state.
        context["selected_team_id"] = selected_team_id if selected_team_id else 0

        # Fetch players for the determined team ID.
        players_for_team = []
        if selected_team_id:
            players_for_team = Player.objects.filter(
                team_id=selected_team_id, team__tournament=selected_tournament
            ).order_by("name")

        context["all_teams"] = all_teams
        context["players_for_team"] = players_for_team
    else:
        context["all_teams"] = []
        context["players_for_team"] = []
        context["selected_team_id"] = 0

    return render(request, "league/players.html", context)


def player_profile_view(request, player_id):
    active_tab = "Players"
    context = get_base_context(active_tab, request)
    selected_tournament = context["selected_tournament"]

    player = get_object_or_404(Player, id=player_id)
    # Instantiate the form for both cases
    image_form = PlayerImageForm()

    if selected_tournament:
        # Check if the player belongs to the selected tournament
        if player.team.tournament != selected_tournament:
            # Handle the case where the player is not in the current tournament.
            # You might want to redirect, show an error, or just return an empty profile.
            # For now, we'll return an an empty profile page.
            # return render(request, "league/players.html", context)
            return redirect(f"/players/?tournament={selected_tournament.id}")

        # Fetch total goals for the player in this tournament
        total_goals = (
            Goal.objects.filter(
                player=player, match__tournament=selected_tournament
            ).aggregate(Sum("goals"))["goals__sum"]
            or 0
        )

        # Fetch all goals scored by the player in this tournament
        goals = Goal.objects.filter(
            player=player, match__tournament=selected_tournament
        ).order_by("match__match_date")

        # Fetch all cards for the player in this tournament
        cards = Card.objects.filter(
            player=player, match__tournament=selected_tournament
        ).order_by("match__match_date")

        # Fetch Man of the Match (MOM) details for the player in this tournament
        moms = Match.objects.filter(
            mom=player, tournament=selected_tournament
        ).order_by("week_number")

        # Add the player-specific data to the context
        context.update(
            {
                "player": player,
                "total_goals": total_goals,
                "goals": goals,
                "cards": cards,
                "moms": moms,  # Add the MOM queryset
                "form": image_form,  # Pass the form in the context
            }
        )
    else:
        context.update(
            {
                "player": None,
                "total_goals": 0,
                "goals": [],
                "cards": [],
                "moms": [],
                "form": image_form,  # Pass the form in the contextx`x`
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


def player_upload_image(request, player_id):
    if request.method == "POST":
        form = PlayerImageForm(request.POST, request.FILES)
        if form.is_valid():
            player = get_object_or_404(Player, pk=player_id)
            image_file = form.cleaned_data["image"]

            try:
                # Use cloudinary.uploader.upload to send the image
                # 'folder' organizes the images in your Cloudinary account
                # 'public_id' gives the image a unique name
                upload_result = cloudinary.uploader.upload(
                    image_file, folder="player_images", public_id=f"player_{player.id}"
                )

                # Get the secure URL from the upload result
                player.image = upload_result["secure_url"]
                player.save()
                messages.success(request, "Profile picture updated successfully!")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")

            # Redirect back to the player's profile page
            return redirect("player_profile", player_id=player.id)

    # If not a POST request, redirect back to the profile page
    return redirect("player_profile", player_id=player_id)


def team_of_the_week(request):
    active_tab = "TeamOfTheWeek"
    context = get_base_context(active_tab, request)

    tournament_id = request.GET.get("tournament")
    selected_tournament = Tournament.objects.get(id=tournament_id)

    # Get the latest week number for the selected tournament
    latest_week = TeamOfTheWeek.objects.filter(
        tournament=selected_tournament
    ).aggregate(Max("week_number"))
    latest_week_number = (
        latest_week["week_number__max"] if latest_week["week_number__max"] else 1
    )

    # Get selected week number (default to the latest week if not provided)
    week_number = request.GET.get("week_number")
    if week_number:
        week_number = int(week_number)
    else:
        week_number = latest_week_number

    # Try to fetch team for this week
    try:
        selected_team = TeamOfTheWeek.objects.get(
            tournament=selected_tournament, week_number=week_number
        )
    except TeamOfTheWeek.DoesNotExist:
        selected_team = None

    # Labels for dropdown (week → formatted string)
    week_labels = {}
    all_weeks = TeamOfTheWeek.objects.filter(tournament=selected_tournament).order_by(
        "week_number"
    )
    for team in all_weeks:
        week_labels[team.week_number] = (
            f"{team.week_number} - {team.weekend_date.strftime('%A, %d %B %Y')}"
        )

    # If selected week has no label, still add it (so dropdown stays valid)
    if week_number not in week_labels:
        from datetime import date

        week_labels[week_number] = f"{week_number} - (No date)"

    context.update(
        {
            "tournaments": Tournament.objects.all(),
            "selected_tournament": selected_tournament,
            "active_tab": "TeamOfTheWeek",
            "week_labels": week_labels,
            "selected_week_number": week_number,
            "week_date_str": selected_team.weekend_date.strftime("%A, %d %B %Y")
            if selected_team
            else "N/A",
            "selected_team": selected_team,
        }
    )
    return render(request, "league/team_of_the_week.html", context)


def sponsors_view(request):
    active_tab = "Sponsors"
    context = get_base_context(active_tab, request)

    return render(request, "league/sponsors.html", context)
