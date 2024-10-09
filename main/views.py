import logging
from datetime import datetime
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.forms import modelformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    BatchForm,
    BatchIngredientForm,
    BottleForm,
    FinishBatchForm,
    ProcessEntryForm,
)
from .models import (
    Batch,
    BatchIngredient,
    Bottle,
    FinishedProduct,
    Ingredient,
    ProcessEntry,
    ProductLike,
    SharedProduct,
)

logger = logging.getLogger(__name__)


def home_view(request):
    """
    Just a simple view to display the main application home page.
    """
    return render(request, "main_home.html")


@login_required
def user_home_view(request):
    """
    View for the user's home page. This is what the user sees after
    logging in.
    """
    return render(request, "user_main_home.html")


@login_required
def add_batch(request):
    """
    View to handle the creation of a new batch.

    This view handles both GET and POST requests. On a GET request, it
    initializes the necessary forms and passes them to the template.
    On a POST request, it validates the forms, saves the batch and its
    associated ingredients and process entry, and redirects the user to
    the batch details page.

    :param request: The current request object.
    :return: A redirect to the batch details page on success, or a rendered
             template with form errors on failure.
    """
    # Formsets for ingredients and processes
    BatchIngredientFormSet = modelformset_factory(
        BatchIngredient, form=BatchIngredientForm, extra=1, can_delete=True
    )

    if request.method == "POST":
        batch_form = BatchForm(request.POST)
        ingredient_formset = BatchIngredientFormSet(
            request.POST, queryset=BatchIngredient.objects.none()
        )
        process_form = ProcessEntryForm(request.POST)

        if batch_form.is_valid() and ingredient_formset.is_valid():
            # Save the batch
            batch = batch_form.save(commit=False)
            batch.creator = request.user
            batch.save()

            # Save each ingredient from the formset
            for form in ingredient_formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    batch_ingredient = form.save(commit=False)
                    batch_ingredient.batch = batch
                    batch_ingredient.save()

            # Only save the process entry if the form has data
            if process_form.has_changed():
                if process_form.is_valid():
                    process_entry = process_form.save(commit=False)
                    process_entry.batch = batch
                    process_entry.save()
                else:
                    messages.warning(
                        request,
                        "Process entry was not saved due to invalid data. You can add it later.",
                    )

            messages.success(request, "Batch created successfully!")
            return redirect("main:view_batch", batch_id=batch.id)
        else:
            messages.error(
                request,
                "There was an error with your submission. Please check the form and try again.",
            )

    else:
        batch_form = BatchForm()
        ingredient_formset = BatchIngredientFormSet(
            queryset=BatchIngredient.objects.none()
        )
        process_form = ProcessEntryForm()

    # Pass available ingredients to the template
    ingredients = list(Ingredient.objects.values("id", "name"))
    context = {
        "batch_form": batch_form,
        "ingredient_formset": ingredient_formset,
        "process_form": process_form,
        "ingredients": ingredients,
    }
    return render(request, "add_batch.html", context)


@login_required
def edit_batch(request, batch_id):
    """
    View to handle the editing of a batch.

    Args:
        request (HttpRequest): The HTTP request object.
        batch_id (int): The ID of the batch to be edited.

    Returns:
        HttpResponse: The rendered HTML template for the edit batch page.
    """
    # Get the batch object with the given ID and creator
    batch = get_object_or_404(Batch, id=batch_id, creator=request.user)

    # Create formsets for BatchIngredient and ProcessEntry
    BatchIngredientFormSet = modelformset_factory(
        BatchIngredient, form=BatchIngredientForm, extra=1, can_delete=False
    )
    ProcessEntryFormSet = modelformset_factory(
        ProcessEntry, form=ProcessEntryForm, extra=1, can_delete=False
    )

    if request.method == "POST":
        # Create form instances with the request data
        batch_form = BatchForm(request.POST, instance=batch)
        ingredient_formset = BatchIngredientFormSet(
            request.POST, queryset=BatchIngredient.objects.none(), prefix="ingredients"
        )
        process_formset = ProcessEntryFormSet(
            request.POST, queryset=ProcessEntry.objects.none(), prefix="processes"
        )

        if (
            batch_form.is_valid()
            and ingredient_formset.is_valid()
            and process_formset.is_valid()
        ):
            batch = batch_form.save()

            # Handle deleted ingredients
            deleted_ingredients = request.POST.getlist("delete_ingredient")
            BatchIngredient.objects.filter(id__in=deleted_ingredients).delete()

            # Handle deleted process entries
            deleted_processes = request.POST.getlist("delete_process")
            ProcessEntry.objects.filter(id__in=deleted_processes).delete()

            # Save new ingredients
            for form in ingredient_formset:
                if form.cleaned_data:
                    ingredient = form.save(commit=False)
                    ingredient.batch = batch
                    ingredient.save()

            # Save new process entries
            for form in process_formset:
                if form.cleaned_data:
                    process = form.save(commit=False)
                    process.batch = batch
                    process.save()

            return redirect("main:view_batch", batch_id=batch.id)

    else:
        # Create form instances with the initial data
        batch_form = BatchForm(instance=batch)
        ingredient_formset = BatchIngredientFormSet(
            queryset=BatchIngredient.objects.none(), prefix="ingredients"
        )
        process_formset = ProcessEntryFormSet(
            queryset=ProcessEntry.objects.none(), prefix="processes"
        )

    context = {
        "batch_form": batch_form,
        "ingredient_formset": ingredient_formset,
        "process_formset": process_formset,
        "batch": batch,
    }

    return render(request, "edit_batch.html", context)


@login_required
def view_batch(request, batch_id):
    """
    View to handle the viewing of a batch.

    Args:
        request (HttpRequest): The HTTP request object.
        batch_id (int): The ID of the batch to be viewed.

    Returns:
        HttpResponse: The rendered HTML template for the view batch page.
    """
    # Get the batch object with the given ID and user
    batch = get_object_or_404(Batch, id=batch_id, creator=request.user)

    # Create a dictionary to pass to the template
    context = {
        "batch": batch,
        "abv": batch.abv,
    }

    # Render the template and return the response
    return render(request, "view_batch.html", context)


@login_required
def list_batches(request):
    """
    View to handle the listing of batches.

    This view displays a list of all batches created by the user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered HTML template for the batch list page.
    """
    # Get all batches created by the user, with their ingredients pre-fetched
    batches = Batch.objects.filter(creator=request.user).prefetch_related(
        "batchingredient_set__ingredient"
    )

    # Create a dictionary to pass to the template
    context = {
        "batches": batches,
    }

    # Render the template and return the response
    return render(request, "list_batches.html", context)


@login_required
def finish_batch(request, batch_id):
    """
    View to handle the finishing of a batch.

    Args:
        request (HttpRequest): The HTTP request object.
        batch_id (int): The ID of the batch to be finished.

    Returns:
        HttpResponse: The rendered HTML template for the finish batch page.
    """
    batch = get_object_or_404(Batch, id=batch_id, creator=request.user)

    if batch.is_finished:
        return redirect("main:view_batch", batch_id=batch_id)

    if request.method == "POST":
        form = FinishBatchForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    finished_product = form.save(commit=False)
                    finished_product.batch = batch
                    finished_product.creator = request.user  # Set the creator
                    finished_product.abv = batch.abv or form.cleaned_data.get("abv", 0)

                    # Combine all process entries into a single description
                    process_entries = batch.process_entries.all().order_by("date")
                    combined_process = "\n".join(
                        [
                            f"{entry.date}: {entry.description}"
                            for entry in process_entries
                        ]
                    )

                    finished_product.description = f"{finished_product.description
                                                      or ''}\n\nProcess:\n{combined_process}"

                    finished_product.save()

                    batch.is_finished = True
                    batch.save()

                return redirect(
                    "main:view_finished_product", product_id=finished_product.id
                )
            except Exception as e:
                form.add_error(
                    None, f"An error occurred while finishing the batch: {str(e)}"
                )
    else:
        form = FinishBatchForm(
            initial={
                "start_date": batch.start_date,
                "finish_date": datetime.now().date(),
                "abv": batch.abv or 0,
            }
        )

    context = {"form": form, "batch": batch}
    return render(request, "finish_batch.html", context)


@login_required
def view_finished_product(request, product_id):
    """
    View to handle the display of a finished product.

    This view retrieves a FinishedProduct object with the given ID and its associated
    user, and renders the view_finished_product.html template with the product
    information.

    Args:
        request (HttpRequest): The current request object.
        product_id (int): The ID of the finished product to display.

    Returns:
        HttpResponse: The rendered HTML template for the view finished product page.
    """
    # Get the finished product object with the given ID and user
    product = get_object_or_404(
        FinishedProduct, id=product_id, batch__creator=request.user
    )

    # Create a context dictionary to pass to the template
    context = {"product": product}

    # Render the template and return the response
    return render(request, "view_finished_product.html", context)


# View to handle the addition of bottles to a finished product
@login_required
def bottle_product(request, product_id):
    """
    View to handle the addition of bottles to a finished product.

    This view handles both GET and POST requests. On a GET request, it
    initializes a formset for adding bottles and passes it to the template.
    On a POST request, it validates the formset, saves the bottles, and
    redirects the user to the view finished product page.

    Args:
        request (HttpRequest): The current request object.
        product_id (int): The ID of the finished product to add bottles to.

    Returns:
        HttpResponse: The rendered HTML template for the bottle product page.
    """
    # Get the finished product object with the given ID and user
    product = get_object_or_404(
        FinishedProduct, id=product_id, batch__creator=request.user
    )

    # Create a formset factory for adding bottles
    BottleFormSet = modelformset_factory(
        Bottle, form=BottleForm, extra=1, can_delete=False
    )

    if request.method == "POST":
        # Create a formset instance with the request data
        formset = BottleFormSet(request.POST, queryset=Bottle.objects.none())

        # Check if an action is specified in the request
        if "action" in request.POST:
            # Handle the "add_bottle" action
            if request.POST["action"] == "add_bottle":
                # Add a new form to the formset
                BottleFormSet = modelformset_factory(
                    Bottle,
                    form=BottleForm,
                    extra=formset.total_form_count() + 1,
                    can_delete=False,
                )
                formset = BottleFormSet(queryset=Bottle.objects.none())
            # Handle the "save_bottles" action
            elif request.POST["action"] == "save_bottles" and formset.is_valid():
                # Save the bottles
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.finished_product = product
                    instance.save()
                # Redirect to the view finished product page
                return redirect("main:view_finished_product", product_id=product.id)
    else:
        # Create a formset instance with no data
        formset = BottleFormSet(queryset=Bottle.objects.none())

    # Create a context dictionary to pass to the template
    context = {
        "product": product,
        "formset": formset,
    }
    # Render the template and return the response
    return render(request, "bottle_product.html", context)


# View to handle the listing of finished products
@login_required
def list_finished_products(request):
    """
    View to handle the listing of finished products for the current user.

    This view retrieves all finished products for the current user, adds a boolean
    attribute to each product indicating whether it has been shared, and renders the
    list_finished_products.html template with the list of products.

    Args:
        request (HttpRequest): The current request object.

    Returns:
        HttpResponse: The rendered HTML template for the list finished products page.
    """
    # Get all finished products for the current user
    finished_products = FinishedProduct.objects.filter(creator=request.user)

    # Add a boolean attribute to each product indicating whether it has been shared
    for product in finished_products:
        product.is_shared = SharedProduct.objects.filter(product=product).exists()

    context = {
        "finished_products": finished_products,
    }
    # Render the template and return the response
    return render(request, "list_finished_products.html", context)


# View to handle the display of a specific bottle
@login_required
def show_bottle(request, product_id, bottle_id):
    """
    View to handle the display of a specific bottle.

    This view retrieves a bottle object with the given ID and its associated product,
    and renders the show_bottle.html template with the bottle and product information.

    Args:
        request (HttpRequest): The current request object.
        product_id (int): The ID of the product that the bottle belongs to.
        bottle_id (int): The ID of the bottle to display.

    Returns:
        HttpResponse: The rendered HTML template for the show bottle page.
    """
    # Get the product object with the given ID and user
    product = get_object_or_404(
        FinishedProduct, id=product_id, batch__creator=request.user
    )
    # Get the bottle object with the given ID and product
    bottle = get_object_or_404(Bottle, id=bottle_id, finished_product=product)

    # Create a context dictionary to pass to the template
    context = {
        "bottle": bottle,
        "product": product,
        "batch": product.batch,
    }
    # Render the template and return the response
    return render(request, "show_bottle.html", context)


# View to handle the generation of a QR code for a specific object
@login_required
def generate_qr_code(request, object_type, object_id):
    """
    View to handle the generation of a QR code for a specific object.

    This view generates a QR code for the given object type and ID, and returns
    the QR code image as a PNG response.

    Args:
        request (HttpRequest): The current request object.
        object_type (str): The type of object to generate the QR code for (e.g. batch, finished_product, bottle).
        object_id (int): The ID of the object to generate the QR code for.

    Returns:
        HttpResponse: The QR code image as a PNG response.
    """
    # Determine the URL name based on the object type
    if object_type == "batch":
        url_name = "main:view_batch"
        kwargs = {"batch_id": object_id}
    elif object_type == "finished_product":
        url_name = "main:view_finished_product"
        kwargs = {"product_id": object_id}
    elif object_type == "bottle":
        url_name = "main:public_show_bottle"
        bottle = get_object_or_404(Bottle, id=object_id)
        kwargs = {"product_id": bottle.finished_product.id, "bottle_id": object_id}
    else:
        # Return an error response if the object type is invalid
        return HttpResponse("Invalid object type", status=400)

    # Build the absolute URL for the object
    object_url = request.build_absolute_uri(reverse(url_name, kwargs=kwargs))

    # Create a QR code object
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    # Add the object URL to the QR code
    qr.add_data(object_url)
    # Make the QR code fit the data
    qr.make(fit=True)
    # Create a QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Create a BytesIO buffer to store the image
    buffer = BytesIO()
    # Save the image to the buffer
    img.save(buffer, format("PNG"))
    # Return the image as a PNG response
    return HttpResponse(buffer.getvalue(), content_type="image/png")


def public_show_bottle(request, product_id, bottle_id):
    """
    View to handle the display of a specific bottle.

    This view retrieves a bottle object with the given ID and its associated product,
    and renders the show_bottle.html template with the bottle and product information.

    Args:
        request (HttpRequest): The current request object.
        product_id (int): The ID of the finished product.
        bottle_id (int): The ID of the bottle to display.

    Returns:
        HttpResponse: The rendered HTML template for the show bottle page.
    """
    # Get the bottle object with the given ID
    product = get_object_or_404(FinishedProduct, id=product_id)
    bottle = get_object_or_404(Bottle, id=bottle_id, finished_product=product)
    batch = product.batch

    # Create a context dictionary to pass to the template
    context = {
        "bottle": bottle,
        "product": product,
        "batch": batch,
    }
    # Render the template and return the response
    return render(request, "public_show_bottle.html", context)


@login_required
def share_product(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(
            FinishedProduct, id=product_id, creator=request.user
        )

        shared_product, created = SharedProduct.objects.get_or_create(
            product=product, shared_by=request.user
        )

        if created:
            messages.success(
                request,
                f"Product {product.serial_number} has been shared with all users.",
            )
        else:
            messages.info(
                request, f"Product {product.serial_number} is already shared."
            )

    return redirect("main:list_finished_products")


@login_required
def shared_products(request):
    """
    View to handle the list of all shared finished products.
    """
    # Retrieve all shared finished products, excluding those shared by the current user
    all_shared = SharedProduct.objects.exclude(shared_by=request.user).select_related(
        "product", "shared_by"
    )

    # Get the top 10 most liked products
    top_liked = all_shared.annotate(likes_count=Count("likes")).order_by(
        "-likes_count"
    )[:10]

    # Get the rest of the shared products
    other_shared = all_shared.exclude(id__in=top_liked.values_list("id", flat=True))

    # Create a context dictionary to pass to the template
    context = {
        "top_liked_products": top_liked,
        "other_shared_products": other_shared,
    }

    # Render the template and return the response
    return render(request, "shared_products.html", context)


@login_required
def view_shared_product(request, product_id):
    """
    View to display details of a shared product.
    """
    shared_product = get_object_or_404(SharedProduct, product_id=product_id)
    product = shared_product.product

    # Check if the current user is the one who shared the product
    if shared_product.shared_by == request.user:
        return redirect("main:view_finished_product", product_id=product_id)

    # Check if the current user has liked this product
    user_has_liked = shared_product.likes.filter(user=request.user).exists()
    likes_count = shared_product.likes.count()

    context = {
        "product": product,
        "shared_by": shared_product.shared_by,
        "shared_date": shared_product.shared_date,
        "user_has_liked": user_has_liked,
        "likes_count": likes_count,
        "shared_product_id": shared_product.id,
    }
    return render(request, "view_shared_product.html", context)


@login_required
@require_POST
def like_shared_product(request, shared_product_id):
    """
    Like a shared product.

    This view is only accessible via an AJAX request. It will either create a new
    ProductLike object if the user has not previously liked the shared product, or
    do nothing if the user has already liked it.

    Args:
        request (HttpRequest): The current request object.
        shared_product_id (int): The ID of the shared product to like.

    Returns:
        JsonResponse: A JSON response containing the updated like count.
    """
    shared_product = get_object_or_404(SharedProduct, id=shared_product_id)
    like, created = ProductLike.objects.get_or_create(
        user=request.user, shared_product=shared_product
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"likes_count": shared_product.likes.count()})
    return redirect("main:view_shared_product", product_id=shared_product.product.id)


@login_required
@require_POST
def unlike_shared_product(request, shared_product_id):
    """
    Unlike a shared product.

    This view is only accessible via an AJAX request. It will delete the
    ProductLike object associated with the current user and the shared product,
    or do nothing if the user has not previously liked the shared product.

    Args:
        request (HttpRequest): The current request object.
        shared_product_id (int): The ID of the shared product to unlike.

    Returns:
        JsonResponse: A JSON response containing the updated like count.
    """
    shared_product = get_object_or_404(SharedProduct, id=shared_product_id)
    # Delete the ProductLike object associated with the user and the shared product
    ProductLike.objects.filter(
        user=request.user, shared_product=shared_product
    ).delete()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # Return a JSON response with the updated like count
        return JsonResponse({"likes_count": shared_product.likes.count()})
    # Redirect to the view shared product page if the request is not an AJAX call
    return redirect("main:view_shared_product", product_id=shared_product.product.id)
