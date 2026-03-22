from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import math

app = FastAPI()

# ----------------------------
# Day 1: Data & GET endpoints
# ----------------------------
menu = [
    {"id":1,"name":"Margherita Pizza","price":250,"category":"Pizza","is_available":True},
    {"id":2,"name":"Pepperoni Pizza","price":300,"category":"Pizza","is_available":True},
    {"id":3,"name":"Cheeseburger","price":150,"category":"Burger","is_available":True},
    {"id":4,"name":"Coke","price":50,"category":"Drink","is_available":True},
    {"id":5,"name":"Brownie","price":100,"category":"Dessert","is_available":False},
    {"id":6,"name":"Veggie Burger","price":140,"category":"Burger","is_available":True},
]

orders = []
order_counter = 1
cart = []

@app.get("/")
def home():
    return {"message":"Welcome to QuickBite Food Delivery"}

@app.get("/menu")
def get_menu():
    return {"total": len(menu), "items": menu}

@app.get("/menu/summary")
def menu_summary():
    available = sum(item["is_available"] for item in menu)
    unavailable = len(menu) - available
    categories = list({item["category"] for item in menu})
    return {"total_items": len(menu), "available": available, "unavailable": unavailable, "categories": categories}

@app.get("/menu/{item_id}")
def get_menu_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/orders")
def get_orders():
    return {"total_orders": len(orders), "orders": orders}

# ----------------------------
# Day 2 & 3: Pydantic + Helpers
# ----------------------------
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: Optional[str] = "delivery"

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

def find_menu_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None

def calculate_bill(price: int, quantity: int, order_type: str = "delivery"):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total

def filter_menu_logic(category: Optional[str]=None, max_price: Optional[int]=None, is_available: Optional[bool]=None):
    result = menu
    if category is not None:
        result = [i for i in result if i["category"].lower() == category.lower()]
    if max_price is not None:
        result = [i for i in result if i["price"] <= max_price]
    if is_available is not None:
        result = [i for i in result if i["is_available"] == is_available]
    return result

@app.post("/orders")
def place_order(req: OrderRequest):
    global order_counter
    item = find_menu_item(req.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item["is_available"]:
        raise HTTPException(status_code=400, detail="Item unavailable")
    total = calculate_bill(item["price"], req.quantity, req.order_type)
    order = {"order_id": order_counter, "item": item, "quantity": req.quantity,
             "customer_name": req.customer_name, "delivery_address": req.delivery_address,
             "order_type": req.order_type, "total_price": total}
    orders.append(order)
    order_counter += 1
    return order

@app.get("/menu/filter")
def menu_filter(category: Optional[str]=None, max_price: Optional[int]=None, is_available: Optional[bool]=None):
    filtered = filter_menu_logic(category, max_price, is_available)
    return {"count": len(filtered), "items": filtered}

# ----------------------------
# Day 4: CRUD Menu
# ----------------------------
class NewMenuItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    is_available: Optional[bool] = True

@app.post("/menu")
def add_menu_item(item: NewMenuItem):
    if any(i["name"].lower() == item.name.lower() for i in menu):
        raise HTTPException(status_code=400, detail="Duplicate item name")
    new_id = max(i["id"] for i in menu)+1
    new_item = item.dict()
    new_item["id"] = new_id
    menu.append(new_item)
    return new_item

@app.put("/menu/{item_id}")
def update_menu_item(item_id: int, price: Optional[int]=None, is_available: Optional[bool]=None):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if price is not None:
        item["price"] = price
    if is_available is not None:
        item["is_available"] = is_available
    return item

@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    menu.remove(item)
    return {"message": f"{item['name']} deleted successfully"}

# ----------------------------
# Day 5: Cart / Workflow
# ----------------------------
@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)
    if not item or not item["is_available"]:
        raise HTTPException(status_code=400, detail="Item not available")
    for c in cart:
        if c["item"]["id"] == item_id:
            c["quantity"] += quantity
            return c
    cart_item = {"item": item, "quantity": quantity}
    cart.append(cart_item)
    return cart_item

@app.get("/cart")
def get_cart():
    grand_total = sum(calculate_bill(c["item"]["price"], c["quantity"]) for c in cart)
    return {"grand_total": grand_total, "items": cart}

@app.delete("/cart/{item_id}")
def remove_from_cart(item_id: int):
    for c in cart:
        if c["item"]["id"] == item_id:
            cart.remove(c)
            return {"message": f"{c['item']['name']} removed from cart"}
    raise HTTPException(status_code=404, detail="Item not in cart")

@app.post("/cart/checkout")
def checkout(req: CheckoutRequest):
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    global order_counter
    placed_orders = []
    total = 0
    for c in cart:
        o_total = calculate_bill(c["item"]["price"], c["quantity"])
        order = {"order_id": order_counter, "item": c["item"], "quantity": c["quantity"],
                 "customer_name": req.customer_name, "delivery_address": req.delivery_address,
                 "order_type": "delivery", "total_price": o_total}
        orders.append(order)
        order_counter += 1
        total += o_total
        placed_orders.append(order)
    cart.clear()
    return {"grand_total": total, "placed_orders": placed_orders}

# ----------------------------
# Day 6: Search, Sort, Pagination
# ----------------------------
@app.get("/menu/search")
def search_menu(keyword: str):
    keyword_lower = keyword.lower()
    found = [i for i in menu if keyword_lower in i["name"].lower() or keyword_lower in i["category"].lower()]
    if not found:
        return {"message":"No items found for your search"}
    return {"total_found": len(found), "items": found}

@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price","name","category"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by")
    if order not in ["asc","desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")
    sorted_menu = sorted(menu, key=lambda x: x[sort_by], reverse=(order=="desc"))
    return {"sort_by": sort_by, "order": order, "items": sorted_menu}

@app.get("/menu/page")
def paginate_menu(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    start = (page-1)*limit
    items = menu[start:start+limit]
    total_pages = math.ceil(len(menu)/limit)
    return {"page": page, "limit": limit, "total": len(menu), "total_pages": total_pages, "items": items}

@app.get("/orders/search")
def search_orders(customer_name: str):
    cn_lower = customer_name.lower()
    found = [o for o in orders if cn_lower in o["customer_name"].lower()]
    return {"total_found": len(found), "orders": found}

@app.get("/orders/sort")
def sort_orders(order: str = "asc"):
    sorted_orders = sorted(orders, key=lambda o: o["total_price"], reverse=(order=="desc"))
    return {"order": order, "orders": sorted_orders}

@app.get("/menu/browse")
def browse_menu(keyword: Optional[str]=None, sort_by: str="price", order: str="asc",
                page: int=1, limit: int=4):
    result = menu
    if keyword:
        result = [i for i in result if keyword.lower() in i["name"].lower() or keyword.lower() in i["category"].lower()]
    if sort_by not in ["price","name","category"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by")
    result = sorted(result, key=lambda x: x[sort_by], reverse=(order=="desc"))
    start = (page-1)*limit
    items_page = result[start:start+limit]
    total_pages = math.ceil(len(result)/limit)
    return {"page": page, "limit": limit, "total": len(result), "total_pages": total_pages, "items": items_page}
