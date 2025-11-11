from django.urls import path
from . import views


urlpatterns = [
    # Home & Product URLs
    path('', views.index, name='index'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('search/', views.search, name='search'),
    

    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/count/', views.get_cart_count, name='cart_count'),
    
    # Checkout & Order URLs
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order/success/<str:order_code>/', views.order_success, name='order_success'),
    path('order/<str:order_code>/', views.order_detail, name='order_detail'),
    path('my-orders/', views.my_orders, name='my_orders'),
    
    # M-Pesa URLs
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('payment/status/<str:order_code>/', views.check_payment_status, name='check_payment_status'),
    
    # Staff URLs
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/verify-order/', views.verify_order, name='verify_order'),
    
    # API Endpoints
    path('api/check-availability/<int:menu_item_id>/', views.check_item_availability, name='check_item_availability'),
    path('api/meal-period-status/', views.get_meal_period_status, name='meal_period_status'),
    
    # Utility Pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
]