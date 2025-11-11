from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time, date
from decimal import Decimal
from ecommerce.models import (
    Category, SubCategory, MealPeriod, FoodItem, 
    DailyMenu, DailyMenuItem, StudentProfile, MessStaff, SystemSettings
)


class Command(BaseCommand):
    help = 'Seeds the database with Muranga University mess system data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        # Create users
        self.create_users()
        
        # Create meal periods
        self.create_meal_periods()
        
        # Create categories and subcategories
        self.create_categories()
        
        # Create food items
        self.create_food_items()
        
        # Create student profiles
        self.create_student_profiles()
        
        # Create mess staff
        self.create_mess_staff()
        
        # Create system settings
        self.create_system_settings()
        
        # Create sample daily menu
        self.create_sample_menu()
        
        self.stdout.write(self.style.SUCCESS('✓ Data seeding completed successfully!'))

    def create_users(self):
        self.stdout.write('Creating users...')
        
        # Admin/IT user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@mut.ac.ke',
                password='admin123',
                first_name='John',
                last_name='Kamau'
            )
        
        # Sample students
        students_data = [
            ('SC211-0530-2022', 'Faith', 'Wanjiru', 'faith.wanjiru'),
            ('SC211-0531-2022', 'Peter', 'Mwangi', 'peter.mwangi'),
            ('SC211-0532-2022', 'Mary', 'Njeri', 'mary.njeri'),
            ('SC211-0533-2022', 'James', 'Kariuki', 'james.kariuki'),
            ('SC211-0534-2022', 'Lucy', 'Wambui', 'lucy.wambui'),
        ]
        
        for reg_no, first, last, username in students_data:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f'{username}@students.mut.ac.ke',
                    password='student123',
                    first_name=first,
                    last_name=last
                )
        
        # Staff users
        staff_data = [
            ('attendant1', 'Grace', 'Muthoni', 'grace.muthoni@mut.ac.ke'),
            ('chef1', 'David', 'Omondi', 'david.omondi@mut.ac.ke'),
            ('manager1', 'Sarah', 'Wangari', 'sarah.wangari@mut.ac.ke'),
        ]
        
        for username, first, last, email in staff_data:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=email,
                    password='staff123',
                    first_name=first,
                    last_name=last
                )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Users created'))

    def create_meal_periods(self):
        self.stdout.write('Creating meal periods...')
        
        periods = [
            {
                'name': 'breakfast',
                'start_time': time(6, 0),
                'end_time': time(10, 0),
                'ordering_start_time': time(4, 0),
                'ordering_end_time': time(9, 0),
                'serving_start_time': time(6, 30),
                'serving_end_time': time(10, 0),
            },
            {
                'name': 'lunch',
                'start_time': time(12, 0),
                'end_time': time(15, 0),
                'ordering_start_time': time(4, 0),
                'ordering_end_time': time(14, 0),
                'serving_start_time': time(12, 30),
                'serving_end_time': time(15, 0),
            },
            {
                'name': 'supper',
                'start_time': time(18, 0),
                'end_time': time(21, 0),
                'ordering_start_time': time(4, 0),
                'ordering_end_time': time(20, 0),
                'serving_start_time': time(18, 30),
                'serving_end_time': time(21, 0),
            },
        ]
        
        for period_data in periods:
            MealPeriod.objects.get_or_create(
                name=period_data['name'],
                defaults=period_data
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Meal periods created'))

    def create_categories(self):
        self.stdout.write('Creating categories and subcategories...')
        
        categories_data = [
            {
                'name': 'Main Dishes',
                'icon': 'bi-bowl-hot-fill',
                'description': 'Primary meal options',
                'display_order': 1,
                'subcategories': [
                    'Rice Dishes',
                    'Ugali Options',
                    'Chapati & Bread',
                    'Other Carbs'
                ]
            },
            {
                'name': 'Proteins',
                'icon': 'bi-egg-fried',
                'description': 'Meat, beans, and protein sources',
                'display_order': 2,
                'subcategories': [
                    'Beef',
                    'Chicken',
                    'Fish',
                    'Beans & Legumes',
                    'Eggs'
                ]
            },
            {
                'name': 'Vegetables',
                'icon': 'bi-carrot',
                'description': 'Vegetable sides and salads',
                'display_order': 3,
                'subcategories': [
                    'Cooked Vegetables',
                    'Traditional Greens',
                    'Salads'
                ]
            },
            {
                'name': 'Beverages',
                'icon': 'bi-cup-hot-fill',
                'description': 'Drinks and beverages',
                'display_order': 4,
                'subcategories': [
                    'Hot Drinks',
                    'Cold Drinks',
                    'Traditional Drinks'
                ]
            },
            {
                'name': 'Breakfast Specials',
                'icon': 'bi-sunrise-fill',
                'description': 'Breakfast specific items',
                'display_order': 5,
                'subcategories': [
                    'Porridge',
                    'Bread & Spreads',
                    'Breakfast Proteins'
                ]
            },
        ]
        
        for cat_data in categories_data:
            subcats = cat_data.pop('subcategories', [])
            category, _ = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            
            for i, subcat_name in enumerate(subcats):
                SubCategory.objects.get_or_create(
                    category=category,
                    name=subcat_name,
                    defaults={'display_order': i}
                )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Categories created'))

    def create_food_items(self):
        self.stdout.write('Creating food items...')
        
        # Get categories
        main_dishes = Category.objects.get(name='Main Dishes')
        proteins = Category.objects.get(name='Proteins')
        vegetables = Category.objects.get(name='Vegetables')
        beverages = Category.objects.get(name='Beverages')
        breakfast = Category.objects.get(name='Breakfast Specials')
        
        # Get subcategories
        rice_dishes = SubCategory.objects.get(name='Rice Dishes')
        ugali = SubCategory.objects.get(name='Ugali Options')
        chapati = SubCategory.objects.get(name='Chapati & Bread')
        beef_sub = SubCategory.objects.get(name='Beef')
        chicken_sub = SubCategory.objects.get(name='Chicken')
        beans_sub = SubCategory.objects.get(name='Beans & Legumes')
        cooked_veg = SubCategory.objects.get(name='Cooked Vegetables')
        greens = SubCategory.objects.get(name='Traditional Greens')
        hot_drinks = SubCategory.objects.get(name='Hot Drinks')
        porridge_sub = SubCategory.objects.get(name='Porridge')
        
        food_items = [
            # Main Dishes
            {'category': main_dishes, 'subcategory': rice_dishes, 'name': 'Plain Rice', 'price': Decimal('50.00')},
            {'category': main_dishes, 'subcategory': rice_dishes, 'name': 'Pilau', 'price': Decimal('70.00')},
            {'category': main_dishes, 'subcategory': rice_dishes, 'name': 'Fried Rice', 'price': Decimal('60.00')},
            {'category': main_dishes, 'subcategory': ugali, 'name': 'Ugali', 'price': Decimal('30.00')},
            {'category': main_dishes, 'subcategory': chapati, 'name': 'Chapati (2 pcs)', 'price': Decimal('40.00')},
            {'category': main_dishes, 'subcategory': chapati, 'name': 'Mandazi (2 pcs)', 'price': Decimal('30.00')},
            {'category': main_dishes, 'subcategory': None, 'name': 'Githeri', 'price': Decimal('45.00')},
            {'category': main_dishes, 'subcategory': None, 'name': 'Mukimo', 'price': Decimal('50.00')},
            
            # Proteins
            {'category': proteins, 'subcategory': beef_sub, 'name': 'Beef Stew', 'price': Decimal('80.00')},
            {'category': proteins, 'subcategory': beef_sub, 'name': 'Beef Fry', 'price': Decimal('90.00')},
            {'category': proteins, 'subcategory': chicken_sub, 'name': 'Chicken Stew', 'price': Decimal('100.00')},
            {'category': proteins, 'subcategory': chicken_sub, 'name': 'Fried Chicken', 'price': Decimal('120.00')},
            {'category': proteins, 'subcategory': beans_sub, 'name': 'Beans', 'price': Decimal('40.00')},
            {'category': proteins, 'subcategory': beans_sub, 'name': 'Green Grams', 'price': Decimal('45.00')},
            {'category': proteins, 'subcategory': beans_sub, 'name': 'Ndengu', 'price': Decimal('45.00')},
            {'category': proteins, 'subcategory': None, 'name': 'Fish (Tilapia)', 'price': Decimal('110.00')},
            {'category': proteins, 'subcategory': None, 'name': 'Omena', 'price': Decimal('60.00')},
            {'category': proteins, 'subcategory': None, 'name': 'Boiled Eggs (2 pcs)', 'price': Decimal('40.00')},
            
            # Vegetables
            {'category': vegetables, 'subcategory': cooked_veg, 'name': 'Cabbage', 'price': Decimal('30.00')},
            {'category': vegetables, 'subcategory': cooked_veg, 'name': 'Carrots', 'price': Decimal('30.00')},
            {'category': vegetables, 'subcategory': cooked_veg, 'name': 'Mixed Vegetables', 'price': Decimal('35.00')},
            {'category': vegetables, 'subcategory': greens, 'name': 'Sukuma Wiki', 'price': Decimal('25.00')},
            {'category': vegetables, 'subcategory': greens, 'name': 'Managu', 'price': Decimal('30.00')},
            {'category': vegetables, 'subcategory': greens, 'name': 'Terere', 'price': Decimal('30.00')},
            
            # Beverages
            {'category': beverages, 'subcategory': hot_drinks, 'name': 'Tea', 'price': Decimal('20.00')},
            {'category': beverages, 'subcategory': hot_drinks, 'name': 'Coffee', 'price': Decimal('25.00')},
            {'category': beverages, 'subcategory': hot_drinks, 'name': 'Cocoa', 'price': Decimal('30.00')},
            {'category': beverages, 'subcategory': None, 'name': 'Soda (500ml)', 'price': Decimal('50.00')},
            {'category': beverages, 'subcategory': None, 'name': 'Juice', 'price': Decimal('40.00')},
            {'category': beverages, 'subcategory': None, 'name': 'Drinking Water', 'price': Decimal('20.00')},
            
            # Breakfast
            {'category': breakfast, 'subcategory': porridge_sub, 'name': 'Uji (Porridge)', 'price': Decimal('25.00')},
            {'category': breakfast, 'subcategory': porridge_sub, 'name': 'Porridge (Wimbi)', 'price': Decimal('30.00')},
            {'category': breakfast, 'subcategory': None, 'name': 'Bread (4 slices)', 'price': Decimal('30.00')},
            {'category': breakfast, 'subcategory': None, 'name': 'Blue Band', 'price': Decimal('10.00')},
        ]
        
        for item_data in food_items:
            FoodItem.objects.get_or_create(
                category=item_data['category'],
                name=item_data['name'],
                defaults={
                    'subcategory': item_data.get('subcategory'),
                    'price_per_plate': item_data['price'],
                    'is_available': True,
                    'is_active': True,
                }
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Food items created'))

    def create_student_profiles(self):
        self.stdout.write('Creating student profiles...')
        
        students_data = [
            {
                'username': 'faith.wanjiru',
                'reg_no': 'SC211-0530-2022',
                'phone': '+254712345678',
                'course': 'Bachelor of Science in Computer Science',
                'year': 3
            },
            {
                'username': 'peter.mwangi',
                'reg_no': 'SC211-0531-2022',
                'phone': '+254723456789',
                'course': 'Bachelor of Science in Information Technology',
                'year': 3
            },
            {
                'username': 'mary.njeri',
                'reg_no': 'SC211-0532-2022',
                'phone': '+254734567890',
                'course': 'Bachelor of Business Information Technology',
                'year': 3
            },
            {
                'username': 'james.kariuki',
                'reg_no': 'SC211-0533-2022',
                'phone': '+254745678901',
                'course': 'Bachelor of Science in Software Engineering',
                'year': 3
            },
            {
                'username': 'lucy.wambui',
                'reg_no': 'SC211-0534-2022',
                'phone': '+254756789012',
                'course': 'Bachelor of Science in Computer Science',
                'year': 3
            },
        ]
        
        for student_data in students_data:
            user = User.objects.get(username=student_data['username'])
            StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'registration_number': student_data['reg_no'],
                    'phone_number': student_data['phone'],
                    'course': student_data['course'],
                    'year_of_study': student_data['year'],
                    'is_active': True,
                }
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Student profiles created'))

    def create_mess_staff(self):
        self.stdout.write('Creating mess staff...')
        
        staff_data = [
            {
                'username': 'admin',
                'role': 'it_admin',
                'employee_id': 'MUT-IT-001',
                'phone': '+254700000001'
            },
            {
                'username': 'attendant1',
                'role': 'attendant',
                'employee_id': 'MUT-ATT-001',
                'phone': '+254700000002'
            },
            {
                'username': 'chef1',
                'role': 'chef',
                'employee_id': 'MUT-CHF-001',
                'phone': '+254700000003'
            },
            {
                'username': 'manager1',
                'role': 'manager',
                'employee_id': 'MUT-MGR-001',
                'phone': '+254700000004'
            },
        ]
        
        for staff in staff_data:
            user = User.objects.get(username=staff['username'])
            MessStaff.objects.get_or_create(
                user=user,
                defaults={
                    'role': staff['role'],
                    'employee_id': staff['employee_id'],
                    'phone_number': staff['phone'],
                    'is_active': True,
                }
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Mess staff created'))

    def create_system_settings(self):
        self.stdout.write('Creating system settings...')
        
        settings = [
            {
                'key': 'mpesa_paybill',
                'value': '174379',
                'description': 'M-Pesa PayBill number for payments'
            },
            {
                'key': 'mpesa_consumer_key',
                'value': 'your_consumer_key',
                'description': 'Safaricom M-Pesa API Consumer Key'
            },
            {
                'key': 'mpesa_consumer_secret',
                'value': 'your_consumer_secret',
                'description': 'Safaricom M-Pesa API Consumer Secret'
            },
            {
                'key': 'mess_location',
                'value': 'Muranga University of Technology Main Campus',
                'description': 'Physical location of the mess'
            },
            {
                'key': 'order_expiry_hours',
                'value': '24',
                'description': 'Hours before unpaid orders expire'
            },
            {
                'key': 'max_plates_per_item',
                'value': '5',
                'description': 'Maximum plates per food item per order'
            },
            {
                'key': 'enable_guest_orders',
                'value': 'true',
                'description': 'Allow non-registered students to order'
            },
        ]
        
        for setting in settings:
            SystemSettings.objects.get_or_create(
                key=setting['key'],
                defaults={
                    'value': setting['value'],
                    'description': setting['description'],
                    'is_active': True,
                }
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ System settings created'))

    def create_sample_menu(self):
        self.stdout.write('Creating sample daily menu...')
        
        today = timezone.now().date()
        lunch_period = MealPeriod.objects.get(name='lunch')
        admin_user = User.objects.get(username='admin')
        
        # Create daily menu
        daily_menu, created = DailyMenu.objects.get_or_create(
            date=today,
            meal_period=lunch_period,
            defaults={
                'is_active': True,
                'is_published': True,
                'created_by': admin_user,
                'notes': 'Special lunch menu for today'
            }
        )
        
        if created:
            # Add menu items
            menu_items = [
                {'food': 'Plain Rice', 'sufurias': 5, 'plates_per': 20},
                {'food': 'Beef Stew', 'sufurias': 3, 'plates_per': 25},
                {'food': 'Cabbage', 'sufurias': 4, 'plates_per': 30},
                {'food': 'Sukuma Wiki', 'sufurias': 4, 'plates_per': 30},
                {'food': 'Chapati (2 pcs)', 'sufurias': 6, 'plates_per': 20},
                {'food': 'Beans', 'sufurias': 3, 'plates_per': 25},
            ]
            
            for item_data in menu_items:
                food_item = FoodItem.objects.get(name=item_data['food'])
                DailyMenuItem.objects.create(
                    daily_menu=daily_menu,
                    food_item=food_item,
                    sufuria_count=item_data['sufurias'],
                    plates_per_sufuria=item_data['plates_per'],
                    is_available=True
                )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Sample menu created'))