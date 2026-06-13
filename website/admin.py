from flask import Blueprint, render_template, flash, send_from_directory, redirect, request
from flask_login import login_required, current_user
from .forms import ProductsForm, OrderForm
from werkzeug.utils import secure_filename
from .models import Product, Order, User
from . import database

admin = Blueprint('admin', __name__)

# to display image from media in products page
@admin.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)

@admin.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.id == 1:
        form = ProductsForm()

        if form.validate_on_submit():
            product_name = form.product_name.data
            price = form.price.data
            description = form.description.data
            in_stock = form.in_stock.data
            main_category = form.main_category.data
            sub_category = form.sub_category.data

            file = form.product_picture.data
            if not file:
                flash('Product Picture is required for new items!')
                return render_template('add_product.html', form=form)

            file_name = secure_filename(file.filename)
            file_path = f'./media/{file_name}'
            file.save(file_path)

            new_product = Product()
            new_product.product_name = product_name
            new_product.price = price
            new_product.description = description
            new_product.in_stock = in_stock
            new_product.main_category = main_category
            new_product.sub_category = sub_category

            new_product.product_picture = file_path

            try:
                database.session.add(new_product)
                database.session.commit()
                flash(f'{product_name} added Successfully')
                print('Product Added')
                return render_template('add_product.html', form=form)
            except Exception as e:
                print(e)
                flash('Product Not Added!!')

        return render_template('add_product.html', form=form)
    
    return render_template('404.html')

@admin.route('/view_products', methods=['GET', 'POST'])
@login_required
def view_products():
    if current_user.id == 1:
        products = Product.query.order_by(Product.date_added).all()
        return render_template('view_products.html', products=products)
    return render_template('404.html')

@admin.route('/update_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def update_product(product_id):
    if current_user.id == 1:
        update = Product.query.get_or_404(product_id)
        form = ProductsForm(request.form, obj=update)

        if form.validate_on_submit() and form.update_product.data:
            update.product_name = form.product_name.data
            update.price = form.price.data
            update.description = form.description.data
            update.in_stock = form.in_stock.data
            update.main_category = form.main_category.data
            update.sub_category = form.sub_category.data
            
            file = form.product_picture.data
            if file and getattr(file, 'filename', None):
                file_name = secure_filename(file.filename)
                file_path = f'./media/{file_name}'
                file.save(file_path)
                update.product_picture = file_path

            database.session.add(update)
            try:
                database.session.commit()
                flash(f'{update.product_name} updated Successfully')
                print('Product Upadted')
                return redirect('/view_products')
            except Exception as e:
                print('Product not Upated', e)
                flash('Item Not Updated!!!')

        return render_template('update_product.html', form=form, product=update)
    return render_template('404.html')

@admin.route('/delete_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    if current_user.id == 1:
        try:
            delete = Product.query.get(product_id)
            database.session.delete(delete)
            database.session.commit()
            flash('One product deleted')
            return redirect('/view_products')
        except Exception as e:
            flash('product not deleted!!')
        return redirect('/view_products')

    return render_template('404.html')

@admin.route('/view_orders')
@login_required
def view_orders():
    if current_user.id == 1:
        orders = Order.query.all()
        return render_template('view_orders.html', orders=orders)
    return render_template('404.html')

@admin.route('/update_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def update_status(order_id):
    if current_user.id == 1:
        form = OrderForm()

        order = Order.query.get(order_id)

        if form.validate_on_submit():
            change_status = form.status.data
            order.status = change_status

            try:
                database.session.commit()
                flash(f'Order {order_id} Updated successfully')
                return redirect('/view_orders')
            except Exception as e:
                print(e)
                flash(f'Order {order_id} not updated')
                return redirect('/update_order')

        return render_template('update_order.html', form=form)

    return render_template('404.html')

@admin.route('/view_customers')
@login_required
def view_customers():
    if current_user.id == 1:
        users = User.query.all()
        return render_template('view_customers.html', user=users)
    return render_template('404.html')

@admin.route('/admin')
@login_required
def admin_dashbord():
    if current_user.id == 1:
        return render_template('admin.html')
    return render_template('404.html')