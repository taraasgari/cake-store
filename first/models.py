from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# ============================================
# مدل کاربر
# ============================================

class User(AbstractUser):
    USER_ROLES = (
        ('user', 'کاربر عادی'),
        ('admin', 'ادمین'),
        ('owner', 'مالک'),
    )

    role = models.CharField(max_length=10, choices=USER_ROLES, default='user', verbose_name="نقش کاربری")
    email = models.EmailField(unique=True, verbose_name="ایمیل")
    phone = models.CharField(max_length=11, unique=True, verbose_name="شماره تلفن")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name="تصویر پروفایل")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # OTP / password reset security
    # The OTP itself is stored as a password hash, never as plaintext.
    otp_code = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )
    otp_created_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    otp_verified = models.BooleanField(
        default=False
    )
    otp_attempts = models.PositiveSmallIntegerField(
        default=0
    )
    otp_last_sent_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    otp_locked_until = models.DateTimeField(
        blank=True,
        null=True,
    )

    # بازیابی رمز (قدیمی)
    reset_password_token = models.CharField(max_length=100, blank=True, null=True)
    reset_password_token_created = models.DateTimeField(blank=True, null=True)

    # ===== نقش‌های ادمین =====
    admin_roles = models.ManyToManyField(
        'AdminRole',
        blank=True,
        related_name='users',
        verbose_name="نقش‌های ادمین"
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

    @property
    def is_owner(self):
        return self.role == 'owner'

    @property
    def is_admin(self):
        return self.role in ['admin', 'owner']

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ['-created_at']


# ============================================
# مدل‌های دسته‌بندی و برند
# ============================================
class Category(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="نام دسته‌بندی"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="اسلاگ"
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="آیکون"
    )

    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name='تصویر دسته‌بندی'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات"
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subcategories'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/category/{self.slug}/"
class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام برند")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="اسلاگ")
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام نوع محصول")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="اسلاگ")
    icon = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "نوع محصول"
        verbose_name_plural = "انواع محصولات"
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="نام تگ")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="اسلاگ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تگ"
        verbose_name_plural = "تگ‌ها"
        ordering = ['name']

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=50, verbose_name="نام رنگ")
    code = models.CharField(max_length=7, verbose_name="کد رنگ (Hex)", help_text="مثال: #FF0000")
    image = models.ImageField(upload_to='colors/', blank=True, null=True, verbose_name="تصویر رنگ")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "رنگ"
        verbose_name_plural = "رنگ‌ها"
        ordering = ['name']

    def __str__(self):
        return self.name


# ============================================
# مدل محصول
# ============================================

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام محصول")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="اسلاگ")
    description = models.TextField(verbose_name="توضیحات کامل", blank=True, null=True)
    short_description = models.CharField(max_length=300, blank=True, null=True, verbose_name="توضیحات کوتاه")

    # ===== قیمت‌ها (برای محصولات بدون تنوع) =====
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="قیمت پایه (تومان)")
    discount_price = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True, verbose_name="قیمت تخفیف‌خورده")
    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی کل")

    # ===== روابط =====
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, blank=True, null=True, related_name='products')
    product_type = models.ForeignKey(ProductType, on_delete=models.SET_NULL, blank=True, null=True, related_name='products')
    tags = models.ManyToManyField(Tag, blank=True, related_name='products', verbose_name="تگ‌ها")

    # ===== وضعیت‌ها =====
    is_available = models.BooleanField(default=True, verbose_name="موجود")
    is_featured = models.BooleanField(default=False, verbose_name="محصول ویژه")
    is_new = models.BooleanField(default=False, verbose_name="محصول جدید")
    is_best_seller = models.BooleanField(default=False, verbose_name="پرفروش")

    # ===== ویژگی جدید =====
    has_variants = models.BooleanField(default=False, verbose_name="دارای تنوع (رنگ/حجم)")

    # ===== تصاویر =====
    main_image = models.ImageField(upload_to='products/', verbose_name="تصویر اصلی")
    specifications = models.JSONField(default=dict, blank=True, verbose_name="مشخصات فنی")

    # ===== آمار =====
    views_count = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")
    sales_count = models.PositiveIntegerField(default=0, verbose_name="تعداد فروش")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name="امتیاز")

    # ===== وضعیت نهایی =====
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/product/{self.slug}/"

    @property
    def final_price(self):
        if self.has_variants:
            variant = self.variants.filter(is_default=True, is_active=True).first()
            if not variant:
                variant = self.variants.filter(is_active=True, stock__gt=0).first()
            if variant:
                return variant.final_price
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def discount_percent(self):
        if self.has_variants:
            default = self.variants.filter(is_default=True, is_active=True).first()
            if default and default.discount_percent > 0:
                return default.discount_percent
        if self.discount_price and self.discount_price < self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def total_stock(self):
        if self.has_variants:
            return sum(v.stock for v in self.variants.filter(is_active=True))
        return self.stock

    @property
    def is_in_stock(self):
        if self.has_variants:
            return self.variants.filter(is_active=True, stock__gt=0).exists()
        return self.stock > 0 and self.is_available

    @property
    def available_variants(self):
        return self.variants.filter(is_active=True, stock__gt=0)

    @property
    def colors_list(self):
        colors = []
        for variant in self.variants.filter(is_active=True):
            if variant.color and variant.color not in colors:
                colors.append(variant.color)
        return colors

    @property
    def first_variant(self):
        return self.variants.filter(is_active=True).first()


# ============================================
# مدل تنوع محصول
# ============================================

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="محصول")

    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='variants', verbose_name="رنگ")
    color_code = models.CharField(max_length=7, blank=True, null=True, verbose_name="کد رنگ (Hex)")

    volume_ml = models.PositiveIntegerField(null=True, blank=True, verbose_name="حجم (میلی‌لیتر)")
    size = models.CharField(max_length=20, blank=True, null=True, verbose_name="سایز (S/M/L)")

    price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                                verbose_name="قیمت این تنوع")
    discount_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                                         verbose_name="قیمت تخفیف‌خورده")
    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی")

    image = models.ImageField(upload_to='products/variants/', blank=True, null=True,
                              verbose_name="تصویر تنوع")

    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="SKU")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_default = models.BooleanField(default=False, verbose_name="تنوع پیش‌فرض")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع‌های محصول"
        unique_together = ['product', 'color', 'volume_ml', 'size']
        ordering = ['color__name', 'volume_ml']

    def __str__(self):
        parts = [self.product.name]
        if self.color:
            parts.append(self.color.name)
        if self.volume_ml:
            parts.append(f"{self.volume_ml}ml")
        if self.size:
            parts.append(self.size)
        return " - ".join(parts)

    @property
    def final_price(self):
        base = self.price or self.product.price
        if self.discount_price and self.discount_price < base:
            return self.discount_price
        return base

    @property
    def discount_percent(self):
        base = self.price or self.product.price
        if self.discount_price and self.discount_price < base:
            return int(((base - self.discount_price) / base) * 100)
        return 0

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.is_active

    def save(self, *args, **kwargs):
        if not self.sku:
            import secrets

            prefix = (
                self.product.slug[:4].upper()
                if self.product.slug
                else "PRD"
            )

            for _ in range(20):
                suffix = f"{secrets.randbelow(10**8):08d}"
                candidate = f"{prefix}-{suffix}"

                if not type(self).objects.filter(
                    sku=candidate
                ).exclude(pk=self.pk).exists():
                    self.sku = candidate
                    break
            else:
                raise RuntimeError(
                    'Could not generate a unique product SKU.'
                )

        super().save(*args, **kwargs)


# ============================================
# مدل انبار
# ============================================

class InventoryBatch(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE,
                                related_name='batches', verbose_name="تنوع")

    batch_code = models.CharField(max_length=50, unique=True, verbose_name="کد سری")
    quantity = models.PositiveIntegerField(verbose_name="تعداد ورودی")
    remaining = models.PositiveIntegerField(verbose_name="موجودی باقیمانده")

    production_date = models.DateField(verbose_name="تاریخ تولید")
    expiry_date = models.DateField(verbose_name="تاریخ انقضا")

    purchase_price = models.DecimalField(max_digits=12, decimal_places=0,
                                         verbose_name="قیمت خرید")
    selling_price = models.DecimalField(max_digits=12, decimal_places=0,
                                        verbose_name="قیمت فروش")

    supplier = models.CharField(max_length=100, blank=True, null=True,
                                verbose_name="تامین‌کننده")
    note = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سری انبار"
        verbose_name_plural = "سری‌های انبار"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.variant.product.name} - {self.batch_code}"

    @property
    def is_expired(self):
        return timezone.now().date() > self.expiry_date

    @property
    def is_low_stock(self):
        return self.remaining <= 5

    def reduce_stock(self, quantity):
        if self.remaining < quantity:
            raise ValueError(f"موجودی کافی در سری {self.batch_code} وجود ندارد")
        self.remaining -= quantity
        self.save()
        self.variant.stock -= quantity
        self.variant.save()


# ============================================
# مدل کد تخفیف
# ============================================

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percent', 'درصدی'),
        ('fixed', 'مبلغ ثابت'),
    )

    code = models.CharField(max_length=50, unique=True, verbose_name="کد تخفیف")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES,
                                     default='percent', verbose_name="نوع تخفیف")
    discount_value = models.DecimalField(max_digits=10, decimal_places=0,
                                         verbose_name="مقدار تخفیف")

    min_purchase = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                       verbose_name="حداقل مبلغ خرید")
    max_discount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                                       verbose_name="حداکثر تخفیف")

    valid_from = models.DateTimeField(verbose_name="شروع اعتبار")
    valid_to = models.DateTimeField(verbose_name="پایان اعتبار")

    max_use = models.PositiveIntegerField(default=1, verbose_name="حداکثر استفاده")
    used_count = models.PositiveIntegerField(default=0, verbose_name="تعداد استفاده")

    products = models.ManyToManyField(Product, blank=True, verbose_name="محصولات مشمول")
    categories = models.ManyToManyField(Category, blank=True, verbose_name="دسته‌بندی‌های مشمول")
    users = models.ManyToManyField(User, blank=True, verbose_name="کاربران مشمول")

    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_unlimited = models.BooleanField(default=False, verbose_name="استفاده نامحدود")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.discount_value}%)"

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_to:
            return False
        if not self.is_unlimited and self.used_count >= self.max_use:
            return False
        return True

    def apply_discount(self, total):
        if not self.is_valid:
            return total

        if self.discount_type == 'percent':
            discount = (total * self.discount_value) / 100
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:
            discount = self.discount_value

        return max(0, total - discount)


# ============================================
# مدل‌های تصاویر و نظرات
# ============================================

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    is_main = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=100, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.order}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}⭐"


# ============================================
# مدل‌های سبد خرید
# ============================================

class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"

    def __str__(self):
        return f"سبد خرید {self.user.username}"

    @property
    def total_price(self):
        # Sum before discount.
        return sum(
            item.total_price
            for item in self.items.all()
        )

    @property
    def total_discount(self):
        return sum(
            item.discount_amount
            for item in self.items.all()
        )

    @property
    def final_price(self):
        # Sum final line prices directly so discount is never subtracted twice.
        return sum(
            item.final_price
            for item in self.items.all()
        )

    @property
    def total_items(self):
        return sum(
            item.quantity
            for item in self.items.all()
        )


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        null=True,
        blank=True
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='cart_items',
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "آیتم سبد خرید"
        verbose_name_plural = "آیتم‌های سبد خرید"
        unique_together = ['cart', 'product', 'variant']

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"

    @property
    def item_name(self):
        if self.variant:
            return str(self.variant)
        if self.product:
            return self.product.name
        return "محصول"

    @property
    def base_unit_price(self):
        if self.variant:
            return self.variant.price or self.variant.product.price
        if self.product:
            return self.product.price
        return self.price

    @property
    def final_unit_price(self):
        if self.variant:
            return self.variant.final_price
        if self.product:
            return self.product.final_price
        return self.price

    @property
    def total_price(self):
        return self.base_unit_price * self.quantity

    @property
    def discount_amount(self):
        discount_per_unit = self.base_unit_price - self.final_unit_price
        if discount_per_unit < 0:
            discount_per_unit = 0
        return discount_per_unit * self.quantity

    @property
    def final_price(self):
        return self.final_unit_price * self.quantity



# ============================================
# مدل‌های سفارشات
# ============================================

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
        ('refunded', 'بازگشت وجه'),
    ]

    PAYMENT_METHODS = [
        ('online', 'پرداخت آنلاین'),
        ('cash', 'پرداخت در محل'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=0)
    discount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=0)

    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=11)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='online')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    coupon_discount = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"
        ordering = ['-created_at']

    def __str__(self):
        return f"سفارش #{self.order_number} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import secrets

            for _ in range(20):
                candidate = (
                    f"{secrets.randbelow(10**10):010d}"
                )

                if not type(self).objects.filter(
                    order_number=candidate
                ).exists():
                    self.order_number = candidate
                    break
            else:
                raise RuntimeError(
                    'Could not generate a unique order number.'
                )

        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name='order_items',
        null=True,
        blank=True,
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        related_name='order_items',
        null=True,
        blank=True,
    )

    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=0)

    variant_info = models.JSONField(default=dict, blank=True, verbose_name="اطلاعات تنوع")

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


# ============================================
# مدل‌های دیگر
# ============================================

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "علاقه‌مندی"
        verbose_name_plural = "علاقه‌مندی‌ها"
        unique_together = ['user', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='آرایشی شاپ', verbose_name="نام سایت")
    site_title = models.CharField(max_length=100, default='آرایشی شاپ - لوکس ترین فروشگاه آرایشی', verbose_name="عنوان سایت")
    site_description = models.TextField(max_length=500, default='مرجع تخصصی لوازم آرایشی با کیفیت و اصالت تضمینی', verbose_name="توضیحات سایت")

    logo = models.ImageField(upload_to='settings/', blank=True, null=True)
    favicon = models.ImageField(upload_to='settings/', blank=True, null=True)
    default_product_image = models.ImageField(upload_to='settings/', blank=True, null=True)
    default_avatar = models.ImageField(upload_to='settings/', blank=True, null=True)

    primary_color = models.CharField(max_length=7, default='#ec407a', verbose_name="رنگ اصلی")
    secondary_color = models.CharField(max_length=7, default='#d81b60', verbose_name="رنگ ثانویه")
    accent_color = models.CharField(max_length=7, default='#ab47bc', verbose_name="رنگ تاکید")
    background_color = models.CharField(max_length=7, default='#fdf2f8', verbose_name="رنگ پس‌زمینه")
    text_color = models.CharField(max_length=7, default='#1a1a2e', verbose_name="رنگ متن")

    background_image = models.ImageField(upload_to='settings/bg/', blank=True, null=True)

    footer_text = models.CharField(max_length=200, default='© ۱۴۰۴ آرایشی شاپ - تمامی حقوق محفوظ است', verbose_name="متن فوتر")
    footer_bg_color = models.CharField(max_length=7, default='#1a0a1a', verbose_name="رنگ پس‌زمینه فوتر")

    instagram = models.CharField(max_length=200, blank=True, null=True)
    telegram = models.CharField(max_length=200, blank=True, null=True)
    whatsapp = models.CharField(max_length=200, blank=True, null=True)
    youtube = models.CharField(max_length=200, blank=True, null=True)

    phone = models.CharField(max_length=20, default='۰۲۱-۱۲۳۴۵۶۷۸', verbose_name="شماره تماس")
    email = models.EmailField(default='info@arayeshi.shop', verbose_name="ایمیل")
    address = models.TextField(default='تهران، خیابان ولیعصر، پلاک ۱۲۳', verbose_name="آدرس")
    number_format = models.CharField(
        max_length=10,
        choices=[
            ('persian', 'فارسی (۱۲۳)'),
            ('english', 'انگلیسی (123)'),
        ],
        default='persian',
        verbose_name="فرمت اعداد"
    )

    # ===== فیلدهای ویرایشگر بصری =====
    customizer_rules = models.TextField(default='[]', blank=True, verbose_name="قوانین ویرایشگر بصری")
    customizer_theme = models.JSONField(default=dict, blank=True, verbose_name="تم ویرایشگر بصری")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return f"تنظیمات سایت - {self.site_name}"

    @classmethod
    def get_settings(cls):
        settings = cls.objects.first()
        if not settings:
            settings = cls.objects.create()
        return settings


class SliderImage(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="عنوان اسلایدر")
    subtitle = models.CharField(max_length=300, blank=True, null=True, verbose_name="زیر عنوان")
    image = models.ImageField(upload_to='slider/', verbose_name="تصویر اسلایدر")
    link = models.CharField(max_length=300, blank=True, null=True, verbose_name="لینک (اختیاری)")
    button_text = models.CharField(max_length=50, blank=True, null=True, verbose_name="متن دکمه")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "اسلایدر"
        verbose_name_plural = "اسلایدرها"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title if self.title else f"اسلایدر {self.id}"


# ============================================
# مدل‌های مدیریت دسترسی (RBAC)
# ============================================

class AdminPermission(models.Model):
    """دسترسی‌های قابل انتخاب برای ادمین‌ها"""
    PERMISSION_CHOICES = [
        ('dashboard', 'داشبورد مدیریت'),
        ('products_view', 'مشاهده محصولات'),
        ('products_add', 'افزودن محصول'),
        ('products_edit', 'ویرایش محصول'),
        ('products_delete', 'حذف محصول'),
        ('orders_view', 'مشاهده سفارشات'),
        ('orders_update', 'تغییر وضعیت سفارش'),
        ('reviews_view', 'مشاهده نظرات'),
        ('reviews_verify', 'تایید نظرات'),
        ('reviews_delete', 'حذف نظرات'),
        ('users_view', 'مشاهده کاربران'),
        ('users_manage', 'مدیریت کاربران'),
        ('admins_manage', 'مدیریت ادمین‌ها'),
        ('warehouse_view', 'مشاهده انبار'),
        ('warehouse_edit', 'ویرایش انبار'),
        ('site_settings', 'تنظیمات ظاهر'),
        ('reports_view', 'مشاهده گزارشات'),
        ('support_view', 'مشاهده تیکت‌های پشتیبانی'),
        ('support_reply', 'پاسخگویی به تیکت‌های پشتیبانی'),
        ('returns_manage', 'مدیریت لغو و مرجوعی سفارش‌ها'),
    ]

    name = models.CharField(max_length=50, choices=PERMISSION_CHOICES, unique=True, verbose_name="نام دسترسی")
    label = models.CharField(max_length=100, verbose_name="برچسب نمایشی")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "دسترسی ادمین"
        verbose_name_plural = "دسترسی‌های ادمین"
        ordering = ['name']

    def __str__(self):
        return self.label


class AdminRole(models.Model):
    """نقش‌های از پیش تعریف شده برای ادمین‌ها"""
    ROLE_TYPES = [
        ('super_admin', 'مدیر کل'),
        ('product_manager', 'مدیر محصولات'),
        ('order_manager', 'مدیر سفارشات'),
        ('content_manager', 'مدیر محتوا'),
        ('support', 'پشتیبانی'),
        ('custom', 'سفارشی'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_TYPES, unique=True, verbose_name="نام نقش")
    display_name = models.CharField(max_length=100, default='نقش', verbose_name="نام نمایشی")
    permissions = models.ManyToManyField(AdminPermission, blank=True, related_name='roles', verbose_name="دسترسی‌ها")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_default = models.BooleanField(default=False, verbose_name="نقش پیش‌فرض")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "نقش ادمین"
        verbose_name_plural = "نقش‌های ادمین"
        ordering = ['name']

    def __str__(self):
        return self.display_name


class AdminUserPermission(models.Model):
    """دسترسی‌های شخصی‌سازی شده برای هر ادمین"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_permissions', verbose_name="کاربر")
    permission = models.ForeignKey(AdminPermission, on_delete=models.CASCADE, related_name='user_permissions', verbose_name="دسترسی")
    is_allowed = models.BooleanField(default=True, verbose_name="مجاز")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "دسترسی شخصی ادمین"
        verbose_name_plural = "دسترسی‌های شخصی ادمین"
        unique_together = ['user', 'permission']

    def __str__(self):
        return f"{self.user.username} - {self.permission.label}"
