from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from decimal import Decimal
import json
import requests
import base64
from datetime import datetime, timedelta

from .models import (
    Category, SubCategory, FoodItem, MealPeriod, DailyMenu, 
    DailyMenuItem, Order, OrderItem, StudentProfile, MPesaTransaction,
    OrderReceipt, MessStaff
)


# ==================== AUTHENTICATION VIEWS ====================

def register(request):
    """Student registration view"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        registration_number = request.POST.get('registration_number', '').strip().upper()
        phone_number = request.POST.get('phone_number', '').strip()
        course = request.POST.get('course', '').strip()
        year_of_study = request.POST.get('year_of_study', '')
        
        # Validation
        errors = []
        
        if not all([username, email, password1, password2, registration_number, phone_number]):
            errors.append("All required fields must be filled.")
        
        if password1 != password2:
            errors.append("Passwords do not match.")
        
        if len(password1) < 6:
            errors.append("Password must be at least 6 characters.")
        
        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        
        if User.objects.filter(email=email).exists():
            errors.append("Email already registered.")
        
        if StudentProfile.objects.filter(registration_number=registration_number).exists():
            errors.append("Registration number already registered.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'accounts/register.html', {'data': request.POST})
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create student profile
            StudentProfile.objects.create(
                user=user,
                registration_number=registration_number,
                phone_number=phone_number,
                course=course,
                year_of_study=int(year_of_study) if year_of_study else None
            )
            
            # Send welcome email
            try:
                send_mail(
                    'Welcome to Muranga University Mess System',
                    f'Hello {first_name},\n\nYour account has been created successfully!\n\nRegistration Number: {registration_number}\nUsername: {username}\n\nYou can now login and order your meals.\n\nBest regards,\nMuranga University Mess Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, "Registration successful! Please login to continue.")
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'accounts/register.html', {'data': request.POST})
    
    return render(request, 'accounts/register.html')


def login_view(request):
    """Student login view"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            
            # Redirect to next page or index
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'accounts/login.html', {'username': username})
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('index')


# ==================== HOME & PRODUCT VIEWS ====================

def index(request):
    """Homepage with current meal period and featured items"""
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    # Get current meal period
    current_meal_period = None
    for period in MealPeriod.objects.filter(is_active=True):
        if period.start_time <= current_time <= period.end_time:
            current_meal_period = period
            break
    
    # Get today's menu for current meal period
    current_menu = None
    menu_items = []
    
    if current_meal_period:
        try:
            current_menu = DailyMenu.objects.get(
                date=current_date,
                meal_period=current_meal_period,
                is_published=True,
                is_active=True
            )
            menu_items = current_menu.menu_items.filter(
                is_available=True,
                plates_remaining__gt=0
            ).select_related('food_item', 'food_item__category')
        except DailyMenu.DoesNotExist:
            pass
    
    # Get all active categories
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    
    # Get featured items (items with most orders)
    featured_items = FoodItem.objects.filter(
        is_active=True,
        is_available=True
    ).annotate(
        order_count=Count('order_items')
    ).order_by('-order_count')[:6]
    
    context = {
        'current_meal_period': current_meal_period,
        'current_menu': current_menu,
        'menu_items': menu_items,
        'categories': categories,
        'featured_items': featured_items,
        'can_order': current_menu and current_menu.is_ordering_allowed() if current_menu else False,
    }
    
    return render(request, 'mess/index.html', context)


def product_list(request):
    """List all available food items for current meal period"""
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    # Get current meal period
    current_meal_period = None
    for period in MealPeriod.objects.filter(is_active=True):
        if period.ordering_start_time <= current_time <= period.ordering_end_time:
            current_meal_period = period
            break
    
    if not current_meal_period:
        messages.warning(request, "No meal period is currently accepting orders.")
        return redirect('index')
    
    # Get today's menu
    try:
        current_menu = DailyMenu.objects.get(
            date=current_date,
            meal_period=current_meal_period,
            is_published=True,
            is_active=True
        )
    except DailyMenu.DoesNotExist:
        messages.warning(request, "No menu available for the current meal period.")
        return redirect('index')
    
    # Get filters
    category_slug = request.GET.get('category')
    subcategory_slug = request.GET.get('subcategory')
    search_query = request.GET.get('q', '').strip()
    
    # Get menu items
    menu_items = current_menu.menu_items.filter(
        is_available=True,
        plates_remaining__gt=0
    ).select_related('food_item', 'food_item__category', 'food_item__subcategory')
    
    # Apply filters
    if category_slug:
        menu_items = menu_items.filter(food_item__category__slug=category_slug)
    
    if subcategory_slug:
        menu_items = menu_items.filter(food_item__subcategory__slug=subcategory_slug)
    
    if search_query:
        menu_items = menu_items.filter(
            Q(food_item__name__icontains=search_query) |
            Q(food_item__description__icontains=search_query)
        )
    
    # Get all categories for filter
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    
    context = {
        'menu_items': menu_items,
        'current_menu': current_menu,
        'current_meal_period': current_meal_period,
        'categories': categories,
        'selected_category': category_slug,
        'selected_subcategory': subcategory_slug,
        'search_query': search_query,
        'can_order': current_menu.is_ordering_allowed(),
    }
    
    return render(request, 'mess/product_list.html', context)


def product_detail(request, slug):
    """Detail view for a specific food item"""
    food_item = get_object_or_404(FoodItem, slug=slug, is_active=True)
    
    # Get current menu item if available
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    current_meal_period = None
    for period in MealPeriod.objects.filter(is_active=True):
        if period.ordering_start_time <= current_time <= period.ordering_end_time:
            current_meal_period = period
            break
    
    menu_item = None
    can_order = False
    
    if current_meal_period:
        try:
            current_menu = DailyMenu.objects.get(
                date=current_date,
                meal_period=current_meal_period,
                is_published=True,
                is_active=True
            )
            menu_item = DailyMenuItem.objects.get(
                daily_menu=current_menu,
                food_item=food_item,
                is_available=True
            )
            can_order = current_menu.is_ordering_allowed() and menu_item.plates_remaining > 0
        except (DailyMenu.DoesNotExist, DailyMenuItem.DoesNotExist):
            pass
    
    # Get related items
    related_items = FoodItem.objects.filter(
        category=food_item.category,
        is_active=True,
        is_available=True
    ).exclude(id=food_item.id)[:4]
    
    context = {
        'food_item': food_item,
        'menu_item': menu_item,
        'can_order': can_order,
        'related_items': related_items,
        'current_meal_period': current_meal_period,
    }
    
    return render(request, 'mess/product_detail.html', context)


def category_list(request):
    """List all categories"""
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'mess/category_list.html', context)


def category_detail(request, slug):
    """View items in a specific category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get current meal period and menu
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    current_meal_period = None
    for period in MealPeriod.objects.filter(is_active=True):
        if period.ordering_start_time <= current_time <= period.ordering_end_time:
            current_meal_period = period
            break
    
    menu_items = []
    can_order = False
    
    if current_meal_period:
        try:
            current_menu = DailyMenu.objects.get(
                date=current_date,
                meal_period=current_meal_period,
                is_published=True,
                is_active=True
            )
            menu_items = current_menu.menu_items.filter(
                food_item__category=category,
                is_available=True,
                plates_remaining__gt=0
            ).select_related('food_item', 'food_item__subcategory')
            can_order = current_menu.is_ordering_allowed()
        except DailyMenu.DoesNotExist:
            pass
    
    context = {
        'category': category,
        'menu_items': menu_items,
        'can_order': can_order,
        'current_meal_period': current_meal_period,
    }
    
    return render(request, 'mess/category_detail.html', context)


# ==================== CART VIEWS ====================

def get_cart(request):
    """Get cart from session"""
    return request.session.get('cart', {})


def save_cart(request, cart):
    """Save cart to session"""
    request.session['cart'] = cart
    request.session.modified = True


@require_http_methods(["POST"])
def add_to_cart(request):
    """Add item to cart (AJAX)"""
    try:
        data = json.loads(request.body)
        menu_item_id = data.get('menu_item_id')
        quantity = int(data.get('quantity', 1))
        
        # Validate quantity (only 1 plate per item allowed)
        if quantity != 1:
            return JsonResponse({
                'success': False,
                'message': 'You can only order 1 plate per food item.'
            }, status=400)
        
        # Get menu item
        menu_item = get_object_or_404(DailyMenuItem, id=menu_item_id, is_available=True)
        
        # Check if available
        if menu_item.plates_remaining < 1:
            return JsonResponse({
                'success': False,
                'message': 'This item is out of stock.'
            }, status=400)
        
        # Check if ordering is allowed
        if not menu_item.daily_menu.is_ordering_allowed():
            return JsonResponse({
                'success': False,
                'message': 'Ordering is not allowed at this time.'
            }, status=400)
        
        # Get cart
        cart = get_cart(request)
        
        # Check if item already in cart
        if str(menu_item_id) in cart:
            return JsonResponse({
                'success': False,
                'message': 'This item is already in your cart. You can only order 1 plate per item.'
            }, status=400)
        
        # Add to cart
        cart[str(menu_item_id)] = {
            'menu_item_id': menu_item_id,
            'food_item_id': menu_item.food_item.id,
            'food_item_name': menu_item.food_item.name,
            'food_item_slug': menu_item.food_item.slug,
            'price': str(menu_item.food_item.price_per_plate),
            'quantity': 1,
            'subtotal': str(menu_item.food_item.price_per_plate),
            'daily_menu_id': menu_item.daily_menu.id,
        }
        
        save_cart(request, cart)
        
        # Calculate cart totals
        cart_count = len(cart)
        cart_total = sum(Decimal(item['subtotal']) for item in cart.values())
        
        return JsonResponse({
            'success': True,
            'message': f'{menu_item.food_item.name} added to cart!',
            'cart_count': cart_count,
            'cart_total': str(cart_total)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
def update_cart(request):
    """Update cart item quantity (AJAX) - Not really needed since quantity is always 1"""
    try:
        data = json.loads(request.body)
        menu_item_id = str(data.get('menu_item_id'))
        
        cart = get_cart(request)
        
        if menu_item_id not in cart:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart.'
            }, status=404)
        
        # Since quantity is always 1, this just confirms the item
        return JsonResponse({
            'success': True,
            'message': 'Cart updated!',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
def remove_from_cart(request):
    """Remove item from cart (AJAX)"""
    try:
        data = json.loads(request.body)
        menu_item_id = str(data.get('menu_item_id'))
        
        cart = get_cart(request)
        
        if menu_item_id in cart:
            del cart[menu_item_id]
            save_cart(request, cart)
            
            # Calculate new totals
            cart_count = len(cart)
            cart_total = sum(Decimal(item['subtotal']) for item in cart.values())
            
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart!',
                'cart_count': cart_count,
                'cart_total': str(cart_total)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart.'
            }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def cart_view(request):
    """View cart"""
    cart = get_cart(request)
    cart_items = []
    cart_total = Decimal('0.00')
    
    for item_id, item_data in cart.items():
        try:
            menu_item = DailyMenuItem.objects.select_related('food_item').get(
                id=item_data['menu_item_id']
            )
            
            cart_items.append({
                'menu_item': menu_item,
                'quantity': item_data['quantity'],
                'subtotal': Decimal(item_data['subtotal'])
            })
            cart_total += Decimal(item_data['subtotal'])
        except DailyMenuItem.DoesNotExist:
            continue
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': len(cart_items),
    }
    
    return render(request, 'mess/cart.html', context)


def clear_cart(request):
    """Clear cart"""
    request.session['cart'] = {}
    request.session.modified = True
    messages.success(request, "Cart cleared successfully.")
    return redirect('cart')


# ==================== CHECKOUT & ORDER VIEWS ====================

def checkout(request):
    """Checkout page"""
    cart = get_cart(request)
    
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('product_list')
    
    # Get cart items and validate
    cart_items = []
    cart_total = Decimal('0.00')
    daily_menu = None
    
    for item_id, item_data in cart.items():
        try:
            menu_item = DailyMenuItem.objects.select_related(
                'food_item', 'daily_menu', 'daily_menu__meal_period'
            ).get(id=item_data['menu_item_id'])
            
            # Validate availability
            if not menu_item.is_available or menu_item.plates_remaining < 1:
                messages.error(request, f"{menu_item.food_item.name} is no longer available.")
                return redirect('cart')
            
            # Validate ordering time
            if not menu_item.daily_menu.is_ordering_allowed():
                messages.error(request, "Ordering time has expired for these items.")
                return redirect('cart')
            
            # Set daily menu (all items should be from same menu)
            if daily_menu is None:
                daily_menu = menu_item.daily_menu
            elif daily_menu.id != menu_item.daily_menu.id:
                messages.error(request, "Cart contains items from different meal periods.")
                return redirect('cart')
            
            cart_items.append({
                'menu_item': menu_item,
                'quantity': item_data['quantity'],
                'subtotal': Decimal(item_data['subtotal'])
            })
            cart_total += Decimal(item_data['subtotal'])
            
        except DailyMenuItem.DoesNotExist:
            continue
    
    # Get student info if logged in
    student_profile = None
    if request.user.is_authenticated:
        try:
            student_profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            pass
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'daily_menu': daily_menu,
        'student_profile': student_profile,
    }
    
    return render(request, 'mess/checkout.html', context)


@require_http_methods(["POST"])
def place_order(request):
    """Place order and initiate M-Pesa payment"""
    try:
        cart = get_cart(request)
        
        if not cart:
            return JsonResponse({
                'success': False,
                'message': 'Your cart is empty.'
            }, status=400)
        
        # Get form data
        phone_number = request.POST.get('phone_number', '').strip()
        registration_number = request.POST.get('registration_number', '').strip().upper()
        full_name = request.POST.get('full_name', '').strip()
        
        if not all([phone_number, registration_number, full_name]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            }, status=400)
        
        # Validate phone number format (254...)
        if not phone_number.startswith('254') or len(phone_number) != 12:
            return JsonResponse({
                'success': False,
                'message': 'Phone number must be in format 254XXXXXXXXX'
            }, status=400)
        
        # Create order
        daily_menu = None
        order_total = Decimal('0.00')
        
        # Validate cart items and calculate total
        for item_id, item_data in cart.items():
            menu_item = DailyMenuItem.objects.select_related('daily_menu').get(
                id=item_data['menu_item_id']
            )
            
            if not menu_item.is_available or menu_item.plates_remaining < 1:
                return JsonResponse({
                    'success': False,
                    'message': f'{menu_item.food_item.name} is no longer available.'
                }, status=400)
            
            if daily_menu is None:
                daily_menu = menu_item.daily_menu
            
            order_total += Decimal(item_data['subtotal'])
        
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            student_profile=request.user.student_profile if request.user.is_authenticated and hasattr(request.user, 'student_profile') else None,
            guest_registration_number=registration_number if not request.user.is_authenticated else '',
            guest_name=full_name if not request.user.is_authenticated else '',
            guest_phone=phone_number if not request.user.is_authenticated else '',
            daily_menu=daily_menu,
            total_amount=order_total,
            mpesa_phone_number=phone_number,
            status='pending'
        )
        
        # Create order items and update stock
        for item_id, item_data in cart.items():
            menu_item = DailyMenuItem.objects.select_related('food_item').get(
                id=item_data['menu_item_id']
            )
            
            OrderItem.objects.create(
                order=order,
                daily_menu_item=menu_item,
                food_item=menu_item.food_item,
                quantity=item_data['quantity'],
                price_per_plate=menu_item.food_item.price_per_plate
            )
            
            # Update stock
            menu_item.plates_ordered += item_data['quantity']
            menu_item.save()
        
        # Initiate M-Pesa STK Push
        mpesa_response = initiate_stk_push(order, phone_number, order_total)
        
        if mpesa_response.get('success'):
            # Clear cart
            request.session['cart'] = {}
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': 'Order placed! Please complete payment on your phone.',
                'order_code': order.order_code,
                'checkout_request_id': mpesa_response.get('checkout_request_id')
            })
        else:
            # Delete order if M-Pesa failed
            order.delete()
            return JsonResponse({
                'success': False,
                'message': mpesa_response.get('message', 'Payment initiation failed.')
            }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ==================== M-PESA INTEGRATION ====================

def get_mpesa_access_token():
    """Get M-Pesa access token"""
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = settings.MPESA_AUTH_URL
    
    try:
        response = requests.get(
            api_url,
            auth=(consumer_key, consumer_secret)
        )
        response.raise_for_status()
        json_response = response.json()
        return json_response.get('access_token')
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None


def initiate_stk_push(order, phone_number, amount):
    """Initiate M-Pesa STK Push"""
    access_token = get_mpesa_access_token()
    
    if not access_token:
        return {
            'success': False,
            'message': 'Failed to authenticate with M-Pesa'
        }
    
    api_url = settings.MPESA_STK_PUSH_URL
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    business_short_code = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    
    # Generate password
    password_string = f"{business_short_code}{passkey}{timestamp}"
    password = base64.b64encode(password_string.encode()).decode('utf-8')
    
    payload = {
        'BusinessShortCode': business_short_code,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': business_short_code,
        'PhoneNumber': phone_number,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': order.order_code,
        'TransactionDesc': f'Muranga Mess Order {order.order_code}'
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        json_response = response.json()
        
        if json_response.get('ResponseCode') == '0':
            # Create M-Pesa transaction record
            MPesaTransaction.objects.create(
                order=order,
                merchant_request_id=json_response.get('MerchantRequestID'),
                checkout_request_id=json_response.get('CheckoutRequestID'),
                phone_number=phone_number,
                amount=amount,
                status='pending'
            )
            
            return {
                'success': True,
                'checkout_request_id': json_response.get('CheckoutRequestID'),
                'merchant_request_id': json_response.get('MerchantRequestID')
            }
        else:
            return {
                'success': False,
                'message': json_response.get('CustomerMessage', 'Payment initiation failed')
            }
    
    except Exception as e:
        print(f"STK Push Error: {e}")
        return {
            'success': False,
            'message': 'Failed to initiate payment. Please try again.'
        }


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """M-Pesa callback URL"""
    try:
        data = json.loads(request.body)
        
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        
        # Get transaction
        try:
            transaction = MPesaTransaction.objects.get(
                checkout_request_id=checkout_request_id
            )
            order = transaction.order
            
            if result_code == 0:
                # Payment successful
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                
                mpesa_receipt = None
                transaction_date = None
                phone_number = None
                
                for item in callback_metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_receipt = item.get('Value')
                    elif item.get('Name') == 'TransactionDate':
                        transaction_date = item.get('Value')
                    elif item.get('Name') == 'PhoneNumber':
                        phone_number = item.get('Value')
                
                # Update transaction
                transaction.status = 'completed'
                transaction.mpesa_receipt_number = mpesa_receipt
                transaction.result_code = str(result_code)
                transaction.result_desc = result_desc
                if transaction_date:
                    transaction.transaction_date = datetime.strptime(str(transaction_date), '%Y%m%d%H%M%S')
                transaction.save()
                
                # Update order
                order.status = 'confirmed'
                order.mpesa_receipt_number = mpesa_receipt
                order.mpesa_transaction_id = merchant_request_id
                order.payment_date = timezone.now()
                order.confirmed_at = timezone.now()
                order.save()
                
                # Send receipt email/SMS
                send_order_receipt(order)
                
            else:
                # Payment failed
                transaction.status = 'failed'
                transaction.result_code = str(result_code)
                transaction.result_desc = result_desc
                transaction.save()
                
                order.status = 'cancelled'
                order.save()
                
                # Restore stock
                for order_item in order.items.all():
                    menu_item = order_item.daily_menu_item
                    menu_item.plates_ordered -= order_item.quantity
                    menu_item.save()
        
        except MPesaTransaction.DoesNotExist:
            print(f"Transaction not found: {checkout_request_id}")
        
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
    
    except Exception as e:
        print(f"Callback error: {e}")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})


@require_http_methods(["GET"])
def check_payment_status(request, order_code):
    """Check payment status (AJAX)"""
    try:
        order = get_object_or_404(Order, order_code=order_code)
        
        return JsonResponse({
            'success': True,
            'status': order.status,
            'status_display': order.get_status_display(),
            'paid': order.status in ['paid', 'confirmed', 'ready', 'served'],
            'mpesa_receipt': order.mpesa_receipt_number or '',
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def mpesa_query_status(checkout_request_id):
    """Query M-Pesa transaction status"""
    access_token = get_mpesa_access_token()
    
    if not access_token:
        return None
    
    api_url = settings.MPESA_QUERY_URL
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    business_short_code = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    
    password_string = f"{business_short_code}{passkey}{timestamp}"
    password = base64.b64encode(password_string.encode()).decode('utf-8')
    
    payload = {
        'BusinessShortCode': business_short_code,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Query status error: {e}")
        return None


def send_order_receipt(order):
    """Send order receipt via email and/or SMS"""
    try:
        # Prepare receipt data
        context = {
            'order': order,
            'order_items': order.items.select_related('food_item'),
            'student_name': order.user.get_full_name() if order.user else order.guest_name,
            'registration_number': order.get_student_identifier(),
        }
        
        # Send email
        if order.user and order.user.email:
            email_html = render_to_string('mess/email/order_receipt.html', context)
            email_text = render_to_string('mess/email/order_receipt.txt', context)
            
            send_mail(
                subject=f'Order Receipt - {order.order_code}',
                message=email_text,
                html_message=email_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=True,
            )
            
            # Create receipt record
            OrderReceipt.objects.create(
                order=order,
                receipt_type='email',
                recipient_email=order.user.email,
                is_sent=True
            )
        
        # TODO: Implement SMS sending via Africa's Talking or similar
        # send_sms(order.mpesa_phone_number, sms_message)
        
    except Exception as e:
        print(f"Error sending receipt: {e}")


# ==================== ORDER MANAGEMENT VIEWS ====================

def order_success(request, order_code):
    """Order success page"""
    order = get_object_or_404(Order, order_code=order_code)
    
    # Verify user owns this order
    if order.user:
        if not request.user.is_authenticated or order.user != request.user:
            messages.error(request, "You don't have permission to view this order.")
            return redirect('index')
    
    context = {
        'order': order,
        'order_items': order.items.select_related('food_item'),
    }
    
    return render(request, 'mess/order_success.html', context)


def order_detail(request, order_code):
    """View order details"""
    order = get_object_or_404(Order, order_code=order_code)
    
    # Verify user owns this order or is staff
    if order.user:
        if not request.user.is_authenticated or (order.user != request.user and not request.user.is_staff):
            messages.error(request, "You don't have permission to view this order.")
            return redirect('index')
    
    context = {
        'order': order,
        'order_items': order.items.select_related('food_item', 'daily_menu_item'),
        'can_be_served': order.can_be_served(),
        'is_expired': order.is_expired(),
    }
    
    return render(request, 'mess/order_detail.html', context)


@login_required
def my_orders(request):
    """View user's orders"""
    try:
        student_profile = request.user.student_profile
        orders = Order.objects.filter(
            Q(user=request.user) | Q(student_profile=student_profile)
        ).select_related('daily_menu', 'daily_menu__meal_period').order_by('-ordered_at')
    except StudentProfile.DoesNotExist:
        orders = Order.objects.filter(user=request.user).select_related(
            'daily_menu', 'daily_menu__meal_period'
        ).order_by('-ordered_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'mess/my_orders.html', context)


# ==================== STAFF VIEWS ====================

@login_required
def verify_order(request):
    """Staff view to verify and serve orders"""
    # Check if user is staff
    try:
        mess_staff = request.user.mess_staff
    except MessStaff.DoesNotExist:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('index')
    
    if request.method == 'POST':
        order_code = request.POST.get('order_code', '').strip().upper()
        
        if not order_code:
            messages.error(request, "Please enter an order code.")
            return render(request, 'mess/verify_order.html')
        
        try:
            order = Order.objects.get(order_code=order_code)
            
            # Check if order can be served
            if order.is_expired():
                messages.error(request, f"Order {order_code} has expired. This meal period has ended.")
                context = {'order': order, 'expired': True}
                return render(request, 'mess/verify_order.html', context)
            
            if order.status == 'served':
                messages.warning(request, f"Order {order_code} has already been served.")
                context = {'order': order, 'already_served': True}
                return render(request, 'mess/verify_order.html', context)
            
            if order.status != 'confirmed':
                messages.error(request, f"Order {order_code} payment is not confirmed.")
                context = {'order': order, 'not_paid': True}
                return render(request, 'mess/verify_order.html', context)
            
            if not order.can_be_served():
                messages.error(request, "This order cannot be served at this time.")
                context = {'order': order}
                return render(request, 'mess/verify_order.html', context)
            
            # Mark as served
            order.mark_as_served(request.user)
            messages.success(request, f"Order {order_code} marked as served successfully!")
            
            context = {
                'order': order,
                'served': True,
                'order_items': order.items.select_related('food_item'),
            }
            return render(request, 'mess/verify_order.html', context)
            
        except Order.DoesNotExist:
            messages.error(request, f"Order {order_code} not found.")
            return render(request, 'mess/verify_order.html')
    
    return render(request, 'mess/verify_order.html')


@login_required
def staff_dashboard(request):
    """Staff dashboard"""
    try:
        mess_staff = request.user.mess_staff
    except MessStaff.DoesNotExist:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('index')
    
    today = timezone.now().date()
    
    # Get today's menus
    todays_menus = DailyMenu.objects.filter(
        date=today,
        is_active=True
    ).select_related('meal_period').prefetch_related('menu_items')
    
    # Get today's orders
    todays_orders = Order.objects.filter(
        daily_menu__date=today
    ).select_related('daily_menu', 'daily_menu__meal_period')
    
    # Statistics
    stats = {
        'total_orders': todays_orders.count(),
        'confirmed_orders': todays_orders.filter(status='confirmed').count(),
        'served_orders': todays_orders.filter(status='served').count(),
        'pending_orders': todays_orders.filter(status='pending').count(),
        'total_revenue': todays_orders.filter(
            status__in=['confirmed', 'served']
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
    }
    
    context = {
        'mess_staff': mess_staff,
        'todays_menus': todays_menus,
        'todays_orders': todays_orders[:10],
        'stats': stats,
    }
    
    return render(request, 'mess/staff_dashboard.html', context)


# ==================== SEARCH & FILTER VIEWS ====================

def search(request):
    """Global search"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        messages.warning(request, "Please enter a search term.")
        return redirect('product_list')
    
    # Get current menu
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    current_meal_period = None
    for period in MealPeriod.objects.filter(is_active=True):
        if period.ordering_start_time <= current_time <= period.ordering_end_time:
            current_meal_period = period
            break
    
    menu_items = []
    current_menu = None
    
    if current_meal_period:
        try:
            current_menu = DailyMenu.objects.get(
                date=current_date,
                meal_period=current_meal_period,
                is_published=True,
                is_active=True
            )
            
            menu_items = current_menu.menu_items.filter(
                Q(food_item__name__icontains=query) |
                Q(food_item__description__icontains=query) |
                Q(food_item__category__name__icontains=query),
                is_available=True,
                plates_remaining__gt=0
            ).select_related('food_item', 'food_item__category')
        except DailyMenu.DoesNotExist:
            pass
    
    context = {
        'query': query,
        'menu_items': menu_items,
        'current_menu': current_menu,
        'current_meal_period': current_meal_period,
    }
    
    return render(request, 'mess/search_results.html', context)


# ==================== API ENDPOINTS ====================

@require_http_methods(["GET"])
def get_cart_count(request):
    """Get cart count (AJAX)"""
    cart = get_cart(request)
    return JsonResponse({
        'count': len(cart)
    })


@require_http_methods(["GET"])
def check_item_availability(request, menu_item_id):
    """Check if item is still available (AJAX)"""
    try:
        menu_item = get_object_or_404(DailyMenuItem, id=menu_item_id)
        
        return JsonResponse({
            'available': menu_item.is_available and menu_item.plates_remaining > 0,
            'plates_remaining': menu_item.plates_remaining,
            'is_ordering_allowed': menu_item.daily_menu.is_ordering_allowed(),
        })
    except Exception as e:
        return JsonResponse({
            'available': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_meal_period_status(request):
    """Get current meal period status (AJAX)"""
    now = timezone.now()
    current_time = now.time()
    
    current_period = None
    for period in MealPeriod.objects.filter(is_active=True):
        if period.start_time <= current_time <= period.end_time:
            current_period = period
            break
    
    if current_period:
        return JsonResponse({
            'has_period': True,
            'period_name': current_period.get_name_display(),
            'is_ordering_open': current_period.is_ordering_open(),
            'is_serving_time': current_period.is_serving_time(),
            'ordering_end_time': current_period.ordering_end_time.strftime('%H:%M'),
        })
    else:
        return JsonResponse({
            'has_period': False,
            'message': 'No active meal period at this time.'
        })


# ==================== UTILITY VIEWS ====================

def about(request):
    """About page"""
    return render(request, 'mess/about.html')


def contact(request):
    """Contact page"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if all([name, email, subject, message]):
            try:
                # Send contact email to admin
                send_mail(
                    subject=f'Contact Form: {subject}',
                    message=f'From: {name} ({email})\n\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, "Your message has been sent successfully!")
                return redirect('contact')
            except Exception as e:
                messages.error(request, "Failed to send message. Please try again.")
        else:
            messages.error(request, "All fields are required.")
    
    return render(request, 'mess/contact.html')


def terms(request):
    """Terms and conditions"""
    return render(request, 'mess/terms.html')


def privacy(request):
    """Privacy policy"""
    return render(request, 'mess/privacy.html')