from easy import SQL
from argon2 import PasswordHasher

db = SQL("database.db")
ph = PasswordHasher()

## CREATES THE TABLES: ##

def init_database(db):
    db.run("""
    CREATE TABLE IF NOT EXISTS Users (
        UserID INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        address TEXT,
        postcode TEXT,
        loyalty_points INTEGER NOT NULL DEFAULT 0,
        membership_level TEXT NOT NULL DEFAULT 'Standard'
        )
    """)

    db.run("""
    CREATE TABLE IF NOT EXISTS Producers (
        producerID INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        contactEmail TEXT NOT NULL,
        contactPhone TEXT NOT NULL,
        image TEXT
        )
    """)

    db.run("""
    CREATE TABLE IF NOT EXISTS Products (
        productID INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price_cents INTEGER NOT NULL,
        transparency_details TEXT NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        producerID INTEGER NOT NULL,
        image TEXT,
        FOREIGN KEY (producerID) REFERENCES Producers(producerID)
        )
    """)

    db.run("""
    CREATE TABLE IF NOT EXISTS Baskets (
        orderID INTEGER PRIMARY KEY,
        userID INTEGER NOT NULL UNIQUE,
        FOREIGN KEY (userID) REFERENCES Users(UserID)
        )
    """)

    db.run("""
    CREATE TABLE IF NOT EXISTS User_basket (
        orderItemsID INTEGER PRIMARY KEY,
        orderID INTEGER NOT NULL,
        productID INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (orderID) REFERENCES Baskets(orderID),
        FOREIGN KEY (productID) REFERENCES Products(productID)
        )
    """)

    db.run("""
    CREATE TABLE IF NOT EXISTS Orders (
        orderID INTEGER PRIMARY KEY,
        userID INTEGER NOT NULL,
        orderDate TEXT NOT NULL,
        status TEXT NOT NULL,
        delivery_option TEXT NOT NULL,
        delivery_address TEXT,
        delivery_postcode TEXT,
        FOREIGN KEY (userID) REFERENCES Users(UserID)
        )
    """)

    db.run("""
    CREATE TABLE IF NOT EXISTS Order_contents (
        orderItemsID INTEGER PRIMARY KEY,
        orderID INTEGER NOT NULL,
        productID INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (orderID) REFERENCES Orders(orderID),
        FOREIGN KEY (productID) REFERENCES Products(productID)
        )
    """)

    db.run("""
    CREATE TABLE IF NOT EXISTS Promotions (
        promoID INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        discount_percent INTEGER NOT NULL,
        is_member_only INTEGER NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    seed_data(db) # function for filling in example data


def seed_data(db):
    existing = db.run("SELECT COUNT(*) AS c FROM Producers") ## checking to see if there is data in the database
    if existing and int(existing["c"]) > 0:
        return ## if there is already data in the db, skip the queries
    
    # if theres not any data in the databases, run these queries:
    query = """
        INSERT INTO Producers (producerID, first_name, last_name, username, password_hash, name, description, contactEmail, contactPhone, image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

## Example Producers with logins
    db.run(query, (1, "Quinn", "Walker", "producer1", ph.hash("Producer1!Pass"),
               "Quartz Farm",
               "A 20-acre grass-fed farm on the west coast of Cornwall. Known for fresh bacon, milk, and seasonal fruit.",
               "quartzfarm@example.com", 
               "+44 1013 387654", 
               "farm1.png"))
    
    db.run(query, (2, "Rowan", "Simmons", "producer2", ph.hash("Producer2!Pass"),
               "Farmers Together - Hartlepool",
               "A cooperative of local growers delivering reliable stock and transparent pricing to GLH customers.",
               "hartlepool@example.com", 
               "+44 1912 555123", 
               "farm2.png"))
    
    db.run(query, (3, "Cerys", "Evans", "producer3", ph.hash("Producer3!Pass"),
               "Green Valley Organics",
               "Family-run organic farm in the Brecon Beacons, Wales. Specialising in artisan dairy and preserves.",
               "greenvalley@example.com", 
               "+44 1874 220988",
               "farm3.png"))
    

## Example products   
    query2 = """
        INSERT INTO Products (productID, name, price_cents, transparency_details, stock, producerID, image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    db.run(query2, (1,
                    "Fairtrade Bacon",
                    899, 
                    "Transparent pricing: fair wages, quality supply chain, reduces local waste.", 
                    54, 
                    1, 
                    "bacon.png"))
    
    db.run(query2, (2,  
                    "Freshway Semi-Skimmed Milk", 
                    399, 
                    "Transparent pricing: seasonal feed costs and cold-chain handling for freshness.",      
                    61, 
                    1, 
                    "milk.png"))
    
    db.run(query2, (3, 
                    "Local Apples", 
                    279, 
                    "Transparent pricing: weather variability and FEFO inventory management.",          
                    40, 
                    1, 
                    "apples.png"))

    db.run(query2, (4,  
                    "Organic Free-Range Eggs",   
                    459, 
                    "Transparent pricing: free-range standards and small-batch production for quality.",               
                    22, 
                    2, 
                    "eggs.png"))
    
    db.run(query2, (5,  
                    "Seasonal Salad Mix",      
                    349, 
                    "Transparent pricing: harvested at peak ripeness to reduce leftover stock.",                       
                    34, 
                    2, 
                    "salad.png"))
    
    db.run(query2, (6,  
                    "Heritage Potatoes",      
                    329, 
                    "Transparent pricing: traditional varieties, slower to grow but richer in flavour.",               
                    48, 
                    2, 
                    "potato.png"))

    db.run(query2, (7,  
                    "Welsh Caerphilly Cheese", 
                    549, 
                    "Transparent pricing: hand-pressed in small batches using traditional Welsh methods.",             
                    18, 
                    3, 
                    "cheese.png"))
    
    db.run(query2, (8,  
                    "Organic Sourdough Loaf",         
                    380, 
                    "Transparent pricing: long fermentation process requires skilled labour and time.",                 
                    15, 
                    3, 
                    "sourdough.png"))
    
    db.run(query2, (9,  "Wildflower Honey",        
                    699, 
                    "Transparent pricing: low yield per hive and labour-intensive extraction process.",                
                    25, 
                    3, 
                    "honey.jpg"))
    
# Example Promotions
    query3 = """
        INSERT INTO Promotions (promoID, title, description, discount_percent, is_member_only, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    db.run(query3, (1, "Member Discount",
                "Signed-in customers get 10% off all products. Shop local and save with GLH.",
                10, 
                0, 
                1))
    
    db.run(query3, (2, "Seasonal Bundle Deal",
                "A limited-time promotion encouraging you to try seasonal produce. Discount applies to everyone.",
                5, 
                0, 
                1))
    
    db.run(query3, (3, "Dairy Lovers Week",
                "Extra savings on all dairy products this week. Available to all GLH shoppers.",
                8, 
                0, 
                1))
    
    print("Example Data added to the database.")