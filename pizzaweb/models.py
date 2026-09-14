from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


# ============================================================
# 1. PIZZA
# ============================================================

class Pizza(models.Model):

    name = models.CharField(
        max_length=200,
        verbose_name="Tên pizza"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Mô tả"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Giá"
    )

    image = models.ImageField(
        upload_to="pizzas/",
        blank=True,
        null=True,
        verbose_name="Hình ảnh"
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="Đang bán"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Ngày cập nhật"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pizza"
        verbose_name_plural = "Pizza"

    def __str__(self):
        return self.name


# ============================================================
# 2. TOPPING
# ============================================================

class Topping(models.Model):

    name = models.CharField(
        max_length=100,
        verbose_name="Tên topping"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Giá"
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Tồn kho"
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="Đang bán"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Topping"
        verbose_name_plural = "Topping"

    def __str__(self):
        return self.name


# ============================================================
# 3. CUSTOM PIZZA
# ============================================================

class CustomPizza(models.Model):

    SIZE_CHOICES = [
        ("S", "Nhỏ"),
        ("M", "Vừa"),
        ("L", "Lớn"),
    ]

    CRUST_CHOICES = [
        ("thin", "Đế mỏng"),
        ("thick", "Đế dày"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="custom_pizzas",
        verbose_name="Khách hàng"
    )

    size = models.CharField(
        max_length=1,
        choices=SIZE_CHOICES,
        default="M",
        verbose_name="Kích thước"
    )

    crust = models.CharField(
        max_length=10,
        choices=CRUST_CHOICES,
        default="thin",
        verbose_name="Đế bánh"
    )

    toppings = models.ManyToManyField(
        Topping,
        blank=True,
        related_name="custom_pizzas",
        verbose_name="Topping"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Giá"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    def __str__(self):
        return f"Custom Pizza #{self.id} - {self.get_size_display()}"

    def calculate_price(self):

        size_price = {
            "S": Decimal("0"),
            "M": Decimal("20000"),
            "L": Decimal("40000"),
        }

        crust_price = {
            "thin": Decimal("0"),
            "thick": Decimal("15000"),
        }

        total = (
            Decimal("80000")
            + size_price.get(self.size, Decimal("0"))
            + crust_price.get(self.crust, Decimal("0"))
        )

        total += sum(
            (topping.price for topping in self.toppings.all()),
            Decimal("0")
        )

        return total


# ============================================================
# 4. CART
# ============================================================

class Cart(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="Khách hàng"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Ngày cập nhật"
    )

    class Meta:
        verbose_name = "Giỏ hàng"
        verbose_name_plural = "Giỏ hàng"

    def __str__(self):
        return f"Giỏ hàng của {self.user.username}"

    def get_total(self):

        return sum(
            (
                item.get_subtotal()
                for item in self.items.all()
            ),
            Decimal("0")
        )

    def get_total_quantity(self):

        return sum(
            item.quantity
            for item in self.items.all()
        )


# ============================================================
# 5. CART ITEM
# ============================================================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Giỏ hàng"
    )

    pizza = models.ForeignKey(
        Pizza,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Pizza"
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Số lượng"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày thêm"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "pizza"],
                name="unique_pizza_in_cart"
            )
        ]

        verbose_name = "Sản phẩm trong giỏ"
        verbose_name_plural = "Sản phẩm trong giỏ"

    def __str__(self):
        return f"{self.pizza.name} x {self.quantity}"

    def get_subtotal(self):

        return self.pizza.price * self.quantity


# ============================================================
# 6. VOUCHER
# ============================================================

class Voucher(models.Model):

    DISCOUNT_TYPE_CHOICES = [
        ("percent", "Phần trăm"),
        ("fixed", "Số tiền"),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Mã voucher"
    )

    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default="percent",
        verbose_name="Loại giảm"
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Mức giảm"
    )

    min_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Giá trị đơn tối thiểu"
    )

    start = models.DateTimeField(
        verbose_name="Bắt đầu"
    )

    end = models.DateTimeField(
        verbose_name="Kết thúc"
    )

    usage_limit = models.PositiveIntegerField(
        default=1,
        verbose_name="Giới hạn sử dụng"
    )

    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Đã sử dụng"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Voucher"
        verbose_name_plural = "Voucher"

    def __str__(self):
        return self.code

    def is_valid(self, order_total):

        now = timezone.now()

        if not self.is_active:
            return False

        if now < self.start or now > self.end:
            return False

        if self.usage_count >= self.usage_limit:
            return False

        if order_total < self.min_order_value:
            return False

        return True

    def calculate_discount(self, order_total):

        if not self.is_valid(order_total):
            return Decimal("0")

        if self.discount_type == "percent":

            discount_amount = (
                order_total * self.discount / Decimal("100")
            )

        else:

            discount_amount = self.discount

        if discount_amount > order_total:
            discount_amount = order_total

        return discount_amount


# ============================================================
# 7. INVENTORY
# ============================================================

class Inventory(models.Model):

    ingredient = models.CharField(
        max_length=200,
        verbose_name="Nguyên liệu"
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Số lượng tồn"
    )

    min_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Mức tồn tối thiểu"
    )

    unit = models.CharField(
        max_length=30,
        default="kg",
        verbose_name="Đơn vị"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Ngày cập nhật"
    )

    class Meta:
        ordering = ["ingredient"]
        verbose_name = "Tồn kho"
        verbose_name_plural = "Tồn kho"

    def __str__(self):
        return f"{self.ingredient} - {self.quantity} {self.unit}"

    def is_low_stock(self):

        return self.quantity < self.min_quantity


# ============================================================
# 8. ORDER
# ============================================================

class Order(models.Model):

    STATUS_CHOICES = [
        ("ordered", "Đã đặt hàng"),
        ("confirmed", "Đã xác nhận"),
        ("preparing", "Đang chuẩn bị"),
        ("shipping", "Đang giao"),
        ("completed", "Hoàn thành"),
        ("cancelled", "Đã hủy"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("unpaid", "Chưa thanh toán"),
        ("paid", "Đã thanh toán"),
        ("failed", "Thanh toán thất bại"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Khách hàng"
    )

    full_name = models.CharField(
        max_length=200,
        verbose_name="Họ và tên"
    )

    phone = models.CharField(
        max_length=20,
        verbose_name="Số điện thoại"
    )

    address = models.TextField(
        verbose_name="Địa chỉ giao hàng"
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Tạm tính"
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Giảm giá"
    )

    shipping_fee = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Phí giao hàng"
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Tổng tiền"
    )

    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Voucher"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ordered",
        verbose_name="Trạng thái đơn"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="unpaid",
        verbose_name="Trạng thái thanh toán"
    )

    note = models.TextField(
        blank=True,
        verbose_name="Ghi chú"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày đặt"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"

    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.user.username}"

    def calculate_total(self):

        return (
            self.subtotal
            + self.shipping_fee
            - self.discount
        )

    def get_status_display_name(self):

        return self.get_status_display()


# ============================================================
# 9. ORDER ITEM
# ============================================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Đơn hàng"
    )

    pizza = models.ForeignKey(
        Pizza,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Pizza"
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Số lượng"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Đơn giá"
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Thành tiền"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    class Meta:
        verbose_name = "Chi tiết đơn hàng"
        verbose_name_plural = "Chi tiết đơn hàng"

    def __str__(self):
        return f"{self.pizza.name} x {self.quantity}"

    def save(self, *args, **kwargs):

        self.subtotal = self.price * self.quantity

        super().save(*args, **kwargs)


# ============================================================
# 10. PAYMENT
# ============================================================

class Payment(models.Model):

    METHOD_CHOICES = [
        ("cod", "Thanh toán khi nhận hàng"),
        ("banking", "Chuyển khoản"),
        ("momo", "MoMo"),
        ("vnpay", "VNPay"),
    ]

    STATUS_CHOICES = [
        ("pending", "Đang chờ"),
        ("paid", "Đã thanh toán"),
        ("failed", "Thất bại"),
        ("cancelled", "Đã hủy"),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment",
        verbose_name="Đơn hàng"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Số tiền"
    )

    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default="cod",
        verbose_name="Phương thức"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Trạng thái"
    )

    transaction_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Mã giao dịch"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ngày thanh toán"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Thanh toán"
        verbose_name_plural = "Thanh toán"

    def __str__(self):
        return f"Thanh toán đơn #{self.order.id}"


# ============================================================
# 11. REVIEW
# ============================================================

class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Khách hàng"
    )

    order_item = models.ForeignKey(
    OrderItem,
    on_delete=models.CASCADE,
    related_name="reviews",
    verbose_name="Sản phẩm trong đơn",
    null=True,
    blank=True
    )

    rating = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ],
        verbose_name="Số sao"
    )

    comment = models.TextField(
        blank=True,
        verbose_name="Nhận xét"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày đánh giá"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Ngày cập nhật"
    )

    # 0 = chưa sửa/xóa
    # 1 = đã sử dụng quyền sửa hoặc xóa
    action_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Số lần chỉnh sửa/xóa"
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Đã xóa"
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "order_item"],
                name="one_review_per_user_per_order_item"
            )
        ]

        verbose_name = "Đánh giá"
        verbose_name_plural = "Đánh giá"

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.order_item.pizza.name} - "
            f"{self.rating}/5"
        )

    # ============================================================
# 12. PROFILE
# ============================================================

# ============================================================
# 12. PROFILE
# ============================================================

class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Tài khoản"
    )

    full_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Họ và tên"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Số điện thoại"
    )

    address = models.TextField(
        blank=True,
        verbose_name="Địa chỉ"
    )

    class Meta:
        verbose_name = "Thông tin tài khoản"
        verbose_name_plural = "Thông tin tài khoản"

    def __str__(self):
        return self.user.username