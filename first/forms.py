from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()

# ============================================
# فرم ثبت‌نام
# ============================================

class SignUpForm(UserCreationForm):
    agree_terms = forms.BooleanField(
        required=True,
        label='پذیرش قوانین و مقررات',
        error_messages={
            'required': 'برای ثبت‌نام باید قوانین و مقررات را بپذیرید.'
        },
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
            'placeholder': 'ایمیل خود را وارد کنید *',
            'dir': 'ltr'
        }),
        error_messages={
            'required': 'وارد کردن ایمیل الزامی است',
            'invalid': 'لطفاً یک ایمیل معتبر وارد کنید',
            'unique': 'این ایمیل قبلاً ثبت شده است'
        }
    )
    
    phone = forms.CharField(
        max_length=11,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
            'placeholder': 'شماره تلفن *',
            'dir': 'ltr'
        }),
        error_messages={
            'required': 'وارد کردن شماره تلفن الزامی است',
            'max_length': 'شماره تلفن نباید بیشتر از ۱۱ رقم باشد'
        }
    )
    
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'phone',
            'password1',
            'password2',
            'agree_terms',
        )
    
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for field_name in ['username', 'password1', 'password2']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
                'dir': 'ltr'
            })
        
        self.fields['username'].widget.attrs['placeholder'] = 'نام کاربری *'
        self.fields['password1'].widget.attrs['placeholder'] = 'رمز عبور *'
        self.fields['password2'].widget.attrs['placeholder'] = 'تکرار رمز عبور *'
        
        self.fields['username'].error_messages = {
            'required': 'وارد کردن نام کاربری الزامی است',
            'unique': 'این نام کاربری قبلاً ثبت شده است',
            'invalid': 'نام کاربری شامل حروف، اعداد و @/./+/-/_ است'
        }
        self.fields['password1'].error_messages = {
            'required': 'وارد کردن رمز عبور الزامی است'
        }
        self.fields['password2'].error_messages = {
            'required': 'تکرار رمز عبور الزامی است',
            'password_mismatch': 'رمز عبور با تکرار آن مطابقت ندارد'
        }
    
    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("این ایمیل قبلاً ثبت شده است")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError("وارد کردن شماره تلفن الزامی است")
        if not re.match(r'^09\d{9}$', phone):
            raise ValidationError("شماره تلفن باید با ۰۹ شروع شود و ۱۱ رقم باشد")
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("این شماره تلفن قبلاً ثبت شده است")
        return phone
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError("نام کاربری باید حداقل ۳ کاراکتر باشد")
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError("نام کاربری شامل حروف، اعداد و @/./+/-/_ است")
        return username


# ============================================
# فرم ورود
# ============================================

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام کاربری',
            'dir': 'ltr',
            'autocomplete': 'username',
            'autocapitalize': 'none',
            'spellcheck': 'false',
        }),
        error_messages={
            'required': 'وارد کردن نام کاربری الزامی است',
        },
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور',
            'dir': 'ltr',
            'autocomplete': 'current-password',
        }),
        error_messages={
            'required': 'وارد کردن رمز عبور الزامی است',
        },
    )

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise ValidationError('نام کاربری را وارد کنید')
        return username


# ============================================
# فرم ویرایش پروفایل
# ============================================

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'profile_image']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
                'placeholder': 'نام خود را وارد کنید'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
                'placeholder': 'نام خانوادگی خود را وارد کنید'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
                'placeholder': 'ایمیل خود را وارد کنید'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
                'placeholder': 'شماره تلفن خود را وارد کنید'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
                'placeholder': 'آدرس خود را وارد کنید',
                'rows': 3
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
                'accept': 'image/*'
            }),
        }
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'ایمیل',
            'phone': 'شماره تلفن',
            'address': 'آدرس',
            'profile_image': 'تصویر پروفایل',
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        query = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise ValidationError('این ایمیل قبلاً ثبت شده است')
        return email

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not re.fullmatch(r'^09\d{9}$', phone):
            raise ValidationError('شماره تلفن باید با ۰۹ شروع شود و ۱۱ رقم باشد')
        query = User.objects.filter(phone=phone)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise ValidationError('این شماره تلفن قبلاً ثبت شده است')
        return phone


# ============================================
# فرم‌های بازیابی رمز (OTP)
# ============================================

class ForgotPasswordForm(forms.Form):
    """فرم درخواست کد OTP"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
            'placeholder': 'ایمیل خود را وارد کنید',
            'dir': 'ltr'
        }),
        error_messages={
            'required': 'وارد کردن ایمیل الزامی است',
            'invalid': 'لطفاً یک ایمیل معتبر وارد کنید'
        }
    )


class OTPVerificationForm(forms.Form):
    """فرم تأیید کد OTP"""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50 text-center text-2xl tracking-[10px]',
            'placeholder': 'کد ۶ رقمی را وارد کنید',
            'dir': 'ltr',
            'maxlength': '6',
            'autocomplete': 'off'
        }),
        error_messages={
            'required': 'وارد کردن کد تأیید الزامی است',
            'min_length': 'کد تأیید باید ۶ رقم باشد',
            'max_length': 'کد تأیید باید ۶ رقم باشد'
        }
    )


class SetNewPasswordForm(SetPasswordForm):
    """فرم تنظیم رمز عبور جدید بعد از تأیید OTP"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
            'placeholder': 'رمز عبور جدید *',
            'dir': 'ltr'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-pink-500 focus:ring-4 focus:ring-pink-100 transition-all outline-none bg-white/50',
            'placeholder': 'تکرار رمز عبور جدید *',
            'dir': 'ltr'
        })
