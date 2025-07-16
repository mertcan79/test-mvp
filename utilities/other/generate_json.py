import json
import random
from datetime import datetime, timedelta

# Sample product catalog and features
product_catalog = [
    {"productName": "TÜRK KAHVESİ", "unitPrice": 25.00, "feature": "ORTA"},
    {"productName": "MEYVELİ SODA", "unitPrice": 12.00, "feature": "ELMA"},
    {"productName": "CHURCHİLL", "unitPrice": 25.00, "feature": ""},
    {"productName": "AYRAN", "unitPrice": 10.00, "feature": ""},
    {"productName": "LAHMACUN", "unitPrice": 35.00, "feature": "ACI"},
    {"productName": "TAVUK DÖNER", "unitPrice": 40.00, "feature": "EKMEKSİZ"},
    {"productName": "KÖFTE", "unitPrice": 45.00, "feature": "AZ PİŞMİŞ"},
]

waiters = ["Azad Gok", "Ece Kaya", "Yusuf Demir", "Ayşe Yıldız"]
tables = [f"Masa {i}" for i in range(1, 31)]
sales_channels = ["Ana Kanal", "Yemeksepeti", "Getir Yemek", "Trendyol"]

orders = []
for i in range(100):
    order_id = random.randint(100000000, 999999999)
    insert_date = datetime(2023, 8, random.randint(1, 30), random.randint(10, 21), random.randint(0, 59))
    update_date = insert_date + timedelta(minutes=random.randint(10, 45))
    num_products = random.randint(1, 4)

    products = []
    total_amount = 0
    for _ in range(num_products):
        prod = random.choice(product_catalog)
        quantity = random.randint(1, 3)
        price = prod["unitPrice"]
        product_total = price * quantity
        total_amount += product_total
        product_id = random.randint(1000000, 9999999)
        prod_entry = {
            "id": random.randint(100000000, 999999999),
            "orderId": order_id,
            "quantity": float(quantity),
            "unitPrice": price,
            "productName": prod["productName"],
            "productNote": None,
            "productCode": None,
            "productUnitId": random.randint(1000000, 9999999),
            "isMenu": False,
            "parentId": None,
            "cost": 0.0,
            "totalAmount": product_total,
            "groupName": None,
            "groupId": 0,
            "unitId": 4,
            "productId": product_id,
            "discountAmount": 0.00,
            "insertDate": insert_date.isoformat(),
            "description": None,
            "cancelReason": None,
            "features": [
                {
                    "featureName": prod["feature"],
                    "additionalPrice": 0.00,
                    "featureId": random.randint(100000, 999999),
                    "orderDetailId": random.randint(100000000, 999999999)
                }
            ] if prod["feature"] else []
        }
        products.append(prod_entry)

    tax_amount = round(total_amount * 0.10, 2)
    order_entry = {
        "id": order_id,
        "waiterName": random.choice(waiters),
        "deliveryUserName": None,
        "externalAppName": None,
        "restaurantName": None,
        "orderTotal": round(total_amount, 2),
        "paymentMethodName": "Nakit",
        "paymentMethodId": 1,
        "deliveryTime": None,
        "discountAmount": 0.00,
        "currency": "TRY",
        "orderNote": None,
        "salesChannelId": random.randint(10000, 99999),
        "salesChannelName": random.choice(sales_channels),
        "externalAppId": None,
        "statusId": 7,
        "status": "Kapandı",
        "integrationRestaurantName": None,
        "orderCancelReason": None,
        "tableName": random.choice(tables),
        "orderNumber": i + 1,
        "taxAmount": tax_amount,
        "insertDate": insert_date.isoformat(),
        "updateDate": update_date.isoformat(),
        "orderTypeId": 1,
        "orderType": "Masa Siparişi",
        "customerId": 0,
        "integrationOrderId": None,
        "restaurantKey": 38910,
        "externalAppKey": 0,
        "customer": None,
        "products": products,
        "payments": [
            {
                "orderId": order_id,
                "paymentTypeId": 1,
                "paymentName": "Nakit",
                "amount": round(total_amount, 2),
                "customerId": None,
                "customerName": None,
                "customerSurname": None,
                "isDebit": False,
                "currencyId": 1,
                "currency": "TRY",
                "exchangeRate": 1.00,
                "insertDate": update_date.isoformat()
            }
        ]
    }
    orders.append(order_entry)

mock_data = {
    "orders": orders,
    "closedOrdersReceived": 99,
    "canceledOrdersReceived": 1,
    "totalCount": 100,
    "pageCount": 1,
    "status": 100,
    "message": "İşlem Başarılı!"
}

# Save to JSON
with open("data/mock_adisyo_orders.json", "w", encoding="utf-8") as f:
    json.dump(mock_data, f, ensure_ascii=False, indent=2)
