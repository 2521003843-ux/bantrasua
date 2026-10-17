import ast

app_code = '''import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import random

# ---------------------------------------------------------
# 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE (LƯU VĨNH VIỄN)
# ---------------------------------------------------------
DB_FILE = "viet_coffee_pos.db"

def init_db():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_time TEXT,
            customer_phone TEXT,
            order_type TEXT,
            items_json TEXT,
            total_amount REAL,
            discount_amount REAL,
            final_amount REAL,
            payment_method TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            phone TEXT PRIMARY KEY,
            name TEXT,
            points INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_order_to_db(phone, order_type, items, total, discount, final, pay_method):
    conn = sqlite3.connect(DB_FILE, timeout=15)
    c = conn.cursor()
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    items_str = json.dumps(items, ensure_ascii=False)
    c.execute("""
        INSERT INTO orders (order_time, customer_phone, order_type, items_json, total_amount, discount_amount, final_amount, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now_str, phone, order_type, items_str, total, discount, final, pay_method))
    
    if phone:
        earned_pts = int(final // 10000)
        c.execute("""
            INSERT INTO customers (phone, name, points) VALUES (?, 'Khách hàng', ?) 
            ON CONFLICT(phone) DO UPDATE SET points = points + ?
        """, (phone, earned_pts, earned_pts))
        
    conn.commit()
    conn.close()

def get_customer_points(phone):
    if not phone:
        return 0
    conn = sqlite3.connect(DB_FILE, timeout=15)
    c = conn.cursor()
    c.execute("SELECT points FROM customers WHERE phone = ?", (phone,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def load_orders_history():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    df = pd.read_sql("SELECT id, order_time, customer_phone, order_type, final_amount, payment_method FROM orders ORDER BY id DESC", conn)
    conn.close()
    return df

# ---------------------------------------------------------
# 2. CẤU HÌNH GIAO DIỆN PHIN VIỆT COFFEE ☕🇻🇳
# ---------------------------------------------------------
st.set_page_config(
    page_title="Phin Việt Coffee - Cà Phê Đất Việt ☕🇻🇳",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #FDFBF7;
    }

    /* BANNER CHÍNH */
    .coffee-banner {
        background: linear-gradient(135deg, #2C1A1D 0%, #4A2810 50%, #8C4A27 100%);
        border-radius: 20px;
        padding: 30px 20px;
        color: #FFF8E1;
        text-align: center;
        box-shadow: 0 10px 25px rgba(44, 26, 29, 0.3);
        margin-bottom: 25px;
        border: 2px solid #D97706;
    }
    
    .coffee-banner h1 {
        color: #FBBF24 !important;
        font-size: 2.6rem;
        font-weight: 800;
        margin-bottom: 8px;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
    }
    
    .coffee-banner p {
        color: #F3E8DC;
        font-size: 1.15rem;
        margin: 0;
        font-weight: 500;
    }

    /* CARD SẢN PHẨM */
    .product-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1.5px solid #E5D5C5;
        text-align: center;
        margin-bottom: 15px;
    }

    .product-card h4 {
        color: #2C1A1D;
        margin-bottom: 5px;
        font-weight: 700;
    }

    .product-price {
        color: #B91C1C;
        font-size: 1.25rem;
        font-weight: 800;
        margin-bottom: 10px;
    }

    /* GIỎ HÀNG */
    .cart-container {
        background-color: #FFFFFF;
        border-radius: 18px;
        padding: 20px;
        border-top: 6px solid #8C4A27;
        box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    }
    </style>
""", unsafe_allow_html=True)

if "cart" not in st.session_state:
    st.session_state.cart = []
if "applied_discount" not in st.session_state:
    st.session_state.applied_discount = 0

MENU_DATA = {
    "☕ Cà Phê Phin Truyền Thống": [
        {"id": "CF01", "name": "Cà Phê Sữa Đá Phin", "price": 32000, "img": "☕", "desc": "Cà phê Robusta Buôn Ma Thuột đậm đà pha phin truyền thống với sữa đặc"},
        {"id": "CF02", "name": "Cà Phê Đen Đá Nguyên Chất", "price": 28000, "img": "☕", "desc": "Đắng thanh, thơm nồng đậm vị đặc trưng của hạt Robusta đồi núi Tây Nguyên"},
        {"id": "CF03", "name": "Bạc Xỉu Sài Gòn", "price": 35000, "img": "🥛", "desc": "Hương vị chuẩn phố thị Sài Gòn - nhiều sữa thơm ngậy, vị cà phê đắng nhẹ"},
        {"id": "CF04", "name": "Cà Phê Trứng Hà Nội", "price": 45000, "img": "🥚", "desc": "Lớp kem trứng đánh bông béo ngậy thơm mịn phủ trên cốt cà phê phin nóng"},
        {"id": "CF05", "name": "Cà Phê Muối Kem Béo", "price": 39000, "img": "🧂", "desc": "Sự kết hợp giữa lớp kem muối mặn nhẹ béo ngậy và vị đắng đậm đà của cà phê"},
        {"id": "CF06", "name": "Cà Phê Dừa Đá Xay", "price": 42000, "img": "🥥", "desc": "Nước cốt dừa dẻo mịn đá xay kết hợp hoàn hảo cùng shot cà phê phin thơm lừng"}
    ],
    "🌿 Trà Việt & Đồ Uống Mới": [
        {"id": "TR01", "name": "Trà Sen Vàng Củ Năng", "price": 45000, "img": "🍵", "desc": "Trà Oolong thanh mát kết hợp hạt sen bùi ngậy và củ năng giòn ngọt"},
        {"id": "TR02", "name": "Trà Đào Cam Sả Tươi", "price": 39000, "img": "🍑", "desc": "Đào miếng giòn rụm, vị thơm đượm nồng của sả tươi và cam sành"},
        {"id": "TR03", "name": "Trà Quất Mật Ong Tắc", "price": 32000, "img": "🍋", "desc": "Vị chua dịu lành lành từ quả tắc tươi hòa quyện mật ong rừng"}
    ],
    "🍰 Bánh Đi Kèm Cà Phê": [
        {"id": "BN01", "name": "Bánh Mì Chà Bông Trứng Muối", "price": 35000, "img": "🧁", "desc": "Sốt phô mai tan chảy đậm đà kết hợp chà bông gà và trứng muối mặn bùi"},
        {"id": "BN02", "name": "Bánh Mì Chuối Nướng Bơ", "price": 28000, "img": "🍌", "desc": "Bánh mì chuối thơm lừng mùi bơ tươi, vỏ giòn ruột mềm dẻo"},
        {"id": "BN03", "name": "Bánh Bông Lan Phô Mai Cà Phê", "price": 35000, "img": "🍰", "desc": "Lớp bánh mềm mịn thơm đượm hương cà phê đắng nhẹ và phô mai"}
    ]
}

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #8C4A27;'>☕ PHIN VIỆT</h1>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center;'>Cà Phê Đất Việt Nguyên Bản</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    sidebar_menu = st.radio(
        "📌 Menu Chức Năng:",
        [
            "🛒 Gọi Món POS & Giỏ Hàng",
            "🎰 Vòng Quay May Mắn Cà Phê",
            "👤 Tích Điểm Khách Hàng",
            "📈 Báo Cáo Doanh Thu Real-Time"
        ]
    )

st.markdown("""
    <div class="coffee-banner">
        <h1>☕ PHIN VIỆT COFFEE - ĐẬM VỊ ĐẤT VIỆT 🇻🇳</h1>
        <p>"Thưởng Thức Hương Vị Cà Phê Nguyên Bản Từ Đồi Núi Tây Nguyên"</p>
    </div>
""", unsafe_allow_html=True)
'''

ast.parse(app_code)
print("Updated App code AST verified successfully!")
