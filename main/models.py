"""
Models for the application.

Contains the following models:

- Ingredient: Represents an ingredient used in a batch.
- Batch: Represents a batch of a product.
- BatchIngredient: Represents an ingredient used in a batch.
- ProcessEntry: Represents a process entry for a batch.
- FinishedProduct: Represents a finished product in the system.
- Bottle: Represents a bottle of a finished product.
- SharedProduct: Represents a finished product that has been shared with other users.
- ProductLike: Represents a user's like for a shared product.

"""

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max


class Ingredient(models.Model):
    """
    Represents an ingredient used in a batch.

    Attributes:
        name (str): The name of the ingredient.
        description (str): A description of the ingredient.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Batch(models.Model):
    """
    Represents a batch of a product.

    Attributes:

       batch_number (str): A unique identifier for the batch.
       start_date (date): The date the batch started.
       start_gravity (float): The initial gravity of the batch.
       middle_gravity (float): The middle gravity of the batch (optional).
       final_gravity (float): The final gravity of the batch (optional).
       ingredients (ManyToManyField): The ingredients used in the batch.
       is_finished (bool): Whether the batch is finished.
    """

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_batches",
    )
    batch_number = models.CharField(max_length=50, unique=True, editable=False)
    start_date = models.DateField()
    start_gravity = models.FloatField()
    middle_gravity = models.FloatField(null=True, blank=True)
    final_gravity = models.FloatField(null=True, blank=True)
    ingredients = models.ManyToManyField(Ingredient, through="BatchIngredient")
    is_finished = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.batch_number:
            last_batch = (
                Batch.objects.filter(creator=self.creator)
                .order_by("-batch_number")
                .first()
            )
            if last_batch:
                last_number = int(last_batch.batch_number.split("-")[-1])
                self.batch_number = f"{self.creator.id}-{last_number + 1:04d}"
            else:
                self.batch_number = f"{self.creator.id}-0001"

        super().save(*args, **kwargs)

    @property
    def abv(self):
        """
        Calculates the ABV (alcohol by volume) of the batch.

        Returns:
            float: The ABV of the batch, or None if not calculable.
        """
        if self.start_gravity and self.final_gravity:
            return round((self.start_gravity - self.final_gravity) * 131.25, 2)
        return None

    def __str__(self):
        return f"Batch {self.batch_number} - {self.creator.username}"


class BatchIngredient(models.Model):
    """
    Represents an ingredient used in a batch.

    Attributes:
        UNITS (list): A list of valid units for ingredient amounts.
        batch (Batch): The batch the ingredient is used in.
        ingredient (Ingredient): The ingredient itself.
        amount (float): The amount of the ingredient used.
        unit (str): The unit of the ingredient amount.
    """

    UNITS = [
        ("kg", "Kilograms"),
        ("g", "Grams"),
        ("l", "Liters"),
        ("ml", "Milliliters"),
    ]
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.FloatField()
    unit = models.CharField(max_length=10, choices=UNITS)

    def __str__(self):
        return f"{self.ingredient.name} - {self.amount} {self.unit}"


class ProcessEntry(models.Model):
    """
    Represents a process entry for a batch.

    Attributes:
        batch (Batch): The batch the process entry is for.
        date (date): The date of the process entry.
        description (str): A description of the process entry.
    """

    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="process_entries"
    )
    date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return f"Process for {self.batch.batch_number} on {self.date}"


class FinishedProduct(models.Model):
    """
    Represents a finished product in the system.

    Attributes:
        PRODUCT_TYPES (list): A list of valid product types.
        batch (Batch): The batch that this finished product belongs to.
        product_type (str): The type of product (e.g. WINE, MEAD).
        serial_number (str): A unique serial number for the product.
        start_date (date): The date when the product was started.
        finish_date (date): The date when the product was finished.
        description (str): A description of the product.
        abv (float): The alcohol by volume (ABV) of the product.
    """

    PRODUCT_TYPES = [
        ("WINE", "Wine"),
        ("MEAD", "Mead"),
    ]

    batch = models.OneToOneField(
        Batch, on_delete=models.CASCADE, related_name="finished_product"
    )
    product_type = models.CharField(max_length=4, choices=PRODUCT_TYPES)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="finished_products",
    )
    serial_number = models.CharField(max_length=50, unique=True, editable=False)
    start_date = models.DateField()
    finish_date = models.DateField()
    description = models.TextField(blank=True)
    abv = models.FloatField(verbose_name="ABV (%)")

    def save(self, *args, **kwargs):
        if not self.serial_number:
            # Get the last serial number for this user and product type
            last_product = FinishedProduct.objects.filter(
                batch__creator=self.batch.creator, product_type=self.product_type
            ).aggregate(Max("serial_number"))["serial_number__max"]

            if last_product:
                # Extract the number part and increment it
                last_number = int(last_product[-4:])
                new_number = last_number + 1
            else:
                new_number = 1

            # Keep trying new serial numbers until we find an unused one
            while True:
                self.serial_number = f"{self.start_date.strftime('%Y%m')}{self.product_type}{new_number:04d}"
                if not FinishedProduct.objects.filter(
                    serial_number=self.serial_number
                ).exists():
                    break
                new_number += 1

        if not self.abv:
            self.abv = self.batch.abv or 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_product_type_display()} - {self.serial_number} (ABV: {self.abv}%)"


class Bottle(models.Model):
    """
    Represents a bottle of a finished product.

    Attributes:
        finished_product (FinishedProduct): The finished product that this bottle belongs to.
        bottle_number (str): A unique identifier for the bottle.
        volume (float): The volume of the bottle in liters.
        date_bottled (date): The date when the bottle was bottled.
    """

    finished_product = models.ForeignKey(
        FinishedProduct, on_delete=models.CASCADE, related_name="bottles"
    )
    bottle_number = models.CharField(max_length=50, unique=True, editable=False)
    volume = models.FloatField(help_text="Volume in liters")
    date_bottled = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.bottle_number:
            last_bottle = (
                Bottle.objects.filter(finished_product=self.finished_product)
                .order_by("-bottle_number")
                .first()
            )
            if last_bottle:
                last_number = int(last_bottle.bottle_number[-2:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.bottle_number = (
                f"{self.finished_product.serial_number}{new_number:02d}"
            )

        if not self.date_bottled:
            self.date_bottled = datetime.now().date()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bottle {self.bottle_number} of {self.finished_product}"


class SharedProduct(models.Model):
    """
    Represents a finished product that has been shared with other users.

    Attributes:
        product (FinishedProduct): The finished product that was shared.

        shared_by (ForeignKey): The user that shared the product.
        shared_date (DateTimeField): The date when the product was shared.
    """

    product = models.ForeignKey(
        "FinishedProduct", on_delete=models.CASCADE, related_name="shared_products"
    )
    shared_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="products_shared"
    )
    shared_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} shared by {self.shared_by}"


class ProductLike(models.Model):
    """
    Represents a user's like for a shared product.

    Attributes:
        user (ForeignKey): The user that liked the product.
        shared_product (ForeignKey): The shared product that was liked.
        created_at (DateTimeField): The date when the user liked the product.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_product = models.ForeignKey(
        "SharedProduct", on_delete=models.CASCADE, related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "shared_product")

    def __str__(self):
        return f"{self.user.username} likes {self.shared_product.product.serial_number}"
