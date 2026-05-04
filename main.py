from easy import SQL
from flask import Flask, render_template, request, redirect, url_for, session
from argon2 import PasswordHasher
from datetime import date, datetime
import secrets

db = SQL("database.db")
ph = PasswordHasher()
app = Flask(__name__)

app.secret_key = "bD097anDna46amLD20nA"

from queries import init_database
init_database(db) 
# This checks to see if there is any DB file yet, 
# if not it then builds the databases for you and seeds them with some test data.

@app.route("/")
def landing_page():
    query_producers = """
        SELECT producerID, name, description, image FROM producers ORDER BY producerID ASC LIMIT 3
    """
    producers_result = db.run(query_producers)

    ## These conditions ensure that a list is always the result, making outputs easier
    if producers_result is None:
        producers = []
    elif isinstance(producers_result, dict):
        producers = [producers_result]
    elif isinstance(producers_result, list):
        producers = producers_result
    else:
        producers = []

    # fetch the first 3 products to show as a featured preview
    query_featured = """
        SELECT product.productID, product.name, product.price_cents, product.stock,
            product.transparency_details, product.image,
            prod.name AS producer_name
        FROM Products product
        JOIN Producers prod ON prod.producerID = product.producerID
        ORDER BY product.productID ASC LIMIT 3
    """
    featured_result = db.run(query_featured)

    if featured_result is None:
        featured_products = []
    elif isinstance(featured_result, dict):
        featured_products = [featured_result]
    elif isinstance(featured_result, list):
        featured_products = featured_result
    else:
        featured_products = []

    print("Home page Visited")
    return render_template("landing.html", producers=producers, featured_products=featured_products)


@app.route("/products")
def products():
    # we need to get the users search from the search filter (empty str if nothing is searched)
    search_query = request.args.get("q", "")

    # get the list of producer IDS the user has selected in the tickboxes for filtering
    selected_producer_ids = request.args.getlist("producer_id") #gets a list of all producerIDs

    # fetch every product with the name and ID of the producer that supplies it
    query_all_products = """
        SELECT product.productID, product.name, product.price_cents, product.stock,
            product.transparency_details, product.image,
            prod.producerID AS producerID, prod.name AS producer_name
        FROM Products product
        JOIN Producers prod ON prod.producerID = product.producerID
        ORDER BY product.productID ASC
    """
    all_products_result = db.run(query_all_products)

    if all_products_result is None:
        all_products = []
    elif isinstance(all_products_result, dict):
        all_products = [all_products_result]
    elif isinstance(all_products_result, list):
        all_products = all_products_result
    else:
        all_products = []

    # we need to stip the search and filter products by the users input
    if search_query:
        all_products = [product for product in all_products if search_query.lower() in product["name"].lower()]

    # now we check to see if there was any checkboxes selected for the filtering
    if selected_producer_ids:
        all_products = [product for product in all_products if str(product["producerID"]) in selected_producer_ids]

    #now we need to fetch all producer names for the filter checkboxes
    query_producers_list = """
        SELECT producerID, name FROM Producers ORDER BY name ASC
    """

    producers_list_result = db.run(query_producers_list)

    if producers_list_result is None:
        all_producers = []
    elif isinstance(producers_list_result, dict):
        all_producers = [producers_list_result]
    elif isinstance(producers_list_result, list):
        all_producers = producers_list_result
    else:
        all_producers = []

    print("Product page Visited")
    return render_template("products.html", products=all_products, all_producers=all_producers,
                           q=search_query, selected_producers=selected_producer_ids)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    # we need to fetch the specifically clicked product and attatch the producer information
    query_product = """
        SELECT product.productID, product.name, product.price_cents, product.stock,
            product.transparency_details, product.image, 
            prod.producerID, prod.name AS producer_name, prod.description
        FROM Products product
        JOIN Producers prod ON prod.producerID = product.producerID
        WHERE product.productID = ?
    """
    data = (product_id,)
    product = db.run(query_product, data)


    if not product:
        message = "Product not found."
        return render_template("error.html", message=message)

    # calculate the 10% member discount price for signed-in customers
    # member_price stays None if the user is not a signed-in customer

    member_price = None
    if session.get("role") == "customer":
        member_price = int(product["price_cents"] * 0.9)

    print(f"Product {product_id} viewed")
    return render_template("product.html", product=product, member_price=member_price)


@app.route("/producers")
def producers_page():
    query_producers = """
        SELECT producerID, name, description, image FROM Producers ORDER BY producerID ASC
    """
    producers_result = db.run(query_producers)

    if producers_result is None:
        producers = []
    elif isinstance(producers_result, dict):
        producers = [producers_result]
    elif isinstance(producers_result, list):
        producers = producers_result
    else:
        producers = []

    print("Producers page loaded")
    return render_template("producers.html", producers=producers)

@app.route("/about")
def about():
    print("About page loaded")
    return render_template("about.html")

@app.route("/settings")
def settings():
    # the settings page uses a JS function to save user preferences to the browsers local storage
    print("Settings page loaded")
    return render_template("settings.html")

@app.route("/alerts")
def alerts():
    # fetch all promotions from the database
    query_active_promotions = """
        SELECT title, description, discount_percent, is_member_only
        FROM Promotions
        WHERE is_active = 1
        ORDER BY promoID ASC
    """
    promotions_result = db.run(query_active_promotions)
    if promotions_result is None:
        promotions = []
    elif isinstance(promotions_result, dict):
        promotions = [promotions_result]
    elif isinstance(promotions_result, list):
        promotions = promotions_result
    else:
        promotions = []

    print("Alert page loaded")
    return render_template("alerts.html", promotions=promotions)

@app.route("/sign-up")
def get_sign_up():
    # just render the html page, we use a POST route for collecting the form
    return render_template("sign_up.html")

@app.route("/sign-up", methods=["POST"])
def post_sign_up():
    # first we need to collect all form data
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = request.form.get("password")

    # now we can validate each field individually so we can give 
    # unique error messages based on the condition that causes the error

    # this validation ensures that all fields are filled in, making our database more robust
    if not first_name:
        message = "You must enter a first name!"
        return render_template("sign_up.html", message=message)
    
    if not last_name:
        message = "You must enter a last name!"
        return render_template("sign_up.html", message=message)
    
    if not email:
        message = "You must enter an email!"
        return render_template("sign_up.html", message=message)

    if not password:
        message = "You must enter a password!"
        return render_template("sign_up.html", message=message)


    # password complexity rule enforcement:
    has_number = any(character.isdigit() for character in password) #checks for any instance of a number in the password
    has_special = any(not character.isalnum() for character in password) #checks for any instance of a special character in the password

    if len(password) < 8 or not has_number or not has_special:
        message = "Password must be 8+ characters and must contain a number and a special character"
        return render_template("sign_up.html", message=message)
    

    # now we need to hash the password using argon2, 
    # this ensures plain text is never stored in the database
    password_hash = ph.hash(password)

    query_insert_user = """
        INSERT INTO Users (first_name, last_name, email, password_hash)
        VALUES (?, ?, ?, ?)
    """

    data = (first_name, last_name, email, password_hash)

    # now we try to insert the new user into the
    try:
        db.run(query_insert_user, data)
    except:
        message = "That email is already registered to an account"
        return render_template("sign_up.html", message=message)

    print(f"User {email} has just signed up!")
    return redirect(url_for("get_sign_in"))

@app.route("/sign-in")
def get_sign_in():
    return render_template("sign_in.html")

@app.route("/sign-in", methods=["POST"])
def post_sign_in():
    email = request.form.get("email")
    password = request.form.get("password")

    # find the account that matches the inputted email
    query_find_user = """
        SELECT * FROM Users WHERE email = ?
    """

    data = (email,)
    user_row = db.run(query_find_user, data)

    if not user_row:
        # if no account exists with this email
        message = "Incorrect email or password"
        return render_template("sign_in.html", message=message)
    
    stored_hash = user_row["password_hash"]

    try:
        ph.verify(stored_hash, password) 
        # checking to see if the hashed version of the user entered password matches the same hash as the account password
    except:
        message = "Incorrect email or password"
        return render_template("sign_in.html", message=message)
    
    # create cookies to hold user information 
    session["email"] = email
    session["user_id"] = user_row["UserID"]
    session["first_name"] = user_row["first_name"]
    session["role"] = "customer"

    print(f"User {email} has logged in!")
    return redirect(url_for("landing_page"))

@app.route("/producer/sign-in")
def get_producer_sign_in():
    return render_template("producers_login.html")

@app.route("/producer/sign-in", methods=["POST"])
def post_producer_sign_in():
    # fetch all fields from the form
    email = request.form.get("email")
    password = request.form.get("password")
    producer_id = request.form.get("producer_id")

    if not email or not password or not producer_id:
        # ensure all fields are filled
        message = "Please fill in all fields"
        return render_template("producers_login.html", message=message)
    
    # find the producer login that matches the users input
    query_find_producer = """
        SELECT * FROM Producers WHERE contactEmail = ? AND producerID = ?
    """
    data = (email, producer_id)
    producer_row = db.run(query_find_producer, data)

    if not producer_row:
        message = "Incorrect producer credentials"
        return render_template("producers_login.html", message=message)
    
    stored_hash = producer_row["password_hash"]

    try:
        ph.verify(stored_hash, password)
    except:
        message = "Incorrect producer credentials"
        return render_template("producers_login.html", message=message)

    session["role"] = "producer"
    session["producer_id"] = producer_row["producerID"]
    session["producer_name"] = producer_row["name"]
    session["first_name"] = producer_row["first_name"]

    print(f"Producer {email} has logged in!")
    return redirect(url_for("producer_dashboard"))

@app.route("/sign-out")
def sign_out():
    # simple clear of cookies
    session.clear()
    print("User has logged out")
    return redirect(url_for("landing_page"))

@app.route("/basket")
def basket():
    if session.get("role") not in ("customer", "guest"):
        return redirect(url_for("get_sign_in"))
    
    user_id = session.get("user_id")

    # find the basket associated with the users ID
    query_find_basket = """
        SELECT orderID FROM Baskets WHERE userID = ?
    """
    basket_row = db.run(query_find_basket, (user_id,))

    if not basket_row:
        db.run("INSERT INTO Baskets (userID) VALUES (?)", (user_id,))
        basket_row = db.run(query_find_basket, (user_id,))

    basket_id = basket_row["orderID"]

    # fetch all basket and product information, join the tables and order it by product ID
    query_basket_items = """
        SELECT userbasket.productID, userbasket.quantity,
            product.name, product.price_cents, product.stock, product.image, product.transparency_details,
            prod.name AS producer_name
        FROM User_basket userbasket
        JOIN Products product ON product.productID = userbasket.productID
        JOIN Producers prod ON prod.producerID = product.producerID
        WHERE userbasket.orderID = ?
        ORDER BY userbasket.productID ASC
    """
    items_result = db.run(query_basket_items, (basket_id,))

    if items_result is None:
        items = []
    elif isinstance(items_result, dict):
        items = [items_result]
    elif isinstance(items_result, list):
        items = items_result
    else:
        items = []

    total_cents = 0
    item_count = 0
    for item in items:
        # tally how much money and quantity total 
        total_cents += item["price_cents"] * item["quantity"]
        item_count += item["quantity"]

    print("Basket viewed")
    return render_template("basket.html", items=items, total_cents=total_cents, item_count=item_count)

@app.route("/basket/add", methods=["POST"])
def basket_add():
    if session.get("role") == 'producer':
        message = "Producers cannot add items to basket."
        return render_template("error.html", message=message)
    
    if session.get("role") not in ("customer", "guest"):
        # for guests - generate a guest email so our database doesnt miss any fields
        guest_email = f"guest_{secrets.token_hex(6)}@glh.local"

        query_create_guest = """
        INSERT INTO Users (first_name, last_name, email, password_hash)
        VALUES (?, ?, ?, ?)
    """
        # 'guest' is a placeholder hash as guests cant have passwords
        guest_data = ("Guest", "User", guest_email, "GUEST")
        db.run(query_create_guest, guest_data)

        guest_row = db.run("SELECT UserID FROM Users WHERE email = ?", (guest_email,))
        session["user_id"] = guest_row["UserID"]
        session["role"] = "guest"
        print(f"Guest user created")

    user_id = session.get("user_id")
    product_id = request.form.get("product_id")
    quantity = int(request.form.get("quantity", 1))

    query_find_basket = """
        SELECT orderID FROM Baskets WHERE userID = ?
    """
    basket_row = db.run(query_find_basket, (user_id,))

    if not basket_row:
        db.run("INSERT INTO Baskets (userID) VALUES (?)", (user_id,))
        basket_row = db.run(query_find_basket, (user_id,))

    basket_id = basket_row["orderID"]

    stock_row = db.run("SELECT stock FROM Products WHERE productID = ?", (product_id,))

    if not stock_row:
        message = "Product not found"
        return render_template("error.html", message=message)
    
    existing_basket_item = db.run("SELECT orderItemsID, quantity FROM User_basket WHERE orderID = ? AND productID = ?", (basket_id, product_id))
    
    if existing_basket_item:
        if isinstance(existing_basket_item, list):
            existing_basket_item = existing_basket_item[0]
        
        new_quantity = existing_basket_item["quantity"] + quantity
        if new_quantity > stock_row["stock"]:
            message = "Quantity exceeds available stock"
            return render_template("error.html", message=message)
        db.run("UPDATE User_basket SET quantity = ? WHERE orderItemsID = ?", (new_quantity, existing_basket_item["orderItemsID"]))
    else:
        if quantity > stock_row["stock"]:
            message = "Quantity exceeds available stock."
            return render_template("error.html", message=message)
        db.run("INSERT INTO User_basket (orderID, productID, quantity) VALUES (?, ?, ?)", (basket_id, product_id, quantity))

    print(f"Product {product_id} added to basket")
    return redirect(url_for("basket"))

@app.route("/basket/remove/<int:product_id>", methods=["POST"])
def basket_remove(product_id):
    if session.get("role") not in ('customer', 'guest'):
        return redirect(url_for("get_sign_in"))
    
    user_id = session.get("user_id")

    query_find_basket = """
        SELECT orderID FROM Baskets WHERE userID = ?
    """
    basket_row = db.run(query_find_basket, (user_id,))

    if basket_row:
        basket_id = basket_row["orderID"]
        # fetch the specific product ID and delete it from the basket database
        db.run("DELETE FROM User_basket WHERE orderID = ? AND productID = ?", (basket_id, product_id))
        print(f"Product {product_id} removed from basket")

    return redirect(url_for("basket"))

@app.route("/basket/update", methods=["POST"])
def basket_update():
    if session.get("role") not in ('customer', 'guest'):
        return redirect(url_for("get_sign_in"))
    
    user_id = session.get("user_id")
    product_id = request.form.get("product_id")
    new_quantity = int(request.form.get("quantity", 1))

    query_find_basket = """
        SELECT orderID FROM Baskets WHERE userID = ?
    """
    basket_row = db.run(query_find_basket, (user_id,))

    if not basket_row:
        return redirect(url_for("basket"))
    
    basket_id = basket_row["orderID"]

    if new_quantity <= 0:
        # deletes from the basket table if the quantity is below 1
        db.run("DELETE FROM User_basket WHERE orderID = ? AND productID = ?", (basket_id, product_id))
        return redirect(url_for("basket"))

    stock_row = db.run("SELECT stock FROM Products WHERE productID = ?", (product_id,))
    if stock_row and new_quantity > stock_row["stock"]:
        # we check to see if the update exceeds the amount of stock to prevent 
        # overselling a product
        message = "Quantity exceeds available stock."
        return render_template("error.html", message=message)
    
    # update the new quantity in the basket database
    db.run("UPDATE User_basket SET quantity = ? WHERE orderID = ? AND productID = ?", (new_quantity, basket_id, product_id))

    print("Basket quantity updated")
    return redirect(url_for("basket"))

@app.route("/checkout")
def checkout():
    if session.get("role") not in ('customer', 'guest'):
        return redirect(url_for("get_sign_in"))
    
    user_id = session.get("user_id")

    query_find_basket = """
        SELECT orderID FROM Baskets WHERE userID = ?
    """
    basket_row = db.run(query_find_basket, (user_id,))

    if not basket_row:
        return render_template("checkout.html", items=[], total_cents=0, item_count=0, address="", postcode="", is_guest=False)
    
    basket_id = basket_row["orderID"]

    # fetch all basket details and product details
    query_checkout_items = """
        SELECT userbasket.productID, userbasket.quantity,
            product.name, product.price_cents, product.stock, product.image, product.transparency_details,
            prod.name AS producer_name
        FROM User_basket userbasket
        JOIN Products product ON product.productID = userbasket.productID
        JOIN Producers prod ON prod.producerID = product.producerID
        WHERE userbasket.orderID = ?
        ORDER BY userbasket.productID ASC
    """

    items_result = db.run(query_checkout_items, (basket_id,))

    if items_result is None:
        items = []
    elif isinstance(items_result, dict):
        items = [items_result]
    elif isinstance(items_result, list):
        items = items_result
    else:
        items = []

    total_cents = 0
    item_count = 0
    for item in items:
        # tally the cost and quantity
        total_cents += item["price_cents"] * item["quantity"]
        item_count += item["quantity"]

    # prefill the saved address for the user
    address = ""
    postcode = ""
    is_guest = session.get("role") == "guest"

    if session.get("role") == "customer":
        customer_row = db.run("SELECT address, postcode FROM Users WHERE UserID = ?", (user_id,))

        if customer_row:
            address = customer_row.get("address") or "" # fetch users address, if not then leave blanbk
            postcode = customer_row.get("postcode") or ""

    print("Checkout page loaded")
    return render_template("checkout.html", items=items, total_cents=total_cents, item_count=item_count, address=address, postcode=postcode, is_guest=is_guest)


@app.route("/checkout/confirm", methods=["POST"])
def checkout_confirm():
    if session.get("role") not in ('customer', 'guest'):
        return redirect(url_for("get_sign_in"))
    
    user_id = session.get("user_id")

    if session.get("role") == 'guest':
        guest_email = (request.form.get("guest_email") or "").strip()
        if not guest_email or "@" not in guest_email:
            # invalid email format, throws an error
            message = "Please enter a valid email address to complete your guest order."
            return render_template("error.html", message=message)
    
    delivery_option = request.form.get("delivery_option") or "delivery" # can be only these 2 formats

    if delivery_option == "collection":
        delivery_address = request.form.get("collection_store") or "Collection" # Prefilled from the dropdown menu
        delivery_postcode = ""
    else:
        delivery_address = request.form.get("delivery_address") or "" # fetches from the form
        delivery_postcode = request.form.get("delivery_postcode") or ""

    query_find_basket = """
        SELECT orderID FROM Baskets WHERE userID = ?
    """
    basket_row = db.run(query_find_basket, (user_id,))

    if not basket_row:
        message = "Your basket is empty!"
        return render_template("error.html", message=message)
    
    basket_id = basket_row["orderID"]

    query_basket_items = """
        SELECT userbasket.productID, userbasket.quantity, product.stock
        FROM User_basket userbasket
        JOIN Products product ON product.productID = userbasket.productID
        WHERE userbasket.orderID = ?
    """
    items_result = db.run(query_basket_items, (basket_id,))

    if items_result is None:
        items = []
    elif isinstance(items_result, dict):
        items = [items_result]
    elif isinstance(items_result, list):
        items = items_result
    else:
        items = []

    # error handling
    if not items:
        message = "Your basket is empty!"
        return render_template("error.html", message=message)
    
    for item in items:
        if item["quantity"] > item["stock"]:
            message = "Not enough stock for one of your items"
            return render_template("error.html", message=message)
    
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M") # store the time and date of the order

    # insert the order into the database
    query_create_order = """
        INSERT INTO Orders (userID, orderDate, status, delivery_option, delivery_address, delivery_postcode)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    order_data = (user_id, order_date, "Processing", delivery_option, delivery_address, delivery_postcode)
    db.run(query_create_order, order_data)

    # fetches the latest order by the user (the one that just got submitted)
    latest_order = db.run("SELECT orderID FROM Orders WHERE userID = ? ORDER BY orderID DESC LIMIT 1", (user_id,))
    order_id = latest_order["orderID"]

    # insert the item into the orders db, update the stock levels to decrease the amount from the confirmed order
    for item in items:
        db.run("INSERT INTO Order_contents (orderID, productID, quantity) VALUES (?, ?, ?)", (order_id, item["productID"], item["quantity"]))
        db.run("UPDATE Products SET stock = stock - ? WHERE productID = ?", (item["quantity"], item["productID"]))

    db.run("DELETE FROM User_basket WHERE orderID = ?", (basket_id,))
    db.run("DELETE FROM Baskets WHERE orderID = ?", (basket_id,))

    print(f"Order #{order_id} placed!")
    return redirect(url_for("order_confirmed", order_id=order_id))

@app.route("/orders/<int:order_id>/confirmed")
def order_confirmed(order_id):
    if session.get("role") not in ("customer", "guest"):
        return redirect(url_for("get_sign_in"))
    
    user_id = session.get("user_id")

    query_find_order = """
        SELECT * FROM Orders WHERE orderID = ? AND userID = ?
    """

    order = db.run(query_find_order, (order_id, user_id))

    if not order:
        message = "Order not found"
        return render_template("error.html", message=message)
    
    # fetch all order details from the confirmed order
    query_order_items = """
        SELECT ordercontents.quantity, product.name, product.price_cents, product.image,
            prod.name AS producer_name
        FROM Order_contents ordercontents
        JOIN Products product ON product.productID = ordercontents.productID
        JOIN Producers prod ON prod.producerID = product.producerID
        WHERE ordercontents.orderID = ?
    """

    items_result = db.run(query_order_items, (order_id,))

    if items_result is None:
        items = []
    elif isinstance(items_result, dict):
        items = [items_result]
    elif isinstance(items_result, list):
        items = items_result
    else:
        items = []

    total_cents = 0
    for item in items:
        total_cents += item["price_cents"] * item["quantity"] # tally up the total 
    
    print(f"Order confirmed! Order #{order_id}")
    return render_template("order_confirmed.html", order=order, items=items, total_cents=total_cents)

@app.route("/my-orders")
def my_orders():
    if session.get("role") != "customer":
        return redirect(url_for("get_sign_in"))

    user_id = session.get("user_id")

    # Now we join 3 tables in order to have all of the relevent data and variables for the page
    query_order_history = """
        SELECT product.name, product.price_cents, product.transparency_details, product.image,
            prod.name AS producer_name,
            ordercontents.quantity,
            ord.orderDate, ord.status, ord.orderID, ord.delivery_option, ord.delivery_address, ord.delivery_postcode
        FROM Order_contents ordercontents
        JOIN Products product ON product.productID = ordercontents.productID
        JOIN Producers prod ON prod.producerID = product.producerID
        JOIN Orders ord ON ord.orderID = ordercontents.orderID
        WHERE ord.userID = ?
        ORDER BY ord.orderID DESC
    """

    data = (user_id,)
    history_result = db.run(query_order_history, data)

    if history_result is None:
        order_items = []
    elif isinstance(history_result, dict):
        order_items = [history_result]
    elif isinstance(history_result, list):
        order_items = history_result
    else:
        order_items = []

    for item in order_items:
        # works out the members price and the full price
        item["amount_paid"] = int(item["price_cents"] * 0.9) * item["quantity"]
        item["full_price_paid"] = item["price_cents"] * item["quantity"]

        # fetches the date and time from each item
        raw_date = str(item["orderDate"])
        if " " in raw_date:
            date_parts = raw_date.split(" ") # strip it into the correct format
            item["order_date_part"] = date_parts[0] # split the date into diffent parts (date, time)
            item["order_time_part"] = date_parts[1]
        else:
            item["order_date_part"] = raw_date
            item["order_time_part"] = ""

    print(f"User {session.get('email')} is viewing their orders")
    return render_template("my_orders.html", order_items=order_items)

@app.route("/account")
def my_account():
    if session.get("role") != "customer":
        return redirect(url_for("get_sign_in"))
    
    # fetches all user details
    query_get_user = """
        SELECT * FROM Users WHERE UserID = ?
    """
    data = (session.get("user_id"),)
    customer = db.run(query_get_user, data)

    if not customer:
        customer = {}

    print(f"User {session.get('email')} is viewing their account")
    return render_template("my_account.html", customer=customer)

@app.route("/account", methods=["POST"])
def update_account():
    if session.get("role") != "customer":
        return redirect(url_for("get_sign_in"))

    # fetches for each form field  
    user_id = session.get("user_id")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    address = request.form.get("address")
    postcode = request.form.get("postcode")

    # error handling to prevent empty fields
    if not first_name or not last_name:
        message = "First and last name must be entered."
        return render_template("error.html", message=message)
    
    # update the users database to contain all of the updated user info fields from the form
    query_update_user = """
        UPDATE Users SET first_name = ?, last_name = ?, address = ?, postcode = ?
        WHERE UserID = ?
    """

    data = (first_name, last_name, address, postcode, user_id)
    db.run(query_update_user, data)

    session["first_name"] = first_name

    print(f"User {session.get('email')} updated their account")
    return redirect(url_for("my_account"))

@app.route("/account/delete", methods=["POST"])
def delete_account():
    if session.get("role") != "customer":
	    return redirect(url_for("get_sign_in"))

    # simple delete user based on userID query
    query_delete_user = """DELETE FROM Users WHERE UserID = ?"""

    db.run(query_delete_user, (session.get("user_id"),))

    session.clear()
    print("User deleted their account")
    return redirect(url_for("landing_page"))


@app.route("/producer/profile")
def producer_profile():
    if session.get("role") != "producer":
        message = "You must be logged in as a producer to view this page"
        return render_template("error.html", message=message)

    # fetches all producer information
    query_get_producer = """
        SELECT * FROM Producers WHERE producerID = ?
    """
    producer = db.run(query_get_producer, (session.get("producer_id"),))

    if not producer:
        producer = {}

    print(f"Producer {session.get('producer_name')} viewed their profile")
    return render_template("producer_profile.html", producer=producer)


@app.route("/producer/profile", methods=["POST"])
def update_producer_profile():
    if session.get("role") != "producer":
        message = "You must be logged in as a producer to view this page."
        return render_template("error.html", message=message)

    # fetches all form fields for the producer profile
    producer_id = session.get("producer_id")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    business_name = request.form.get("name")
    description = request.form.get("description")
    contact_email = request.form.get("contactEmail")
    contact_phone = request.form.get("contactPhone")

    # prevent missing form fields
    if not first_name or not last_name or not business_name:
        message = "Missing required fields"
        return render_template("error.html", message=message)
    
    query_update_producer = """
        UPDATE Producers SET first_name = ?, last_name = ?, name = ?, description = ?,
            contactEmail = ?, contactPhone = ?
        WHERE producerID = ?
    """
    data = (first_name, last_name, business_name, description, contact_email, contact_phone, producer_id)
    db.run(query_update_producer, data)

    session["first_name"] = first_name
    session["producer_name"] = business_name

    print(f"Producer {producer_id} updated their profile")
    return redirect(url_for("producer_profile"))

@app.route("/producer/dashboard")
def producer_dashboard():
    if session.get("role") != "producer":
        message = "You must be logged in as a producer to view this page"
        return render_template("error.html", message=message)
    
    # fetch the current producer and todays date
    producer_id = session.get("producer_id")
    today = date.today().isoformat()

    # select all of the producers inventory
    query_inventory = """
        SELECT productID, name, price_cents, stock, transparency_details
        FROM Products
        WHERE producerID = ?
        ORDER BY name ASC
    """
    inventory_result = db.run(query_inventory, (producer_id,))

    if inventory_result is None:
        inventory = []
    elif isinstance(inventory_result, dict):
        inventory = [inventory_result]
    elif isinstance(inventory_result, list):
        inventory = inventory_result
    else:
        inventory = []

    # calculate the total revenue based on the orders that have 'delivered' status
    query_total_revenue = """
        SELECT COALESCE(SUM(ordercontents.quantity * product.price_cents), 0) AS total
        FROM Order_contents ordercontents
        JOIN Products product ON product.productID = ordercontents.productID
        JOIN Orders ord ON ord.orderID = ordercontents.orderID
        WHERE product.producerID = ? AND ord.status = "Delivered"
    """
    revenue_row = db.run(query_total_revenue, (producer_id,))

    if revenue_row:
        total_revenue = revenue_row["total"]
    else:
        total_revenue = 0
    
    # find the stock with the lowest amounts, order it lowest to highest
    query_low_stock = """
        SELECT name, stock FROM Products WHERE producerID = ?
        ORDER BY stock ASC LIMIT 5
    """
    low_stock_result = db.run(query_low_stock, (producer_id,))

    if low_stock_result is None:
        low_stock = []
    elif isinstance(low_stock_result, dict):
        low_stock = [low_stock_result]
    elif isinstance(low_stock_result, list):
        low_stock = low_stock_result
    else:
        low_stock = []

    # we find the most sold using a left join so products with 0 sales still show up.
    # the 'LIKE ?' uses pattern matching to find any order placed today
    query_top_today = """
        SELECT product.name, product.price_cents, product.stock, product.image,
            COALESCE(SUM(ordercontents.quantity), 0) AS amount_sold
        FROM Products product
        LEFT JOIN Order_contents ordercontents ON ordercontents.productID = product.productID
        LEFT JOIN Orders ord ON ord.orderID = ordercontents.orderID AND ord.orderDate LIKE ?
        WHERE product.producerID = ?
        GROUP BY product.productID
        ORDER BY amount_sold DESC
    """
    top_today_result = db.run(query_top_today, (today + "%", producer_id))

    if top_today_result is None:
        top_today = []
    elif isinstance(top_today_result, dict):
        top_today = [top_today_result]
    elif isinstance(top_today_result, list):
        top_today = top_today_result
    else:
        top_today = []

    for row in top_today:
        row["amount_sold"] = int(row["amount_sold"] or 0) #convet to an integer

    query_chart_data = """
        SELECT ord.orderDate, ordercontents.quantity
        FROM Orders ord
        JOIN Order_contents ordercontents ON ordercontents.orderID = ord.orderID
        JOIN Products product ON product.productID = ordercontents.productID
        WHERE product.producerID = ? AND ord.orderDate LIKE ?
    """
    chart_result = db.run(query_chart_data, (producer_id, today + "%"))

    if chart_result is None:
        chart_rows = []
    elif isinstance(chart_result, dict):
        chart_rows = [chart_result]
    elif isinstance(chart_result, list):
        chart_rows = chart_result
    else:
        chart_rows = []


    # here we are going to use integer division to split up the sales from the full day into
    # 6 hour chunks. these 6 hour chuinks will be the bars that we use on the dashboard

    # i have reused some dashboard functionality from my own personal project from earlier in the year :)
    blocks = [0, 0, 0, 0] # think of each of these 'bloks' as '00:00-06:00' , '06:00-12:00' ect..
    for row in chart_rows:
        try:
            time_part = str(row["orderDate"]).split(" ")[1] if " " in str(row["orderDate"]) else "00:00"
            hour = int(time_part.split(":")[0])
            # here is where the ineger division is used
            # it is integer division by 6, used for mapping the hours to the block's index
            blocks[hour // 6] += row["quantity"]
        except:
            pass
    

    # now we fetch all orders that contain at least 1 of the logged in producer's products
    query_orders = """
        SELECT DISTINCT ord.orderID, ord.orderDate, ord.status,
            usr.first_name, usr.last_name,
            ord.delivery_option, ord.delivery_address, ord.delivery_postcode
        FROM Orders ord
        JOIN Users usr ON usr.UserID = ord.userID
        JOIN Order_contents ordercontents ON ordercontents.orderID = ord.orderID
        JOIN Products product ON product.productID = ordercontents.productID
        WHERE product.producerID = ?
        ORDER BY ord.orderID DESC
    """
    orders_result = db.run(query_orders, (producer_id,))

    if orders_result is None:
        orders = []
    elif isinstance(orders_result, dict):
        orders = [orders_result]
    elif isinstance(orders_result, list):
        orders = orders_result
    else:
        orders = []

    order_cards = []
    for order in orders:
        # fetch order item details
        query_order_items = """
            SELECT product.name, ordercontents.quantity
            FROM Order_contents ordercontents
            JOIN Products product ON product.productID = ordercontents.productID
            WHERE ordercontents.orderID = ? AND product.producerID = ?
        """
        order_items_result = db.run(query_order_items, (order["orderID"], producer_id))

        if order_items_result is None:
            order_items_list = []
        elif isinstance(order_items_result, dict):
            order_items_list = [order_items_result]
        elif isinstance(order_items_result, list):
            order_items_list = order_items_result
        else:
            order_items_list = []

        # we can group the orders with their items into a dictionary for the template
        order_cards.append({"order": order, "items": order_items_list})

    print(f"producer {session.get('producer_name')} loaded the dashboard")
    return render_template("producer_dashboard.html",
                               inventory=inventory, total_revenue=total_revenue,
                               low_stock=low_stock, top_today=top_today, 
                               blocks=blocks, order_cards=order_cards)


@app.route("/producer/orders/<int:order_id>/status", methods=["POST"])
def producer_set_order_status(order_id):
    if session.get("role") != "producer":
        message = "You must be logged in as a producer"
        return render_template("error.html", message=message)
    
    new_status = request.form.get("status")

    # now we limit to the only 3 acceptable status's
    if new_status not in ("Processing", "Out for delivery", "Delivered"):
        message = "Invalid order status"
        return render_template("error.html", message=message)
    
    # then we can update the product stauses in the database
    query_update_status = """
        UPDATE Orders SET status = ? WHERE orderID = ?
    """
    db.run(query_update_status, (new_status, order_id))

    print(f"Order {order_id} status has been updated to {new_status}")
    return redirect(url_for("producer_dashboard"))

@app.route("/producer/product/add", methods=["POST"])
def producer_add_product():
    if session.get("role") != "producer":
        message = "You must be logged in as a producer"
        return render_template("error.html", message=message)
    
    # fetch the product details from the form
    producer_id = session.get("producer_id")
    product_name = request.form.get("name")
    price_cents = request.form.get("price_cents")
    stock = request.form.get("stock")
    transparency_details = request.form.get("transparency_details")

    if not product_name or not price_cents or not stock:
        message = "Missing product details"
        return render_template("error.html", message=message)
    
    # insert the product into the database
    query_add_product = """
        INSERT INTO Products (name, price_cents, stock, transparency_details, producerID)
        VALUES (?, ?, ?, ?, ?)
    """
    data = (product_name, int(price_cents), int(stock), transparency_details or "", producer_id)
    db.run(query_add_product, data)

    print(f"Producer {producer_id} added a new product: {product_name}")
    return redirect(url_for("producer_dashboard"))

@app.route("/producer/product/update/<int:product_id>", methods=["POST"])
def producer_update_product(product_id):
    if session.get("role") != "producer":
        message = "You must be logged in as a producer"
        return render_template("error.html", message=message)
    
    # fetch the updated info from the form
    product_name = request.form.get("name")
    price_cents = request.form.get("price_cents")
    stock = request.form.get("stock")
    transparency_details = request.form.get("transparency_details")

    # check to make sure all fields are within boundaries and dont exceed stock count
    if not product_name or not price_cents or not stock:
        message = "Missing product details"
        return render_template("error.html", message=message)
    
    # update the product in the database
    query_update_product = """
        UPDATE Products SET name = ?, price_cents = ?, stock = ?, transparency_details = ?
        WHERE productID = ? AND producerID = ?
    """
    data = (product_name, int(price_cents), int(stock), transparency_details or "", product_id, session.get("producer_id"))
    db.run(query_update_product, data)

    print(f"Product #{product_id} has been updated")
    return redirect(url_for("producer_dashboard"))

@app.route("/producer/product/delete/<int:product_id>", methods=["POST"])
def producer_delete_product(product_id):
    if session.get("role") != "producer":
        message = "You must be logged in as a producer"
        return render_template("error.html", message=message)
    
    # remove from baskets first
    db.run("DELETE FROM User_basket WHERE productID = ?", (product_id,))

    # remove from order histories 
    # (not the best practice but i think keeping it in histories was creating errors in my table contraints)
    db.run("DELETE FROM Order_contents WHERE productID = ?", (product_id,))

    query_delete_product = """
        DELETE FROM Products WHERE productID = ? AND producerID = ?
    """
    db.run(query_delete_product, (product_id, session.get("producer_id")))

    print(f"Product #{product_id} has been deleted")
    return redirect(url_for("producer_dashboard"))



if __name__ == "__main__":
    app.run(debug=True)