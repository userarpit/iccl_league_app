from django.test import TestCase
from league.models import (
    Tournament,
    Team,
    Player,
    Match,
    Team_Standing,
    Goal,
    Card,
)
from django.utils import timezone


class ModelTest(TestCase):
    """
    Test suite for all models in the league app.
    """

    def setUp(self):
        """
        Set up common data for all model tests.
        """
        self.tournament = Tournament.objects.create(
            short_description="T_test"  # Pass only existing fields
        )
        self.team1 = Team.objects.create(name="Team A", tournament=self.tournament)
        self.team2 = Team.objects.create(name="Team B", tournament=self.tournament)
        self.player1 = Player.objects.create(
            name="Player A", team=self.team1, tournament=self.tournament
        )
        self.match = Match.objects.create(
            week_number=1,
            match_date=timezone.now().date(),
            home_team=self.team1,
            away_team=self.team2,
            is_played=True,
            home_score=2,
            away_score=1,
            mom=self.player1,
            tournament=self.tournament,
        )
        self.standing = Team_Standing.objects.create(
            name="Team A",
            matches_played=1,
            wins=1,
            points=3,
            tournament=self.tournament,
        )
        self.goal = Goal.objects.create(
            match=self.match, player=self.player1, goals=2, tournament=self.tournament
        )
        self.card = Card.objects.create(
            match=self.match,
            player=self.player1,
            card_type="YELLOW",
            tournament=self.tournament,
        )

    def test_tournament_creation(self):
        # Match the output of your actual model's __str__ method
        expected_output = f"Tournament ID: {self.tournament.id} - T_test"
        self.assertEqual(self.tournament.__str__(), expected_output)

    def test_team_creation(self):
        """Test that a Team instance can be created."""
        self.assertTrue(isinstance(self.team1, Team))
        self.assertEqual(self.team1.__str__(), "Team A")

    def test_player_creation(self):
        """Test that a Player instance can be created."""
        self.assertTrue(isinstance(self.player1, Player))
        self.assertEqual(self.player1.__str__(), "Player A (Team A)")

    def test_match_creation(self):
        """Test that a Match instance can be created."""
        self.assertTrue(isinstance(self.match, Match))
        self.assertEqual(self.match.__str__(), "Week 1: Team A vs Team B")

    def test_team_standing_creation(self):
        """Test that a Team_Standing instance can be created."""
        self.assertTrue(isinstance(self.standing, Team_Standing))
        self.assertEqual(self.standing.__str__(), "Team A")

    def test_goal_creation(self):
        """Test that a Goal instance can be created."""
        self.assertTrue(isinstance(self.goal, Goal))
        self.assertEqual(
            self.goal.__str__(), "Player A - Week 1: Team A vs Team B (Goal)"
        )

    def test_card_creation(self):
        """Test that a Card instance can be created."""
        self.assertTrue(isinstance(self.card, Card))
        self.assertEqual(
            self.card.__str__(), "YELLOW - Player A (Team A) (Week 1: Team A vs Team B)"
        )
