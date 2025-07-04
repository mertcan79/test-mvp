import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid
import os

os.makedirs('data', exist_ok=True)

item_names = [
    "Tavuk Şiş", "Köfte", "Adana Dürüm", "Urfa Dürüm", "Lahmacun", "Pide", "Mantı", "İskender",
    "Pilav Üstü Tavuk", "Çorba", "Mercimek Çorbası", "Ayran", "Kola", "Fanta", "Su", "Baklava",
    "Künefe", "Sütlaç", "Cheesecake", "Tiramisu"
]

# 1. Menu data
menu_items = []
categories = ['Ana Yemek', 'Aperatif', 'İçecek', 'Tatlı']
for i in range(1, 21):
    cost = round(random.uniform(10, 50), 2)
    price = round(cost * random.uniform(1.5, 2.5), 2)
    menu_items.append({
        'item_id': i,
        'item_name': item_names[i - 1],
        'category': random.choice(categories),
        'price': price,
        'cost': cost,
        'ingredients': "|".join(random.sample(
            ['Tavuk', 'Et', 'Domates', 'Biber', 'Pirinç', 'Patates', 'Peynir', 'Yoğurt'], 
            3)),
        'available': random.choice([True, True, True, False])
    })
pd.DataFrame(menu_items).to_csv('data/menu.csv', index=False)

# 2. Inventory data
inventory = []
ingredients = set()
for itm in menu_items:
    ingredients.update(itm['ingredients'].split('|'))
ingredients = list(ingredients)
for ing in ingredients:
    inventory.append({
        'ingredient': ing,
        'stock_qty_kg': round(random.uniform(5, 50), 2),
        'restock_threshold_kg': round(random.uniform(2, 10), 2),
        'supplier': random.choice(['Metro', 'Tedarikçi A', 'Tedarikçi B'])
    })
pd.DataFrame(inventory).to_csv('data/inventory.csv', index=False)

# 3. Orders data
orders = []
start = datetime.now() - timedelta(days=30)
for oid in range(1, 501):
    dt = start + timedelta(minutes=random.randint(0, 30*24*60))
    channel = random.choice(['Yemeksepeti', 'In-Store', 'Phone', 'Trendyol'])
    n_items = random.randint(1, 5)
    chosen = random.sample(menu_items, n_items)
    items = [{'item_id': itm['item_id'], 'quantity': random.randint(1,3)} for itm in chosen]
    total_price = sum(itm['price'] * itm2['quantity'] for itm, itm2 in zip(chosen, items))
    orders.append({
        'order_id': oid,
        'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
        'channel': channel,
        'items': str(items),
        'total_price': round(total_price, 2),
        'payment_method': random.choice(['Credit Card', 'Cash', 'Wallet']),
        'location': random.choice(['Kadıköy', 'Beşiktaş', 'Üsküdar']),
        'customer_type': random.choice(['New', 'Returning'])
    })
pd.DataFrame(orders).to_csv('data/orders.csv', index=False)
