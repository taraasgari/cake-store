from django.urls import path

from . import views


app_name = 'customer_care'


urlpatterns = [
    path(
        'order-track/',
        views.order_tracking,
        name='order_tracking',
    ),

    path(
        'support/',
        views.support_home,
        name='support_home',
    ),
    path(
        'support/new/',
        views.support_create,
        name='support_create',
    ),
    path(
        'support/<str:reference>/',
        views.support_detail,
        name='support_detail',
    ),
    path(
        'support/<str:reference>/reply/',
        views.support_reply,
        name='support_reply',
    ),

    path(
        'returns/',
        views.order_actions_home,
        name='order_actions_home',
    ),
    path(
        'returns/<int:pk>/',
        views.order_action_detail,
        name='order_action_detail',
    ),
    path(
        'order/<str:order_number>/cancel-request/',
        views.cancel_order_request,
        name='cancel_order_request',
    ),
    path(
        'order/<str:order_number>/return-request/',
        views.return_order_request,
        name='return_order_request',
    ),

    path(
        'admin-panel/support/',
        views.admin_support_list,
        name='admin_support_list',
    ),
    path(
        'admin-panel/support/<str:reference>/',
        views.admin_support_detail,
        name='admin_support_detail',
    ),
    path(
        'admin-panel/support/<str:reference>/reply/',
        views.admin_support_reply,
        name='admin_support_reply',
    ),
    path(
        'admin-panel/support/<str:reference>/status/',
        views.admin_support_status,
        name='admin_support_status',
    ),

    path(
        'admin-panel/returns/',
        views.admin_order_actions_list,
        name='admin_order_actions_list',
    ),
    path(
        'admin-panel/returns/<int:pk>/',
        views.admin_order_action_detail,
        name='admin_order_action_detail',
    ),
    path(
        'admin-panel/returns/<int:pk>/update/',
        views.admin_order_action_update,
        name='admin_order_action_update',
    ),
]
