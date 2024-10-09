"""
Configuration for the main app.

This app contains the models and views for the main page of the site.
"""

from django.apps import AppConfig


class MainConfig(AppConfig):
    """
    Configuration for the main app.

    Attributes:
        default_auto_field (str): The default auto field to use for models in
            this app.
        name (str): The name of the app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "main"
