from django.apps import AppConfig


class LeagueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "league"

    def ready(self):
        # Import models here to avoid circular imports during app loading
        import league.signals
