from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Order, Profile, Review


# =========================================================
# FORM ĐĂNG KÝ TÀI KHOẢN
# =========================================================

class RegisterForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
        ]


# =========================================================
# FORM CHECKOUT / ĐẶT HÀNG
# =========================================================

class CheckoutForm(forms.ModelForm):

    class Meta:
        model = Order

        fields = [
            "full_name",
            "phone",
            "address",
            "note",
        ]

        widgets = {

            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nhập họ và tên",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ví dụ: 0912345678",
                    "maxlength": "13",
                    "inputmode": "tel",
                    "autocomplete": "tel",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nhập địa chỉ giao hàng",
                    "rows": 3,
                }
            ),

            "note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ghi chú cho đơn hàng (không bắt buộc)",
                    "rows": 3,
                }
            ),
        }

        labels = {
            "full_name": "Họ và tên",
            "phone": "Số điện thoại",
            "address": "Địa chỉ giao hàng",
            "note": "Ghi chú",
        }

    def clean_phone(self):

        phone = self.cleaned_data.get("phone", "")

        # Xóa khoảng trắng đầu/cuối
        phone = phone.strip()

        # Xóa khoảng trắng ở giữa
        phone = phone.replace(" ", "")

        # =====================================================
        # +84xxxxxxxxx → 0xxxxxxxxx
        # =====================================================

        if phone.startswith("+84"):
            phone = "0" + phone[3:]

        # =====================================================
        # 84xxxxxxxxx → 0xxxxxxxxx
        # =====================================================

        elif phone.startswith("84"):
            phone = "0" + phone[2:]

        # =====================================================
        # CHỈ ĐƯỢC CÓ CHỮ SỐ
        # =====================================================

        if not phone.isdigit():
            raise forms.ValidationError(
                "Số điện thoại chỉ được chứa chữ số."
            )

        # =====================================================
        # PHẢI ĐÚNG 10 SỐ
        # =====================================================

        if len(phone) != 10:
            raise forms.ValidationError(
                "Số điện thoại phải có đúng 10 chữ số."
            )

        # =====================================================
        # PHẢI BẮT ĐẦU BẰNG 0
        # =====================================================

        if not phone.startswith("0"):
            raise forms.ValidationError(
                "Số điện thoại phải bắt đầu bằng số 0."
            )

        # Trả về số điện thoại đã chuẩn hóa
        return phone


# =========================================================
# FORM THÔNG TIN TÀI KHOẢN
# =========================================================

class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile

        fields = [
            "full_name",
            "phone",
            "address",
        ]

        labels = {
            "full_name": "Họ và tên",
            "phone": "Số điện thoại",
            "address": "Địa chỉ",
        }

        widgets = {

            "full_name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nhập họ và tên",
                    "autocomplete": "name",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nhập số điện thoại",
                    "maxlength": "13",
                    "inputmode": "tel",
                    "autocomplete": "tel",
                }
            ),

            "address": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nhập địa chỉ giao hàng",
                    "autocomplete": "street-address",
                }
            ),
        }

    def clean_phone(self):

        phone = self.cleaned_data.get("phone", "").strip()

        # Xóa khoảng trắng
        phone = phone.replace(" ", "")

        # =====================================================
        # +84xxxxxxxxx → 0xxxxxxxxx
        # =====================================================

        if phone.startswith("+84"):
            phone = "0" + phone[3:]

        # =====================================================
        # 84xxxxxxxxx → 0xxxxxxxxx
        # =====================================================

        elif phone.startswith("84"):
            phone = "0" + phone[2:]

        # =====================================================
        # CHỈ ĐƯỢC CÓ CHỮ SỐ
        # =====================================================

        if not phone.isdigit():
            raise forms.ValidationError(
                "Số điện thoại chỉ được chứa chữ số."
            )

        # =====================================================
        # PHẢI ĐÚNG 10 SỐ
        # =====================================================

        if len(phone) != 10:
            raise forms.ValidationError(
                "Số điện thoại phải có 10 chữ số."
            )

        # =====================================================
        # PHẢI BẮT ĐẦU BẰNG 0
        # =====================================================

        if not phone.startswith("0"):
            raise forms.ValidationError(
                "Số điện thoại phải bắt đầu bằng số 0."
            )

        # Trả về số điện thoại đã chuẩn hóa
        return phone


# =========================================================
# FORM ĐÁNH GIÁ PIZZA
# =========================================================

# =========================================================
# FORM ĐÁNH GIÁ PIZZA
# =========================================================

class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review

        fields = [
            "rating",
            "comment",
        ]

        labels = {
            "rating": "Đánh giá",
            "comment": "Nhận xét",
        }

        widgets = {

            # Rating sẽ được điều khiển bằng 5 ngôi sao
            # trong create_review.html / edit_review.html
            "rating": forms.HiddenInput(),

            "comment": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "placeholder": "Chia sẻ cảm nhận của bạn về Pizza...",
                    "rows": 4,
                }
            ),
        }