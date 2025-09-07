from django.db import models
from datetime import date, timedelta
import re
from pathlib import Path

# ========================
# League Config (These could be in settings.py or a config file, but for simplicity,
# we'll keep them here for now, similar to the original app)
# ========================
LEAGUE_START = date(2025, 6, 29)  # First Sunday
MATCH_TIMES = ["6:00 PM", "6:45 PM", "7:30 PM", "8:15 PM", "9:00 PM", "9:45 PM"]
VENUE = "Dugout"
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


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # Add other team stats if needed (wins, losses, draws, goals scored, etc.)

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = "league_team"


class Player(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, related_name="players", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="players/", null=True, blank=True)

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

    mom = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mom_awards",
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

# Call this function from an AppConfig ready method or a management command
# We'll set this up in apps.py to run on app readiness.


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

    def __str__(self):
        return f"{self.card_type} - {self.player} ({self.match})"

    class Meta:
        managed = True


class Goal(models.Model):
    match = models.ForeignKey("Match", on_delete=models.CASCADE, related_name="goals")
    player = models.ForeignKey("Player", on_delete=models.CASCADE)
    own_goal = models.BooleanField(default=False)  # flag if it’s an own goal
    goals = models.PositiveIntegerField(default=1)

    def __str__(self):
        return (
            f"{self.player.name} - {self.match} ({'OG' if self.own_goal else 'Goal'})"
        )

    class Meta:
        managed = True
