"""
Custom views for authentication and user management
"""

from django.contrib.auth import login
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView

from .forms import (CustomAuthenticationForm, CustomPasswordChangeForm,
                    CustomUserCreationForm, UserEditForm)


class CustomRegisterView(CreateView):
    """
    Custom view for registering new users.

    Use a custom form that extends the default UserCreationForm and adds
    email, first_name, and last_name fields.
    """

    template_name = "register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("main:user_home")

    def form_valid(self, form):
        """
        Save the form and log the user in.

        After the form is valid, save the form and log the user in using the
        ModelBackend.
        """
        user = form.save()
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(self.success_url)


class CustomLoginView(LoginView):
    """
    Custom view for logging in users.

    Use a custom form that extends the default AuthenticationForm and adds
    a "remember me" field.
    """

    form_class = CustomAuthenticationForm
    template_name = "login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        """
        Save the form and log the user in.

        If the user has checked the "remember me" field, set the session
        expiry to 2 weeks. Otherwise, set the session expiry to 0.
        """
        remember_me = form.cleaned_data.get("remember_me")
        auth_login(self.request, form.get_user())

        if not remember_me:
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(1209600)

        return redirect(self.get_success_url())

    def get_success_url(self):
        """
        Return the URL to redirect to after the user has logged in.

        If the user has specified a "next" URL in the request, use that.
        Otherwise, use the url of the user_home view.
        """
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse_lazy("main:user_home")


class CustomLogoutView(LogoutView):
    """
    Custom view for logging out users.

    Replaces the default LogoutView to provide a template for the logout
    page.
    """

    template_name = "logout.html"
    next_page = reverse_lazy("accounts:logout")

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to the logout page.

        Redirect the user to the logout page.
        """
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to the logout page.

        Log the user out and redirect them to the logout page.
        """
        return super().post(request, *args, **kwargs)


class UserEditView(UpdateView):
    """
    Custom view for editing a user's details.

    This view extends the default UpdateView and is used to edit a user's
    details in the user panel page.
    """

    model = User
    form_class = UserEditForm
    template_name = "user_panel.html"
    success_url = reverse_lazy("main:user_home")

    def get_object(self, queryset=None):
        """
        Return the user object to edit.
        """
        return self.request.user  # return the user object


class CustomPasswordChangeView(PasswordChangeView):
    """
    Custom view for changing a user's password.

    Use a custom form that extends the default PasswordChangeForm and adds
    a help text to the new_password1 field.
    """

    form_class = CustomPasswordChangeForm
    template_name = "password_change.html"
    success_url = reverse_lazy("accounts:user_panel")
