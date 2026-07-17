import pandas as pd
from sqlalchemy import text
from database import engine

try: 
    df=pd.read_csv("data\Sample - Superstore.csv",
                   encoding="latin1")
except Exception as e:
    print("khong the doc du lieu")
    print(e)
    exit()
df.columns = df.columns.str.replace(' ', '_').str.replace('-','_').str.lower()
print(f"file read successfully. total columns {len(df)}")

with engine.connect() as conn:
    conn.execute(text("drop table if exists orders cascade;"))
    conn.execute(text("drop table if exists customers cascade;"))
    conn.execute(text("drop table if exists products cascade;"))
    conn.commit()
    print("tables deleted successfully")

customers_df = df[[
    'customer_id', 'customer_name', 'segment', 
    'country', 'city', 'state', 'postal_code', 'region'
]].drop_duplicates(subset=['customer_id'])

products_df = df[[
    'product_id', 'category', 'sub_category', 'product_name'
]].drop_duplicates(subset=['product_id'])

orders_df = df[[
    'row_id', 'order_id', 'order_date', 'ship_date', 'ship_mode',
    'customer_id', 'product_id', 'sales', 'quantity', 'discount', 'profit'
]].copy()

orders_df['order_date']=pd.to_datetime(orders_df['order_date'])
orders_df['ship_date']=pd.to_datetime(orders_df['ship_date'])

customers_df.to_sql('customers', con=engine, if_exists='append', index=False)
products_df.to_sql('products', con=engine, if_exists='append', index=False)
orders_df.to_sql('orders', con=engine, if_exists='append', index=False)

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE customers ADD PRIMARY KEY (customer_id);"))
    conn.execute(text("ALTER TABLE products ADD PRIMARY KEY (product_id);"))
    conn.execute(text("ALTER TABLE orders ADD PRIMARY KEY (row_id);"))
    
    conn.execute(text("""
        ALTER TABLE orders 
        ADD CONSTRAINT fk_orders_customers 
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id);
    """))
    conn.execute(text("""
        ALTER TABLE orders 
        ADD CONSTRAINT fk_orders_products 
        FOREIGN KEY (product_id) REFERENCES products(product_id);
    """))
    conn.commit()
    print("tables created successfully")