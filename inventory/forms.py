from django import forms

from .models import Category, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "maxlength": 80}),
            "description": forms.TextInput(
                attrs={"class": "form-control", "maxlength": 240}
            ),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        categories = Category.objects.filter(user=self.user, name__iexact=name)
        if self.instance.pk:
            categories = categories.exclude(pk=self.instance.pk)
        if categories.exists():
            raise forms.ValidationError("You already have a category with this name.")
        return name


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name",
            "sku",
            "category",
            "description",
            "quantity",
            "unit_price",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "maxlength": 120}),
            "sku": forms.TextInput(attrs={"class": "form-control", "maxlength": 40}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "unit_price": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(user=user)
        self.fields["category"].required = False
        if not self.is_bound and not self.instance.pk:
            default_category = self.fields["category"].queryset.filter(
                name="General"
            ).first()
            if default_category:
                self.initial["category"] = default_category.pk

    def clean_sku(self):
        sku = self.cleaned_data["sku"].strip().upper()
        products = Product.objects.filter(user=self.user, sku__iexact=sku)
        if self.instance.pk:
            products = products.exclude(pk=self.instance.pk)
        if products.exists():
            raise forms.ValidationError("You already have a product with this SKU.")
        return sku

    def clean_category(self):
        category = self.cleaned_data.get("category")
        if category and category.user_id != self.user.pk:
            raise forms.ValidationError("Choose one of your own categories.")
        return category