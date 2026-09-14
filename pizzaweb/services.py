# ============================================================
# SERVICE LAYER
# ------------------------------------------------------------
# Theo đề xuất "Kiến trúc phân lớp" (Báo cáo Phân tích & Thiết
# kế - mục 5): tách business logic ra khỏi views.py để dễ kiểm
# thử (unit test) và tái sử dụng, thay vì để toàn bộ tính toán
# nằm rải rác trong view như mã nguồn gốc.
#
# - VoucherService : nghiệp vụ áp dụng / kiểm tra mã giảm giá
#   (UC03 - Áp dụng voucher, báo cáo 1 mục 7).
# - DashboardService : tổng hợp số liệu cho Dashboard quản trị
#   (UC05, báo cáo 1 mục 9).
# ============================================================

from decimal import Decimal

from django.db.models import Sum, Count, F
from django.utils import timezone

from .models import Voucher, Order, OrderItem, Inventory


class VoucherService:
    """Đóng gói toàn bộ nghiệp vụ liên quan tới Voucher (UC03)."""

    @staticmethod
    def get_valid_voucher(code, order_total):
        """
        Kiểm tra mã voucher theo đúng luồng đặc tả UC03:
        1. Tồn tại mã.
        2. Còn hiệu lực (thời gian, số lần dùng, đơn tối thiểu).

        Trả về tuple (voucher_hoac_None, thong_bao_loi_hoac_None)
        """

        code = (code or "").strip().upper()

        if not code:
            return None, "Vui lòng nhập mã giảm giá."

        voucher = Voucher.objects.filter(
            code__iexact=code
        ).first()

        if not voucher:
            return None, "Mã giảm giá không tồn tại."

        if not voucher.is_active:
            return None, "Mã giảm giá đã ngừng hoạt động."

        now = timezone.now()

        if now < voucher.start:
            return None, "Mã giảm giá chưa đến thời gian sử dụng."

        if now > voucher.end:
            return None, "Mã giảm giá đã hết hạn sử dụng."

        if voucher.usage_count >= voucher.usage_limit:
            return None, "Mã giảm giá đã hết lượt sử dụng."

        if order_total < voucher.min_order_value:
            return None, (
                "Đơn hàng chưa đạt giá trị tối thiểu "
                f"{voucher.min_order_value:.0f}₫ để áp dụng mã này."
            )

        return voucher, None

    @staticmethod
    def calculate_discount(voucher, order_total):
        """Tính số tiền được giảm dựa trên loại giảm giá."""

        if voucher is None:
            return Decimal("0")

        return voucher.calculate_discount(order_total)

    @staticmethod
    def mark_used(voucher):
        """Tăng số lần sử dụng khi đơn hàng được tạo thành công."""

        if voucher is None:
            return

        voucher.usage_count = F("usage_count") + 1
        voucher.save(update_fields=["usage_count"])


class DashboardService:
    """Tổng hợp số liệu cho Dashboard quản trị (UC05)."""

    @staticmethod
    def get_summary():

        orders = Order.objects.exclude(status="cancelled")

        total_revenue = orders.aggregate(
            total=Sum("total_price")
        )["total"] or Decimal("0")

        total_orders = Order.objects.count()

        total_customers = Order.objects.values(
            "user"
        ).distinct().count()

        pending_orders = Order.objects.filter(
            status__in=["ordered", "confirmed", "preparing", "shipping"]
        ).count()

        top_pizzas = (
            OrderItem.objects
            .exclude(order__status="cancelled")
            .values("pizza__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("-total_quantity")[:5]
        )

        low_stock_items = Inventory.objects.filter(
            quantity__lt=F("min_quantity")
        ).order_by("quantity")

        recent_orders = Order.objects.select_related(
            "user"
        ).order_by("-created_at")[:8]

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "pending_orders": pending_orders,
            "top_pizzas": top_pizzas,
            "low_stock_items": low_stock_items,
            "recent_orders": recent_orders,
        }
