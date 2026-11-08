from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm
from inventory.models import Category


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Category.objects.create(user=user, name="General")
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("dashboard")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def account_view(request):
    return redirect("dashboard")