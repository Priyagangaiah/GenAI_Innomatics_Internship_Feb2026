from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# --- Data Store ---
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Mechanical Keyboard", "price": 1999, "category": "Electronics", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 99, "category": "Stationery", "in_stock": True},
]

# --- Models ---
class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

# --- Helper Functions ---
def find_product(product_id: int):
    return next((p for p in products if p['id'] == product_id), None)

# --- Routes ---

@app.get('/products')
def get_all_products():
    return {"products": products, "total": len(products)}

# Q5: Inventory Audit (Placed ABOVE the dynamic {product_id} route)
@app.get('/products/audit')
def get_inventory_audit():
    total_count = len(products)
    in_stock_items = [p for p in products if p['in_stock']]
    out_of_stock_names = [p['name'] for p in products if not p['in_stock']]
    
    # Calculation: Sum of (Price * 10 units) for in-stock items
    total_val = sum(p['price'] * 10 for p in in_stock_items)
    
    # Logic for most expensive product
    most_expensive = None
    if products:
        m_item = max(products, key=lambda x: x['price'])
        most_expensive = {"name": m_item['name'], "price": m_item['price']}

    return {
        "total_products": total_count,
        "in_stock_count": len(in_stock_items),
        "out_of_stock_names": out_of_stock_names,
        "total_stock_value": total_val,
        "most_expensive": most_expensive
    }

@app.get('/products/{product_id}')
def get_product_by_id(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    return product

# Q1 & Q4: Add Product
@app.post('/products', status_code=status.HTTP_201_CREATED)
def add_product(new_item: NewProduct, response: Response):
    # Check for duplicate names
    if any(p['name'].lower() == new_item.name.lower() for p in products):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": f"Product '{new_item.name}' already exists"}
    
    # Auto-generate ID
    new_id = max(p['id'] for p in products) + 1 if products else 1
    
    product_dict = new_item.model_dump()
    product_dict['id'] = new_id
    products.append(product_dict)
    
    return {"message": "Product added", "product": product_dict}

# Q2 & Q4: Update Product
@app.put('/products/{product_id}')
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None, response: Response = None):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    
    if price is not None:
        product['price'] = price
    
    # Note: Use 'is not None' because False is a valid value
    if in_stock is not None:
        product['in_stock'] = in_stock
        
    return {"message": "Product updated", "product": product}

# Q3 & Q4: Delete Product
@app.delete('/products/{product_id}')
def delete_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    
    products.remove(product)
    return {"message": f"Product '{product['name']}' deleted"}


@app.put('/products/discount')
def apply_category_discount(category: str, discount_percent: int, response: Response):
    # Validation: discount must be between 1 and 99
    if not (1 <= discount_percent <= 99):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Discount percent must be between 1 and 99"}

    updated_products = []
    
    # Loop through all products
    for product in products:
        if product['category'].lower() == category.lower():
            # Apply the math formula: new_price = price * (1 - discount/100)
            product['price'] = int(product['price'] * (1 - discount_percent / 100))
            updated_products.append({"name": product['name'], "new_price": product['price']})

    # If no products were found in that category
    if not updated_products:
        return {"message": f"No products found in category '{category}'"}

    return {
        "message": f"Applied {discount_percent}% discount to {category}",
        "updated_count": len(updated_products),
        "updates": updated_products
    }

    