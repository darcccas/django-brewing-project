"""
URL configuration for the main application.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("user_home/", views.user_home_view, name="user_home"),
]

# batch urls

urlpatterns += [
    path("batches/", views.list_batches, name="list_batches"),
    path("batches/add/", views.add_batch, name="add_batch"),
    path("batches/<int:batch_id>/", views.view_batch, name="view_batch"),
    path("batches/<int:batch_id>/edit/", views.edit_batch, name="edit_batch"),
    path(
        "<str:object_type>/<int:object_id>/qr-code/",
        views.generate_qr_code,
        name="generate_qr_code",
    ),
]

# finished product urls

urlpatterns += [
    path("batches/<int:batch_id>/finish/", views.finish_batch, name="finish_batch"),
    path("products/", views.list_finished_products, name="list_finished_products"),
    path(
        "products/<int:product_id>/",
        views.view_finished_product,
        name="view_finished_product",
    ),
    path(
        "products/<int:product_id>/bottle/", views.bottle_product, name="bottle_product"
    ),
    path(
        "products/<int:product_id>/bottle/<int:bottle_id>/",
        views.show_bottle,
        name="show_bottle",
    ),
    path(
        "products/<int:product_id>/bottle/<int:bottle_id>/public/",
        views.public_show_bottle,
        name="public_show_bottle",
    ),
]

# shared product urls

urlpatterns += [
    path("products/<int:product_id>/share/", views.share_product, name="share_product"),
    path("products/shared/", views.shared_products, name="shared_products"),
    path(
        "shared-products/<int:product_id>/",
        views.view_shared_product,
        name="view_shared_product",
    ),
    path(
        "shared-product/<int:shared_product_id>/like/",
        views.like_shared_product,
        name="like_shared_product",
    ),
    path(
        "shared-product/<int:shared_product_id>/unlike/",
        views.unlike_shared_product,
        name="unlike_shared_product",
    ),
]
