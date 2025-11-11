from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, RegexValidator
import uuid
from datetime import datetime, time, timedelta


class Category(models.Model):
    """Food categories like Main Dishes, Side Dishes, Beverages"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    """Subcategories like Rice Dishes, Meat Options, Vegetable Sides"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "SubCategories"
        ordering = ['display_order', 'name']
        unique_together = ['category', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.category.name}-{self.name}")
            self.slug = base_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class MealPeriod(models.Model):
    """Breakfast, Lunch, Supper"""
    BREAKFAST = 'breakfast'
    LUNCH = 'lunch'
    SUPPER = 'supper'
    
    PERIOD_CHOICES = [
        (BREAKFAST, 'Breakfast'),
        (LUNCH, 'Lunch'),
        (SUPPER, 'Supper'),
    ]
    
    name = models.CharField(max_length=20, choices=PERIOD_CHOICES, unique=True)
    slug = models.SlugField(max_length=30, unique=True, blank=True)
    start_time = models.TimeField(help_text="When this meal period starts")
    end_time = models.TimeField(help_text="When this meal period ends")
    ordering_start_time = models.TimeField(help_text="When students can start ordering")
    ordering_end_time = models.TimeField(help_text="When ordering closes")
    serving_start_time = models.TimeField(help_text="When meal serving starts")
    serving_end_time = models.TimeField(help_text="When meal serving ends")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_name_display()

    def is_ordering_open(self):
        """Check if ordering is currently open for this meal period"""
        now = timezone.now().time()
        return self.ordering_start_time <= now <= self.ordering_end_time

    def is_serving_time(self):
        """Check if it's currently serving time"""
        now = timezone.now().time()
        return self.serving_start_time <= now <= self.serving_end_time


class FoodItem(models.Model):
    """Individual food items like Rice, Beef, Githeri, Cabbage, Chapati"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='food_items')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='food_items')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    price_per_plate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='food_items/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True, help_text="Currently available for ordering")
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        unique_together = ['category', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.category.slug}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - KES {self.price_per_plate}"


class DailyMenu(models.Model):
    """Daily menu created by IT person at 4:00 AM"""
    date = models.DateField(default=timezone.now)
    meal_period = models.ForeignKey(MealPeriod, on_delete=models.CASCADE, related_name='daily_menus')
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False, help_text="Menu published and visible to students")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_menus')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True, help_text="Special notes for this menu")

    class Meta:
        ordering = ['-date', 'meal_period__start_time']
        unique_together = ['date', 'meal_period']
        verbose_name_plural = "Daily Menus"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.date}-{self.meal_period.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.meal_period.name.title()}"

    def is_ordering_allowed(self):
        """Check if ordering is allowed for this menu"""
        if not self.is_published or not self.is_active:
            return False
        
        # Check if it's the correct date
        if self.date != timezone.now().date():
            return False
        
        # Check if ordering time is open
        return self.meal_period.is_ordering_open()

    def is_served(self):
        """Check if this meal has already been served"""
        now = timezone.now()
        if self.date < now.date():
            return True
        elif self.date == now.date():
            return now.time() > self.meal_period.serving_end_time
        return False


class DailyMenuItem(models.Model):
    """Food items available in a daily menu with quantities"""
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='menu_items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='daily_appearances')
    sufuria_count = models.IntegerField(validators=[MinValueValidator(1)], help_text="Number of sufurias cooked")
    plates_per_sufuria = models.IntegerField(validators=[MinValueValidator(1)], help_text="Estimated plates per sufuria")
    total_plates_available = models.IntegerField(validators=[MinValueValidator(0)], editable=False)
    plates_ordered = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    plates_remaining = models.IntegerField(validators=[MinValueValidator(0)], editable=False)
    is_available = models.BooleanField(default=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['food_item__display_order', 'food_item__name']
        unique_together = ['daily_menu', 'food_item']

    def save(self, *args, **kwargs):
        # Calculate total plates
        self.total_plates_available = self.sufuria_count * self.plates_per_sufuria
        self.plates_remaining = self.total_plates_available - self.plates_ordered
        
        # Auto-disable if no plates remaining
        if self.plates_remaining <= 0:
            self.is_available = False
        
        if not self.slug:
            self.slug = slugify(f"{self.daily_menu.slug}-{self.food_item.slug}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.daily_menu} - {self.food_item.name} ({self.plates_remaining} remaining)"

    def has_stock(self, quantity=1):
        """Check if there's enough stock"""
        return self.is_available and self.plates_remaining >= quantity


class StudentProfile(models.Model):
    """Student profile with registration number"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    registration_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2}\d{3}-\d{4}-\d{4}$',
                message='Registration number must be in format: SC211-0530-2022'
            )
        ],
        help_text="Format: SC211-0530-2022"
    )
    phone_number = models.CharField(max_length=15, blank=True)
    course = models.CharField(max_length=200, blank=True)
    year_of_study = models.IntegerField(blank=True, null=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['registration_number']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.registration_number)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.registration_number} - {self.user.get_full_name() or self.user.username}"


class Order(models.Model):
    """Student food orders"""
    ORDER_STATUS = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('confirmed', 'Confirmed'),
        ('ready', 'Ready for Pickup'),
        ('served', 'Served'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    order_code = models.CharField(max_length=12, unique=True, editable=False, db_index=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    
    # Student info (can be null if guest order)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Guest student info (if not registered)
    guest_registration_number = models.CharField(max_length=20, blank=True)
    guest_name = models.CharField(max_length=200, blank=True)
    guest_phone = models.CharField(max_length=15, blank=True)
    
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='orders')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    
    # M-Pesa Integration
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    mpesa_phone_number = models.CharField(max_length=15, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Order lifecycle
    ordered_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True)
    served_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='served_orders')
    expires_at = models.DateTimeField(editable=False)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-ordered_at']
        indexes = [
            models.Index(fields=['order_code']),
            models.Index(fields=['status', 'daily_menu']),
            models.Index(fields=['guest_registration_number']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = self.generate_order_code()
        
        if not self.slug:
            self.slug = slugify(self.order_code)
        
        # Set expiration time based on meal period serving end time
        if not self.expires_at:
            meal_end_time = datetime.combine(
                self.daily_menu.date,
                self.daily_menu.meal_period.serving_end_time
            )
            self.expires_at = timezone.make_aware(meal_end_time)
        
        super().save(*args, **kwargs)

    def __str__(self):
        student_id = self.get_student_identifier()
        return f"Order {self.order_code} - {student_id} - {self.status}"

    @staticmethod
    def generate_order_code():
        """Generate unique 12-character order code"""
        return str(uuid.uuid4()).replace('-', '').upper()[:12]

    def get_student_identifier(self):
        """Get student registration number"""
        if self.student_profile:
            return self.student_profile.registration_number
        return self.guest_registration_number or 'Guest'

    def is_expired(self):
        """Check if order has expired"""
        return timezone.now() > self.expires_at and self.status not in ['served', 'cancelled']

    def can_be_served(self):
        """Check if order can be served"""
        if self.is_expired():
            return False
        return self.status == 'confirmed' and self.daily_menu.meal_period.is_serving_time()

    def mark_as_served(self, served_by_user):
        """Mark order as served"""
        self.status = 'served'
        self.served_at = timezone.now()
        self.served_by = served_by_user
        self.save()


class OrderItem(models.Model):
    """Individual items in an order (limited to 1 per food item)"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    daily_menu_item = models.ForeignKey(DailyMenuItem, on_delete=models.CASCADE, related_name='order_items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    price_per_plate = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['order', 'food_item']

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.price_per_plate
        
        if not self.slug:
            self.slug = slugify(f"{self.order.order_code}-{self.food_item.slug}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.food_item.name} x{self.quantity} - {self.order.order_code}"


class MPesaTransaction(models.Model):
    """Track M-Pesa transactions"""
    TRANSACTION_STATUS = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='mpesa_transactions')
    merchant_request_id = models.CharField(max_length=100, unique=True)
    checkout_request_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='initiated')
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    result_code = models.CharField(max_length=10, blank=True, null=True)
    result_desc = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['merchant_request_id']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.order.order_code}-{self.checkout_request_id[:20]}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MPesa {self.merchant_request_id} - {self.status}"


class OrderReceipt(models.Model):
    """Receipt/SMS/Email records for orders"""
    RECEIPT_TYPE = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email & SMS'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='receipt')
    receipt_type = models.CharField(max_length=10, choices=RECEIPT_TYPE)
    recipient_email = models.EmailField(blank=True, null=True)
    recipient_phone = models.CharField(max_length=15, blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"receipt-{self.order.order_code}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt for {self.order.order_code}"


class MessStaff(models.Model):
    """IT staff and mess attendants"""
    STAFF_ROLES = [
        ('it_admin', 'IT Administrator'),
        ('attendant', 'Mess Attendant'),
        ('chef', 'Chef'),
        ('manager', 'Mess Manager'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mess_staff')
    role = models.CharField(max_length=20, choices=STAFF_ROLES)
    employee_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Mess Staff"
        ordering = ['role', 'user__first_name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.employee_id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"


class SystemSettings(models.Model):
    """System-wide settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"