import pandas as pd
import os
from website import create_webapp, database
from website.models import Product

def import_csv():
    app = create_webapp()
    with app.app_context():
        df = pd.read_csv('amazon_products.csv')
        
        imported_count = 0
        for index, row in df.iterrows():
            if imported_count >= 500:
                break

            product_id = row['product_id']
            product_name = row['product_name']
            price = row['price(OMR)']
            description = row['about_product']
            main_category = row['main_category']
            sub_category = row['sub_category']
            
            # Check if image exists
            image_path = f'media/{product_id}.jpg'
            if os.path.exists(image_path):
                product_picture = f'/media/{product_id}.jpg'
            else:
                print(f"Image not found for {product_id}, skipping")
                continue
            
            in_stock = 10
            
            # Create product
            new_product = Product(
                product_name=product_name,
                price=price,
                description=description,
                in_stock=in_stock,
                product_picture=product_picture,
                main_category=main_category,
                sub_category=sub_category
            )
            
            database.session.add(new_product)
            imported_count += 1
        
        try:
            database.session.commit()
            print("successfully")
        except Exception as e:
            database.session.rollback()
            print(f"Error: {e}")

if __name__ == '__main__':
    import_csv()