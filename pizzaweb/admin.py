
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import (
    Pizza,
    Topping,
    CustomPizza,
    Voucher,
    Inventory,
    Order,
    OrderItem,
    Review,
    Profile,
)


# ============================================================
# MIXIN - THÊM NÚT "XÓA TẤT CẢ"
# ============================================================

class DeleteAllAdminMixin:

    change_list_template = "admin/delete_all_change_list.html"

    def changelist_view(self, request, extra_context=None):

        # ----------------------------------------------------
        # XỬ LÝ NÚT "XÓA TẤT CẢ"
        # ----------------------------------------------------

        if (
            request.method == "POST"
            and request.POST.get("_delete_all") == "1"
        ):

            if not self.has_delete_permission(request):
                raise PermissionDenied

            try:
                with transaction.atomic():

                    deleted_count, deleted_details = (
                        self.model.objects.all().delete()
                    )

                messages.success(
                    request,
                    f"Đã xóa toàn bộ dữ liệu thành công "
                    f"({deleted_count} bản ghi)."
                )

            except ProtectedError:

                messages.error(
                    request,
                    "Không thể xóa toàn bộ dữ liệu vì "
                    "một số bản ghi đang được dữ liệu khác tham chiếu."
                )

            return redirect(request.path)

        # ----------------------------------------------------
        # ĐẾM SỐ LƯỢNG BẢN GHI
        # ----------------------------------------------------

        extra_context = extra_context or {}

        extra_context["delete_all_count"] = (
            self.model.objects.count()
        )

        return super().changelist_view(
            request,
            extra_context=extra_context
        )


# ============================================================
# PIZZA
# ============================================================

@admin.register(Pizza)
class PizzaAdmin(DeleteAllAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "price",
        "is_available",
        "created_at",
    )

    list_filter = (
        "is_available",
    )

    search_fields = (
        "name",
    )


# ============================================================
# TOPPING
# ============================================================

@admin.register(Topping)
class ToppingAdmin(DeleteAllAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "price",
        "stock",
        "is_available",
        "created_at",
    )

    list_filter = (
        "is_available",
    )

    search_fields = (
        "name",
    )


# ============================================================
# CUSTOM PIZZA
# ============================================================

@admin.register(CustomPizza)
class CustomPizzaAdmin(DeleteAllAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "size",
        "crust",
        "price",
        "created_at",
    )

    list_filter = (
        "size",
        "crust",
        "created_at",
    )

    search_fields = (
        "user__username",
    )


# ============================================================
# VOUCHER
# ============================================================

@admin.register(Voucher)
class VoucherAdmin(DeleteAllAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "code",
        "discount_type",
        "discount",
        "min_order_value",
        "start",
        "end",
        "usage_limit",
        "usage_count",
        "is_active",
    )

    list_filter = (
        "discount_type",
        "is_active",
        "start",
        "end",
    )

    search_fields = (
        "code",
    )


# ============================================================
# INVENTORY
# ============================================================

@admin.register(Inventory)
class InventoryAdmin(DeleteAllAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "ingredient",
        "quantity",
        "min_quantity",
        "unit",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "unit",
        "created_at",
    )

    search_fields = (
        "ingredient",
    )


# ============================================================
# ORDER
# ============================================================

@admin.register(Order)
class OrderAdmin(DeleteAllAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "full_name",
        "phone",
        "total_price",
        "status",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "created_at",
    )

    search_fields = (
        "full_name",
        "phone",
        "user__username",
    )


# ============================================================
# ORDER ITEM
# ============================================================

@admin.register(OrderItem)
class OrderItemAdmin(DeleteAllAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "pizza",
        "quantity",
        "price",
        "subtotal",
        "created_at",
    )

    search_fields = (
        "pizza__name",
        "order__full_name",
        "order__user__username",
    )


# ============================================================
# REVIEW
# ============================================================

@admin.register(Review)
class ReviewAdmin(DeleteAllAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "order_item",
        "rating",
        "is_deleted",
        "action_count",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "rating",
        "is_deleted",
        "created_at",
    )

    search_fields = (
        "user__username",
        "comment",
        "order_item__pizza__name",
    )


# ============================================================
# PROFILE INLINE
# ============================================================

class ProfileInline(admin.StackedInline):

    model = Profile

    can_delete = True

    extra = 0

    verbose_name = "Thông tin cá nhân"
    verbose_name_plural = "Thông tin cá nhân"

    fields = (
        "full_name",
        "phone",
        "address",
    )


# ============================================================
# USER
# ============================================================

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(DeleteAllAdminMixin, UserAdmin):

    inlines = (
        ProfileInline,
    )

    fieldsets = (
        (
            "Tài khoản",
            {
                "fields": (
                    "username",
                    "email",
                    "password",
                )
            },
        ),

        (
            "Quyền quản trị",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),

        (
            "Ngày quan trọng",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            "Tạo tài khoản",
            {
                "classes": ("wide",),

                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

