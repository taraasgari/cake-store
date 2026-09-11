from django.urls import path
from . import views
from .analytics_views import (
    analytics_dashboard,
    analytics_export_csv,
    analytics_pdf_preview,
    analytics_download_pdf,
)

app_name = 'first'

urlpatterns = [
    # ===== صفحات اصلی =====
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path(
        'customer-service/<slug:page_slug>/',
        views.customer_service_page,
        name='customer_service',
    ),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # ===== پنل مالک =====
    path('owner-panel/', views.owner_panel, name='owner_panel'),
    path('owner-panel/profile-edit/', views.owner_profile_edit, name='owner_profile_edit'),
    path('owner-panel/change-password/', views.owner_change_password, name='owner_change_password'),
    
    # ===== OTP و بازیابی رمز =====
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('set-new-password/', views.set_new_password, name='set_new_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    
    # ===== محصولات =====
    path('products/', views.product_list, name='product_list'),
    path('product/<str:slug>/', views.product_detail, name='product_detail'),
    path('product/review/<int:product_id>/', views.add_review, name='add_review'),
    path('category/<str:slug>/', views.category_products, name='category_products'),
    path('brand/<str:slug>/', views.brand_products, name='brand_products'),
    path('search/', views.search_products, name='search_products'),
    
    # ===== محصولات ویژه =====
    path('best-sellers/', views.best_sellers, name='best_sellers'),
    path('discounts/', views.discounts, name='discounts'),
    
    # ===== سبد خرید =====
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # ===== سفارشات =====
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/', views.user_orders, name='user_orders'),
    
    # ===== علاقه‌مندی‌ها =====
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # ===== پنل مدیریت =====
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/products/', views.admin_products, name='admin_products'),
    path('admin-panel/products/add/', views.admin_add_product, name='admin_add_product'),
    path('admin-panel/products/edit/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),
    path('admin-panel/products/delete/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
    path('admin-panel/product/edit/<int:product_id>/', views.admin_edit_product_from_site, name='admin_edit_product_site'),
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/order/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin-panel/reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-panel/review/verify/<int:review_id>/', views.review_verify, name='review_verify'),
    path('admin-panel/review/delete/<int:review_id>/', views.review_delete, name='review_delete'),
    path('admin-panel/site-settings/', views.site_settings, name='site_settings'),
    path('admin-panel/site-settings/reset/', views.reset_site_settings, name='reset_site_settings'),
    
    # ===== مدیریت ادمین‌ها (فقط مالک) =====
    path('admin-panel/manage-admins/', views.manage_admins, name='manage_admins'),
    path('admin-panel/make-admin/<int:user_id>/', views.make_admin, name='make_admin'),
    path('admin-panel/remove-admin/<int:user_id>/', views.remove_admin, name='remove_admin'),
    path('admin-panel/toggle-user/<int:user_id>/', views.toggle_user_active, name='toggle_user_active'),
    
    # ===== مدیریت دسترسی ادمین‌ها (فقط مالک) =====
    path('admin-panel/manage-permissions/', views.manage_admin_permissions, name='manage_admin_permissions'),
    path('admin-panel/toggle-permission/<int:user_id>/<int:permission_id>/', views.toggle_admin_permission, name='toggle_admin_permission'),
    
# ===== مدیریت Ajax =====
path(
    'admin-panel/category/add/',
    views.ajax_add_category,
    name='ajax_add_category',
),
path(
    'admin-panel/category/delete/<int:item_id>/',
    views.ajax_delete_category,
    name='ajax_delete_category',
),
path(
    'admin-panel/brand/add/',
    views.ajax_add_brand,
    name='ajax_add_brand',
),
path(
    'admin-panel/brand/delete/<int:item_id>/',
    views.ajax_delete_brand,
    name='ajax_delete_brand',
),
path(
    'admin-panel/product-type/add/',
    views.ajax_add_product_type,
    name='ajax_add_product_type',
),
path(
    'admin-panel/product-type/delete/<int:item_id>/',
    views.ajax_delete_product_type,
    name='ajax_delete_product_type',
),
path(
    'admin-panel/color/add/',
    views.ajax_add_color,
    name='ajax_add_color',
),
    # ===== انبار (فقط مالک) =====
    path('admin-panel/warehouse/', views.warehouse, name='warehouse'),
    path('admin-panel/warehouse/products/', views.warehouse_products, name='warehouse_products'),
    path('admin-panel/warehouse/update-stock/<int:product_id>/', views.update_stock, name='update_stock'),
    
    # ===== ویرایشگر بصری (فقط مالک) =====
    path('customizer/', views.customizer, name='customizer'),
    path('customizer/save/', views.customizer_save, name='customizer_save'),
    path('customizer/reset/', views.customizer_reset, name='customizer_reset'),
    path('customizer/upload/', views.customizer_upload, name='customizer_upload'),
    path('customizer/product/save/', views.customizer_product_save, name='customizer_product_save'),
    path('customizer/product/delete/<int:product_id>/', views.customizer_product_delete, name='customizer_product_delete'),
    path('admin-panel/load-visual-changes/', views.customizer_load, name='load_visual_changes'),

    # ================================================================
    # ===== آمار و گزارش‌های پیشرفته (فقط مالک) =====
    # ================================================================
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('analytics/export-csv/', analytics_export_csv, name='analytics_export_csv'),
    path('analytics/pdf-preview/', analytics_pdf_preview, name='analytics_pdf_preview'),
    path('analytics/download-pdf/', analytics_download_pdf, name='analytics_download_pdf'),
    path('toggle-number-format/', views.toggle_number_format, name='toggle_number_format'),
    path('settings/number-format/', views.number_format_settings, name='number_format_settings'),
    path('settings/number-format/update/', views.update_number_format, name='update_number_format'),
]
