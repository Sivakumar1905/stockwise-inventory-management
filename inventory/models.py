from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


# Kept because the earlier image migration refers to this function.
def product_image_path(instance, filename):
    return f"products/{instance.user_id}/{filename}"


class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inventory_categories",
    )
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_category_per_user")
        ]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inventory_products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=40)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "sku"], name="unique_product_sku_per_user")
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"