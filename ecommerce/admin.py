from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from .models import (
    Category, SubCategory, FoodItem, MealPeriod, DailyMenu,
    DailyMenuItem, StudentProfile, Order, OrderItem, MPesaTransaction,
    OrderReceipt, MessStaff, SystemSettings
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'display_order', 'subcategory_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'display_order']
    
    def subcategory_count(self, obj):
        return obj.subcategories.count()
    subcategory_count.short_description = 'Subcategories'


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'is_active', 'display_order']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'category__name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'display_order']


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'subcategory', 'price_per_plate', 'is_active', 'is_available', 'display_order']
    list_filter = ['category', 'subcategory', 'is_active', 'is_available', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_available', 'price_per_plate', 'display_order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'subcategory', 'description')
        }),
        ('Pricing & Availability', {
            'fields': ('price_per_plate', 'is_active', 'is_available')
        }),
        ('Display', {
            'fields': ('image', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MealPeriod)
class MealPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time', 'ordering_window', 'serving_window', 'is_active']
    list_filter = ['is_active']
    prepopulated_fields = {'slug': ('name',)}
    
    def ordering_window(self, obj):
        return f"{obj.ordering_start_time.strftime('%H:%M')} - {obj.ordering_end_time.strftime('%H:%M')}"
    ordering_window.short_description = 'Ordering Window'
    
    def serving_window(self, obj):
        return f"{obj.serving_start_time.strftime('%H:%M')} - {obj.serving_end_time.strftime('%H:%M')}"
    serving_window.short_description = 'Serving Window'


class DailyMenuItemInline(admin.TabularInline):
    model = DailyMenuItem
    extra = 1
    fields = ['food_item', 'sufuria_count', 'plates_per_sufuria', 'plates_ordered', 'plates_remaining', 'is_available']
    readonly_fields = ['plates_ordered', 'plates_remaining']


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ['date', 'meal_period', 'is_published', 'is_active', 'total_items', 'total_plates', 'created_by']
    list_filter = ['date', 'meal_period', 'is_published', 'is_active']
    search_fields = ['notes']
    prepopulated_fields = {'slug': ('date', 'meal_period')}
    inlines = [DailyMenuItemInline]
    readonly_fields = ['created_at', 'updated_at']
    
    def total_items(self, obj):
        return obj.menu_items.count()
    total_items.short_description = 'Items'
    
    def total_plates(self, obj):
        total = obj.menu_items.aggregate(Sum('total_plates_available'))['total_plates_available__sum']
        return total or 0
    total_plates.short_description = 'Total Plates'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DailyMenuItem)
class DailyMenuItemAdmin(admin.ModelAdmin):
    list_display = ['daily_menu', 'food_item', 'sufuria_count', 'plates_per_sufuria', 
                    'total_plates_available', 'plates_ordered', 'plates_remaining', 'is_available']
    list_filter = ['daily_menu__date', 'daily_menu__meal_period', 'is_available', 'food_item__category']
    search_fields = ['food_item__name', 'daily_menu__date']
    readonly_fields = ['total_plates_available', 'plates_remaining', 'created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing
            return self.readonly_fields + ['plates_ordered']
        return self.readonly_fields


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'user', 'phone_number', 'course', 'year_of_study', 'is_active', 'order_count']
    list_filter = ['year_of_study', 'is_active', 'created_at']
    search_fields = ['registration_number', 'user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number']
    prepopulated_fields = {'slug': ('registration_number',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def order_count(self, obj):
        return obj.orders.count()
    order_count.short_description = 'Orders'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['food_item', 'quantity', 'price_per_plate', 'subtotal']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'student_info', 'daily_menu', 'total_amount', 'status_badge', 
                    'payment_status', 'ordered_at', 'is_expired_badge']
    list_filter = ['status', 'daily_menu__date', 'daily_menu__meal_period', 'ordered_at']
    search_fields = ['order_code', 'user__username', 'guest_registration_number', 'guest_name', 
                     'mpesa_receipt_number', 'mpesa_transaction_id']
    readonly_fields = ['order_code', 'slug', 'ordered_at', 'confirmed_at', 'served_at', 
                      'payment_date', 'expires_at', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_code', 'slug', 'daily_menu', 'total_amount', 'status')
        }),
        ('Student Information', {
            'fields': ('user', 'student_profile', 'guest_registration_number', 'guest_name', 'guest_phone')
        }),
        ('Payment Information', {
            'fields': ('mpesa_phone_number', 'mpesa_transaction_id', 'mpesa_receipt_number', 'payment_date')
        }),
        ('Order Lifecycle', {
            'fields': ('ordered_at', 'confirmed_at', 'served_at', 'served_by', 'expires_at')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_info(self, obj):
        return obj.get_student_identifier()
    student_info.short_description = 'Student'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'paid': '#17a2b8',
            'confirmed': '#28a745',
            'ready': '#007bff',
            'served': '#6c757d',
            'expired': '#dc3545',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status(self, obj):
        if obj.mpesa_receipt_number:
            return format_html('<span style="color: green;">✓ Paid</span>')
        return format_html('<span style="color: orange;">⊗ Pending</span>')
    payment_status.short_description = 'Payment'
    
    def is_expired_badge(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        return format_html('<span style="color: green;">✓ Active</span>')
    is_expired_badge.short_description = 'Validity'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'food_item', 'quantity', 'price_per_plate', 'subtotal']
    list_filter = ['order__daily_menu__date', 'food_item__category']
    search_fields = ['order__order_code', 'food_item__name']
    readonly_fields = ['subtotal', 'created_at']


@admin.register(MPesaTransaction)
class MPesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['merchant_request_id', 'order', 'phone_number', 'amount', 'status_badge', 
                    'mpesa_receipt_number', 'transaction_date']
    list_filter = ['status', 'transaction_date', 'created_at']
    search_fields = ['merchant_request_id', 'checkout_request_id', 'mpesa_receipt_number', 
                     'phone_number', 'order__order_code']
    readonly_fields = ['created_at', 'updated_at']
    
    def status_badge(self, obj):
        colors = {
            'initiated': '#ffc107',
            'pending': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(OrderReceipt)
class OrderReceiptAdmin(admin.ModelAdmin):
    list_display = ['order', 'receipt_type', 'recipient_email', 'recipient_phone', 'is_sent', 'sent_at']
    list_filter = ['receipt_type', 'is_sent', 'sent_at']
    search_fields = ['order__order_code', 'recipient_email', 'recipient_phone']
    readonly_fields = ['sent_at', 'created_at']


@admin.register(MessStaff)
class MessStaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'employee_id', 'phone_number', 'is_active']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'employee_id', 'phone_number']
    prepopulated_fields = {'slug': ('employee_id',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['key', 'value', 'description']
    
    def value_preview(self, obj):
        return obj.value[:100] + '...' if len(obj.value) > 100 else obj.value
    value_preview.short_description = 'Value'


# Customize admin site
admin.site.site_header = 'Muranga University Mess System'
admin.site.site_title = 'Mess Admin'
admin.site.index_title = 'Welcome to Mess Administration'