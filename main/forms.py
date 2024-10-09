"""
Forms for the main application.

This module contains form classes for creating and editing batches, batch ingredients,
process entries, finished products, and bottles.
"""

from django import forms

from .models import (Batch, BatchIngredient, Bottle, FinishedProduct,
                     Ingredient, ProcessEntry)


class BatchForm(forms.ModelForm):
    """
    Form for creating or editing a Batch.
    """

    final_gravity = forms.FloatField(initial=1.000, required=False)

    class Meta:
        """
        Define the model, fields and widgets for the form.
        """

        model = Batch
        fields = ["start_date", "start_gravity", "middle_gravity", "final_gravity"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Set start_gravity as required and middle_gravity as not required.
        """
        super().__init__(*args, **kwargs)
        self.fields["start_gravity"].required = True
        self.fields["middle_gravity"].required = False


class BatchIngredientForm(forms.ModelForm):
    """
    A form for creating or editing a BatchIngredient.

    This form allows the user to select an existing ingredient or enter a new one.
    It also includes fields for the amount and unit of the ingredient.
    """

    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "ingredient-select"}),
    )
    new_ingredient = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "New ingredient name"}),
    )

    class Meta:
        """
        Define the model and fields for the form.
        """

        model = BatchIngredient
        fields = ["ingredient", "amount", "unit"]

    def clean(self):
        """
        Clean and validate the form data.

        Raises a ValidationError if neither an existing ingredient nor a new ingredient is provided.
        """
        cleaned_data = super().clean()
        ingredient = cleaned_data.get("ingredient")
        new_ingredient = cleaned_data.get("new_ingredient")

        if not ingredient and not new_ingredient:
            raise forms.ValidationError(
                "Please select an existing ingredient or enter a new one."
            )

        return cleaned_data

    def save(self, commit=True):
        """
        Saves the form instance.

        If a new ingredient is provided, it creates a new Ingredient instance and assigns it to the form instance.
        Then, it saves the form instance to the database.

        Args:
            commit (bool): Whether to commit the changes to the database. Defaults to True.

        Returns:
            The saved form instance.
        """
        instance = super().save(commit=False)
        new_ingredient = self.cleaned_data.get("new_ingredient")

        if new_ingredient:
            ingredient, created = Ingredient.objects.get_or_create(name=new_ingredient)
            instance.ingredient = ingredient

        if commit:
            instance.save()
        return instance


class ProcessEntryForm(forms.ModelForm):
    """
    A form for creating or editing a ProcessEntry instance.

    This form includes fields for the date and description of the process entry.
    """

    class Meta:
        """
        Metaclass for ProcessEntryForm.

        Defines the model and fields used in the form.
        """

        model = ProcessEntry
        fields = ["date", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        """
        Clean and validate the form data.

        Raises a ValidationError if a description is provided without a date.

        Returns:
            The cleaned and validated form data.
        """
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        description = cleaned_data.get("description")
        if description and not date:
            self.add_error("date", "Date is required when adding a process entry.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        """
        Initializes the ProcessEntryForm instance.

        Sets the date and description fields as not required.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.fields["date"].required = False
        self.fields["description"].required = False


class FinishBatchForm(forms.ModelForm):
    """
    Form class for finishing a batch.

    Extends the ModelForm class and defines the fields and widgets used in the form.
    """

    class Meta:
        """
        Metaclass for FinishBatchForm.

        Defines the model and fields used in the form.
        """

        model = FinishedProduct
        fields = ["product_type", "start_date", "finish_date", "description", "abv"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "finish_date": forms.DateInput(attrs={"type": "date"}),
            "abv": forms.NumberInput(attrs={"step": "0.1"}),
        }


class BottleForm(forms.ModelForm):
    """
    Form class for creating a bottle instance.

    Extends the ModelForm class and defines the fields and widgets used in the form.
    """

    class Meta:
        """
        Metaclass for BottleForm.

        Defines the model and fields used in the form.
        """

        model = Bottle
        fields = ["volume", "date_bottled"]
        widgets = {
            "volume": forms.NumberInput(attrs={"step": "0.001", "min": "0"}),
            "date_bottled": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initializes the BottleForm instance.

        Sets the date_bottled field as not required.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.fields["date_bottled"].required = False
