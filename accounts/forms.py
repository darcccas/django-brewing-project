"""
Custom forms for user authentication.

This module contains custom forms for user authentication. These forms are used
in the login, logout, and registration views.

The forms include a custom AuthenticationForm, PasswordChangeForm, and
UserCreationForm. The custom AuthenticationForm includes a hidden field for
the next page. The custom PasswordChangeForm is the same as the default
PasswordChangeForm, but it includes a docstring. The custom UserCreationForm
extends the default UserCreationForm and adds email, first_name, and last_name
fields. It also adds a placeholder attribute to the username field.

The forms include a custom clean_email method to validate the email field.
"""

from django import forms
from django.contrib.auth.forms import (AuthenticationForm, PasswordChangeForm,
                                       UserCreationForm)
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    """
    Custom form for creating a new user.

    This form extends the default UserCreationForm and adds email, first_name,
    and last_name fields. It also adds a placeholder attribute to the username
    field.

    The form includes a custom clean_email method to validate the email field.
    """
    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "First Name"}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Last Name"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that adds a "remember me" field.

    This form extends the default AuthenticationForm and adds a
    "remember_me" field. If the "remember me" field is checked,
    the session will not expire when the user closes their browser.
    """
    remember_me = forms.BooleanField(
        required=False,
        label="Remember me",
        help_text="If checked, your session will not expire when you close your browser."
    )


class UserEditForm(forms.ModelForm):
    """
    Custom form for editing a user.

    This form extends the default ModelForm and adds email, first_name,
    and last_name fields. It also adds a placeholder attribute to the
    username field.

    The form includes a custom clean_email method to validate the email
    field.
    """
    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "First Name"}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Last Name"}),
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
        }

    def clean_email(self):
        """
        Validate the email field.

        Check if a user with the same email address already exists.
        """
        email = self.cleaned_data.get("email")
        user_id = self.instance.id
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        """
        Save the form instance.

        Assign the email, first_name, and last_name fields to the
        user instance and save it to the database.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom form for changing a user's password.

    Extends the default PasswordChangeForm and adds a help text to the
    new_password1 field.
    """

    old_password = forms.CharField(
        label="Old password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True}
        ),
    )
    new_password1 = forms.CharField(
        label="New password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Enter a strong password.",
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_old_password(self):
        """
        Validate the old password field.

        Check if the old password is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                "Your old password was entered incorrectly. Please enter it again."
            )
        return old_password

    def save(self, commit=True):
        """
        Save the form instance.

        Assign the new password to the user instance and save it to the
        database.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["new_password1"])
        if commit:
            user.save()
        return user
