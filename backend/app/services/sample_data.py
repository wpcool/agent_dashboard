"""
示例数据生成器
创建模拟电商数据用于演示
"""
import sqlite3
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


def generate_sample_database(db_path: str = "./sample_data.db") -> str:
    """生成示例数据库"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表
    cursor.executescript("""
        -- 商品表
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            price DECIMAL(10,2) NOT NULL,
            cost DECIMAL(10,2),
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 客户表
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            city VARCHAR(50),
            register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vip_level INTEGER DEFAULT 1
        );

        -- 订单表
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            order_no VARCHAR(50) UNIQUE,
            total_amount DECIMAL(10,2),
            discount_amount DECIMAL(10,2) DEFAULT 0,
            final_amount DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'completed',
            pay_method VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        -- 订单明细表
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            product_name VARCHAR(100),
            quantity INTEGER,
            unit_price DECIMAL(10,2),
            total_price DECIMAL(10,2),
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        -- 门店表
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            city VARCHAR(50),
            address VARCHAR(200),
            manager VARCHAR(50),
            open_date TIMESTAMP
        );
    """)

    # 商品数据
    products_data = [
        ("iPhone 15 Pro", "手机数码", 7999.00, 6500.00, 100),
        ("iPhone 15", "手机数码", 5999.00, 4800.00, 150),
        ("MacBook Pro 14", "电脑办公", 14999.00, 12000.00, 50),
        ("MacBook Air", "电脑办公", 8999.00, 7000.00, 80),
        ("AirPods Pro 2", "数码配件", 1899.00, 1400.00, 200),
        ("iPad Pro", "平板电脑", 6799.00, 5500.00, 60),
        ("小米14", "手机数码", 3999.00, 3200.00, 120),
        ("华为Mate 60", "手机数码", 6999.00, 5500.00, 80),
        ("戴森吸尘器", "家用电器", 2999.00, 2200.00, 40),
        ("索尼WH-1000XM5", "数码配件", 2499.00, 1800.00, 60),
        ("乐高城市组", "玩具", 399.00, 280.00, 100),
        ("Switch游戏机", "游戏", 2099.00, 1600.00, 70),
        ("SK-II神仙水", "美妆", 1540.00, 1100.00, 90),
        ("雅诗兰黛小棕瓶", "美妆", 1080.00, 780.00, 80),
        ("耐克运动鞋", "服饰", 899.00, 550.00, 150),
    ]

    cursor.executemany(
        "INSERT INTO products (name, category, price, cost, stock) VALUES (?, ?, ?, ?, ?)",
        products_data
    )

    # 城市列表
    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "苏州"]

    # 客户数据
    customers_data = []
    for i in range(1, 51):
        city = random.choice(cities)
        customers_data.append((
            f"客户{i:03d}",
            f"customer{i}@example.com",
            f"138{random.randint(10000000, 99999999)}",
            city,
            (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
            random.randint(1, 3)
        ))

    cursor.executemany(
        "INSERT INTO customers (name, email, phone, city, register_date, vip_level) VALUES (?, ?, ?, ?, ?, ?)",
        customers_data
    )

    # 门店数据
    stores_data = [
        ("北京朝阳旗舰店", "北京", "朝阳区建国路88号", "张经理", "2023-01-15"),
        ("上海浦东店", "上海", "浦东新区陆家嘴环路1000号", "李经理", "2023-03-20"),
        ("广州天河店", "广州", "天河区天河路208号", "王经理", "2023-02-10"),
        ("深圳南山店", "深圳", "南山区科技园南路88号", "陈经理", "2023-04-05"),
        ("杭州西湖店", "杭州", "西湖区文三路478号", "刘经理", "2023-05-18"),
    ]

    cursor.executemany(
        "INSERT INTO stores (name, city, address, manager, open_date) VALUES (?, ?, ?, ?, ?)",
        stores_data
    )

    # 生成订单数据（最近30天）
    order_statuses = ['completed', 'completed', 'completed', 'completed', 'refunded']  # 80%完成率
    pay_methods = ['微信支付', '支付宝', '银行卡', '信用卡']

    order_id = 0
    for day_offset in range(30, 0, -1):
        date = datetime.now() - timedelta(days=day_offset)
        # 每天5-20个订单
        daily_orders = random.randint(5, 20)

        for _ in range(daily_orders):
            order_id += 1
            customer_id = random.randint(1, 50)
            order_no = f"ORD{date.strftime('%Y%m%d')}{order_id:04d}"
            status = random.choice(order_statuses)
            pay_method = random.choice(pay_methods)

            # 每个订单1-5个商品
            items_count = random.randint(1, 5)
            total_amount = 0

            # 先创建订单明细
            order_items_data = []
            for _ in range(items_count):
                product_id = random.randint(1, 15)
                quantity = random.randint(1, 3)
                cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
                product = cursor.fetchone()
                if product:
                    product_name, unit_price = product
                    item_total = unit_price * quantity
                    total_amount += item_total
                    order_items_data.append((
                        order_id, product_id, product_name, quantity, unit_price, item_total
                    ))

            # 折扣
            discount = random.choice([0, 0, 0, 50, 100, 200]) if total_amount > 1000 else 0
            final_amount = total_amount - discount

            # 创建订单
            created_at = date + timedelta(hours=random.randint(9, 22), minutes=random.randint(0, 59))
            cursor.execute(
                """INSERT INTO orders
                   (id, customer_id, order_no, total_amount, discount_amount, final_amount, status, pay_method, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (order_id, customer_id, order_no, total_amount, discount, final_amount, status, pay_method, created_at)
            )

            # 插入订单明细
            cursor.executemany(
                """INSERT INTO order_items
                   (order_id, product_id, product_name, quantity, unit_price, total_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                order_items_data
            )

    conn.commit()
    conn.close()

    return db_path


def get_sample_schema() -> Dict[str, Any]:
    """获取示例数据库的Schema"""
    return {
        "tables": [
            {
                "name": "products",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                    {"name": "category", "type": "VARCHAR(50)", "nullable": True},
                    {"name": "price", "type": "DECIMAL(10,2)", "nullable": False},
                    {"name": "cost", "type": "DECIMAL(10,2)", "nullable": True},
                    {"name": "stock", "type": "INTEGER", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": True},
                ],
                "primary_key": ["id"]
            },
            {
                "name": "customers",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                    {"name": "email", "type": "VARCHAR(100)", "nullable": True},
                    {"name": "phone", "type": "VARCHAR(20)", "nullable": True},
                    {"name": "city", "type": "VARCHAR(50)", "nullable": True},
                    {"name": "register_date", "type": "TIMESTAMP", "nullable": True},
                    {"name": "vip_level", "type": "INTEGER", "nullable": True},
                ],
                "primary_key": ["id"]
            },
            {
                "name": "orders",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "customer_id", "type": "INTEGER", "nullable": True},
                    {"name": "order_no", "type": "VARCHAR(50)", "nullable": True},
                    {"name": "total_amount", "type": "DECIMAL(10,2)", "nullable": True},
                    {"name": "discount_amount", "type": "DECIMAL(10,2)", "nullable": True},
                    {"name": "final_amount", "type": "DECIMAL(10,2)", "nullable": True},
                    {"name": "status", "type": "VARCHAR(20)", "nullable": True},
                    {"name": "pay_method", "type": "VARCHAR(20)", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": True},
                ],
                "primary_key": ["id"]
            },
            {
                "name": "order_items",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "order_id", "type": "INTEGER", "nullable": True},
                    {"name": "product_id", "type": "INTEGER", "nullable": True},
                    {"name": "product_name", "type": "VARCHAR(100)", "nullable": True},
                    {"name": "quantity", "type": "INTEGER", "nullable": True},
                    {"name": "unit_price", "type": "DECIMAL(10,2)", "nullable": True},
                    {"name": "total_price", "type": "DECIMAL(10,2)", "nullable": True},
                ],
                "primary_key": ["id"]
            },
            {
                "name": "stores",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                    {"name": "city", "type": "VARCHAR(50)", "nullable": True},
                    {"name": "address", "type": "VARCHAR(200)", "nullable": True},
                    {"name": "manager", "type": "VARCHAR(50)", "nullable": True},
                    {"name": "open_date", "type": "TIMESTAMP", "nullable": True},
                ],
                "primary_key": ["id"]
            },
        ]
    }


if __name__ == "__main__":
    path = generate_sample_database()
    print(f"示例数据库已生成: {path}")
