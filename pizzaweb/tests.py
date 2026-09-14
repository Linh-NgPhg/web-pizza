# ============================================================
# BỘ TEST CASE
# ------------------------------------------------------------
# Hiện thực hoá "Kế hoạch kiểm thử" (Báo cáo Phân tích & Thiết
# kế - mục 9), áp dụng vào các luồng nghiệp vụ đang có trong
# mã nguồn: giỏ hàng (session), voucher (UC03), checkout (UC01)
# và chuyển trạng thái đơn hàng (UC07).
# ============================================================

from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Pizza, Order, OrderItem, Voucher
from .services import VoucherService


def make_pizza(**kwargs):

    defaults = {
        "name": "Pizza Hải Sản",
        "description": "Mô tả",
        "price": Decimal("100000"),
        "is_available": True,
    }

    defaults.update(kwargs)

    return Pizza.objects.create(**defaults)


class CartTests(TestCase):
    """TC-01, TC-02, TC-03 - Nghiệp vụ giỏ hàng (session)."""

    def setUp(self):

        self.pizza = make_pizza()

    def test_tc01_add_available_pizza_to_cart(self):

        response = self.client.post(
            reverse("add_to_cart", args=[self.pizza.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.session["cart"][str(self.pizza.id)],
            1
        )

    def test_tc02_add_unavailable_pizza_returns_404(self):

        unavailable = make_pizza(
            name="Pizza Ngừng Bán",
            is_available=False
        )

        response = self.client.post(
            reverse("add_to_cart", args=[unavailable.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_tc03_decrease_quantity_to_zero_removes_item(self):

        session = self.client.session
        session["cart"] = {str(self.pizza.id): 1}
        session.save()

        self.client.get(
            reverse("decrease_quantity", args=[self.pizza.id])
        )

        self.assertNotIn(
            str(self.pizza.id),
            self.client.session.get("cart", {})
        )


class CheckoutTests(TestCase):
    """TC-04 - Đặt hàng với giỏ hàng rỗng."""

    def setUp(self):

        self.user = User.objects.create_user(
            username="khach01",
            password="password123"
        )

        self.client.login(
            username="khach01",
            password="password123"
        )

    def test_tc04_checkout_with_empty_cart_redirects_to_cart(self):

        response = self.client.get(
            reverse("checkout"),
            follow=True
        )

        self.assertRedirects(response, reverse("cart"))


class VoucherServiceTests(TestCase):
    """TC-05 - Áp dụng mã giảm giá (UC03)."""

    def setUp(self):

        now = timezone.now()

        self.valid_voucher = Voucher.objects.create(
            code="GIAM10",
            discount_type="percent",
            discount=Decimal("10"),
            min_order_value=Decimal("0"),
            start=now - timedelta(days=1),
            end=now + timedelta(days=1),
            usage_limit=5,
            usage_count=0,
            is_active=True,
        )

        self.expired_voucher = Voucher.objects.create(
            code="HETHAN",
            discount_type="percent",
            discount=Decimal("10"),
            min_order_value=Decimal("0"),
            start=now - timedelta(days=10),
            end=now - timedelta(days=1),
            usage_limit=5,
            usage_count=0,
            is_active=True,
        )

    def test_tc05_expired_voucher_is_rejected(self):

        voucher, error = VoucherService.get_valid_voucher(
            "HETHAN",
            Decimal("200000")
        )

        self.assertIsNone(voucher)
        self.assertIsNotNone(error)

    def test_valid_voucher_calculates_discount(self):

        voucher, error = VoucherService.get_valid_voucher(
            "GIAM10",
            Decimal("200000")
        )

        self.assertIsNotNone(voucher)
        self.assertIsNone(error)

        discount = VoucherService.calculate_discount(
            voucher,
            Decimal("200000")
        )

        self.assertEqual(discount, Decimal("20000"))

    def test_voucher_below_minimum_order_value_is_rejected(self):

        self.valid_voucher.min_order_value = Decimal("500000")
        self.valid_voucher.save()

        voucher, error = VoucherService.get_valid_voucher(
            "GIAM10",
            Decimal("200000")
        )

        self.assertIsNone(voucher)
        self.assertIsNotNone(error)

    def test_apply_voucher_view_stores_code_in_session(self):

        User.objects.create_user(
            username="khach02",
            password="password123"
        )

        self.client.login(
            username="khach02",
            password="password123"
        )

        pizza = make_pizza()

        session = self.client.session
        session["cart"] = {str(pizza.id): 2}
        session.save()

        self.client.post(
            reverse("apply_voucher"),
            {"voucher_code": "GIAM10"},
            follow=True
        )

        self.assertEqual(
            self.client.session.get("voucher_code"),
            "GIAM10"
        )


class OrderStatusTransitionTests(TestCase):
    """TC-08 - Chuyển trạng thái đơn hàng không hợp lệ."""

    def setUp(self):

        self.staff = User.objects.create_user(
            username="admin01",
            password="password123",
            is_staff=True,
        )

        self.customer = User.objects.create_user(
            username="khach03",
            password="password123",
        )

        self.pizza = make_pizza()

        self.order = Order.objects.create(
            user=self.customer,
            full_name="Nguyễn Văn A",
            phone="0900000000",
            address="123 Đường ABC",
            subtotal=Decimal("100000"),
            total_price=Decimal("100000"),
            status="ordered",
        )

        OrderItem.objects.create(
            order=self.order,
            pizza=self.pizza,
            quantity=1,
            price=self.pizza.price,
        )

        self.client.login(
            username="admin01",
            password="password123",
        )

    def test_tc08_invalid_transition_is_rejected(self):

        self.client.post(
            reverse("manage_orders"),
            {
                "order_id": self.order.id,
                "status": "completed",
            },
            follow=True,
        )

        self.order.refresh_from_db()

        # Không cho phép nhảy thẳng từ "ordered" sang "completed"
        self.assertEqual(self.order.status, "ordered")

    def test_valid_transition_is_accepted(self):

        self.client.post(
            reverse("manage_orders"),
            {
                "order_id": self.order.id,
                "status": "confirmed",
            },
            follow=True,
        )

        self.order.refresh_from_db()

        self.assertEqual(self.order.status, "confirmed")

    def test_non_staff_cannot_manage_orders(self):

        self.client.logout()

        self.client.login(
            username="khach03",
            password="password123",
        )

        self.client.post(
            reverse("manage_orders"),
            {
                "order_id": self.order.id,
                "status": "confirmed",
            },
            follow=True,
        )

        self.order.refresh_from_db()

        self.assertEqual(self.order.status, "ordered")
