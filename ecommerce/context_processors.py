"""
Context processors for making data available across all templates
"""
from django.utils import timezone
from .models import Category, MealPeriod, DailyMenu


def site_context(request):
    """
    Make common site data available to all templates
    """
    # Get all active categories with their subcategories
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    
    # Get current meal period
    current_time = timezone.now().time()
    current_meal_period = None
    try:
        current_meal_period = MealPeriod.objects.filter(
            is_active=True,
            start_time__lte=current_time,
            end_time__gte=current_time
        ).first()
    except MealPeriod.DoesNotExist:
        pass
    
    # Get today's active menu
    today = timezone.now().date()
    todays_menu = None
    if current_meal_period:
        try:
            todays_menu = DailyMenu.objects.filter(
                date=today,
                meal_period=current_meal_period,
                is_published=True,
                is_active=True
            ).first()
        except DailyMenu.DoesNotExist:
            pass
    
    # Get cart count from session
    cart = request.session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values())
    
    # Check if ordering is currently allowed
    ordering_allowed = False
    if todays_menu and current_meal_period:
        ordering_allowed = todays_menu.is_ordering_allowed()
    
    return {
        'site_name': 'Muranga University Food Mess',
        'site_short_name': 'MUT Mess',
        'categories': categories,
        'current_meal_period': current_meal_period,
        'todays_menu': todays_menu,
        'cart_count': cart_count,
        'ordering_allowed': ordering_allowed,
        'current_year': timezone.now().year,
    }