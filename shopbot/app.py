from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255))
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database with sample data
def init_database():
    with app.app_context():
        db.create_all()
        
        # Check if products already exist
        if Product.query.count() == 0:
            # Sample products (100+ items)
            products = [
                # Electronics
                {"name": "iPhone 15 Pro", "description": "Latest Apple smartphone with A17 Pro chip", "price": 999.99, "category": "Electronics", "brand": "Apple", "stock": 50, "rating": 4.8},
                {"name": "Samsung Galaxy S24", "description": "Flagship Android smartphone with AI features", "price": 899.99, "category": "Electronics", "brand": "Samsung", "stock": 45, "rating": 4.7},
                {"name": "MacBook Pro 14", "description": "Professional laptop with M3 chip", "price": 1999.99, "category": "Electronics", "brand": "Apple", "stock": 25, "rating": 4.9},
                {"name": "Dell XPS 13", "description": "Ultrabook with Intel Core i7", "price": 1299.99, "category": "Electronics", "brand": "Dell", "stock": 30, "rating": 4.6},
                {"name": "iPad Air", "description": "Versatile tablet for work and play", "price": 599.99, "category": "Electronics", "brand": "Apple", "stock": 40, "rating": 4.7},
                {"name": "Sony WH-1000XM5", "description": "Premium noise-canceling headphones", "price": 399.99, "category": "Electronics", "brand": "Sony", "stock": 60, "rating": 4.8},
                {"name": "Nintendo Switch OLED", "description": "Hybrid gaming console with OLED screen", "price": 349.99, "category": "Electronics", "brand": "Nintendo", "stock": 35, "rating": 4.8},
                {"name": "AirPods Pro 2", "description": "Wireless earbuds with active noise cancellation", "price": 249.99, "category": "Electronics", "brand": "Apple", "stock": 70, "rating": 4.6},
                {"name": "Samsung 55\" QLED TV", "description": "4K Smart TV with Quantum Dot technology", "price": 1199.99, "category": "Electronics", "brand": "Samsung", "stock": 20, "rating": 4.7},
                {"name": "Canon EOS R6", "description": "Mirrorless camera for professionals", "price": 2499.99, "category": "Electronics", "brand": "Canon", "stock": 15, "rating": 4.9},
                
                # Clothing
                {"name": "Nike Air Max 270", "description": "Comfortable running shoes", "price": 149.99, "category": "Clothing", "brand": "Nike", "stock": 80, "rating": 4.5},
                {"name": "Adidas Ultraboost 23", "description": "Performance running shoes", "price": 189.99, "category": "Clothing", "brand": "Adidas", "stock": 65, "rating": 4.6},
                {"name": "Levi's 501 Jeans", "description": "Classic straight-fit jeans", "price": 89.99, "category": "Clothing", "brand": "Levi's", "stock": 100, "rating": 4.4},
                {"name": "North Face Jacket", "description": "Waterproof outdoor jacket", "price": 199.99, "category": "Clothing", "brand": "The North Face", "stock": 45, "rating": 4.7},
                {"name": "Champion Hoodie", "description": "Comfortable cotton hoodie", "price": 49.99, "category": "Clothing", "brand": "Champion", "stock": 90, "rating": 4.3},
                {"name": "Nike Dri-FIT Shirt", "description": "Moisture-wicking athletic shirt", "price": 29.99, "category": "Clothing", "brand": "Nike", "stock": 120, "rating": 4.4},
                {"name": "Ray-Ban Aviators", "description": "Classic aviator sunglasses", "price": 154.99, "category": "Clothing", "brand": "Ray-Ban", "stock": 55, "rating": 4.6},
                {"name": "Converse Chuck Taylor", "description": "Classic canvas sneakers", "price": 65.99, "category": "Clothing", "brand": "Converse", "stock": 85, "rating": 4.5},
                {"name": "Patagonia Fleece", "description": "Warm fleece jacket", "price": 119.99, "category": "Clothing", "brand": "Patagonia", "stock": 40, "rating": 4.8},
                {"name": "Under Armour Shorts", "description": "Athletic performance shorts", "price": 39.99, "category": "Clothing", "brand": "Under Armour", "stock": 75, "rating": 4.3},
                
                # Home & Garden
                {"name": "KitchenAid Stand Mixer", "description": "Professional-grade stand mixer", "price": 449.99, "category": "Home & Garden", "brand": "KitchenAid", "stock": 25, "rating": 4.9},
                {"name": "Dyson V15 Vacuum", "description": "Cordless vacuum with laser detection", "price": 749.99, "category": "Home & Garden", "brand": "Dyson", "stock": 30, "rating": 4.8},
                {"name": "Ninja Blender", "description": "High-speed blender for smoothies", "price": 159.99, "category": "Home & Garden", "brand": "Ninja", "stock": 50, "rating": 4.6},
                {"name": "Instant Pot Duo", "description": "Multi-use pressure cooker", "price": 99.99, "category": "Home & Garden", "brand": "Instant Pot", "stock": 60, "rating": 4.7},
                {"name": "Roomba i7+", "description": "Self-emptying robot vacuum", "price": 599.99, "category": "Home & Garden", "brand": "iRobot", "stock": 20, "rating": 4.5},
                {"name": "Philips Hue Starter Kit", "description": "Smart LED lighting system", "price": 199.99, "category": "Home & Garden", "brand": "Philips", "stock": 40, "rating": 4.6},
                {"name": "Weber Genesis Grill", "description": "Gas grill for outdoor cooking", "price": 899.99, "category": "Home & Garden", "brand": "Weber", "stock": 15, "rating": 4.8},
                {"name": "Shark Steam Mop", "description": "Steam cleaning mop", "price": 79.99, "category": "Home & Garden", "brand": "Shark", "stock": 45, "rating": 4.4},
                {"name": "Nest Thermostat", "description": "Smart learning thermostat", "price": 249.99, "category": "Home & Garden", "brand": "Google", "stock": 35, "rating": 4.7},
                {"name": "Ring Doorbell Pro", "description": "Smart video doorbell", "price": 199.99, "category": "Home & Garden", "brand": "Ring", "stock": 50, "rating": 4.5},
                
                # Books
                {"name": "The Great Gatsby", "description": "Classic American novel", "price": 12.99, "category": "Books", "brand": "Scribner", "stock": 200, "rating": 4.2},
                {"name": "Atomic Habits", "description": "Self-help book about building habits", "price": 16.99, "category": "Books", "brand": "Avery", "stock": 150, "rating": 4.8},
                {"name": "Where the Crawdads Sing", "description": "Mystery novel set in North Carolina", "price": 14.99, "category": "Books", "brand": "Putnam", "stock": 180, "rating": 4.6},
                {"name": "The 7 Habits", "description": "Stephen Covey's leadership book", "price": 15.99, "category": "Books", "brand": "Free Press", "stock": 120, "rating": 4.7},
                {"name": "Dune", "description": "Science fiction epic", "price": 17.99, "category": "Books", "brand": "Ace", "stock": 100, "rating": 4.5},
                {"name": "The Midnight Library", "description": "Philosophical fiction novel", "price": 13.99, "category": "Books", "brand": "Viking", "stock": 140, "rating": 4.4},
                {"name": "Becoming", "description": "Michelle Obama's memoir", "price": 19.99, "category": "Books", "brand": "Crown", "stock": 90, "rating": 4.9},
                {"name": "The Silent Patient", "description": "Psychological thriller", "price": 15.99, "category": "Books", "brand": "Celadon", "stock": 110, "rating": 4.3},
                {"name": "Educated", "description": "Memoir about education and family", "price": 16.99, "category": "Books", "brand": "Random House", "stock": 130, "rating": 4.7},
                {"name": "The Four Winds", "description": "Historical fiction about the Dust Bowl", "price": 18.99, "category": "Books", "brand": "St. Martin's", "stock": 85, "rating": 4.6},
                
                # Sports & Outdoors
                {"name": "Yeti Rambler Tumbler", "description": "Insulated stainless steel tumbler", "price": 39.99, "category": "Sports & Outdoors", "brand": "Yeti", "stock": 80, "rating": 4.8},
                {"name": "Coleman Camping Tent", "description": "4-person dome tent", "price": 149.99, "category": "Sports & Outdoors", "brand": "Coleman", "stock": 35, "rating": 4.5},
                {"name": "Hydro Flask Water Bottle", "description": "Vacuum insulated water bottle", "price": 44.99, "category": "Sports & Outdoors", "brand": "Hydro Flask", "stock": 100, "rating": 4.7},
                {"name": "REI Co-op Backpack", "description": "Hiking backpack 65L", "price": 199.99, "category": "Sports & Outdoors", "brand": "REI", "stock": 25, "rating": 4.6},
                {"name": "Patagonia Rain Jacket", "description": "Waterproof hiking jacket", "price": 229.99, "category": "Sports & Outdoors", "brand": "Patagonia", "stock": 40, "rating": 4.8},
                {"name": "Garmin Forerunner Watch", "description": "GPS running watch", "price": 349.99, "category": "Sports & Outdoors", "brand": "Garmin", "stock": 30, "rating": 4.7},
                {"name": "Wilson Tennis Racket", "description": "Professional tennis racket", "price": 189.99, "category": "Sports & Outdoors", "brand": "Wilson", "stock": 20, "rating": 4.5},
                {"name": "Spalding Basketball", "description": "Official size basketball", "price": 29.99, "category": "Sports & Outdoors", "brand": "Spalding", "stock": 60, "rating": 4.4},
                {"name": "Nike Golf Clubs", "description": "Complete golf club set", "price": 799.99, "category": "Sports & Outdoors", "brand": "Nike", "stock": 15, "rating": 4.6},
                {"name": "Fitbit Charge 5", "description": "Advanced fitness tracker", "price": 199.99, "category": "Sports & Outdoors", "brand": "Fitbit", "stock": 50, "rating": 4.3},
                
                # Beauty & Health
                {"name": "Olaplex Hair Treatment", "description": "Professional hair repair treatment", "price": 28.99, "category": "Beauty & Health", "brand": "Olaplex", "stock": 70, "rating": 4.6},
                {"name": "The Ordinary Serum", "description": "Niacinamide + Zinc serum", "price": 7.99, "category": "Beauty & Health", "brand": "The Ordinary", "stock": 150, "rating": 4.5},
                {"name": "Fenty Beauty Foundation", "description": "Full coverage foundation", "price": 39.99, "category": "Beauty & Health", "brand": "Fenty Beauty", "stock": 80, "rating": 4.7},
                {"name": "CeraVe Moisturizer", "description": "Daily facial moisturizer", "price": 16.99, "category": "Beauty & Health", "brand": "CeraVe", "stock": 120, "rating": 4.8},
                {"name": "Drunk Elephant Cleanser", "description": "Gentle foaming cleanser", "price": 34.99, "category": "Beauty & Health", "brand": "Drunk Elephant", "stock": 60, "rating": 4.6},
                {"name": "Glossier Cloud Paint", "description": "Gel-cream blush", "price": 18.99, "category": "Beauty & Health", "brand": "Glossier", "stock": 90, "rating": 4.4},
                {"name": "Sunday Riley Serum", "description": "Vitamin C brightening serum", "price": 85.99, "category": "Beauty & Health", "brand": "Sunday Riley", "stock": 40, "rating": 4.7},
                {"name": "Dyson Hair Dryer", "description": "Supersonic hair dryer", "price": 429.99, "category": "Beauty & Health", "brand": "Dyson", "stock": 25, "rating": 4.8},
                {"name": "Charlotte Tilbury Lipstick", "description": "Matte revolution lipstick", "price": 37.99, "category": "Beauty & Health", "brand": "Charlotte Tilbury", "stock": 75, "rating": 4.6},
                {"name": "Tatcha Cleanser", "description": "Rice enzyme powder cleanser", "price": 65.99, "category": "Beauty & Health", "brand": "Tatcha", "stock": 55, "rating": 4.7}
            ]
            
            for product_data in products:
                product = Product(**product_data)
                db.session.add(product)
            
            db.session.commit()
            print("Database initialized with sample products!")

# Chatbot Logic
class ChatBot:
    def __init__(self):
        self.context = {}
    
    def process_message(self, message, user_id):
        message_lower = message.lower()
        
        # Greeting
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            return {
                'message': "Hello! 👋 Welcome to ShopBot! I'm here to help you find amazing products. You can ask me to:\n\n• Search for products (e.g., 'show me laptops')\n• Find products by category\n• Get product recommendations\n• Check prices and availability\n\nWhat are you looking for today?",
                'type': 'text'
            }
        
        # Product search
        if any(word in message_lower for word in ['search', 'find', 'show', 'looking for', 'need', 'want']):
            return self.search_products(message)
        
        # Category browsing
        if any(word in message_lower for word in ['category', 'categories', 'browse']):
            return self.show_categories()
        
        # Price range queries
        if 'under' in message_lower or 'less than' in message_lower or '$' in message_lower:
            return self.search_by_price(message)
        
        # Help
        if any(word in message_lower for word in ['help', 'what can you do', 'commands']):
            return {
                'message': "I can help you with:\n\n🔍 **Product Search**: 'Find wireless headphones'\n📱 **Categories**: 'Show electronics category'\n💰 **Price Range**: 'Show products under $100'\n⭐ **Recommendations**: 'Recommend popular items'\n🛒 **Product Details**: Ask about specific products\n\nJust tell me what you're looking for!",
                'type': 'text'
            }
        
        # Default response
        return self.search_products(message)
    
    def search_products(self, query):
        # Extract search terms
        search_terms = re.findall(r'\b\w+\b', query.lower())
        
        # Search in product names, descriptions, categories, and brands
        products = Product.query.filter(
            db.or_(
                *[Product.name.ilike(f'%{term}%') for term in search_terms],
                *[Product.description.ilike(f'%{term}%') for term in search_terms],
                *[Product.category.ilike(f'%{term}%') for term in search_terms],
                *[Product.brand.ilike(f'%{term}%') for term in search_terms]
            )
        ).limit(10).all()
        
        if not products:
            return {
                'message': f"I couldn't find any products matching '{query}'. Try searching for:\n\n• Electronics (phones, laptops, headphones)\n• Clothing (shoes, jackets, jeans)\n• Home & Garden (kitchen appliances, furniture)\n• Books (fiction, self-help, mystery)\n• Sports & Outdoors (fitness, camping gear)\n• Beauty & Health (skincare, makeup)",
                'type': 'text'
            }
        
        # Format products for display
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'category': product.category,
                'brand': product.brand,
                'stock': product.stock,
                'rating': product.rating
            })
        
        return {
            'message': f"I found {len(products)} products for '{query}':",
            'type': 'products',
            'products': products_data
        }
    
    def show_categories(self):
        categories = db.session.query(Product.category).distinct().all()
        category_list = [cat[0] for cat in categories]
        
        return {
            'message': f"Here are our available categories:\n\n" + "\n".join([f"• {cat}" for cat in category_list]) + "\n\nClick on any category or tell me which one interests you!",
            'type': 'categories',
            'categories': category_list
        }
    
    def search_by_price(self, query):
        # Extract price from query
        import re
        price_match = re.search(r'\$?(\d+(?:\.\d{2})?)', query)
        if price_match:
            max_price = float(price_match.group(1))
            products = Product.query.filter(Product.price <= max_price).limit(10).all()
            
            products_data = []
            for product in products:
                products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'category': product.category,
                    'brand': product.brand,
                    'stock': product.stock,
                    'rating': product.rating
                })
            
            return {
                'message': f"Here are products under ${max_price}:",
                'type': 'products',
                'products': products_data
            }
        
        return {
            'message': "Please specify a price range (e.g., 'Show products under $100')",
            'type': 'text'
        }

# Initialize chatbot
chatbot = ChatBot()

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            return jsonify({'success': False, 'error': 'Invalid content type, expected application/json'}), 415
        
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
    
    return render_template('login.html')
    
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Username already exists'})
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already exists'})
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    message = data.get('message')
    session_id = data.get('session_id', 'default')
    
    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        message=message,
        is_user=True
    )
    db.session.add(user_msg)
    
    # Process message with chatbot
    response = chatbot.process_message(message, session['user_id'])
    
    # Save bot response
    bot_msg = ChatMessage(
        session_id=session_id,
        message=response['message'],
        is_user=False
    )
    db.session.add(bot_msg)
    db.session.commit()
    
    return jsonify(response)

@app.route('/api/products')
def get_products():
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    query = Product.query
    
    if category:
        query = query.filter(Product.category == category)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    if min_price:
        query = query.filter(Product.price >= min_price)
    
    if max_price:
        query = query.filter(Product.price <= max_price)
    
    products = query.all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'category': p.category,
        'brand': p.brand,
        'stock': p.stock,
        'rating': p.rating
    } for p in products])

@app.route('/api/chat-history/<session_id>')
def get_chat_history(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
    
    return jsonify([{
        'message': msg.message,
        'is_user': msg.is_user,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages])

if __name__ == '__main__':
    init_database()
    app.run(debug=True)