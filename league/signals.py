# your_app_name/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Match, Team_Standing


@receiver(pre_save, sender=Match)
def set_walkover_scores(sender, instance, **kwargs):
    """
    Sets the score for a walkover match before the instance is saved.
    This prevents recursion errors.
    """
    if instance.is_walkover:
        # A walkover match is not considered 'played' in the usual sense.
        # So we ensure is_played remains False.
        instance.is_played = False

        # Set the score based on the walkover winner
        if instance.walkover_winner == instance.home_team:
            instance.home_score = 3
            instance.away_score = 0
        elif instance.walkover_winner == instance.away_team:
            instance.home_score = 0
            instance.away_score = 3
        # No need to call instance.save() here, as Django will save
        # the instance with the new scores immediately after this signal.


@receiver(post_save, sender=Match)
def update_team_standings(sender, instance, **kwargs):
    # This check ensures the signal only runs when the match is marked as played
    # and has scores entered.
    # This block handles walkover matches
    if instance.is_walkover:
        winner = instance.walkover_winner
        if not winner:
            return

        winner_previous_standing = (
            Team_Standing.objects.filter(name=winner)
            .order_by("-matches_played")
            .first()
        )

        winner_matches_played = (
            (winner_previous_standing.matches_played + 1)
            if winner_previous_standing
            else 1
        )
        winner_matches_won = (
            (winner_previous_standing.wins + 1) if winner_previous_standing else 1
        )

        winner_matches_draw = (
            (winner_previous_standing.draws) if winner_previous_standing else 1
        )

        winner_matches_lost = (
            (winner_previous_standing.losses) if winner_previous_standing else 1
        )

        winner_points = (
            (winner_previous_standing.points + 3) if winner_previous_standing else 3
        )
        winner_goals_for = (
            (winner_previous_standing.goals_for + 3) if winner_previous_standing else 3
        )
        winner_goals_against = (
            winner_previous_standing.goals_against if winner_previous_standing else 0
        )
        winner_goal_difference = (
            (winner_previous_standing.goal_difference + 3)
            if winner_previous_standing
            else 3
        )

        Team_Standing.objects.create(
            name=winner,
            match=instance,
            points=winner_points,
            matches_played=winner_matches_played,
            wins=winner_matches_won,
            draws=winner_matches_draw,
            losses=winner_matches_lost,
            goals_for=winner_goals_for,
            goals_against=winner_goals_against,
            goal_difference=winner_goal_difference,
        )

        # Create a new Team_Standing entry for the loser.
        loser = (
            instance.home_team if winner == instance.away_team else instance.away_team
        )
        loser_previous_standing = (
            Team_Standing.objects.filter(name=loser).order_by("-matches_played").first()
        )

        loser_matches_played = (
            (loser_previous_standing.matches_played + 1)
            if loser_previous_standing
            else 1
        )
        loser_matches_won = (
            (loser_previous_standing.wins) if loser_previous_standing else 1
        )
        loser_matches_draw = (
            (loser_previous_standing.draws) if loser_previous_standing else 1
        )
        loser_matches_lost = (
            (loser_previous_standing.losses + 1) if loser_previous_standing else 1
        )
        loser_points = loser_previous_standing.points if loser_previous_standing else 0
        loser_goals_for = (
            loser_previous_standing.goals_for if loser_previous_standing else 0
        )
        loser_goals_against = (
            (loser_previous_standing.goals_against + 3)
            if loser_previous_standing
            else 3
        )
        loser_goal_difference = (
            (loser_previous_standing.goal_difference - 3)
            if loser_previous_standing
            else -3
        )

        Team_Standing.objects.create(
            name=loser,
            match=instance,
            points=loser_points,
            matches_played=loser_matches_played,
            wins=loser_matches_won,
            draws=loser_matches_draw,
            losses=loser_matches_lost,
            goals_for=loser_goals_for,
            goals_against=loser_goals_against,
            goal_difference=loser_goal_difference,
        )
        return

    if (
        not instance.is_played
        or instance.home_score is None
        or instance.away_score is None
    ):
        print("return from here")
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
