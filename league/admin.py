from django.contrib import admin
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from .models import Team, Match, Player, Card, Goal
from more_admin_filters import DropdownFilter
from django.template.loader import render_to_string
from django.utils.html import strip_tags

admin.site.register(Team)
# admin.site.register(Match)


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
class MatchAdmin(admin.ModelAdmin):
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

    readonly_fields = ("match_date", "match_time", "home_team", "away_team")

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


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Player model.
    """

    list_display = ("name", "team")  # Displays the player's name and team in the table
    search_fields = ("name",)  # Adds a search bar for the player's name
    list_filter = ("team_id",)  # Creates a filter for the 'team' field

    # To order the list of players alphabetically by name (A-Z) by default.
    ordering = ("name",)


admin.site.unregister(Group)
