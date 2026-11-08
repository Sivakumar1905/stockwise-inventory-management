from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class InventoryFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="owner-pass-123")
        self.other_user = User.objects.create_user(
            username="other", password="other-pass-123"
        )
        self.category = Category.objects.create(user=self.user, name="Hardware")
        self.product = Product.objects.create(
            user=self.user,
            category=self.category,
            name="Hammer",
            sku="TOOL-01",
            quantity=3,
            unit_price=Decimal("12.50"),
        )
        self.client.force_login(self.user)

    def test_dashboard_shows_inventory_counts(self):
        Product.objects.create(
            user=self.user,
            name="Out of stock item",
            sku="EMPTY-01",
            quantity=0,
            unit_price=Decimal("5.00"),
        )
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Hammer")
        self.assertEqual(response.context["product_count"], 2)
        self.assertEqual(response.context["category_count"], 1)
        self.assertEqual(response.context["out_of_stock_count"], 1)

    def test_product_create_and_search(self):
        create_page = self.client.get(reverse("product_create"))
        self.assertContains(create_page, "Hardware")

        response = self.client.post(
            reverse("product_create"),
            {
                "name": "Wrench",
                "sku": "tool-02",
                "category": self.category.pk,
                "description": "",
                "quantity": 20,
                "unit_price": "8.75",
            },
        )
        created = Product.objects.get(user=self.user, sku="TOOL-02")
        self.assertEqual(created.category, self.category)
        self.assertRedirects(response, reverse("product_detail", args=[created.pk]))

        response = self.client.get(reverse("product_list"), {"q": "WRENCH"})
        self.assertContains(response, "Wrench")
        self.assertNotContains(response, "Hammer")

        Product.objects.create(
            user=self.user,
            name="Uncategorized item",
            sku="MISC-01",
            quantity=1,
            unit_price=Decimal("3.00"),
        )
        response = self.client.get(
            reverse("product_list"), {"category": str(self.category.pk)}
        )
        self.assertContains(response, "Hammer")
        self.assertNotContains(response, "Uncategorized item")

    def test_product_form_creates_and_selects_default_category(self):
        self.category.delete()

        response = self.client.get(reverse("product_create"))

        default_category = Category.objects.get(user=self.user, name="General")
        self.assertEqual(
            response.context["form"]["category"].value(), default_category.pk
        )

    def test_product_can_be_edited_and_deleted(self):
        response = self.client.post(
            reverse("product_update", args=[self.product.pk]),
            {
                "name": "New hammer",
                "sku": self.product.sku,
                "category": self.category.pk,
                "description": "Updated description",
                "quantity": 7,
                "unit_price": "15.00",
            },
        )
        self.assertRedirects(response, reverse("product_detail", args=[self.product.pk]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "New hammer")
        self.assertEqual(self.product.quantity, 7)

        response = self.client.post(reverse("product_delete", args=[self.product.pk]))
        self.assertRedirects(response, reverse("product_list"))
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_category_can_be_created_and_edited(self):
        response = self.client.post(
            reverse("category_create"),
            {"name": "Food", "description": "Food products"},
        )
        category = Category.objects.get(user=self.user, name="Food")
        self.assertRedirects(response, reverse("category_list"))

        response = self.client.post(
            reverse("category_update", args=[category.pk]),
            {"name": "Groceries", "description": "Grocery products"},
        )
        self.assertRedirects(response, reverse("category_list"))
        category.refresh_from_db()
        self.assertEqual(category.name, "Groceries")

    def test_main_pages_load(self):
        urls = [
            reverse("dashboard"),
            reverse("product_list"),
            reverse("product_create"),
            reverse("product_detail", args=[self.product.pk]),
            reverse("product_update", args=[self.product.pk]),
            reverse("product_delete", args=[self.product.pk]),
            reverse("category_list"),
            reverse("category_create"),
            reverse("category_update", args=[self.category.pk]),
            reverse("category_delete", args=[self.category.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

        self.client.logout()
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("register")).status_code, 200)

    def test_duplicate_sku_is_rejected_case_insensitively(self):
        response = self.client.post(
            reverse("product_create"),
            {
                "name": "Different item",
                "sku": "tool-01",
                "category": self.category.pk,
                "quantity": 1,
                "unit_price": "1.00",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already have a product with this SKU")
        self.assertEqual(Product.objects.filter(user=self.user).count(), 1)

    def test_user_cannot_view_or_change_another_users_product(self):
        private_product = Product.objects.create(
            user=self.other_user,
            name="Private item",
            sku="PRIVATE-1",
            quantity=1,
            unit_price=Decimal("1.00"),
        )
        self.assertEqual(
            self.client.get(reverse("product_detail", args=[private_product.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("product_delete", args=[private_product.pk])
            ).status_code,
            404,
        )
        self.assertTrue(Product.objects.filter(pk=private_product.pk).exists())

    def test_deleting_category_keeps_products(self):
        response = self.client.post(reverse("category_delete", args=[self.category.pk]))
        self.assertRedirects(response, reverse("category_list"))
        self.product.refresh_from_db()
        self.assertIsNone(self.product.category)
