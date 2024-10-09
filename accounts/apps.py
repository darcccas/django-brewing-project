"""
Configuration for the accounts app.

This app contains the logic for managing user accounts.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration for the accounts app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
