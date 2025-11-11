# Muranga University Mess System - Setup Guide

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Load Initial Data

```python
# Create management command: mess/management/commands/setup_initial_data.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time
from mess.models import Category, SubCategory, MealPeriod, MessStaff

class Command(BaseCommand):
    help = 'Setup initial data for the system'

    def handle(self, *args, **kwargs):
        # Create Categories
        main_dishes = Category.objects.create(
            name='Main Dishes',
            description='Rice, Ugali, Chapati',
            icon='bi-bowl-food',
            display_order=1
        )
        
        proteins = Category.objects.create(
            name='Proteins',
            description='Beef, Chicken, Fish, Beans',
            icon='bi-egg-fried',
            display_order=2
        )
        
        vegetables = Category.objects.create(
            name='Vegetables',
            description='Cabbage, Sukuma, Spinach',
            icon='bi-carrot',
            display_order=3
        )
        
        # Create SubCategories
        SubCategory.objects.create(category=main_dishes, name='Rice Dishes', display_order=1)
        SubCategory.objects.create(category=main_dishes, name='Ugali', display_order=2)
        SubCategory.objects.create(category=proteins, name='Meat', display_order=1)
        SubCategory.objects.create(category=proteins, name='Legumes', display_order=2)
        
        # Create Meal Periods
        MealPeriod.objects.create(
            name='breakfast',
            start_time=time(6, 0),
            end_time=time(9, 0),
            ordering_start_time=time(5, 0),
            ordering_end_time=time(8, 30),
            serving_start_time=time(6, 30),
            serving_end_time=time(9, 0)
        )
        
        MealPeriod.objects.create(
            name='lunch',
            start_time=time(12, 0),
            end_time=time(15, 0),
            ordering_start_time=time(9, 0),
            ordering_end_time=time(14, 0),
            serving_start_time=time(12, 30),
            serving_end_time=time(15, 0)
        )
        
        MealPeriod.objects.create(
            name='supper',
            start_time=time(18, 0),
            end_time=time(21, 0),
            ordering_start_time=time(15, 0),
            ordering_end_time=time(20, 0),
            serving_start_time=time(18, 30),
            serving_end_time=time(21, 0)
        )
        
        self.stdout.write(self.style.SUCCESS('Initial data created successfully!'))
```

Run the command:
```bash
python manage.py setup_initial_data
```

### 4. M-Pesa Setup

#### Get Daraja API Credentials

1. Visit [Daraja Portal](https://developer.safaricom.co.ke/)
2. Create an account and login
3. Create a new app
4. Get Consumer Key and Consumer Secret
5. Use test credentials for sandbox:
   - **Shortcode**: 174379
   - **Passkey**: bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919

#### Setup Callback URL with ngrok (for testing)

```bash
# Install ngrok
# Download from https://ngrok.com/download

# Start ngrok
ngrok http 8000

# Copy the https URL (e.g., https://xxxx-xx-xxx.ngrok.io)
# Add it to settings.py:
MPESA_CALLBACK_URL = 'https://xxxx-xx-xxx.ngrok.io/mpesa/callback/'
ALLOWED_HOSTS = ['xxxx-xx-xxx.ngrok.io', 'localhost']
CSRF_TRUSTED_ORIGINS = ['https://xxxx-xx-xxx.ngrok.io']
```

### 5. Email Configuration (Gmail)

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Get from Google Account settings
```

**Generate Gmail App Password:**
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate password for "Mail"
5. Use generated password in settings

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

---

## 📋 Daily Operations

### IT Admin Daily Routine (4:00 AM)

1. Login to admin panel: `/admin/`
2. Navigate to **Daily Menus**
3. Click **Add Daily Menu**
4. Select:
   - Date: Today
   - Meal Period: Breakfast/Lunch/Supper
   - Click **Save and continue editing**
5. Add Menu Items:
   - Food Item: Rice
   - Sufuria Count: 10
   - Plates per Sufuria: 50
   - Total Plates: 500 (auto-calculated)
6. Repeat for all items (Beef, Githeri, Cabbage, Chapati)
7. Check **Is Published**
8. Save

### Staff Operations

**Verify and Serve Orders:**
1. Login to staff dashboard: `/staff/dashboard/`
2. Navigate to **Verify Order**
3. Enter student's **Order Code**
4. Verify:
   - Order status: Confirmed ✓
   - Payment: Paid ✓
   - Not expired ✓
   - Correct meal period ✓
5. Click **Mark as Served**
6. Student gets their food

---

## 🎓 Student Flow

### Registered Student

1. Register: `/register/`
   - Registration Number: SC211-0530-2022
   - Username, Email, Password
   - Phone Number (format: 254XXXXXXXXX)

2. Login: `/login/`

3. Browse Menu: `/products/`

4. Add to Cart (1 plate per item max)

5. Checkout: `/checkout/`
   - Enter M-Pesa phone (254...)
   - Confirm order

6. M-Pesa Payment:
   - Receive STK push on phone
   - Enter M-Pesa PIN
   - Confirm payment

7. Receive Receipt:
   - Email with order code
   - SMS (if configured)

8. Show at Mess:
   - Show order code to attendant
   - Get food after verification

### Guest Student

1. Go to `/products/`
2. Add to cart
3. At checkout:
   - Enter Registration Number: SC211-0530-2022
   - Enter Full Name
   - Enter Phone Number: 254XXXXXXXXX
4. Complete M-Pesa payment
5. Show order code at mess

---

## 🔧 Configuration

### Add Food Items

```python
# admin panel or Django shell
from mess.models import Category, FoodItem

# Get category
main_dishes = Category.objects.get(name='Main Dishes')

# Create food item
FoodItem.objects.create(
    category=main_dishes,
    name='Rice',
    description='White rice',
    price_per_plate=50.00,
    is_active=True,
    is_available=True
)
```

### Meal Period Times

Adjust in admin panel:
- **Ordering Start**: When students can start ordering
- **Ordering End**: Last time to order
- **Serving Start**: When food serving begins
- **Serving End**: When serving stops (orders expire)

**Example:**
- **Lunch**
  - Ordering: 9:00 AM - 2:00 PM
  - Serving: 12:30 PM - 3:00 PM
- Students can't order supper during lunch period ✓

---

## 🔒 Security Features

1. **One Plate Rule**: Students can only order 1 plate per food item
2. **Stock Management**: Quantity decreases automatically
3. **Time-based Ordering**: Can't order past meal times
4. **Order Expiration**: Orders expire after serving time ends
5. **Payment Verification**: Must be paid before serving
6. **Registration Number**: Unique per student

---

## 🐛 Troubleshooting

### M-Pesa Issues

**STK Push not received:**
- Check phone number format (254XXXXXXXXX)
- Check if phone has Safaricom line
- Check ngrok is running
- Check callback URL is correct

**Payment successful but order not confirmed:**
- Check callback URL is publicly accessible
- Check server logs: `tail -f debug.log`
- Manually verify in admin panel

### Order Issues

**Can't order:**
- Check if menu is published
- Check current meal period
- Check ordering time window
- Check if items have stock

**Order expired:**
- Orders expire after serving time ends
- Student must order within time window
- No refunds for expired orders

---

## 📱 Test M-Pesa (Sandbox)

Use these test credentials:

**Phone Numbers:**
- 254708374149
- 254712345678

**Amount:** Any amount between KES 1 - 70,000

**PIN:** 
- Sandbox doesn't require actual PIN
- Just click OK on the prompt

---

## 🚀 Production Deployment

### 1. Update Settings

```python
DEBUG = False
MPESA_ENVIRONMENT = 'production'
MPESA_CONSUMER_KEY = 'production_key'
MPESA_CONSUMER_SECRET = 'production_secret'
MPESA_SHORTCODE = 'your_paybill'
MPESA_PASSKEY = 'production_passkey'
MPESA_CALLBACK_URL = 'https://yourdomain.com/mpesa/callback/'
```

### 2. Setup Production Server

```bash
# Install gunicorn
pip install gunicorn

# Collect static files
python manage.py collectstatic

# Run with gunicorn
gunicorn your_project.wsgi:application --bind 0.0.0.0:8000
```

### 3. Setup Nginx (reverse proxy)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

---

## 📞 Support

For issues or questions:
- Email: admin@murangauniversity.ac.ke
- Phone: +254...

---

## 📝 License

Muranga University Mess System © 2024