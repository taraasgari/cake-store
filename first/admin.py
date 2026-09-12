from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import (
    User, Category, Brand, ProductType, Tag, Color, Product, 
    ProductVariant, ProductImage, ProductReview, Order, OrderItem, 
    Wishlist, SiteSettings, SliderImage, NewsletterSubscriber,
    AdminPermission, AdminRole, AdminUserPermission,
    InventoryBatch, Coupon
)

User = get_user_model()

# ============================================
# ادمین کاربر
# ============================================

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'profile_image')}),
        ('نقش کاربری', {'fields': ('role',)}),
        ('نقش‌های ادمین', {'fields': ('admin_roles',)}),
        ('دسترسی‌ها', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('تاریخ‌ها', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'role', 'password1', 'password2'),
        }),
    )

# ثبت ادمین کاربر
if not admin.site.is_registered(User):
    admin.site.register(User, CustomUserAdmin)


# ============================================
# ادمین دسته‌بندی
# ============================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


# ============================================
# ادمین برند
# ============================================

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


# ============================================
# ادمین نوع محصول
# ============================================

@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


# ============================================
# ادمین تگ
# ============================================

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# ============================================
# ادمین رنگ
# ============================================

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('name',)


# ============================================
# ادمین محصول
# ============================================

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 3
    fields = ('color', 'volume_ml', 'size', 'price', 'discount_price', 'stock', 'image', 'sku', 'is_default', 'is_active')
    raw_id_fields = ('color',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'is_main', 'order')


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    fields = ('user', 'rating', 'comment', 'is_verified')
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'price', 'discount_price', 'stock', 'is_available', 
        'final_price_display', 'total_stock', 'is_in_stock_display', 
        'has_variants', 'is_featured', 'category'
    )
    list_filter = ('category', 'brand', 'product_type', 'is_available', 'is_featured', 'is_new', 'is_best_seller', 'has_variants', 'created_at')
    search_fields = ('name', 'description', 'short_description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'discount_price', 'stock', 'is_available', 'is_featured', 'has_variants')
    readonly_fields = ('views_count', 'sales_count', 'rating')
    inlines = [ProductImageInline, ProductReviewInline, ProductVariantInline]
    ordering = ('-created_at',)
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'description', 'short_description', 'category', 'brand', 'product_type', 'main_image')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'discount_price', 'stock', 'is_available', 'has_variants')
        }),
        ('وضعیت', {
            'fields': ('is_featured', 'is_new', 'is_best_seller', 'is_active')
        }),
        ('مشخصات فنی', {
            'fields': ('specifications',)
        }),
        ('آمار', {
            'fields': ('views_count', 'sales_count', 'rating'),
            'classes': ('collapse',)
        }),
    )
    
    def final_price_display(self, obj):
        return f"{obj.final_price:,} تومان"
    final_price_display.short_description = 'قیمت نهایی'
    
    def is_in_stock_display(self, obj):
        return "✅ موجود" if obj.is_in_stock else "❌ ناموجود"
    is_in_stock_display.short_description = 'وضعیت موجودی'


# ============================================
# ادمین تنوع محصول
# ============================================

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'color', 'volume_ml', 'size', 'price', 'discount_price', 
        'stock', 'is_default', 'is_active', 'sku'
    )
    list_filter = ('is_active', 'is_default', 'color', 'product')
    search_fields = ('product__name', 'sku', 'color__name')
    list_editable = ('price', 'discount_price', 'stock', 'is_active', 'is_default')
    raw_id_fields = ('product', 'color')
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('product', 'color', 'color_code', 'volume_ml', 'size')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'discount_price', 'stock')
        }),
        ('تصویر و شناسه', {
            'fields': ('image', 'sku', 'is_active', 'is_default')
        }),
    )


# ============================================
# ادمین انبار
# ============================================

@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ('variant', 'batch_code', 'quantity', 'remaining', 'expiry_date', 'is_expired', 'is_active')
    list_filter = ('is_active', 'expiry_date', 'variant')
    search_fields = ('batch_code', 'variant__product__name')
    list_editable = ('is_active',)
    fieldsets = (
        ('اطلاعات سری', {
            'fields': ('variant', 'batch_code', 'quantity', 'remaining')
        }),
        ('تاریخ‌ها', {
            'fields': ('production_date', 'expiry_date')
        }),
        ('قیمت‌ها', {
            'fields': ('purchase_price', 'selling_price')
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('supplier', 'note', 'is_active')
        }),
    )


# ============================================
# ادمین کد تخفیف
# ============================================

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_value', 'discount_type', 'is_valid_display', 'used_count', 'max_use', 'is_active')
    list_filter = ('is_active', 'discount_type', 'valid_from', 'valid_to')
    search_fields = ('code',)
    list_editable = ('is_active', 'max_use')
    filter_horizontal = ('products', 'categories', 'users')
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('code', 'discount_type', 'discount_value')
        }),
        ('شرایط', {
            'fields': ('min_purchase', 'max_discount', 'valid_from', 'valid_to')
        }),
        ('محدودیت‌ها', {
            'fields': ('max_use', 'is_unlimited', 'is_active')
        }),
        ('مشمولیت‌ها', {
            'fields': ('products', 'categories', 'users')
        }),
    )
    
    def is_valid_display(self, obj):
        return "✅ معتبر" if obj.is_valid else "❌ نامعتبر"
    is_valid_display.short_description = 'وضعیت'


# ============================================
# ادمین تصاویر محصول
# ============================================

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_main', 'order')
    list_filter = ('is_main',)
    list_editable = ('is_main', 'order')


# ============================================
# ادمین نظرات
# ============================================

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_verified', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at')
    list_editable = ('is_verified',)
    search_fields = ('comment', 'user__username', 'product__name')


# ============================================
# ادمین سفارشات
# ============================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total', 'status', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid', 'payment_method', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_email', 'user__username', 'user__email', 'phone')
    list_editable = ('status',)
    readonly_fields = ('order_number', 'customer_name', 'customer_email', 'created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('order_number', 'user', 'customer_name', 'customer_email', 'status', 'is_paid')
        }),
        ('قیمت‌ها', {
            'fields': ('subtotal', 'discount', 'shipping_cost', 'total')
        }),
        ('کد تخفیف', {
            'fields': ('coupon', 'coupon_discount')
        }),
        ('اطلاعات تحویل', {
            'fields': ('address', 'postal_code', 'phone', 'note')
        }),
        ('پرداخت', {
            'fields': ('payment_method', 'payment_id', 'paid_at')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# ادمین آیتم‌های سفارش
# ============================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'price', 'total')
    search_fields = ('product_name', 'order__order_number')
    list_filter = ('order',)


# ============================================
# ادمین علاقه‌مندی‌ها
# ============================================

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')


# ============================================
# ادمین تنظیمات سایت
# ============================================

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'primary_color', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('site_name', 'site_title', 'site_description')
    readonly_fields = ('created_at', 'updated_at', 'customizer_rules', 'customizer_theme')
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('site_name', 'site_title', 'site_description', 'is_active')
        }),
        ('لوگو و تصاویر', {
            'fields': ('logo', 'favicon', 'default_product_image', 'default_avatar', 'background_image')
        }),
        ('رنگ‌بندی', {
            'fields': ('primary_color', 'secondary_color', 'accent_color', 'background_color', 'text_color')
        }),
        ('فوتر', {
            'fields': ('footer_text', 'footer_bg_color')
        }),
        ('اطلاعات تماس', {
            'fields': ('phone', 'email', 'address')
        }),
        ('شبکه‌های اجتماعی', {
            'fields': ('instagram', 'telegram', 'whatsapp', 'youtube')
        }),
        ('ویرایشگر بصری', {
            'fields': ('customizer_rules', 'customizer_theme'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email',)
    list_editable = ('is_active',)
    ordering = ('-created_at',)


# ============================================
# ادمین اسلایدر
# ============================================

@admin.register(SliderImage)
class SliderImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    list_editable = ('order', 'is_active')
    ordering = ('order',)


# ============================================
# ===== ادمین دسترسی‌ها (نهایی) =====
# ============================================

if not admin.site.is_registered(AdminPermission):
    @admin.register(AdminPermission)
    class AdminPermissionAdmin(admin.ModelAdmin):
        list_display = ('name', 'label', 'is_active', 'created_at')
        list_filter = ('is_active',)
        search_fields = ('label', 'name', 'description')
        list_editable = ('is_active',)

if not admin.site.is_registered(AdminRole):
    @admin.register(AdminRole)
    class AdminRoleAdmin(admin.ModelAdmin):
        list_display = ('display_name', 'name', 'is_default', 'is_active', 'created_at')
        list_filter = ('is_active', 'is_default', 'name')
        search_fields = ('display_name', 'description')
        filter_horizontal = ('permissions',)
        list_editable = ('is_active', 'is_default')

if not admin.site.is_registered(AdminUserPermission):
    @admin.register(AdminUserPermission)
    class AdminUserPermissionAdmin(admin.ModelAdmin):
        list_display = ('user', 'permission', 'is_allowed', 'created_at')
        list_filter = ('is_allowed',)
        search_fields = ('user__username', 'permission__label')
        list_editable = ('is_allowed',)
        raw_id_fields = ('user', 'permission')