
import os
import json
from flask import Flask, render_template, jsonify, request, session, send_from_directory
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Set a default session secret for development
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Valid pincodes
VALID_PINCODES = ['591143', '591153', '590018', '590006', '590008']

# Initialize orders storage
orders = []

# Menu data as a Python dictionary
MENU_DATA = {
  "categories": [
    {
      "name": "Starters",
      "items": [
        {
          "id": "1",
          "name": "Paneer Tikka",
          "description": "Grilled cottage cheese marinated in spices",
          "price": 199,
          "image": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8"
        },
        {
          "id": "2",
          "name": "Veg Spring Roll",
          "description": "Crispy rolls filled with mixed vegetables",
          "price": 149,
          "image": "https://images.unsplash.com/photo-1606491956689-2ea866880c84"
        }
      ]
    },
    {
      "name": "Main Course",
      "items": [
        {
          "id": "3",
          "name": "Butter Chicken",
          "description": "Tender chicken in rich tomato butter gravy",
          "price": 299,
          "image": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398"
        },
        {
          "id": "4",
          "name": "Dal Makhani",
          "description": "Creamy black lentils cooked overnight",
          "price": 249,
          "image": "https://images.unsplash.com/photo-1546833999-b9f581a1996d"
        }
      ]
    },
    {
      "name": "Breads",
      "items": [
        {
          "id": "5",
          "name": "Butter Naan",
          "description": "Soft tandoor-baked bread with butter",
          "price": 49,
          "image": "https://images.unsplash.com/photo-1626074353765-517a681e40be"
        },
        {
          "id": "6",
          "name": "Garlic Roti",
          "description": "Whole wheat bread with garlic",
          "price": 39,
          "image": "https://images.unsplash.com/photo-1631515242808-499c2c9f6a49"
        }
      ]
    }
  ]
}

def generate_order_id():
    # Generate a unique order ID using timestamp and uuid
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    unique_id = str(uuid.uuid4())[:8]
    return f"ORD-{timestamp}-{unique_id}"

# HTML Templates as strings
LAYOUT_HTML = '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kitchen Drone - Food Delivery</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.css" rel="stylesheet">
    <style>
        /* CSS Styles */
        body {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .hero-section {
            background-size: cover;
            background-position: center;
            color: white;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .cart-overlay {
            display: none;
            position: fixed;
            top: 0;
            right: 0;
            bottom: 0;
            width: 350px;
            background-color: #343a40;
            box-shadow: -2px 0 5px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            overflow-y: auto;
        }
        .cart-content {
            padding: 20px;
        }
        .cart-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #555;
        }
        .cart-total {
            margin: 20px 0;
        }
        footer {
            margin-top: auto;
        }
        .featured-section .card {
            transition: transform 0.3s;
        }
        .featured-section .card:hover {
            transform: translateY(-5px);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">Kitchen Drone</a>
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
                    <button class="btn btn-outline-light" id="cartButton">
                        <i data-feather="shopping-cart"></i>
                        <span id="cartCount">0</span>
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <div id="cartOverlay" class="cart-overlay">
        <div class="cart-content">
            <h3>Your Cart</h3>
            <div id="cartItems"></div>
            <div class="cart-total">
                <strong>Total: ₹<span id="cartTotal">0.00</span></strong>
            </div>
            <button class="btn btn-primary" onclick="window.location.href='/checkout'">Checkout</button>
            <button class="btn btn-secondary" onclick="closeCart()">Close</button>
        </div>
    </div>

    {content}

    <footer class="footer mt-auto py-3 bg-dark">
        <div class="container text-center">
            <span class="text-muted">© 2024 Kitchen Drone. All rights reserved.</span>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js"></script>
    <script>
        // Cart functionality
        let cart = JSON.parse(localStorage.getItem('cart')) || [];
        
        function updateCart() {
            const cartCount = document.getElementById('cartCount');
            const cartItems = document.getElementById('cartItems');
            const cartTotal = document.getElementById('cartTotal');
            
            if (cartCount) {
                cartCount.textContent = cart.reduce((total, item) => total + item.quantity, 0);
            }
            
            if (cartItems) {
                cartItems.innerHTML = '';
                
                if (cart.length === 0) {
                    cartItems.innerHTML = '<p>Your cart is empty</p>';
                } else {
                    cart.forEach(item => {
                        const cartItem = document.createElement('div');
                        cartItem.className = 'cart-item';
                        cartItem.innerHTML = `
                            <div>
                                <div>${item.name} x ${item.quantity}</div>
                                <div>₹${(item.price * item.quantity).toFixed(2)}</div>
                            </div>
                            <button class="btn btn-sm btn-danger" onclick="removeFromCart('${item.id}')">
                                <i data-feather="trash-2"></i>
                            </button>
                        `;
                        cartItems.appendChild(cartItem);
                    });
                    feather.replace();
                }
            }
            
            if (cartTotal) {
                cartTotal.textContent = cart.reduce((total, item) => total + (item.price * item.quantity), 0).toFixed(2);
            }
            
            // Save to localStorage
            localStorage.setItem('cart', JSON.stringify(cart));
        }
        
        function addToCart(id, name, price) {
            const existingItem = cart.find(item => item.id === id);
            
            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                cart.push({ id, name, price, quantity: 1 });
            }
            
            updateCart();
        }
        
        function removeFromCart(id) {
            cart = cart.filter(item => item.id !== id);
            updateCart();
        }
        
        function openCart() {
            document.getElementById('cartOverlay').style.display = 'block';
        }
        
        function closeCart() {
            document.getElementById('cartOverlay').style.display = 'none';
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            feather.replace();
            updateCart();
            
            const cartButton = document.getElementById('cartButton');
            if (cartButton) {
                cartButton.addEventListener('click', openCart);
            }
            
            // Menu page functionality
            const addToCartButtons = document.querySelectorAll('.add-to-cart');
            addToCartButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const id = this.getAttribute('data-id');
                    const name = this.getAttribute('data-name');
                    const price = parseFloat(this.getAttribute('data-price'));
                    addToCart(id, name, price);
                });
            });
            
            // Search functionality for menu page
            const searchInput = document.getElementById('searchInput');
            const searchButton = document.getElementById('searchButton');
            
            if (searchInput && searchButton) {
                function performSearch() {
                    const query = searchInput.value.toLowerCase();
                    const menuItems = document.querySelectorAll('.menu-item');
                    
                    menuItems.forEach(item => {
                        const name = item.getAttribute('data-name');
                        if (name.includes(query)) {
                            item.style.display = 'block';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                }
                
                searchButton.addEventListener('click', performSearch);
                searchInput.addEventListener('keyup', function(event) {
                    if (event.key === 'Enter') {
                        performSearch();
                    }
                });
            }
            
            // Checkout page functionality
            const placeOrderBtn = document.getElementById('placeOrderBtn');
            if (placeOrderBtn) {
                displayOrderSummary();
                
                placeOrderBtn.addEventListener('click', function() {
                    placeOrder();
                });
            }
            
            // Confirmation page functionality
            const orderNumber = document.getElementById('orderNumber');
            if (orderNumber) {
                const urlParams = new URLSearchParams(window.location.search);
                const order_id = urlParams.get('order_id');
                if (order_id) {
                    orderNumber.textContent = order_id;
                }
                
                // Clear cart after successful order
                cart = [];
                updateCart();
            }
        });
        
        // Checkout page specific functions
        function displayOrderSummary() {
            const orderItems = document.getElementById('orderItems');
            const subtotalElement = document.getElementById('subtotal');
            const totalElement = document.getElementById('total');
            
            if (!orderItems || !subtotalElement || !totalElement) return;
            
            orderItems.innerHTML = '';
            
            if (cart.length === 0) {
                orderItems.innerHTML = '<p>Your cart is empty</p>';
                return;
            }
            
            cart.forEach(item => {
                const itemElement = document.createElement('div');
                itemElement.className = 'd-flex justify-content-between mb-2';
                itemElement.innerHTML = `
                    <span>${item.name} x ${item.quantity}</span>
                    <span>₹${(item.price * item.quantity).toFixed(2)}</span>
                `;
                orderItems.appendChild(itemElement);
            });
            
            const subtotal = cart.reduce((total, item) => total + (item.price * item.quantity), 0);
            
            subtotalElement.textContent = `₹${subtotal.toFixed(2)}`;
            totalElement.textContent = `₹${subtotal.toFixed(2)}`;
        }
        
        function placeOrder() {
            const form = document.getElementById('checkoutForm');
            const nameInput = document.getElementById('name');
            const emailInput = document.getElementById('email');
            const phoneInput = document.getElementById('phone');
            const pincodeInput = document.getElementById('pincode');
            const addressInput = document.getElementById('address');
            const notesInput = document.getElementById('notes');
            
            if (!form || !nameInput || !emailInput || !phoneInput || !pincodeInput || !addressInput) {
                alert('Something went wrong. Please refresh the page.');
                return;
            }
            
            // Simple validation
            if (!nameInput.value || !emailInput.value || !phoneInput.value || !pincodeInput.value || !addressInput.value) {
                alert('Please fill in all required fields.');
                return;
            }
            
            if (cart.length === 0) {
                alert('Your cart is empty');
                return;
            }
            
            const orderData = {
                items: cart,
                customerInfo: {
                    name: nameInput.value,
                    email: emailInput.value,
                    phone: phoneInput.value,
                    pincode: pincodeInput.value,
                    address: addressInput.value,
                    notes: notesInput ? notesInput.value : ''
                }
            };
            
            fetch('/api/place-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = `/confirmation?order_id=${data.order_id}`;
                } else {
                    alert(data.error || 'Failed to place order. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error processing order. Please try again.');
            });
        }
    </script>
</body>
</html>
'''

INDEX_HTML = '''
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
                        <p class="card-text">Grilled cottage cheese with Indian spices</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <img src="https://images.unsplash.com/photo-1546833999-b9f581a1996d" class="card-img-top" alt="Featured Dish">
                    <div class="card-body">
                        <h5 class="card-title">Dal Makhani</h5>
                        <p class="card-text">Creamy black lentils, slow-cooked to perfection</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>
'''

MENU_HTML = '''
<div class="container py-5">
    <h1 class="text-center mb-4">Our Menu</h1>

    <div class="row mb-4">
        <div class="col-md-6 mx-auto">
            <div class="input-group">
                <input type="text" id="searchInput" class="form-control" placeholder="Search menu items...">
                <button class="btn btn-outline-secondary" type="button" id="searchButton">
                    <i data-feather="search"></i>
                </button>
            </div>
        </div>
    </div>

    <div class="menu-categories">
        {categories_html}
    </div>
</div>
'''

CHECKOUT_HTML = '''
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
                            <label for="pincode" class="form-label">Pincode</label>
                            <select class="form-select" id="pincode" required>
                                <option value="">Select Pincode</option>
                                <option value="591143">591143</option>
                                <option value="591153">591153</option>
                                <option value="590018">590018</option>
                                <option value="590006">590006</option>
                                <option value="590008">590008</option>
                            </select>
                            <div id="pincodeError" class="invalid-feedback">
                                Sorry, delivery is not available in this area.
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="address" class="form-label">Delivery Address</label>
                            <textarea class="form-control" id="address" rows="3" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="notes" class="form-label">Special Instructions</label>
                            <textarea class="form-control" id="notes" rows="2"></textarea>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h3 class="card-title">Order Summary</h3>
                    <div id="orderItems" class="mb-3"></div>
                    <hr>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Subtotal:</span>
                        <span id="subtotal">₹0.00</span>
                    </div>
                    <div class="d-flex justify-content-between mb-3">
                        <strong>Total:</strong>
                        <strong id="total">₹0.00</strong>
                    </div>
                    <button class="btn btn-primary w-100" id="placeOrderBtn">Place Order</button>
                </div>
            </div>
        </div>
    </div>
</div>
'''

CONFIRMATION_HTML = '''
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-8 text-center">
            <div class="card">
                <div class="card-body">
                    <i data-feather="check-circle" class="text-success mb-4" style="width: 64px; height: 64px;"></i>
                    <h1 class="card-title mb-4">Order Confirmed!</h1>
                    <p class="lead">Thank you for your order. Your order number is: <strong id="orderNumber">12345</strong></p>
                    <p>We've sent a confirmation email with your order details.</p>
                    <p>Estimated delivery time: 30-45 minutes</p>
                    <div class="mt-4">
                        <a href="/menu" class="btn btn-primary">Order More</a>
                        <a href="/" class="btn btn-secondary">Return Home</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
'''

MY_ORDERS_HTML = '''
<div class="container py-5">
    <h1 class="text-center mb-4">My Order History</h1>

    <div id="orders-container">
        <!-- Orders will be dynamically populated here -->
    </div>
</div>

<!-- Add QRious library for QR code generation -->
<script src="https://cdn.jsdelivr.net/npm/qrious@4.0.2/dist/qrious.min.js"></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Fetch orders and display them
        fetch('/api/get-orders')
            .then(response => response.json())
            .then(data => {
                const ordersContainer = document.getElementById('orders-container');
                
                if (data.length === 0) {
                    ordersContainer.innerHTML = `
                        <div class="text-center">
                            <p class="lead">No orders found</p>
                            <a href="/menu" class="btn btn-primary">Browse Menu</a>
                        </div>
                    `;
                    return;
                }
                
                let ordersHTML = '<div class="row">';
                
                data.forEach(order => {
                    ordersHTML += `
                        <div class="col-12 mb-4" id="order-container-${order.id}">
                            <div class="card">
                                <div class="card-header d-flex justify-content-between align-items-center">
                                    <button class="btn btn-link text-decoration-none" type="button" 
                                            data-bs-toggle="collapse" 
                                            data-bs-target="#order-${order.id}" 
                                            aria-expanded="false">
                                        <span>Order #${order.id}</span>
                                    </button>
                                    <div>
                                        <small class="text-muted me-3">${order.timestamp}</small>
                                        <button class="btn btn-sm btn-outline-danger delete-order" 
                                                data-order-id="${order.id}"
                                                onclick="deleteOrder('${order.id}')">
                                            <i data-feather="trash-2"></i>
                                        </button>
                                    </div>
                                </div>
                                <div class="collapse" id="order-${order.id}">
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-9">
                                                <h5 class="card-title">Order Details</h5>
                                                <div class="table-responsive">
                                                    <table class="table">
                                                        <thead>
                                                            <tr>
                                                                <th>Item</th>
                                                                <th>Quantity</th>
                                                                <th>Price</th>
                                                                <th>Subtotal</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            ${order.items.map(item => `
                                                                <tr>
                                                                    <td>${item.name}</td>
                                                                    <td>${item.quantity}</td>
                                                                    <td>₹${item.price.toFixed(2)}</td>
                                                                    <td>₹${(item.price * item.quantity).toFixed(2)}</td>
                                                                </tr>
                                                            `).join('')}
                                                        </tbody>
                                                        <tfoot>
                                                            <tr>
                                                                <td colspan="3" class="text-end"><strong>Total:</strong></td>
                                                                <td><strong>₹${order.total.toFixed(2)}</strong></td>
                                                            </tr>
                                                        </tfoot>
                                                    </table>
                                                </div>
                                            </div>
                                            <div class="col-md-3">
                                                <div class="text-center">
                                                    <h6 class="mb-3">Order QR Code</h6>
                                                    <canvas id="qr-${order.id}" class="mb-2"></canvas>
                                                    <small class="d-block text-muted">Scan to view order details</small>
                                                </div>
                                            </div>
                                        </div>

                                        <div class="mt-3">
                                            <h6>Delivery Information</h6>
                                            <p class="mb-1">Name: ${order.customer_info.name}</p>
                                            <p class="mb-1">Address: ${order.customer_info.address}</p>
                                            <p class="mb-1">Phone: ${order.customer_info.phone}</p>
                                            ${order.customer_info.notes ? `<p class="mb-1">Notes: ${order.customer_info.notes}</p>` : ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                ordersHTML += '</div>';
                ordersContainer.innerHTML = ordersHTML;
                
                // Generate QR codes and initialize feather icons
                feather.replace();
                data.forEach(order => {
                    new QRious({
                        element: document.getElementById(`qr-${order.id}`),
                        value: order.id,
                        size: 128,
                        background: '#ffffff',
                        foreground: '#000000',
                        level: 'H'
                    });
                });
                
                // Show first order by default if exists
                if (data.length > 0) {
                    document.querySelector('.collapse').classList.add('show');
                }
            })
            .catch(error => {
                console.error('Error fetching orders:', error);
            });
    });

    function deleteOrder(orderId) {
        if (confirm('Are you sure you want to delete this order?')) {
            fetch(`/api/delete-order/${orderId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById(`order-container-${orderId}`).remove();
                    const remainingOrders = document.querySelectorAll('.card').length;
                    if (remainingOrders === 0) {
                        location.reload(); // Reload to show "No orders found" message
                    }
                } else {
                    alert('Failed to delete order. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting order. Please try again.');
            });
        }
    }
</script>
'''

# Helper function to generate menu categories HTML
def generate_menu_categories_html():
    categories_html = ""
    for category in MENU_DATA["categories"]:
        items_html = ""
        for item in category["items"]:
            items_html += f'''
            <div class="col-md-6 col-lg-4 mb-4 menu-item" data-name="{item['name'].lower()}">
                <div class="card h-100">
                    <img src="{item['image']}" class="card-img-top" alt="{item['name']}">
                    <div class="card-body">
                        <h5 class="card-title">{item['name']}</h5>
                        <p class="card-text">{item['description']}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="price">₹{item['price']:.2f}</span>
                            <button class="btn btn-primary add-to-cart" 
                                    data-id="{item['id']}"
                                    data-name="{item['name']}"
                                    data-price="{item['price']}">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        categories_html += f'''
        <div class="category-section mb-5">
            <h2 class="category-title mb-4">{category['name']}</h2>
            <div class="row">
                {items_html}
            </div>
        </div>
        '''
    
    return categories_html

# Flask routes
@app.route('/')
def index():
    logger.debug("Serving index page")
    return LAYOUT_HTML.replace('{content}', INDEX_HTML)

@app.route('/menu')
def menu():
    logger.debug("Loading menu page")
    categories_html = generate_menu_categories_html()
    return LAYOUT_HTML.replace('{content}', MENU_HTML.replace('{categories_html}', categories_html))

@app.route('/checkout')
def checkout():
    logger.debug("Loading checkout page")
    return LAYOUT_HTML.replace('{content}', CHECKOUT_HTML)

@app.route('/my-orders')
def my_orders():
    logger.debug("Loading orders page")
    return LAYOUT_HTML.replace('{content}', MY_ORDERS_HTML)

@app.route('/confirmation')
def confirmation():
    logger.debug("Loading confirmation page")
    return LAYOUT_HTML.replace('{content}', CONFIRMATION_HTML)

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

@app.route('/api/get-orders', methods=['GET'])
def get_orders():
    return jsonify(orders)

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

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=5000, debug=True)
