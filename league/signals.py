# your_app_name/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db.models import Q
from .models import Match, Team_Standing, Goal, Card


@receiver(pre_save, sender=Match)
def set_walkover_scores(sender, instance, **kwargs):
    """
    Sets the score for a walkover match before the instance is saved.
    This prevents recursion errors.
    """
    if instance.is_walkover:
        instance.is_played = False
        if instance.walkover_winner == instance.home_team:
            instance.home_score = 3
            instance.away_score = 0
        elif instance.walkover_winner == instance.away_team:
            instance.home_score = 0
            instance.away_score = 3

