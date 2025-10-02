from django.db import models
from datetime import date
import re
from pathlib import Path
from cloudinary.models import CloudinaryField
from PyPDF2 import PdfFileReader

# ========================
# League Config (These could be in settings.py or a config file, but for simplicity,
# we'll keep them here for now, similar to the original app)
# ========================
LEAGUE_START = date(2025, 6, 29)  # First Sunday
MATCH_TIMES = ["6:00 PM", "6:45 PM", "7:30 PM", "8:15 PM", "9:00 PM", "9:45 PM"]
VENUE = "Dugout Turf, Robot Square, Indore"
PDF_PATH = Path(
    "/mnt/data/Fixtures - ICCL 4.0.pdf"
)  # This path needs to be accessible by Django


# Helper functions from original Streamlit app
def extract_text_from_pdf(path: Path):
    if not path.exists():
        # In a Django app, you might want to log this error
        return ""
    try:
        reader = PdfFileReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        # Log the error, or handle it more gracefully
        print(f"Error reading PDF: {e}")
        return ""


def extract_teams_from_text(text: str):
    m = re.search(r"Teams\s*(.*?)Starting from", text, re.S | re.I)
    block = m.group(1) if m else text
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    candidates = []
    for ln in lines:
        if (
            re.search(r"\bFC\b", ln)
            or "BKFC" in ln
            or "Bon" in ln
            or "Sapphire" in ln
            or "H&H" in ln
            or "Sarco" in ln
            or "Sarthak" in ln
            or "Procure" in ln
            or "Propex" in ln
            or "Reckon" in ln
        ):
            candidates.append(re.sub(r"\s+", " ", ln).strip())
    seen = set()
    return [c for c in candidates if not (c in seen or seen.add(c))]


DEFAULT_TEAMS = [
    "Ektarfa FC (TeamSkeet)",
    "BKFC",
    "Bon Bon FC (Supa)",
    "Cell Kraft FC (Riza)",
    "H&H Boyz",
    "Kanhaiya's Physio FC (Beast)",
    "Procure FC (Carnage)",
    "Propex FC (Galacticos)",
    "Reckon FC (FUTURE)",
    "Sapphire Seven",
    "Sarco FC (LUFC)",
    "Sarthak Singapore FC (Silverbacks)",
]


class Tournament(models.Model):
    """
    A Django model to represent a tournament.

    Django automatically creates an 'id' primary key field for every model.
    """

    # Django automatically adds an 'id' primary key field.

    short_description = models.CharField(
        max_length=255,
        default="Untitled Tournament",  # Added a default value
        help_text="A short description of the tournament.",
    )
    long_description = models.TextField(
        default="No description provided.",  # Added a default value
        help_text="A detailed, long description of the tournament.",
    )

    tournament_start_date = models.DateField(
        null=True,  # Allows the field to be empty in the database
        blank=True,  # Allows the field to be empty in forms/admin
        help_text="The start date of the tournament.",
    )

    def __str__(self):
        """String for representing the Model object."""
        # This will show a user-friendly representation in the admin interface
        return f"{self.short_description}"

    class Meta:
        managed = True


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = CloudinaryField("logo_images", null=True, blank=True)
    
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="teams",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "league_team"


class Player(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, related_name="players", on_delete=models.CASCADE)
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="players",
        null=True,
        blank=True,
    )
    image = CloudinaryField("player_images", null=True, blank=True)

    class Meta:
        managed = True
        db_table = "league_player"

    def __str__(self):
        return f"{self.name} ({self.team.name})"


class Match(models.Model):
    week_number = models.IntegerField()
    match_date = models.DateField()
    home_team = models.ForeignKey(
        Team, related_name="home_matches", on_delete=models.CASCADE
    )
    away_team = models.ForeignKey(
        Team, related_name="away_matches", on_delete=models.CASCADE
    )
    match_time = models.CharField(
        max_length=10, blank=True, null=True
    )  # e.g., "6:00 PM"
    home_score = models.IntegerField(blank=True, null=True)
    away_score = models.IntegerField(blank=True, null=True)
    is_played = models.BooleanField(default=False)
    is_walkover = models.BooleanField(default=False)
    walkover_winner = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="walkover_wins",
    )
    mom = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mom_awards",
    )
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="matches",
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"Week {self.week_number}: {self.home_team.name} vs {self.away_team.name}"
        )

    class Meta:
        verbose_name_plural = "Matches"
        managed = True
        db_table = "league_match"
        ordering = ["week_number", "match_date", "match_time"]


class Team_Standing(models.Model):
    name = models.CharField(max_length=100)
    matches_played = models.IntegerField(default=0)  # MP
    wins = models.IntegerField(default=0)  # W
    draws = models.IntegerField(default=0)  # D
    losses = models.IntegerField(default=0)  # L
    goals_for = models.IntegerField(default=0)  # GF
    goals_against = models.IntegerField(default=0)  # GA
    goal_difference = models.IntegerField(default=0)  # GD
    points = models.IntegerField(default=0)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True)
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="standings",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "league_team_standing"
        ordering = ["-points", "name"]  # Order by points descending, then by name


class Card(models.Model):
    CARD_TYPES = [
        ("YELLOW", "Yellow Card"),
        ("RED", "Red Card"),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="cards")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="cards")
    card_type = models.CharField(max_length=6, choices=CARD_TYPES)
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="cards",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.card_type} - {self.player} ({self.match})"

    class Meta:
        managed = True


class Goal(models.Model):
    match = models.ForeignKey("Match", on_delete=models.CASCADE, related_name="goals")
    player = models.ForeignKey("Player", on_delete=models.CASCADE)
    own_goal = models.BooleanField(default=False)  # flag if it’s an own goal
    goals = models.PositiveIntegerField(default=1)
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="goals",
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.player.name} - {self.match} ({'OG' if self.own_goal else 'Goal'})"
        )

    class Meta:
        managed = True


class TeamOfTheWeek(models.Model):
    id = models.AutoField(primary_key=True)
    week_number = models.PositiveSmallIntegerField()  # 1 to 22
    weekend_date = (
        models.DateField()
    )  # Sundays (29 Jun 2025 → 22 weeks, skip 19 Oct 2025)

    # Player positions
    striker = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="striker_weeks"
    )

    left_mid = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="left_mid_weeks"
    )
    right_mid = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="right_mid_weeks"
    )

    left_defence = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="left_defence_weeks"
    )
    right_defence = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="right_defence_weeks"
    )

    goal_keeper = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="goal_keeper_weeks"
    )

    # Tournament link
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="team_of_the_weeks"
    )

    def __str__(self):
        return f"{self.tournament.short_description} - Week {self.week_number} ({self.weekend_date})"

    class Meta:
        managed = True


class Sponsor(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    name = models.CharField(max_length=60)
    sponsor_type = models.CharField(max_length=30)  # fixed length up to 30

    sponsor_image = CloudinaryField(
        "image", blank=True, null=True, help_text="Sponsor image stored in Cloudinary"
    )
    # path to image file
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    instagram = models.CharField(
        max_length=30, blank=True, null=True
    )  # normal char field
    linktree = models.URLField(blank=True, null=True)
    tournament = models.ForeignKey(
        "Tournament",  # assumes Tournament model exists in same app
        on_delete=models.CASCADE,
        related_name="sponsors",
    )

    def __str__(self):
        return f"{self.name} ({self.sponsor_type})"

    class Meta:
        managed = True
        db_table = "league_sponsor"
