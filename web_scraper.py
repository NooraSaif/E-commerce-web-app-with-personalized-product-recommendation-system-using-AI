import os
import pandas as pd
import requests
import time
import re

# Create a directory to save images
if not os.path.exists('media'):
    os.makedirs('media')

# Load the dataset
dataset = 'amazon_products.csv' 
df = pd.read_csv(dataset)

def clean_amazon_url(url):
    if pd.isna(url) or 'images/I/' not in str(url):
        return url
    match = re.search(r'images/I/([^._]+)', str(url))
    if match:
        return f"https://m.media-amazon.com/images/I/{match.group(1)}.jpg"
    return url

for index, row in df.iterrows():
    product_name = row['product_name']
    product_id = row['product_id']
    
    img_link = clean_amazon_url(row['img_link'])

    if img_link and str(img_link).startswith('http'):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            image_response = requests.get(img_link, headers=headers, timeout=10)
            if image_response.status_code == 200:
                with open(f'media/{product_id}.jpg', 'wb') as f:
                    f.write(image_response.content)
                print(f"Downloaded image for {product_id}")
            else:
                print(f"Failed to download {product_id}: Status {image_response.status_code}")
        except Exception as e:
            print(f"Error downloading image for {product_name} ({product_id}): {e}")
    time.sleep(0.1) 
