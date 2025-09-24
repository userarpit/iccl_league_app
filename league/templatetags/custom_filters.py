from django import template
from ..models import Team
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_team_name(teams, team_id):
    """
    Returns the team name from a queryset of teams based on the team_id.
    """
    print(teams)
    print(team_id)
    try:
        team_id = int(team_id)
        return teams.get(id=team_id).name
    except (ValueError, Team.DoesNotExist):
        return "Unknown Team"


@register.filter
def filter_cards(cards, card_type):
    """
    Filters a list of cards by their type (e.g., 'YELLOW' or 'RED').
    """
    return [card for card in cards if card.card_type == card_type]


@register.filter
def get_opponent(match, team_name):
    """
    Returns the name of the opponent team in a given match.
    """
    if match.home_team.name == team_name:
        return match.away_team.name
    return match.home_team.name

@register.filter
def convert_newlines(text):
    """
    Replaces newline characters with HTML paragraph tags.
    """
    if not text:
        return ""
    # Replaces consecutive newlines with </p><p>
    paragraphs = text.replace('\r\n\r\n', '</p><p class="mt-4">').replace('\n\n', '</p><p class="mt-4">')
    return mark_safe(f"<p>{paragraphs}</p>")