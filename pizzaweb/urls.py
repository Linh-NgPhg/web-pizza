from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path("cart/", views.cart, name="cart"),

    path(
        "add-to-cart/<int:pizza_id>/",
        views.add_to_cart,
        name="add_to_cart"
    ),

    path(
        "remove-from-cart/<int:pizza_id>/",
        views.remove_from_cart,
        name="remove_from_cart"
    ),

    path(
        "increase/<int:pizza_id>/",
        views.increase_quantity,
        name="increase_quantity"
    ),

    path(
        "decrease/<int:pizza_id>/",
        views.decrease_quantity,
        name="decrease_quantity"
    ),

    # UC01
    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    # UC03 - Áp dụng voucher
    path(
        "voucher/apply/",
        views.apply_voucher,
        name="apply_voucher"
    ),

    path(
        "voucher/remove/",
        views.remove_voucher,
        name="remove_voucher"
    ),

    path(
        "order-success/<int:order_id>/",
        views.order_success,
        name="order_success"
    ),

    path(
    "my-orders/",
    views.my_orders,
    name="my_orders"
    ),

    # Đăng nhập
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html"
        ),
        name="login"
    ),

    # Đăng xuất
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout"
    ),

    # Đăng ký
    path(
        "register/",
        views.register,
        name="register"
    ),

    # Thanh toán
    path(
        "payment-success/",
        views.payment_success,
        name="payment_success"
    ),

    path(
        "payment-cancel/",
        views.payment_cancel,
        name="payment_cancel"
    ),
    path(
    "order/<int:order_id>/",
    views.order_detail,
    name="order_detail"
    ),
    path(
    "order/<int:order_id>/cancel/",
    views.cancel_order,
    name="cancel_order",
),
path(
    "manage-orders/",
    views.manage_orders,
    name="manage_orders",
),

path(
    "profile/",
    views.profile,
    name="profile"
),
path(
    "order-item/<int:order_item_id>/review/",
    views.create_review,
    name="create_review",
),

path(
    "review/<int:review_id>/edit/",
    views.edit_review,
    name="edit_review",
),

path(
    "review/<int:review_id>/delete/",
    views.delete_review,
    name="delete_review",
),

# UC05 - Dashboard quản trị
path(
    "dashboard/",
    views.admin_dashboard,
    name="admin_dashboard",
),
]