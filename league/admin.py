from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Team, Match, Player, Card, Goal
from django_admin_listfilter_dropdown.filters import DropdownFilter

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
    )

    readonly_fields = ("match_date", "match_time", "home_team", "away_team")

    def get_fields(self, request, obj=None):
        return [
            "match_date",
            "match_time",
            "home_team",
            "away_team",
            "is_played",
            "home_score",
            "away_score",
            "mom",
        ]

    inlines = [GoalInline, CardInline]

    list_filter = (
        ("week_number", DropdownFilter),  # 👈 dropdown filter instead of list
        "is_played",
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
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        js = ("league/js/match_admin.js",)


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
