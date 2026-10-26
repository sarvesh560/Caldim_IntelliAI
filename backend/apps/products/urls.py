"""
CALDIM Product Knowledge URL routing.
"""
from django.urls import path
from apps.products.views import (
    ProductListView,
    ProductDetailView,
    ProductSearchView,
    StaffProductPreviewSearchView,
    ProductReadinessView,
)

app_name = "products"

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("search/", ProductSearchView.as_view(), name="product_search"),
    path("staff-search/", StaffProductPreviewSearchView.as_view(), name="staff_product_search"),
    path("readiness/", ProductReadinessView.as_view(), name="product_readiness"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
]
