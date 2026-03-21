from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# -----------------------------
# Dummy Database
# -----------------------------
foods = [
    {"id": 1, "name": "Pizza", "price": 250, "category": "Italian"},
    {"id": 2, "name": "Burger", "price": 120, "category": "Fast Food"},
    {"id": 3, "name": "Biryani", "price": 200, "category": "Indian"},
]

cart = []
orders = []

# -----------------------------
# Pydantic Models
# -----------------------------
class Food(BaseModel):
    id: int
    name: str = Field(..., min_length=2)
    price: float = Field(..., gt=0)
    category: str

class CartItem(BaseModel):
    food_id: int
    quantity: int = Field(..., gt=0)

# -----------------------------
# Helper Functions
# -----------------------------
def find_food(food_id: int):
    for food in foods:
        if food["id"] == food_id:
            return food
    return None

def calculate_total(cart_items):
    total = 0
    for item in cart_items:
        food = find_food(item["food_id"])
        if food:
            total += food["price"] * item["quantity"]
    return total

# -----------------------------
# Q1 Home Route
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Food Delivery App"}

# -----------------------------
# Q4 Count API
# Fixed route first
# -----------------------------
@app.get("/foods/count")
def count_foods():
    return {"total_foods": len(foods)}

# -----------------------------
# Q8 Search Food
# Fixed route first
# -----------------------------
@app.get("/foods/search")
def search_food(keyword: str = Query(...)):
    result = [food for food in foods if keyword.lower() in food["name"].lower()]
    return result

# -----------------------------
# Q19 Combined Browse
# Fixed route first
# -----------------------------
@app.get("/foods/browse")
def browse_foods(
    keyword: Optional[str] = None,
    sort_by: Optional[str] = "id",
    order: Optional[str] = "asc",
    page: int = 1,
    limit: int = 10
):
    result = foods

    # Search
    if keyword:
        result = [f for f in result if keyword.lower() in f["name"].lower()]

    # Validate sort field
    if sort_by not in ["id", "name", "price", "category"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    # Sort
    reverse = order.lower() == "desc"
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    # Pagination
    start = (page - 1) * limit
    end = start + limit

    return {
        "total_results": len(result),
        "page": page,
        "limit": limit,
        "foods": result[start:end]
    }

# -----------------------------
# Q2 Get All Foods
# -----------------------------
@app.get("/foods")
def get_foods(
    sort_by: Optional[str] = None,
    order: Optional[str] = "asc",
    page: int = 1,
    limit: int = 10
):
    result = foods.copy()

    # Sorting
    if sort_by:
        reverse = True if order == "desc" else False
        result = sorted(result, key=lambda x: x.get(sort_by, ""), reverse=reverse)

    # Pagination
    start = (page - 1) * limit
    end = start + limit
    return result[start:end]

# -----------------------------
# Q3 Get Food by ID
# Variable route last
# -----------------------------
@app.get("/foods/{food_id}")
def get_food(food_id: int):
    food = find_food(food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    return food

# -----------------------------
# Q5 Create Food
# -----------------------------
@app.post("/foods", status_code=201)
def create_food(food: Food):
    if find_food(food.id):
        raise HTTPException(status_code=400, detail="Food already exists")
    foods.append(food.dict())
    return {"message": "Food added successfully"}

# -----------------------------
# Q6 Update Food
# -----------------------------
@app.put("/foods/{food_id}")
def update_food(food_id: int, updated_food: Food):
    food = find_food(food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    food.update(updated_food.dict())
    return {"message": "Food updated successfully"}

# -----------------------------
# Q7 Delete Food
# -----------------------------
@app.delete("/foods/{food_id}")
def delete_food(food_id: int):
    food = find_food(food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    foods.remove(food)
    return {"message": "Food deleted successfully"}

# -----------------------------
# Q9 Add to Cart
# -----------------------------
@app.post("/cart/add")
def add_to_cart(item: CartItem):
    food = find_food(item.food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    cart.append(item.dict())
    return {"message": "Item added to cart"}

# -----------------------------
# Q10 View Cart
# -----------------------------
@app.get("/cart")
def view_cart():
    return {
        "cart_items": cart,
        "total": calculate_total(cart)
    }

# -----------------------------
# Q11 Clear Cart
# -----------------------------
@app.delete("/cart/clear")
def clear_cart():
    cart.clear()
    return {"message": "Cart cleared"}

# -----------------------------
# Q12 Create Order
# -----------------------------
@app.post("/order/create")
def create_order():
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    total = calculate_total(cart)
    order = {
        "order_id": len(orders) + 1,
        "items": cart.copy(),
        "total": total,
        "status": "created"
    }
    orders.append(order)
    cart.clear()
    return {"message": "Order created", "order": order}

# -----------------------------
# Q13 Get All Orders
# -----------------------------
@app.get("/orders")
def get_orders():
    return orders

# -----------------------------
# Q14 Get Order by ID
# -----------------------------
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return order
    raise HTTPException(status_code=404, detail="Order not found")

# -----------------------------
# Q15 Update Order Status
# -----------------------------
@app.put("/orders/{order_id}")
def update_order(order_id: int, status: str):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = status
            return {"message": "Order updated"}
    raise HTTPException(status_code=404, detail="Order not found")

# -----------------------------
# Q16 Delete Order
# -----------------------------
@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            orders.remove(order)
            return {"message": "Order deleted"}
    raise HTTPException(status_code=404, detail="Order not found")

# -----------------------------
# Q17 Checkout Order
# -----------------------------
@app.post("/order/checkout/{order_id}")
def checkout(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "out for delivery"
            return {"message": "Order is out for delivery"}
    raise HTTPException(status_code=404, detail="Order not found")

# -----------------------------
# Q18 Delivery Complete
# -----------------------------
@app.post("/order/delivered/{order_id}")
def delivered(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "delivered"
            return {"message": "Order delivered"}
    raise HTTPException(status_code=404, detail="Order not found")

# -----------------------------
# Q20 Summary API
# -----------------------------
@app.get("/summary")
def summary():
    return {
        "total_foods": len(foods),
        "total_orders": len(orders),
        "cart_items": len(cart)
    }