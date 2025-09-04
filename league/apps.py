from django.apps import AppConfig

class LeagueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "league"

    def ready(self):
        # Import models here to avoid circular imports during app loading
        # from .models import initialize_league_data
        import league.signals
        # This will run once when the Django app starts
        # initialize_league_data()
        
