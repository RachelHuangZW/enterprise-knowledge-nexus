import sqlite3
import random
from datetime import datetime, timedelta
import os

# ---------------------------------------------------------
# 1. Setup Database Path
# ---------------------------------------------------------
# Determine the absolute path to the data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "knowledge_nexus.db")

# Remove the old database if it exists to ensure a fresh start
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"🗑️  Deleted old database: {DB_PATH}")

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print(f"🚀 Initializing new database...")

# ---------------------------------------------------------
# 2. Define Table Schema
# ---------------------------------------------------------

# A. Products Table: Catalog of services/software sold
cursor.execute('''
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- e.g., Software, Service, Cloud
    price REAL NOT NULL
)
''')

# B. Customers Table: Companies purchasing the products
cursor.execute('''
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    industry TEXT NOT NULL, -- e.g., Manufacturing, Retail, Tech
    region TEXT NOT NULL    -- e.g., North, South, East, West
)
''')

# C. Sales Representatives Table: Internal staff managing accounts
cursor.execute('''
CREATE TABLE sales_reps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    region TEXT NOT NULL    -- Reps are assigned to specific regions
)
''')

# D. Sales Table: Transactional records (The Fact Table)
# This table uses Foreign Keys to link to the three tables above
cursor.execute('''
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    customer_id INTEGER,
    rep_id INTEGER,
    quantity INTEGER,
    total_amount REAL,
    sale_date TEXT,
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(rep_id) REFERENCES sales_reps(id)
)
''')

# ---------------------------------------------------------
# 3. Insert Master Data
# ---------------------------------------------------------

# --- Insert Products ---
products_data = [
    ("SAP HANA License", "Software", 50000.0),
    ("SAP S/4HANA Cloud", "Cloud", 15000.0),
    ("SAP Fiori Implementation", "Service", 12000.0),
    ("Business Consulting", "Service", 2000.0), 
    ("Cloud Hosting (AWS/Azure)", "Cloud", 500.0),
    ("Data Migration Service", "Service", 8000.0),
    ("Oracle DB License", "Software", 45000.0),
    ("Cybersecurity Audit", "Service", 5000.0)
]
cursor.executemany("INSERT INTO products (name, category, price) VALUES (?, ?, ?)", products_data)

# Fetch product IDs for later use in transaction generation
cursor.execute("SELECT id, price FROM products")
product_list = cursor.fetchall()

# --- Insert Customers ---
customers_data = [
    ("TechNova Inc", "Technology", "East"),
    ("Global Mfg Corp", "Manufacturing", "North"),
    ("Retail Giants Ltd", "Retail", "South"),
    ("AutoWorks", "Automotive", "North"),
    ("FinSafe Bank", "Finance", "East"),
    ("GreenEnergy", "Energy", "West"),
    ("HealthPlus", "Healthcare", "South"),
    ("EduTech Solutions", "Education", "West")
]
cursor.executemany("INSERT INTO customers (company_name, industry, region) VALUES (?, ?, ?)", customers_data)

# Fetch customer IDs for transaction generation
cursor.execute("SELECT id, region FROM customers")
customer_list = cursor.fetchall()

# --- Insert Sales Representatives ---
reps_data = [
    ("Alice Smith", "East"),
    ("Bob Johnson", "North"),
    ("Charlie Brown", "South"),
    ("Diana Prince", "West")
]
cursor.executemany("INSERT INTO sales_reps (name, region) VALUES (?, ?)", reps_data)

# Fetch rep IDs for transaction generation
cursor.execute("SELECT id, region FROM sales_reps")
rep_list = cursor.fetchall()

# ---------------------------------------------------------
# 4. Generate Mock Transaction Data (Sales)
# ---------------------------------------------------------
print("🌱 Generating 100 sales records...")

sales_entries = []
for _ in range(100): 
    # 1. Randomly select a product
    prod = random.choice(product_list) 
    prod_id, unit_price = prod[0], prod[1]
    
    # 2. Randomly select a customer
    cust = random.choice(customer_list) 
    cust_id, cust_region = cust[0], cust[1]
    
    # 3. Select a sales rep
    # Logic: Try to find a rep that matches the customer's region
    matching_reps = [r for r in rep_list if r[1] == cust_region]
    if matching_reps:
        rep = random.choice(matching_reps)
    else:
        rep = random.choice(rep_list) # Fallback to random if no match
    rep_id = rep[0]
    
    # 4. Randomize quantity (1 to 10)
    qty = random.randint(1, 10)
    
    # 5. Calculate total amount
    total_amount = qty * unit_price
    
    # 6. Randomize date (within the last 6 months)
    days_ago = random.randint(0, 180)
    sale_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # Append to list
    sales_entries.append((prod_id, cust_id, rep_id, qty, total_amount, sale_date))

# Bulk insert
cursor.executemany("""
    INSERT INTO sales (product_id, customer_id, rep_id, quantity, total_amount, sale_date) 
    VALUES (?, ?, ?, ?, ?, ?)
""", sales_entries)

conn.commit()

# ---------------------------------------------------------
# 5. Verification
# ---------------------------------------------------------
print("\n=== Data Verification: First 5 Sales Records (with JOINS) ===")

# Perform a complex SQL query to ensure relationships work
verify_sql = """
SELECT 
    s.id, 
    p.name as product, 
    c.company_name as customer, 
    r.name as sales_rep, 
    s.total_amount, 
    s.sale_date
FROM sales s
JOIN products p ON s.product_id = p.id
JOIN customers c ON s.customer_id = c.id
JOIN sales_reps r ON s.rep_id = r.id
ORDER BY s.sale_date DESC
LIMIT 5
"""

rows = cursor.execute(verify_sql).fetchall()
for row in rows:
    print(row)

print(f"\n✅ Database generation complete! Created {len(sales_entries)} sales records.")
conn.close()