"""
Register all models from the main app in the admin interface.

This is a workaround for https://code.djangoproject.com/ticket/18151.
"""

from django.apps import apps
from django.contrib import admin

app_config = apps.get_app_config("main")

# Register all models from the main app in the admin interface
for model in app_config.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
