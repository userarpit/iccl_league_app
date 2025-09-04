# your_app_name/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Match, Team_Standing


@receiver(post_save, sender=Match)
def update_team_standings(sender, instance, **kwargs):
    # This check ensures the signal only runs when the match is marked as played
    # and has scores entered.
    if (
        not instance.is_played
        or instance.home_score is None
        or instance.away_score is None
    ):
        return

    # Check if a Team_Standing entry already exists for this match.
    standing_exists = Team_Standing.objects.filter(match=instance).exists()

    # --- Reusable logic to calculate and get previous standings ---
    def get_and_calculate_new_standing_data(team, goals_for, goals_against):
        """
        Helper function to get the previous standing and calculate new values.
        It handles the case where there is no previous standing.
        """
        # We need to filter by the 'team' ForeignKey, not the 'name' field
        previous_standing = (
            Team_Standing.objects.filter(name=team).order_by("-id").first()
        )

        wins, draws, losses, points = 0, 0, 0, 0

        if goals_for > goals_against:
            wins = 1
            points = 3
        elif goals_for < goals_against:
            losses = 1
        else:
            draws = 1
            points = 1

        new_data = {
            "name": team,
            "matches_played": (previous_standing.matches_played + 1)
            if previous_standing
            else 1,
            "wins": (previous_standing.wins + wins) if previous_standing else wins,
            "draws": (previous_standing.draws + draws) if previous_standing else draws,
            "losses": (previous_standing.losses + losses)
            if previous_standing
            else losses,
            "goals_for": (previous_standing.goals_for + goals_for)
            if previous_standing
            else goals_for,
            "goals_against": (previous_standing.goals_against + goals_against)
            if previous_standing
            else goals_against,
            "points": (previous_standing.points + points)
            if previous_standing
            else points,
        }
        new_data["goal_difference"] = new_data["goals_for"] - new_data["goals_against"]
        return new_data

    # --- NEW LOGIC: If a standing for this match already exists, update it. ---
    if standing_exists:
        # Get the existing standing records for this specific match instance.
        home_standing = Team_Standing.objects.get(
            match=instance, name=instance.home_team
        )
        away_standing = Team_Standing.objects.get(
            match=instance, name=instance.away_team
        )
        # Calculate new standing values for the home team
        new_home_standing_data = get_and_calculate_new_standing_data(
            instance.home_team, instance.home_score, instance.away_score
        )
        # Update the existing record with the new data
        for key, value in new_home_standing_data.items():
            print(key, " - ", value)
            setattr(home_standing, key, value)
        home_standing.save()

        # Calculate new standing values for the away team
        new_away_standing_data = get_and_calculate_new_standing_data(
            instance.away_team, instance.away_score, instance.home_score
        )
        # Update the existing record with the new data
        for key, value in new_away_standing_data.items():
            setattr(away_standing, key, value)
        away_standing.save()
        return  # Exit the function after updating

    # --- OLD LOGIC: If it doesn't exist, create a new standing entry. ---
    # Logic for Home Team
    new_home_standing_data = get_and_calculate_new_standing_data(
        instance.home_team, instance.home_score, instance.away_score
    )
    new_home_standing_data["match"] = instance  # Add the match field for creation
    Team_Standing.objects.create(**new_home_standing_data)

    # Logic for Away Team
    new_away_standing_data = get_and_calculate_new_standing_data(
        instance.away_team, instance.away_score, instance.home_score
    )
    new_away_standing_data["match"] = instance  # Add the match field for creation
    Team_Standing.objects.create(**new_away_standing_data)

