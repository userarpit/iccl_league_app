from django.contrib import admin
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from .models import Team, Match, Player, Card, Goal
from .models import Sponsor, Team_Standing, Tournament, TeamOfTheWeek
from more_admin_filters import DropdownFilter
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q

# from tracking.models import Visitor


class TournamentAdminMixin:
    def tournament_short_description(self, obj):
        if hasattr(obj, "tournament"):
            return obj.tournament.short_description
        elif hasattr(obj, "team") and hasattr(obj.team, "tournament"):
            return obj.team.tournament.short_description
        return None

    tournament_short_description.short_description = "Tournament"


# Register the Team model and customize its admin view
@admin.register(Team)
class TeamAdmin(TournamentAdminMixin, admin.ModelAdmin):
    # This list_display will show the team's name and the tournament's short description
    # on the change list page.
    list_display = ("name", "tournament_short_description")

    # This list_filter adds a sidebar to filter teams by tournament.
    list_filter = ("tournament__short_description",)


class CardInline(admin.TabularInline):
    model = Card
    extra = 1
    # autocomplete_fields = ["player"]

    def get_formset(self, request, obj=None, **kwargs):
        """
        Limit player choices to home/away teams of the match.
        `obj` is the Match instance being edited.
        """
        formset = super().get_formset(request, obj, **kwargs)
        if obj:  # editing an existing Match
            formset.form.base_fields["player"].queryset = Player.objects.filter(
                team__in=[obj.home_team, obj.away_team]
            )
        else:  # creating new Match → no teams yet
            formset.form.base_fields["player"].queryset = Player.objects.none()
        return formset


class GoalInline(admin.TabularInline):
    model = Goal
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "player":
            match_id = request.resolver_match.kwargs.get("object_id")
            if match_id:
                try:
                    match = Match.objects.get(pk=match_id)
                    kwargs["queryset"] = Player.objects.filter(
                        team__in=[match.home_team, match.away_team]
                    )
                except Match.DoesNotExist:
                    kwargs["queryset"] = Player.objects.none()
            else:
                kwargs["queryset"] = Player.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Match)
class MatchAdmin(TournamentAdminMixin, admin.ModelAdmin):
    list_display = (
        "week_number",
        "match_date",
        "match_time",
        "home_team",
        "away_team",
        "is_played",
        "is_walkover",
        "walkover_winner",
    )

    readonly_fields = ("match_date", "match_time")

    def get_fields(self, request, obj=None):
        return [
            "match_date",
            "match_time",
            "home_team",
            "away_team",
            "is_played",
            "is_walkover",
            "walkover_winner",
            "home_score",
            "away_score",
            "mom",
        ]

    inlines = [GoalInline, CardInline]

    list_filter = (
        "tournament__short_description",
        ("week_number", DropdownFilter),  # 👈 dropdown filter instead of list
        "is_played",
        "is_walkover",
    )

    search_fields = ("home_team__name", "away_team__name")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mom":
            # Get the match object being edited
            match_id = request.resolver_match.kwargs.get("object_id")
            if match_id:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Player.objects.filter(
                    team__in=[match.home_team, match.away_team]
                )
            else:
                # If creating a new match (no object yet), show empty queryset
                kwargs["queryset"] = Player.objects.none()

        # Filter for Walkover Winner
        if db_field.name == "walkover_winner":
            match_id = request.resolver_match.kwargs.get("object_id")
            if match_id:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Team.objects.filter(
                    id__in=[match.home_team.id, match.away_team.id]
                )
            else:
                kwargs["queryset"] = Team.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        js = ("league/js/match_admin.js",)

    def save_model(self, request, obj, form, change):
        """
        The main object needs to be saved first.
        """
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """
        This method is called after the main object and its inlines are saved.
        """
        super().save_related(request, form, formsets, change)

        # Now, all inlines (Goals, Cards) are guaranteed to be saved.
        match = form.instance

        # Now, call the signal logic from here.
        # We need to manually call the post_save logic here.
        if match.is_played or match.is_walkover:
            _update_or_create_standing(match)
            _cascade_standing_updates(match.home_team, match.week_number)
            _cascade_standing_updates(match.away_team, match.week_number)
            self.send_match_details_email(match)

    def send_match_details_email(self, match):
        """
        Sends an email with the details of the saved match.
        """
        subject = f"Match Details: {match.home_team.name} vs {match.away_team.name}"

        # Render the email content from an HTML template
        html_message = render_to_string(
            "league/match_details_email.html", {"match": match}
        )
        plain_message = strip_tags(html_message)
        from_email = "masterarpit@gmail.com"
        to_email = [
            "masterarpit10@gmail.com",
        ]

        try:
            send_mail(
                subject, plain_message, from_email, to_email, html_message=html_message
            )
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")


# Step 1: Create the custom filter class
class HasImageFilter(admin.SimpleListFilter):
    """
    A custom filter to check if a player has an image uploaded.
    """

    title = "Image Upload Status"  # The title of the filter in the admin sidebar
    parameter_name = "has_image"  # A URL parameter for the filter

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples with the filter options.
        The first element of the tuple is the value for the URL,
        and the second is the human-readable option name.
        """
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(self, request, queryset):
        """
        Applies the filter to the queryset based on the selected option.
        """
        if self.value() == "yes":
            return queryset.filter(image__isnull=False)
        if self.value() == "no":
            return queryset.filter(image__isnull=True)
        return queryset


# Register the Player model
@admin.register(Player)
class PlayerAdmin(TournamentAdminMixin, admin.ModelAdmin):
    """
    Admin configuration for the Player model.
    """

    list_display = (
        "name",
        "team",
        "tournament_short_description",
    )  # Displays the player's name, team, and tournament
    search_fields = ("name",)  # Adds a search bar for the player's name
    list_filter = (
        "tournament__short_description",
        "team",
        HasImageFilter,
    )  # Filters by tournament short description

    # To order the list of players alphabetically by name (A-Z) by default.
    ordering = ("name",)


admin.site.unregister(Group)
admin.site.register(TeamOfTheWeek)

# admin.site.register(Tournament)


# --- Signal-like functions moved here for use in save_related ---
def _update_or_create_standing(match_instance):
    teams = [match_instance.home_team, match_instance.away_team]

    # Get the tournament from the match instance
    tournament_instance = match_instance.tournament

    for team in teams:
        standing_entry = Team_Standing.objects.filter(
            match=match_instance, name=team
        ).first()

        previous_standing = (
            Team_Standing.objects.filter(
                name=team, matches_played=(match_instance.week_number - 1)
            )
            .order_by("-id")
            .first()
        )

        new_data = _calculate_standing_data(match_instance, team, previous_standing)

        if standing_entry:
            for key, value in new_data.items():
                setattr(standing_entry, key, value)
            standing_entry.tournament = tournament_instance
            standing_entry.save()
        else:
            Team_Standing.objects.create(
                name=team,
                match=match_instance,
                tournament=tournament_instance,
                **new_data,
            )


def _cascade_standing_updates(team, start_week):
    subsequent_matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        week_number__gte=start_week,
        is_played=True,
    ).order_by("week_number", "match_date", "match_time")

    for match in subsequent_matches:
        _update_or_create_standing(match)


def _calculate_standing_data(match, team, previous_standing):
    goals_for = match.home_score if team == match.home_team else match.away_score
    goals_against = match.away_score if team == match.home_team else match.home_score

    wins, draws, losses, points = 0, 0, 0, 0
    if goals_for > goals_against:
        wins = 1
        points = 3
    elif goals_for < goals_against:
        losses = 1
    else:
        draws = 1
        points = 1

    base_data = {
        "matches_played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_difference": 0,
        "points": 0,
    }

    if previous_standing:
        base_data = {
            "matches_played": previous_standing.matches_played,
            "wins": previous_standing.wins,
            "draws": previous_standing.draws,
            "losses": previous_standing.losses,
            "goals_for": previous_standing.goals_for,
            "goals_against": previous_standing.goals_against,
            "goal_difference": previous_standing.goal_difference,
            "points": previous_standing.points,
        }

    return {
        "matches_played": base_data["matches_played"] + 1,
        "wins": base_data["wins"] + wins,
        "draws": base_data["draws"] + draws,
        "losses": base_data["losses"] + losses,
        "goals_for": base_data["goals_for"] + goals_for,
        "goals_against": base_data["goals_against"] + goals_against,
        "goal_difference": base_data["goal_difference"] + (goals_for - goals_against),
        "points": base_data["points"] + points,
    }


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        "short_description",
        "long_description",
    )

    readonly_fields = ("short_description", "long_description")


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Player model.
    """

    list_display = (
        "name",
        "sponsor_type",
        "tournament",
    )  # Displays the player's name, team, and tournament

    # To order the list of players alphabetically by name (A-Z) by default.
