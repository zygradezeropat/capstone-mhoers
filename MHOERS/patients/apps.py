from django.apps import AppConfig


class PatientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patients'
    
    def ready(self):
        # Import signal handlers (same pattern as accounts app)
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid import-time crashes if migrations are running
            pass