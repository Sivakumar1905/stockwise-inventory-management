from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, ProductForm
from .models import Category, Product


def _products_for(user):
    return Product.objects.filter(user=user).select_related("category")


def _ensure_default_category(user):
    if not Category.objects.filter(user=user).exists():
        Category.objects.get_or_create(user=user, name="General")


@login_required
def dashboard(request):
    products = _products_for(request.user)
    context = {
        "product_count": products.count(),
        "category_count": Category.objects.filter(user=request.user).count(),
        "out_of_stock_count": products.filter(quantity=0).count(),
        "recent_products": products.order_by("-created_at")[:5],
    }
    return render(request, "inventory/dashboard.html", context)


@login_required
def product_list(request):
    products = _products_for(request.user)
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    if category_id.isdigit():
        products = products.filter(category_id=category_id)

    return render(
        request,
        "inventory/product_list.html",
        {
            "products": products,
            "categories": Category.objects.filter(user=request.user),
            "query": query,
            "selected_category": category_id,
        },
    )


@login_required
def product_detail(request, pk):
    product = get_object_or_404(_products_for(request.user), pk=pk)
    return render(request, "inventory/product_detail.html", {"product": product})


@login_required
def product_create(request):
    _ensure_default_category(request.user)
    form = ProductForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.user = request.user
        product.save()
        messages.success(request, f"{product.name} was added to your inventory.")
        return redirect("product_detail", pk=product.pk)
    return render(
        request,
        "inventory/product_form.html",
        {
            "form": form,
            "is_edit": False,
            "has_categories": Category.objects.filter(user=request.user).exists(),
        },
    )


@login_required
def product_update(request, pk):
    product = get_object_or_404(_products_for(request.user), pk=pk)
    _ensure_default_category(request.user)
    form = ProductForm(
        request.POST or None,
        instance=product,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{product.name} was updated.")
        return redirect("product_detail", pk=product.pk)
    return render(
        request,
        "inventory/product_form.html",
        {
            "form": form,
            "product": product,
            "is_edit": True,
            "has_categories": Category.objects.filter(user=request.user).exists(),
        },
    )


@login_required
def product_delete(request, pk):
    product = get_object_or_404(_products_for(request.user), pk=pk)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f"{name} was deleted.")
        return redirect("product_list")
    return render(request, "inventory/product_confirm_delete.html", {"product": product})


@login_required
def category_list(request):
    _ensure_default_category(request.user)
    categories = Category.objects.filter(user=request.user)
    return render(request, "inventory/category_list.html", {"categories": categories})


@login_required
def category_create(request):
    form = CategoryForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        category = form.save(commit=False)
        category.user = request.user
        category.save()
        messages.success(request, f"{category.name} was created.")
        return redirect("category_list")
    return render(
        request, "inventory/category_form.html", {"form": form, "is_edit": False}
    )


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=category, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{category.name} was updated.")
        return redirect("category_list")
    return render(
        request,
        "inventory/category_form.html",
        {"form": form, "category": category, "is_edit": True},
    )


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == "POST":
        name = category.name
        category.delete()
        messages.success(
            request, f"{name} was deleted. Products in this category were kept."
        )
        return redirect("category_list")
    return render(
        request,
        "inventory/category_confirm_delete.html",
        {"category": category, "product_count": category.products.count()},
    )