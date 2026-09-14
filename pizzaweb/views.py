from decimal import Decimal
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    RegisterForm,
    CheckoutForm,
    ProfileForm,
    ReviewForm,
)

from .models import (
    Pizza,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Voucher,
    Inventory,
    Payment,
    Review,
    Profile,
)

from .services import VoucherService, DashboardService


# ============================================================
# HOME
# ============================================================

def home(request):

    pizzas = Pizza.objects.filter(
        is_available=True
    )

    return render(
        request,
        "home.html",
        {
            "pizzas": pizzas,
        }
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    return redirect("home")


# ============================================================
# CART
# ============================================================

def cart(request):

    cart_items = request.session.get(
        "cart",
        {}
    )

    items = []
    total = Decimal("0")

    for pizza_id, quantity in cart_items.items():

        pizza = get_object_or_404(
            Pizza,
            id=pizza_id
        )

        quantity = int(quantity)

        subtotal = (
            pizza.price * quantity
        )

        items.append({
            "pizza": pizza,
            "quantity": quantity,
            "subtotal": subtotal,
        })

        total += subtotal

    return render(
        request,
        "cart.html",
        {
            "items": items,
            "total": total,
        }
    )


def add_to_cart(request, pizza_id):

    pizza = get_object_or_404(
        Pizza,
        id=pizza_id,
        is_available=True
    )

    cart_data = request.session.get(
        "cart",
        {}
    )

    pizza_id = str(pizza_id)

    if pizza_id in cart_data:

        cart_data[pizza_id] += 1

    else:

        cart_data[pizza_id] = 1

    request.session["cart"] = cart_data
    request.session.modified = True

    return JsonResponse({
        "success": True,
        "message": f"Đã thêm {pizza.name} vào giỏ hàng.",
        "pizza_name": pizza.name,
        "cart_count": sum(
            cart_data.values()
        ),
    })


def remove_from_cart(request, pizza_id):

    cart_data = request.session.get(
        "cart",
        {}
    )

    pizza_id = str(pizza_id)

    if pizza_id in cart_data:

        del cart_data[pizza_id]

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


def increase_quantity(request, pizza_id):

    cart_data = request.session.get(
        "cart",
        {}
    )

    pizza_id = str(pizza_id)

    if pizza_id in cart_data:

        cart_data[pizza_id] += 1

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


def decrease_quantity(request, pizza_id):

    cart_data = request.session.get(
        "cart",
        {}
    )

    pizza_id = str(pizza_id)

    if pizza_id in cart_data:

        cart_data[pizza_id] -= 1

        if cart_data[pizza_id] <= 0:

            del cart_data[pizza_id]

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


# ============================================================
# CHECKOUT
# ============================================================

@login_required
def checkout(request):

    # --------------------------------------------------------
    # LẤY PROFILE
    # --------------------------------------------------------

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    # --------------------------------------------------------
    # LẤY GIỎ HÀNG
    # --------------------------------------------------------

    cart_data = request.session.get(
        "cart",
        {}
    )

    if not cart_data:

        messages.warning(
            request,
            "Giỏ hàng đang trống."
        )

        return redirect("cart")

    items = []
    subtotal = Decimal("0")

    for pizza_id, quantity in cart_data.items():

        pizza = get_object_or_404(
            Pizza,
            id=pizza_id,
            is_available=True
        )

        quantity = int(quantity)

        item_subtotal = (
            pizza.price * quantity
        )

        subtotal += item_subtotal

        items.append({
            "pizza": pizza,
            "quantity": quantity,
            "subtotal": item_subtotal,
        })

    # --------------------------------------------------------
    # TÍNH TIỀN (UC03 - Áp dụng voucher)
    # --------------------------------------------------------

    shipping_fee = Decimal("0")
    discount = Decimal("0")
    voucher = None
    voucher_code = request.session.get("voucher_code")

    if voucher_code:

        voucher, voucher_error = VoucherService.get_valid_voucher(
            voucher_code,
            subtotal
        )

        if voucher:

            discount = VoucherService.calculate_discount(
                voucher,
                subtotal
            )

        else:

            # Voucher đã lưu trong session không còn hợp lệ
            # (vd: hết hạn / hết lượt / đơn không còn đạt mức tối
            # thiểu sau khi giỏ hàng thay đổi) -> tự động gỡ bỏ.
            request.session.pop("voucher_code", None)
            request.session.modified = True

            messages.warning(
                request,
                f"Mã giảm giá không còn hợp lệ: {voucher_error}"
            )

    total_price = (
        subtotal
        + shipping_fee
        - discount
    )

    # --------------------------------------------------------
    # POST - ĐẶT HÀNG
    # --------------------------------------------------------

    if request.method == "POST":

        use_profile = (
            request.POST.get("use_profile") == "1"
        )

        # ====================================================
        # DÙNG THÔNG TIN PROFILE
        # ====================================================

        if use_profile:

            if not profile.full_name:

                messages.warning(
                    request,
                    "Tài khoản chưa có họ và tên. "
                    "Vui lòng cập nhật thông tin tài khoản."
                )

                return redirect("profile")

            if not profile.phone:

                messages.warning(
                    request,
                    "Tài khoản chưa có số điện thoại. "
                    "Vui lòng cập nhật thông tin tài khoản."
                )

                return redirect("profile")

            if not profile.address:

                messages.warning(
                    request,
                    "Tài khoản chưa có địa chỉ. "
                    "Vui lòng cập nhật thông tin tài khoản."
                )

                return redirect("profile")

            order = Order.objects.create(

                user=request.user,

                full_name=profile.full_name,
                phone=profile.phone,
                address=profile.address,

                note=request.POST.get(
                    "note",
                    ""
                ).strip(),

                subtotal=subtotal,
                discount=discount,
                shipping_fee=shipping_fee,
                total_price=total_price,
                voucher=voucher,

                status="ordered",
                payment_status="unpaid",
            )

        # ====================================================
        # DÙNG THÔNG TIN KHÁC
        # ====================================================

        else:

            form = CheckoutForm(
                request.POST
            )

            if not form.is_valid():

                return render(
                    request,
                    "checkout.html",
                    {
                        "form": form,
                        "items": items,
                        "subtotal": subtotal,
                        "shipping_fee": shipping_fee,
                        "discount": discount,
                        "total_price": total_price,
                        "use_profile": False,
                        "voucher": voucher,
                        "voucher_code": voucher_code,
                    }
                )

            order = form.save(
                commit=False
            )

            order.user = request.user

            order.subtotal = subtotal
            order.discount = discount
            order.shipping_fee = shipping_fee
            order.total_price = total_price
            order.voucher = voucher

            order.status = "ordered"
            order.payment_status = "unpaid"

            order.save()

        # ====================================================
        # TẠO ORDER ITEM
        # ====================================================

        for pizza_id, quantity in cart_data.items():

            pizza = get_object_or_404(
                Pizza,
                id=pizza_id
            )

            quantity = int(quantity)

            OrderItem.objects.create(
                order=order,
                pizza=pizza,
                quantity=quantity,
                price=pizza.price,
                subtotal=(
                    pizza.price * quantity
                )
            )

        # ====================================================
        # ĐÁNH DẤU VOUCHER ĐÃ SỬ DỤNG (UC03)
        # ====================================================

        if voucher:

            VoucherService.mark_used(voucher)

        # ====================================================
        # XÓA GIỎ HÀNG + MÃ GIẢM GIÁ ĐANG ÁP DỤNG
        # ====================================================

        request.session["cart"] = {}
        request.session.pop("voucher_code", None)
        request.session.modified = True

        # ====================================================
        # THÔNG BÁO
        # ====================================================

        messages.success(
            request,
            f"Đặt hàng thành công! Mã đơn hàng #{order.id}"
        )

        return redirect(
            "order_success",
            order_id=order.id
        )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    form = CheckoutForm(
        initial={
            "full_name": profile.full_name,
            "phone": profile.phone,
            "address": profile.address,
        }
    )

    return render(
        request,
        "checkout.html",
        {
            "form": form,
            "items": items,
            "subtotal": subtotal,
            "shipping_fee": shipping_fee,
            "discount": discount,
            "total_price": total_price,
            "use_profile": True,
            "voucher": voucher,
            "voucher_code": voucher_code,
        }
    )


# ============================================================
# ÁP DỤNG / GỠ VOUCHER (UC03)
# ============================================================

@login_required
def apply_voucher(request):

    if request.method != "POST":

        return redirect("checkout")

    cart_data = request.session.get(
        "cart",
        {}
    )

    subtotal = Decimal("0")

    for pizza_id, quantity in cart_data.items():

        pizza = Pizza.objects.filter(id=pizza_id).first()

        if pizza:

            subtotal += pizza.price * int(quantity)

    code = request.POST.get("voucher_code", "")

    voucher, error = VoucherService.get_valid_voucher(
        code,
        subtotal
    )

    if voucher:

        request.session["voucher_code"] = voucher.code
        request.session.modified = True

        discount = VoucherService.calculate_discount(
            voucher,
            subtotal
        )

        messages.success(
            request,
            f"Đã áp dụng mã \"{voucher.code}\", giảm "
            f"{discount:.0f}₫."
        )

    else:

        messages.error(
            request,
            error
        )

    return redirect("checkout")


@login_required
def remove_voucher(request):

    if request.method == "POST":

        request.session.pop("voucher_code", None)
        request.session.modified = True

        messages.success(
            request,
            "Đã gỡ bỏ mã giảm giá."
        )

    return redirect("checkout")


# ============================================================
# ORDER SUCCESS
# ============================================================

@login_required
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "order_success.html",
        {
            "order": order,
        }
    )


# ============================================================
# ORDER DETAIL
# ============================================================

# ============================================================
# ORDER DETAIL
# ============================================================

@login_required
def order_detail(request, order_id):

    # Admin / Staff được xem tất cả đơn hàng
    if request.user.is_staff:

        order = get_object_or_404(
            Order.objects.prefetch_related(
                "items__pizza",
                "items__reviews",
            ),
            id=order_id
        )

    # User thường chỉ được xem đơn của chính mình
    else:

        order = get_object_or_404(
            Order.objects.prefetch_related(
                "items__pizza",
                "items__reviews",
            ),
            id=order_id,
            user=request.user
        )

    return render(
        request,
        "order_detail.html",
        {
            "order": order,
        }
    )


# ============================================================
# CANCEL ORDER
# ============================================================

@login_required
def cancel_order(request, order_id):

    if request.method != "POST":

        return redirect(
            "order_detail",
            order_id=order_id
        )

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    # Chỉ được hủy khi Đã đặt hàng
    if order.status == "ordered":

        order.status = "cancelled"

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"Đã hủy đơn hàng #{order.id} thành công."
        )

    else:

        messages.warning(
            request,
            "Đơn hàng này không thể hủy."
        )

    return redirect(
        "order_detail",
        order_id=order.id
    )


# ============================================================
# MY ORDERS
# ============================================================

@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "my_orders.html",
        {
            "orders": orders,
        }
    )


# ============================================================
# REGISTER
# ============================================================

def register(request):

    if request.method == "POST":

        form = RegisterForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            login(
                request,
                user
            )

            messages.success(
                request,
                "Đăng ký tài khoản thành công!"
            )

            return redirect("home")

    else:

        form = RegisterForm()

    return render(
        request,
        "register.html",
        {
            "form": form,
        }
    )


# ============================================================
# PAYMENT
# ============================================================
# Giữ nguyên các view cũ để không phá URL hiện tại.
# Không thêm thanh toán thật / sandbox / QR / OTP.
# ============================================================

def payment_success(request):

    request.session["cart"] = {}
    request.session.modified = True

    return render(
        request,
        "payment_success.html"
    )


def payment_cancel(request):

    return render(
        request,
        "payment_cancel.html"
    )


# ============================================================
# MANAGE ORDERS - STAFF / ADMIN
# ============================================================

@login_required(login_url="/login/")
def manage_orders(request):

    # Chỉ Staff/Admin
    if not request.user.is_staff:

        messages.error(
            request,
            "Bạn không có quyền quản lý đơn hàng."
        )

        return redirect("home")

    # --------------------------------------------------------
    # POST - CẬP NHẬT TRẠNG THÁI
    # --------------------------------------------------------

    if request.method == "POST":

        order_id = request.POST.get(
            "order_id"
        )

        new_status = request.POST.get(
            "status"
        )

        order = get_object_or_404(
            Order,
            id=order_id
        )

        # Các trạng thái hợp lệ
        valid_statuses = dict(
            Order.STATUS_CHOICES
        )

        if new_status not in valid_statuses:

            messages.error(
                request,
                "Trạng thái đơn hàng không hợp lệ."
            )

            return redirect(
                "manage_orders"
            )

        # ----------------------------------------------------
        # QUY TRÌNH TRẠNG THÁI
        # ----------------------------------------------------

        allowed_transitions = {

            "ordered": [
                "confirmed",
                "cancelled",
            ],

            "confirmed": [
                "preparing",
            ],

            "preparing": [
                "shipping",
            ],

            "shipping": [
                "completed",
            ],

            "completed": [],

            "cancelled": [],
        }

        if new_status not in allowed_transitions.get(
            order.status,
            []
        ):

            messages.warning(
                request,
                "Không thể chuyển đơn hàng sang trạng thái này."
            )

            return redirect(
                "manage_orders"
            )

        order.status = new_status

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"Đã cập nhật đơn #{order.id} → "
            f"{order.get_status_display()}."
        )

        return redirect(
            "manage_orders"
        )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    orders = Order.objects.select_related(
        "user"
    ).prefetch_related(
        "items__pizza"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "admin_orders.html",
        {
            "orders": orders,
        }
    )


# ============================================================
# PROFILE
# ============================================================

@login_required
def profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Cập nhật thông tin tài khoản thành công!"
            )

            return redirect(
                "profile"
            )

    else:

        form = ProfileForm(
            instance=profile
        )

    return render(
        request,
        "profile.html",
        {
            "form": form,
        }
    )


# ============================================================
# CREATE REVIEW
# ============================================================

@login_required
def create_review(request, order_item_id):

    # --------------------------------------------------------
    # Lấy đúng OrderItem của user hiện tại
    # --------------------------------------------------------

    order_item = get_object_or_404(
        OrderItem.objects.select_related(
            "order",
            "pizza",
        ),
        id=order_item_id,
        order__user=request.user,
    )

    order = order_item.order

    # --------------------------------------------------------
    # Chỉ đơn Hoàn thành mới được đánh giá
    # --------------------------------------------------------

    if order.status != "completed":

        messages.warning(
            request,
            "Bạn chỉ có thể đánh giá khi đơn hàng đã hoàn thành."
        )

        return redirect(
            "order_detail",
            order_id=order.id,
        )

    # --------------------------------------------------------
    # Kiểm tra đã có đánh giá chưa
    # --------------------------------------------------------

    existing_review = Review.objects.filter(
        user=request.user,
        order_item=order_item,
    ).first()

    if existing_review:

        if existing_review.is_deleted:

            messages.warning(
                request,
                "Bạn đã xóa đánh giá cho Pizza này và không thể đánh giá lại."
            )

        else:

            messages.warning(
                request,
                "Pizza này trong đơn hàng đã được đánh giá."
            )

        return redirect(
            "order_detail",
            order_id=order.id,
        )

    # --------------------------------------------------------
    # POST - Tạo đánh giá
    # --------------------------------------------------------

    if request.method == "POST":

        form = ReviewForm(
            request.POST
        )

        if form.is_valid():

            review = form.save(
                commit=False
            )

            review.user = request.user
            review.order_item = order_item

            review.action_count = 0
            review.is_deleted = False

            review.save()

            messages.success(
                request,
                "Đánh giá của bạn đã được gửi thành công!"
            )

            return redirect(
                "order_detail",
                order_id=order.id,
            )

    # --------------------------------------------------------
    # GET - Hiển thị form
    # --------------------------------------------------------

    else:

        form = ReviewForm()

    return render(
        request,
        "create_review.html",
        {
            "form": form,
            "order_item": order_item,
            "order": order,
        }
    )


# ============================================================
# EDIT REVIEW
# ============================================================

@login_required
def edit_review(request, review_id):

    # --------------------------------------------------------
    # Chỉ chủ review mới được sửa
    # --------------------------------------------------------

    review = get_object_or_404(
        Review,
        id=review_id,
        user=request.user
    )

    # --------------------------------------------------------
    # Kiểm tra OrderItem
    # --------------------------------------------------------

    if not review.order_item:

        messages.error(
            request,
            "Đánh giá này không còn liên kết với sản phẩm."
        )

        return redirect("home")

    order = review.order_item.order

    # --------------------------------------------------------
    # Review đã xóa
    # --------------------------------------------------------

    if review.is_deleted:

        messages.error(
            request,
            "Đánh giá này đã được xóa."
        )

        return redirect(
            "order_detail",
            order_id=order.id
        )

    # --------------------------------------------------------
    # Chỉ đơn Hoàn thành
    # --------------------------------------------------------

    if order.status != "completed":

        messages.error(
            request,
            "Chỉ đánh giá của đơn hàng đã hoàn thành mới được sửa."
        )

        return redirect(
            "order_detail",
            order_id=order.id
        )

    # --------------------------------------------------------
    # Chỉ được sửa hoặc xóa 1 lần
    # --------------------------------------------------------

    if review.action_count >= 1:

        messages.warning(
            request,
            "Bạn đã sử dụng quyền chỉnh sửa hoặc xóa đánh giá này."
        )

        return redirect(
            "order_detail",
            order_id=order.id
        )

    # --------------------------------------------------------
    # Thời hạn 3 ngày
    # --------------------------------------------------------

    deadline = (
        review.created_at
        + timedelta(days=3)
    )

    if timezone.now() > deadline:

        messages.warning(
            request,
            "Đánh giá đã quá thời hạn 3 ngày và không thể chỉnh sửa."
        )

        return redirect(
            "order_detail",
            order_id=order.id
        )

    # --------------------------------------------------------
    # POST - LƯU THAY ĐỔI
    # --------------------------------------------------------

    if request.method == "POST":

        form = ReviewForm(
            request.POST,
            instance=review
        )

        if form.is_valid():

            review = form.save(
                commit=False
            )

            # Đã sử dụng quyền sửa/xóa
            review.action_count = 1

            review.save()

            messages.success(
                request,
                "Đã cập nhật đánh giá."
            )

            return redirect(
                "order_detail",
                order_id=order.id
            )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    else:

        form = ReviewForm(
            instance=review
        )

    return render(
        request,
        "edit_review.html",
        {
            "form": form,
            "review": review,
            "order": order,
        }
    )


# ============================================================
# DELETE REVIEW
# ============================================================

@login_required
def delete_review(request, review_id):

    # --------------------------------------------------------
    # Chỉ POST
    # --------------------------------------------------------

    if request.method != "POST":

        return redirect("home")

    # --------------------------------------------------------
    # Chỉ chủ review mới được xóa
    # --------------------------------------------------------

    review = get_object_or_404(
        Review,
        id=review_id,
        user=request.user
    )

    # --------------------------------------------------------
    # Kiểm tra OrderItem
    # --------------------------------------------------------

    if not review.order_item:

        messages.error(
            request,
            "Đánh giá này không còn liên kết với sản phẩm."
        )

        return redirect("home")

    order = review.order_item.order

    # --------------------------------------------------------
    # Review đã xóa
    # --------------------------------------------------------

    if review.is_deleted:

        messages.error(
            request,
            "Đánh giá này đã được xóa."
        )

        return redirect(
            "order_detail",
            order_id=order.id
        )

    # --------------------------------------------------------
    # Chỉ đơn Hoàn thành
    # --------------------------------------------------------

    if order.status != "completed":

        messages.error(
            request,
            "Chỉ đánh giá của đơn hàng đã hoàn thành mới được xóa."
        )

        return redirect(
            "order_detail",
            order_id=order.id
        )

    # --------------------------------------------------------
    # Chỉ được sửa hoặc xóa 1 lần
    # --------------------------------------------------------

    if review.action_count >= 1:

        messages.warning(
            request,
            "Bạn đã sử dụng quyền chỉnh sửa hoặc xóa đánh giá này."
        )

        return redirect(
            "order_detail",
            order_id=order.id
        )

    # --------------------------------------------------------
    # Thời hạn 3 ngày
    # --------------------------------------------------------

    deadline = (
        review.created_at
        + timedelta(days=3)
    )

    if timezone.now() > deadline:

        messages.warning(
            request,
            "Đánh giá đã quá thời hạn 3 ngày và không thể xóa."
        )

        return redirect(
            "order_detail",
            order_id=order.id
        )

    # --------------------------------------------------------
    # SOFT DELETE
    # --------------------------------------------------------

    review.is_deleted = True
    review.action_count = 1

    review.save(
        update_fields=[
            "is_deleted",
            "action_count",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Đã xóa đánh giá."
    )

    return redirect(
        "order_detail",
        order_id=order.id
    )


# ============================================================
# DASHBOARD QUẢN TRỊ (UC05)
# ============================================================

@login_required(login_url="/login/")
def admin_dashboard(request):

    # Chỉ Admin/Staff được xem dashboard
    if not request.user.is_staff:

        messages.error(
            request,
            "Bạn không có quyền truy cập trang này."
        )

        return redirect("home")

    summary = DashboardService.get_summary()

    return render(
        request,
        "dashboard.html",
        summary
    )