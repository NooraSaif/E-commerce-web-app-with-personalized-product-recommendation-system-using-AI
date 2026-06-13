from flask import Blueprint, render_template, flash, redirect, request, jsonify, url_for
from .models import Product, Cart, Order, user_interaction
from flask_login import login_required, current_user
from . import database
from dotenv import load_dotenv
from datetime import datetime
import stripe
import os
from .recommendation import get_engine
import logging

load_dotenv()
logger = logging.getLogger(__name__)
views = Blueprint('views', __name__)

# Stripe Configuration (Test Environment)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_SECRET_KEY = stripe.api_key
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

@views.route('/')
def home():
    selected_main_category = request.args.get('main_category', '')
    selected_sub_category = request.args.get('sub_category', '')

    product_query = Product.query.filter(Product.in_stock > 0)
    if selected_main_category:
        product_query = product_query.filter(Product.main_category == selected_main_category)
    if selected_sub_category:
        product_query = product_query.filter(Product.sub_category == selected_sub_category)

    all_products = product_query.all()
    main_categories = [row[0] for row in database.session.query(Product.main_category).distinct().order_by(Product.main_category).all()]
    # display recommendations only for authenticated users
    recommendations = get_home_recommendations(num_recs=5) if current_user.is_authenticated else []

    return render_template(
        'home.html',
        products=all_products,
        recommendations=recommendations,
        main_categories=main_categories,
        selected_main_category=selected_main_category,
        selected_sub_category=selected_sub_category,
        cart=Cart.query.filter_by(users_link=current_user.id).all() if current_user.is_authenticated else []
    )

# ==================== recommendation for uthenticated users ====================
def log_user_interaction(user_id, product_id, type):
    try:
        interaction = user_interaction.query.filter_by(
            user_id=user_id,
            product_id=product_id,
            type=type
        ).first()
        
        if interaction:
            # Update existing interaction
            interaction.interaction_count += 1
            interaction.last_interaction_date = datetime.utcnow()
        else:
            # Create new interaction
            interaction = user_interaction(
                user_id=user_id,
                product_id=product_id,
                type=type,
                interaction_count=1
            )
            database.session.add(interaction)
        
        database.session.commit()
        logger.info(f"User interaction logged: user={user_id}, product={product_id}, type={type}")
    except Exception as e:
        logger.error(f"Error logging interaction: {str(e)}")
        database.session.rollback()

# Helper function to get recommendations
def get_product_recommendations(product_id, num_recs=5):
    try:
        engine = get_engine()
        if engine is None:
            return []
        
        similarity_list = engine.get_similar_products(product_id, top_k=num_recs)
        
        if not similarity_list:
            return []
        
        # Get Product objects and filter by stock
        product_ids = [pid for pid, score in similarity_list]
        products = Product.query.filter(
            Product.id.in_(product_ids),
            Product.in_stock > 0
        ).all()
        product_map = {product.id: product for product in products}
        return [product_map[pid] for pid in product_ids if pid in product_map]
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return []


def get_home_recommendations(num_recs=5):
    engine = get_engine()
    if engine is None:
        return Product.query.filter(Product.in_stock > 0).order_by(Product.date_added.desc()).limit(num_recs).all()

    if current_user.is_authenticated:
        recommended_tuples = engine.get_personalized_recommendations(
            current_user,
            top_k=num_recs
        )
        if recommended_tuples:
            recommended_ids = [pid for pid, _ in recommended_tuples]
            products = Product.query.filter(
                Product.id.in_(recommended_ids),
                Product.in_stock > 0
            ).all()
            product_map = {product.id: product for product in products}
            return [product_map[pid] for pid in recommended_ids if pid in product_map]

    return Product.query.filter(Product.in_stock > 0).order_by(Product.date_added.desc()).limit(num_recs).all()

# ==================== CART ====================
@views.route('/add_to_cart/<int:product_id>')
@login_required
def cart(product_id):
    add_products = Product.query.get(product_id)
    product_exist = Cart.query.filter_by(products_link=product_id, users_link=current_user.id).first()
    
    # Log interaction recommendation
    log_user_interaction(current_user.id, product_id, 'add_to_cart')
    
    if product_exist:
        try:
            product_exist.quantity = product_exist.quantity + 1
            database.session.commit()
            flash(f' Quantity of { product_exist.product.product_name } has been updated')
            return redirect(request.referrer)
        except Exception as e:
            print('Quantity not Updated', e)
            flash(f'Quantity of { product_exist.product.product_name } not updated')
            return redirect(request.referrer)

    new_cart = Cart()
    new_cart.quantity = 1
    new_cart.products_link = add_products.id
    new_cart.users_link = current_user.id

    try:
        database.session.add(new_cart)
        database.session.commit()
        flash(f'{new_cart.product.product_name} added to cart')
    except Exception as e:
        print('product not added to cart', e)
        flash(f'{new_cart.product.product_name} has not been added to cart')

    return redirect(request.referrer)

@views.route('/cart')
@login_required
def display_cart():
    cart = Cart.query.filter_by(users_link=current_user.id).all()
    amount = 0
    for product in cart:
        amount += product.product.price * product.quantity

    return render_template('cart.html', cart=cart, amount=f"{amount:.3f}", total=f"{amount+2:.3f}")

@views.route('/plus_cart')
@login_required
def plus_quantity():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_product = Cart.query.get(cart_id)
        cart_product.quantity = cart_product.quantity + 1
        database.session.commit()

        cart = Cart.query.filter_by(users_link=current_user.id).all()

        amount = 0

        for product in cart:
            amount += product.product.price * product.quantity

        details = {
            'quantity': cart_product.quantity,
            'amount': f"{amount:.3f}",
            'total': f"{amount + 2:.3f}"
        }

    return jsonify(details)

@views.route('/minus_cart')
@login_required
def minus_quantity():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_product = Cart.query.get(cart_id)
        cart_product.quantity = cart_product.quantity - 1
        database.session.commit()

        cart = Cart.query.filter_by(users_link=current_user.id).all()

        amount = 0

        for product in cart:
            amount += product.product.price * product.quantity

        details = {
            'quantity': cart_product.quantity,
            'amount': f"{amount:.3f}",
            'total': f"{amount + 2:.3f}"
        }

    return jsonify(details)

@views.route('remove_cart_product')
@login_required
def remove_product():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_product = Cart.query.get(cart_id)
        database.session.delete(cart_product)
        database.session.commit()

        cart = Cart.query.filter_by(users_link=current_user.id).all()

        amount = 0

        for product in cart:
            amount += product.product.price * product.quantity

        details = {
            'quantity': cart_product.quantity,
            'amount': f"{amount:.3f}",
            'total': f"{amount + 2:.3f}"
        }

        return jsonify(details)

@views.route('/checkout')
@login_required
def checkout():
    user_cart = Cart.query.filter_by(users_link=current_user.id).all()
    if not user_cart:
        flash('Your cart is Empty')
        return redirect('/')

    amount = 0
    for product in user_cart:
        amount += product.product.price * product.quantity

    total = f"{amount + 2:.3f}"

    return render_template('checkout.html', cart=user_cart, total=total, stripe_publishable_key=STRIPE_PUBLISHABLE_KEY)


# ==================== Stripe Payment ====================
@views.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent():
    try:
        user_cart = Cart.query.filter_by(users_link=current_user.id).all()
        if not user_cart:
            return jsonify({'error': 'Cart is empty'}), 400

        total_amount = 0
        for product in user_cart:
            total_amount += product.product.price * product.quantity
        total_amount += 2  # Shipping
        
        #assuming 1 OMR = 10 AED
        conversion_rate = 10
        total_in_AED = conversion_rate * total_amount
        
        # Stripe expects amount in cents
        amount_in_cents = int(total_in_AED * 100)

        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='aed',
            automatic_payment_methods={'enabled': True},
            metadata={'user_id': current_user.id}
        )
        return jsonify({'clientSecret': payment_intent.client_secret})
    except Exception as e:
        print(f"Error creating Payment Intent: {e}")
        return jsonify(error=str(e)), 403


@views.route('/confirm-stripe-payment', methods=['POST'])
@login_required
def confirm_stripe_payment():
    data = request.json
    payment_intent_id = data.get('paymentIntentId')

    if not payment_intent_id:
        return jsonify({'error': 'Payment Intent ID is missing'}), 400

    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Verify payment is successful
        if payment_intent.status == 'succeeded':
            try:
                user_cart = Cart.query.filter_by(users_link=current_user.id).all()
                
                if not user_cart:
                    logger.warning(f"No cart items found for user {current_user.id}")
                    return jsonify({'status': 'error', 'message': 'Cart is empty'}), 400
                
                # Process orders
                for product in user_cart:
                    new_order = Order()
                    new_order.quantity = product.quantity
                    new_order.price = product.product.price
                    new_order.status = 'Confirmed'
                    new_order.payment_id = payment_intent_id
                    new_order.products_link = product.products_link
                    new_order.users_link = product.users_link
                    
                    # Update inventory
                    products = Product.query.get(product.products_link)
                    if products:
                        products.in_stock -= product.quantity
                    else:
                        logger.warning(f"Product {product.products_link} not found for order")
                        
                    database.session.add(new_order)
                    database.session.delete(product)
                
                database.session.commit()
                logger.info(f"Order placed successfully for user {current_user.id}")
                return jsonify({'status': 'success', 'redirect_url': url_for('views.user_orders')})
                
            except Exception as db_error:
                database.session.rollback()
                logger.error(f"Database error while processing order: {str(db_error)}")
                print(f"Database Error confirming order: {db_error}")
                return jsonify({'status': 'error', 'message': f'Database error: {str(db_error)}'}), 500
        else:
            return jsonify({'status': 'failed', 'message': f'Payment not succeeded. Status: {payment_intent.status}'}), 400

    except stripe.error.StripeError as e:
        print(f"Stripe Error confirming order: {e}")
        logger.error(f"Stripe error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        print(f"General Error confirming order: {e}")
        logger.error(f"General error confirming order: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred.'}), 500

# ==================== ORDERS ====================
@views.route('/my_orders')
@login_required
def user_orders():
    payment_intent_id = request.args.get('payment_intent')
    
    # Process payment if coming from Stripe redirect
    if payment_intent_id:
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status == 'succeeded':
                user_cart = Cart.query.filter_by(users_link=current_user.id).all()
                
                if user_cart:
                    try:
                        # Process orders
                        for product in user_cart:
                            new_order = Order()
                            new_order.quantity = product.quantity
                            new_order.price = product.product.price
                            new_order.status = 'Confirmed'
                            new_order.payment_id = payment_intent_id 
                            new_order.products_link = product.products_link
                            new_order.users_link = product.users_link
                            
                            # Update inventory
                            products = Product.query.get(product.products_link)
                            if products:
                                products.in_stock -= product.quantity
                            
                            database.session.add(new_order)
                            database.session.delete(product)
                        
                        database.session.commit()
                        logger.info(f"Order placed successfully for user {current_user.id} with payment {payment_intent_id}")
                        flash('Order Placed Successfully')
                    except Exception as db_error:
                        database.session.rollback()
                        logger.error(f"Database error while processing order: {str(db_error)}")
                        flash(f'Error saving order: {str(db_error)}')
                        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying payment: {str(e)}")
            flash(f'Error verifying payment: {str(e)}')
        except Exception as e:
            logger.error(f"Error processing payment from redirect: {str(e)}")
            flash('An error occurred while processing your order.')

    orders = Order.query.filter_by(users_link=current_user.id).all()
    return render_template('my_orders.html', orders=orders)

# ===================== SEARCH ====================
@views.route('/search', methods=['GET', 'POST'])
def find_product():
    if request.method == 'POST':
        find_product = request.form.get('search')
        products = Product.query.filter(Product.product_name.ilike(f'%{find_product}%')).all()
        return render_template('search.html', products=products, cart=Cart.query.filter_by(users_link=current_user.id).all()
                           if current_user.is_authenticated else [])

    return render_template('search.html')

# ==================== RECOMMENDATION ====================

@views.route('/api/recommendations/<int:product_id>')
def get_recommendations_api(product_id):
    try:
        num_recs = request.args.get('num_recs', 5, type=int)
        num_recs = min(num_recs, 10) 
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Log view interaction
        if current_user.is_authenticated:
            log_user_interaction(current_user.id, product_id, 'view')
        
        # Get recommendations
        engine = get_engine()
        if engine is None:
            return jsonify({'recommendations': [], 'message': 'Recommendation engine not available'}), 200
        
        similarity_list = engine.get_similar_products(product_id, top_k=num_recs)
        
        if not similarity_list:
            return jsonify({'recommendations': []}), 200
        
        # Build response with product details
        recommendations = []
        for pid, score in similarity_list:
            prod = Product.query.get(pid)
            if prod and prod.in_stock > 0:
                recommendations.append({
                    'id': prod.id,
                    'name': prod.product_name,
                    'price': prod.price,
                    'image': prod.product_picture,
                    'similarity_score': round(float(score), 2),
                    'in_stock': prod.in_stock
                })
        
        return jsonify({
            'product_id': product_id,
            'product_name': product.product_name,
            'recommendations': recommendations[:num_recs]
        }), 200
        
    except Exception as e:
        logger.error(f"Error in recommendations API: {str(e)}")
        return jsonify({'error': str(e)}), 500


@views.route('/api/personalized-recommendations')
@login_required
def get_personalized_recommendations_api():
    try:
        num_recs = request.args.get('num_recs', 10, type=int)
        num_recs = min(num_recs, 15)  # Cap at 15
        
        engine = get_engine()
        if engine is None:
            return jsonify({
                'recommendations': [],
                'message': 'Recommendation engine not available'
            }), 200
        
        # Get personalized recommendations
        recommendations_tuples = engine.get_personalized_recommendations(
            current_user,
            top_k=num_recs
        )
        
        if not recommendations_tuples:
            # return new arrival products
            popular_products = Product.query.filter(
                Product.in_stock > 0
            ).order_by(Product.id.desc()).limit(num_recs).all()
            
            recommendations = [{
                'id': p.id,
                'name': p.product_name,
                'price': p.price,
                'image': p.product_picture,
                'score': 0.0,
                'in_stock': p.in_stock
            } for p in popular_products]
            
            return jsonify({
                'recommendations': recommendations,
                'message': 'Popular products (no history yet)'
            }), 200
        
        # Build response with product details
        recommendations = []
        for pid, score in recommendations_tuples:
            prod = Product.query.get(pid)
            if prod and prod.in_stock > 0:
                recommendations.append({
                    'id': prod.id,
                    'name': prod.product_name,
                    'price': prod.price,
                    'image': prod.product_picture,
                    'score': round(float(score), 3),
                    'in_stock': prod.in_stock
                })
        
        return jsonify({
            'user_id': current_user.id,
            'recommendations': recommendations,
            'total_interactions': len(current_user.interactions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in personalized recommendations API: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== PRODUCT DETAIL ====================
@views.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            flash('Product not found')
            return redirect('/')
        
        # Log view interaction
        if current_user.is_authenticated:
            log_user_interaction(current_user.id, product_id, 'view')
        
        # Get recommendations for this product
        recommendations = get_product_recommendations(product_id, num_recs=5)
        
        return render_template(
            'product_detail.html',
            product=product,
            recommendations=recommendations,
            cart=Cart.query.filter_by(users_link=current_user.id).all()
            if current_user.is_authenticated else []
        )
    except Exception as e:
        logger.error(f"Error loading product detail: {str(e)}")
        flash('Error loading product')
        return redirect('/')
