"""
URL configuration for the accounts app.

This app contains the logic for managing user accounts.
"""

from django.urls import path

from .views import (CustomLoginView, CustomLogoutView,
                    CustomPasswordChangeView, CustomRegisterView, UserEditView)

app_name = "accounts"

urlpatterns = [
    # registration urls
    path("register/", CustomRegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
]
# user management urls
urlpatterns += [
    # user panel
    path("user/panel/", UserEditView.as_view(), name="user_panel"),
    # password change
    path(
        "user/password/change/",
        CustomPasswordChangeView.as_view(),
        name="password_change",
    ),
]
