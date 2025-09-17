from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from league.models import (
    Tournament,
    Team,
    Player,
    Match,
    Team_Standing,
    Goal,
    Card,
)


class BaseViewTest(TestCase):
    """
    A base class for view tests to set up common test data.
    """

    def setUp(self):
        self.client = Client()
        self.tournament = Tournament.objects.create(short_description="ICCL Test")
        self.team1 = Team.objects.create(name="Test Team A", tournament=self.tournament)
        self.team2 = Team.objects.create(name="Test Team B", tournament=self.tournament)
        self.player1 = Player.objects.create(
            name="Test Player A", team=self.team1, tournament=self.tournament
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
        self.goal = Goal.objects.create(
            match=self.match, player=self.player1, goals=2, tournament=self.tournament
        )
        self.card = Card.objects.create(
            match=self.match,
            player=self.player1,
            card_type="YELLOW",
            tournament=self.tournament,
        )
        self.standing = Team_Standing.objects.create(
            name=self.team1.name,
            matches_played=1,
            wins=1,
            points=3,
            tournament=self.tournament,
        )


class FixtureViewTest(BaseViewTest):
    def test_fixture_view_with_week_number(self):
        """Test the fixture view renders correctly with a specific week number."""
        response = self.client.get(
            reverse("fixtures"),
            {"week_number": 1, "tournament": self.tournament.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "league/fixture.html")
        self.assertEqual(response.context["selected_week_number"], 1)
        self.assertEqual(response.context["fixtures_for_week"].count(), 1)
        self.assertEqual(response.context["fixtures_for_week"].first().week_number, 1)

    def test_fixture_view_without_week_number(self):
        """Test the fixture view defaults to the first week."""
        response = self.client.get(
            reverse("fixtures"), {"tournament": self.tournament.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "league/fixture.html")
        self.assertEqual(response.context["selected_week_number"], 1)


class ResultViewTest(BaseViewTest):
    def test_result_view_renders_correctly(self):
        """Test the result view shows played matches for a week."""
        response = self.client.get(
            reverse("results"),
            {"week_number": 1, "tournament": self.tournament.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "league/result.html")
        self.assertContains(response, "Test Team A")
        self.assertEqual(response.context["results_for_week"].count(), 1)


class TableViewTest(BaseViewTest):
    def test_table_view_renders_correctly(self):
        """Test the table view generates the standings table HTML."""
        response = self.client.get(reverse("table"), {"tournament": self.tournament.id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "league/table.html")
        self.assertIn("league-table", response.context["points_table_html"])
        self.assertIn("Test Team A", response.context["points_table_html"])
        self.assertIn("3", response.context["points_table_html"])


class StatsViewTest(BaseViewTest):
    def test_stats_view_aggregates_data_correctly(self):
        """Test that the stats view correctly aggregates data from models."""
        response = self.client.get(reverse("stats"), {"tournament": self.tournament.id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "league/stats.html")

        # Check top scorers
        self.assertEqual(response.context["top_scorers"][0]["total_goals"], 2)
        self.assertEqual(
            response.context["top_scorers"][0]["player__name"],
            "Test Player A",
        )

        # Check yellow cards
        self.assertEqual(response.context["yellow_cards"][0]["total_yellows"], 1)
        self.assertEqual(
            response.context["yellow_cards"][0]["player__name"],
            "Test Player A",
        )

        # Check MOTM list
        self.assertEqual(response.context["motm_by_week"][0]["week_number"], 1)
        self.assertEqual(
            response.context["motm_by_week"][0]["matches"][0]["mom__name"],
            "Test Player A",
        )


class PlayersViewTest(BaseViewTest):
    def test_players_view_filters_by_team(self):
        """Test that the players view shows players for the selected team."""
        response = self.client.get(
            reverse("players"),
            {"team_id": self.team1.id, "tournament": self.tournament.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "league/players.html")
        self.assertEqual(
            response.context["players_for_team"].first().name, "Test Player A"
        )
        self.assertEqual(response.context["players_for_team"].count(), 1)


class PlayerProfileViewTest(BaseViewTest):
    def test_player_profile_view_valid_player(self):
        """Test the profile view for a valid player ID."""
        response = self.client.get(
            reverse("player_profile", args=[self.player1.id]),
            {"tournament": self.tournament.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "league/player_profile.html")
        self.assertEqual(response.context["player"].name, "Test Player A")
        self.assertEqual(response.context["total_goals"], 2)
        self.assertEqual(response.context["moms"].count(), 1)
