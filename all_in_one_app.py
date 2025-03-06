
import os
import json
from flask import Flask, render_template, jsonify, request, session
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Set a default session secret for development
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Mock menu data directly in the file to avoid file dependency
MENU_DATA = {
    "categories": [
        {
            "id": "starters",
            "name": "Starters",
            "description": "Delicious appetizers to start your meal",
            "items": [
                {"id": "s1", "name": "Paneer Tikka", "description": "Marinated cottage cheese grilled to perfection", "price": 249, "image": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8"},
                {"id": "s2", "name": "Veg Spring Rolls", "description": "Crispy rolls filled with vegetables", "price": 199, "image": "https://images.unsplash.com/photo-1607215823971-3b486880cd8e"},
                {"id": "s3", "name": "Gobi Manchurian", "description": "Crispy cauliflower in manchurian sauce", "price": 229, "image": "https://images.unsplash.com/photo-1625398407796-82650a8c9dd1"}
            ]
        },
        {
            "id": "mains",
            "name": "Main Course",
            "description": "Hearty and satisfying main dishes",
            "items": [
                {"id": "m1", "name": "Butter Chicken", "description": "Tender chicken in a rich buttery tomato sauce", "price": 349, "image": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398"},
                {"id": "m2", "name": "Paneer Butter Masala", "description": "Cottage cheese cubes in a creamy sauce", "price": 299, "image": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7"},
                {"id": "m3", "name": "Vegetable Biryani", "description": "Fragrant rice with mixed vegetables", "price": 279, "image": "https://images.unsplash.com/photo-1589302168068-964664d93dc0"}
            ]
        },
        {
            "id": "breads",
            "name": "Breads",
            "description": "Freshly baked breads to accompany your meal",
            "items": [
                {"id": "b1", "name": "Naan", "description": "Soft leavened flatbread", "price": 49, "image": "https://images.unsplash.com/photo-1633383718081-22ac93e3db65"},
                {"id": "b2", "name": "Butter Roti", "description": "Whole wheat flatbread with butter", "price": 39, "image": "https://images.unsplash.com/photo-1626074353765-517a681e40be"},
                {"id": "b3", "name": "Garlic Naan", "description": "Naan topped with garlic and butter", "price": 59, "image": "https://images.unsplash.com/photo-1574894709920-11b28e7367e3"}
            ]
        },
        {
            "id": "desserts",
            "name": "Desserts",
            "description": "Sweet treats to end your meal",
            "items": [
                {"id": "d1", "name": "Gulab Jamun", "description": "Deep-fried milk solids soaked in sugar syrup", "price": 149, "image": "https://images.unsplash.com/photo-1601303892389-8b0c7532cec6"},
                {"id": "d2", "name": "Rasgulla", "description": "Soft and spongy cottage cheese balls", "price": 129, "image": "https://images.unsplash.com/photo-1614945086549-28afadb1e8c7"},
                {"id": "d3", "name": "Kulfi", "description": "Traditional Indian ice cream", "price": 99, "image": "https://images.unsplash.com/photo-1611502071781-72d60be998c2"}
            ]
        }
    ]
}

def load_menu_data():
    return MENU_DATA

def generate_order_id():
    # Generate a unique order ID using timestamp and uuid
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    unique_id = str(uuid.uuid4())[:8]
    return f"ORD-{timestamp}-{unique_id}"

# Initialize orders storage
orders = []

# Valid pincodes
VALID_PINCODES = ['591143', '591153', '590018', '590006', '590008']

@app.route('/')
def index():
    logger.debug("Serving index page")
    return render_template('index.html')

@app.route('/menu')
def menu():
    logger.debug("Loading menu page")
    menu_data = load_menu_data()
    return render_template('menu.html', menu=menu_data)

@app.route('/checkout')
def checkout():
    logger.debug("Loading checkout page")
    return render_template('checkout.html')

@app.route('/my-orders')
def my_orders():
    logger.debug("Loading orders page")
    return render_template('my-orders.html', orders=orders)

@app.route('/confirmation')
def confirmation():
    logger.debug("Loading confirmation page")
    return render_template('confirmation.html')

@app.route('/api/place-order', methods=['POST'])
def place_order():
    try:
        order_data = request.json
        if not order_data:
            logger.error("No order data received")
            return jsonify({"error": "No order data provided"}), 400

        # Validate pincode
        pincode = order_data['customerInfo'].get('pincode')
        if not pincode or pincode not in VALID_PINCODES:
            logger.error(f"Invalid pincode: {pincode}")
            return jsonify({"error": "Delivery not available in this area"}), 400

        # Add timestamp and order ID
        order = {
            'id': generate_order_id(),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': order_data['items'],
            'customer_info': order_data['customerInfo'],
            'total': sum(item['price'] * item['quantity'] for item in order_data['items'])
        }
        orders.append(order)
        logger.info(f"New order created: {order['id']}")
        return jsonify({"success": True, "order_id": order['id']})
    except Exception as e:
        logger.error(f"Error processing order: {e}")
        return jsonify({"error": "Failed to process order"}), 500

@app.route('/api/delete-order/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        global orders
        original_length = len(orders)
        orders = [order for order in orders if order['id'] != order_id]

        if len(orders) < original_length:
            logger.info(f"Order deleted: {order_id}")
            return jsonify({"success": True})
        else:
            logger.error(f"Order not found: {order_id}")
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting order: {e}")
        return jsonify({"error": "Failed to delete order"}), 500

# Add the HTML templates as strings to serve them directly
TEMPLATES = {
    "layout.html": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kitchen Drone - Food Delivery</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .hero-section {
            background-size: cover;
            background-position: center;
            position: relative;
        }
        
        .hero-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
        }
        
        .hero-section .container {
            position: relative;
            z-index: 1;
        }
        
        .cart-icon {
            position: relative;
        }
        
        .cart-badge {
            position: absolute;
            top: -8px;
            right: -8px;
            background-color: #dc3545;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            font-size: 0.7rem;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .cart-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #28a745;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 1000;
            display: none;
        }
        
        .menu-item {
            transition: transform 0.3s ease;
        }
        
        .menu-item:hover {
            transform: translateY(-5px);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-drone me-2"></i>Kitchen Drone
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/menu">Menu</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/my-orders">My Orders</a>
                    </li>
                </ul>
                <div class="d-flex">
                    <a href="/checkout" class="btn btn-outline-light ms-2 cart-icon">
                        <i class="fas fa-shopping-cart"></i>
                        <span class="cart-badge" id="cartBadge">0</span>
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <div class="cart-notification" id="cartNotification">
        Item added to cart!
    </div>

    {% block content %}{% endblock %}

    <footer class="bg-dark text-white py-4 mt-5">
        <div class="container">
            <div class="row">
                <div class="col-md-4">
                    <h5><i class="fas fa-drone me-2"></i>Kitchen Drone</h5>
                    <p>The future of food delivery</p>
                </div>
                <div class="col-md-4">
                    <h5>Quick Links</h5>
                    <ul class="list-unstyled">
                        <li><a href="/" class="text-white">Home</a></li>
                        <li><a href="/menu" class="text-white">Menu</a></li>
                        <li><a href="/my-orders" class="text-white">My Orders</a></li>
                    </ul>
                </div>
                <div class="col-md-4">
                    <h5>Contact Us</h5>
                    <p><i class="fas fa-map-marker-alt me-2"></i>123 Drone Street, Tech City</p>
                    <p><i class="fas fa-phone me-2"></i>(123) 456-7890</p>
                    <p><i class="fas fa-envelope me-2"></i>info@kitchendrone.com</p>
                </div>
            </div>
            <div class="text-center mt-3">
                <p>&copy; 2023 Kitchen Drone. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Cart functionality
        let cart = [];

        // Load cart from localStorage
        function loadCart() {
            const savedCart = localStorage.getItem('cart');
            if (savedCart) {
                cart = JSON.parse(savedCart);
                updateCartBadge();
            }
        }

        // Save cart to localStorage
        function saveCart() {
            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartBadge();
        }

        // Update cart badge
        function updateCartBadge() {
            const cartBadge = document.getElementById('cartBadge');
            if (cartBadge) {
                const itemCount = cart.reduce((total, item) => total + item.quantity, 0);
                cartBadge.textContent = itemCount;
            }
        }

        // Show cart notification
        function showCartNotification() {
            const notification = document.getElementById('cartNotification');
            notification.style.display = 'block';
            setTimeout(() => {
                notification.style.display = 'none';
            }, 2000);
        }

        // Load cart on page load
        document.addEventListener('DOMContentLoaded', loadCart);
    </script>
</body>
</html>
    """,
    
    "index.html": """
{% extends "layout.html" %}

{% block content %}
<div class="hero-section" style="background-image: url('https://images.unsplash.com/photo-1473968512647-3e447244af8f');">
    <div class="container">
        <div class="row min-vh-100 align-items-center">
            <div class="col-md-6">
                <h1 class="display-4 text-white">Welcome to Kitchen Drone</h1>
                <p class="lead text-white">Experience the future of food delivery - straight from our kitchen to your doorstep via drone!</p>
                <a href="/menu" class="btn btn-primary btn-lg">View Menu</a>
            </div>
        </div>
    </div>
</div>

<section class="featured-section py-5">
    <div class="container">
        <h2 class="text-center mb-4">Featured Dishes</h2>
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <img src="https://images.unsplash.com/photo-1603894584373-5ac82b2ae398" class="card-img-top" alt="Featured Dish">
                    <div class="card-body">
                        <h5 class="card-title">Butter Chicken</h5>
                        <p class="card-text">Rich and creamy butter chicken curry</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <img src="https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8" class="card-img-top" alt="Featured Dish">
                    <div class="card-body">
                        <h5 class="card-title">Paneer Tikka</h5>
                        <p class="card-text">Marinated cottage cheese grilled to perfection</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <img src="https://images.unsplash.com/photo-1589302168068-964664d93dc0" class="card-img-top" alt="Featured Dish">
                    <div class="card-body">
                        <h5 class="card-title">Vegetable Biryani</h5>
                        <p class="card-text">Fragrant rice with mixed vegetables</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="how-it-works py-5 bg-light">
    <div class="container">
        <h2 class="text-center mb-5">How It Works</h2>
        <div class="row text-center">
            <div class="col-md-4 mb-4">
                <div class="p-3">
                    <i class="fas fa-utensils fa-3x mb-3 text-primary"></i>
                    <h4>1. Choose Your Food</h4>
                    <p>Browse our menu and select your favorite dishes</p>
                </div>
            </div>
            <div class="col-md-4 mb-4">
                <div class="p-3">
                    <i class="fas fa-shopping-cart fa-3x mb-3 text-primary"></i>
                    <h4>2. Place Your Order</h4>
                    <p>Add items to your cart and check out</p>
                </div>
            </div>
            <div class="col-md-4 mb-4">
                <div class="p-3">
                    <i class="fas fa-drone fa-3x mb-3 text-primary"></i>
                    <h4>3. Drone Delivery</h4>
                    <p>Your food arrives via our special delivery drone</p>
                </div>
            </div>
        </div>
    </div>
</section>
{% endblock %}
    """,
    
    "menu.html": """
{% extends "layout.html" %}

{% block content %}
<div class="container py-5">
    <h1 class="text-center mb-5">Our Menu</h1>

    <ul class="nav nav-pills mb-4 justify-content-center" id="menu-tabs" role="tablist">
        {% for category in menu.categories %}
        <li class="nav-item" role="presentation">
            <button class="nav-link {% if loop.first %}active{% endif %}" 
                    id="{{ category.id }}-tab" 
                    data-bs-toggle="pill" 
                    data-bs-target="#{{ category.id }}" 
                    type="button" 
                    role="tab">
                {{ category.name }}
            </button>
        </li>
        {% endfor %}
    </ul>

    <div class="tab-content" id="menu-content">
        {% for category in menu.categories %}
        <div class="tab-pane fade {% if loop.first %}show active{% endif %}" id="{{ category.id }}" role="tabpanel">
            <h3 class="mb-3">{{ category.name }}</h3>
            <p class="mb-4">{{ category.description }}</p>
            
            <div class="row">
                {% for item in category.items %}
                <div class="col-md-4 mb-4">
                    <div class="card menu-item h-100">
                        <img src="{{ item.image }}" class="card-img-top" alt="{{ item.name }}">
                        <div class="card-body">
                            <h5 class="card-title">{{ item.name }}</h5>
                            <p class="card-text">{{ item.description }}</p>
                            <p class="card-text"><strong>₹{{ item.price }}</strong></p>
                        </div>
                        <div class="card-footer bg-white border-top-0">
                            <button class="btn btn-outline-primary w-100" 
                                    onclick="addToCart('{{ item.id }}', '{{ item.name }}', {{ item.price }})">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<script>
    // Function to add item to cart
    function addToCart(id, name, price) {
        const existingItem = cart.find(item => item.id === id);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push({
                id: id,
                name: name,
                price: price,
                quantity: 1
            });
        }

        saveCart();
        showCartNotification();
    }
</script>
{% endblock %}
    """,
    
    "checkout.html": """
{% extends "layout.html" %}

{% block content %}
<div class="container py-5">
    <h1 class="text-center mb-4">Checkout</h1>

    <div class="row">
        <div class="col-md-8">
            <div class="card mb-4">
                <div class="card-body">
                    <h3 class="card-title">Delivery Information</h3>
                    <form id="checkoutForm">
                        <div class="mb-3">
                            <label for="name" class="form-label">Full Name</label>
                            <input type="text" class="form-control" id="name" required>
                        </div>
                        <div class="mb-3">
                            <label for="email" class="form-label">Email</label>
                            <input type="email" class="form-control" id="email" required>
                        </div>
                        <div class="mb-3">
                            <label for="phone" class="form-label">Phone</label>
                            <input type="tel" class="form-control" id="phone" required>
                        </div>
                        <div class="mb-3">
                            <label for="address" class="form-label">Address</label>
                            <textarea class="form-control" id="address" rows="3" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="pincode" class="form-label">Pincode</label>
                            <input type="text" class="form-control" id="pincode" required>
                            <div class="invalid-feedback" id="pincodeError">
                                Sorry, delivery is not available in your area.
                            </div>
                            <small class="text-muted">We currently deliver to: 591143, 591153, 590018, 590006, 590008</small>
                        </div>
                        <div class="mb-3">
                            <label for="notes" class="form-label">Delivery Notes (Optional)</label>
                            <textarea class="form-control" id="notes" rows="2"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Place Order</button>
                    </form>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h3 class="card-title">Order Summary</h3>
                    <div id="cartItems">
                        <!-- Cart items will be loaded here -->
                    </div>
                    <hr>
                    <div class="d-flex justify-content-between">
                        <h5>Total:</h5>
                        <h5 id="cartTotal">₹0</h5>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Render cart items
    function renderCart() {
        const cartItemsElement = document.getElementById('cartItems');
        const cartTotalElement = document.getElementById('cartTotal');
        
        if (cart.length === 0) {
            cartItemsElement.innerHTML = '<p>Your cart is empty</p>';
            cartTotalElement.textContent = '₹0';
            return;
        }
        
        let cartHtml = '';
        let total = 0;
        
        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            total += itemTotal;
            
            cartHtml += `
                <div class="mb-3">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6>${item.name}</h6>
                            <p class="text-muted">₹${item.price} x ${item.quantity}</p>
                        </div>
                        <div>
                            <span>₹${itemTotal}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        cartItemsElement.innerHTML = cartHtml;
        cartTotalElement.textContent = `₹${total}`;
    }
    
    // Handle form submission
    document.getElementById('checkoutForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (cart.length === 0) {
            alert('Your cart is empty. Please add some items to your cart.');
            return;
        }
        
        const customerInfo = {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            address: document.getElementById('address').value,
            pincode: document.getElementById('pincode').value,
            notes: document.getElementById('notes').value
        };
        
        // Reset any previous error indicators
        document.getElementById('pincode').classList.remove('is-invalid');
        document.getElementById('pincodeError').style.display = 'none';
        
        try {
            const response = await fetch('/api/place-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    items: cart,
                    customerInfo: customerInfo
                }),
            });
            
            const data = await response.json();
            if (data.success) {
                localStorage.removeItem('cart');
                window.location.href = '/confirmation';
            } else {
                if (data.error === "Delivery not available in this area") {
                    document.getElementById('pincode').classList.add('is-invalid');
                    document.getElementById('pincodeError').style.display = 'block';
                } else {
                    alert(data.error || 'Failed to place order. Please try again.');
                }
            }
        } catch (error) {
            console.error('Error placing order:', error);
            alert('There was an error placing your order. Please try again.');
        }
    });
    
    // Load cart on page load
    document.addEventListener('DOMContentLoaded', function() {
        loadCart();
        renderCart();
    });
</script>
{% endblock %}
    """,
    
    "confirmation.html": """
{% extends "layout.html" %}

{% block content %}
<div class="container py-5 text-center">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-body">
                    <i class="fas fa-check-circle text-success display-1 mb-4"></i>
                    <h1 class="card-title mb-4">Order Confirmed!</h1>
                    <p class="lead">Thank you for your order. Your delicious food is being prepared.</p>
                    <p>Our drone will deliver your order soon. You can track your order in the "My Orders" section.</p>
                    
                    <div class="mt-4">
                        <a href="/menu" class="btn btn-outline-primary me-2">Back to Menu</a>
                        <a href="/my-orders" class="btn btn-primary">View My Orders</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
    """,
    
    "my-orders.html": """
{% extends "layout.html" %}

{% block content %}
<div class="container py-5">
    <h1 class="text-center mb-4">My Orders</h1>

    {% if orders %}
        <div class="row">
            {% for order in orders %}
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Order #{{ order.id }}</h5>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteOrder('{{ order.id }}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    <div class="card-body">
                        <p class="text-muted">Ordered on: {{ order.timestamp }}</p>
                        
                        <div class="mb-3">
                            <h6>Items</h6>
                            <ul class="list-group">
                                {% for item in order.items %}
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    {{ item.name }}
                                    <span>
                                        <span class="badge bg-primary rounded-pill">{{ item.quantity }}</span>
                                        ₹{{ item.price * item.quantity }}
                                    </span>
                                </li>
                                {% endfor %}
                            </ul>
                            <div class="mt-2 text-end">
                                <strong>Total: ₹{{ order.total }}</strong>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <h6>Delivery Information</h6>
                            <p class="mb-1">Name: {{ order.customer_info.name }}</p>
                            <p class="mb-1">Address: {{ order.customer_info.address }}</p>
                            <p class="mb-1">Phone: {{ order.customer_info.phone }}</p>
                            {% if order.customer_info.notes %}
                            <p class="mb-1">Notes: {{ order.customer_info.notes }}</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <div class="text-center">
            <p class="lead">No orders found</p>
            <a href="/menu" class="btn btn-primary">Browse Menu</a>
        </div>
    {% endif %}
</div>

<script>
    async function deleteOrder(orderId) {
        if (confirm('Are you sure you want to delete this order?')) {
            try {
                const response = await fetch(`/api/delete-order/${orderId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('Order deleted successfully');
                    window.location.reload();
                } else {
                    alert(data.error || 'Failed to delete order');
                }
            } catch (error) {
                console.error('Error deleting order:', error);
                alert('There was an error deleting the order');
            }
        }
    }
</script>
{% endblock %}
    """
}

# Override Flask's render_template to use our template strings
def render_template(template_name, **context):
    from jinja2 import Template
    
    # Get the template content from our dictionary
    template_content = TEMPLATES.get(template_name, "Template not found")
    
    # If the template extends another template, we need to handle that
    if "{% extends" in template_content:
        # Extract the parent template name
        import re
        parent_match = re.search(r'{%\s*extends\s*[\'"](.+?)[\'"]', template_content)
        if parent_match:
            parent_name = parent_match.group(1)
            parent_content = TEMPLATES.get(parent_name, "Parent template not found")
            
            # Extract the blocks from the child template
            blocks = {}
            for block_match in re.finditer(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', template_content, re.DOTALL):
                block_name = block_match.group(1)
                block_content = block_match.group(2)
                blocks[block_name] = block_content
            
            # Replace the block placeholders in the parent template
            template_content = parent_content
            for block_name, block_content in blocks.items():
                template_content = re.sub(
                    r'{%\s*block\s+' + block_name + r'\s*%}.*?{%\s*endblock\s*%}',
                    '{% block ' + block_name + ' %}' + block_content + '{% endblock %}',
                    template_content,
                    flags=re.DOTALL
                )
    
    # Create a Jinja2 template
    template = Template(template_content)
    
    # Render the template with the provided context
    rendered = template.render(**context)
    
    return rendered

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
