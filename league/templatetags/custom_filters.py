from django import template
from ..models import Team
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime

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
    paragraphs = text.replace("\r", "<br>").replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
    return mark_safe(f"<p>{paragraphs}</p>")


@register.filter
def add_minutes(match_time_input, minutes):
    """
    Adds minutes to a time value, robustly handling string input like 'HH:MM AM/PM'.
    """
    if not match_time_input:
        return ""

    match_time_str = str(match_time_input).strip()  # Use strip to handle any whitespace

    # 12-hour format with AM/PM: I = 12-hour clock, p = AM/PM
    TIME_FORMAT = "%I:%M %p"

    start_datetime = None

    try:
        # 1. Parse the string into a full datetime object (using 1900-01-01 as the date)
        start_datetime = datetime.strptime(match_time_str, TIME_FORMAT)

        # 2. Add the minutes using timedelta
        end_datetime = start_datetime + timedelta(minutes=int(minutes))

        # 3. Return the resulting time object
        return end_datetime.time()

    except ValueError:
        # If parsing fails due to incorrect format, try common 24-hour formats as fallback
        try:
            start_datetime = datetime.strptime(match_time_str.split(".")[0], "%H:%M:%S")
            end_datetime = start_datetime + timedelta(minutes=int(minutes))
            return end_datetime.time()
        except Exception:
            # If both parsing methods fail, return empty string
            return ""

    except Exception:
        # Failure in arithmetic or other error
        return ""


@register.filter
def first_word_or_full(value, arg=None):
    """
    Returns the first word of a string. If the string contains only one word,
    or if it's very short, it returns the full string.

    This function expects 'value' to be the team name.
    The 'arg' parameter is often unused but required if the filter accepts an argument
    (though your usage of it seems redundant).
    """
    if not isinstance(value, str):
        return value

    # Split the string by spaces
    words = value.split()

    # If the name has one word, return the full name
    if len(words) <= 1:
        return value

    # Optional: If the first word is too long (e.g., > 10 chars), return the whole thing
    if len(words[0]) > 10:
        return value

    # Otherwise, return only the first word
    return words[0]


# You can register a simpler version that returns the first word only:
@register.filter
def first_word(value):
    """Returns only the first word of a string."""
    if not isinstance(value, str):
        return value

    # Split by spaces and return the first element
    return value.split()[0] if value.split() else value
