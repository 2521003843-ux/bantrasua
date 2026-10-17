import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import random

import ast

app_code = '''import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import random

# =========================================================
# 1. CẤU HÌNH TRANG & THEME COFFEE MINI ☕✨
# =========================================================
st.set_page_config(
    page_title="COFFEE MINI - Cà Phê Nhỏ, Niềm Vui Lớn ☕",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. HÀM BẢO VỆ TƯƠNG THÍCH MỌI PHIÊN BẢN STREAMLIT
# =========================================================
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def safe_toast(msg, icon="☕"):
    if hasattr(st, "toast"):
        st.toast(msg, icon=icon)
    else:
        st.success(f"{icon} {msg}")

# =========================================================
# 3. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE
# =========================================================
DB_FILE = "coffee_mini_pos.db"

def get_db_connection():
    return sqlite3.connect(DB_FILE, timeout=15)

def init_db():
    try:
        conn = get_db_connection()
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
    except Exception as e:
        print("Lỗi CSDL:", e)

init_db()

def save_order_to_db(phone, order_type, items, total, discount, final, pay_method):
    try:
        conn = get_db_connection()
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
        return True
    except Exception as e:
        st.error(f"Lỗi khi lưu đơn hàng: {e}")
        return False

def get_customer_points(phone):
    if not phone:
        return 0
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT points FROM customers WHERE phone = ?", (phone,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0

def load_orders_history():
    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT id, order_time, customer_phone, order_type, final_amount, payment_method FROM orders ORDER BY id DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# =========================================================
# 4. GIAO DIỆN & CSS TRANG TRÍ TỐI GIẢN - COFFEE MINI
# =========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #FAF7F2;
    }

    /* BANNER COFFEE MINI */
    .mini-banner {
        background: linear-gradient(135deg, #4A3525 0%, #6F4E37 50%, #A67B5B 100%);
        border-radius: 20px;
        padding: 28px 20px;
        color: #FFFDF9;
        text-align: center;
        box-shadow: 0 10px 25px rgba(74, 53, 37, 0.2);
        margin-bottom: 25px;
        border: 2px solid #ECB176;
    }
    
    .mini-banner h1 {
        color: #FED8B1 !important;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 6px;
        letter-spacing: 1px;
    }
    
    .mini-banner p {
        color: #F6E6D9;
        font-size: 1.1rem;
        margin: 0;
        font-weight: 500;
    }

    /* CARD MÓN ĂN VỚI HÌNH ẢNH MÔ TẢ */
    .product-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1px solid #E8DCD0;
        text-align: center;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }

    .product-img {
        width: 100%;
        height: 140px;
        object-fit: cover;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    .product-card h4 {
        color: #4A3525;
        margin-bottom: 4px;
        font-weight: 700;
        font-size: 1.05rem;
    }

    .product-price {
        color: #C85250;
        font-size: 1.2rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    /* KHUNG GIỎ HÀNG */
    .cart-container {
        background-color: #FFFFFF;
        border-radius: 18px;
        padding: 20px;
        border-top: 6px solid #6F4E37;
        box-shadow: 0 6px 20px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

if "cart" not in st.session_state:
    st.session_state.cart = []
if "applied_discount" not in st.session_state:
    st.session_state.applied_discount = 0

# =========================================================
# 5. THỰC ĐƠN COFFEE MINI CÓ ẢNH MÔ TẢ CHẤT LƯỢNG CAO
# =========================================================
MENU_DATA = {
    "☕ Cà Phê Chữ Ký (Signature Coffee)": [
        {
            "id": "CM01", 
            "name": "Cà Phê Sữa Đá Phin Mini", 
            "price": 29000, 
            "img": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=500&q=80", 
            "desc": "Robusta Buôn Ma Thuột đậm đà pha phin giọt đắng thơm lừng quyện sữa đặc"
        },
        {
            "id": "CM02", 
            "name": "Cà Phê Muối Kem Béo Mini", 
            "price": 35000, 
            "img": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=500&q=80", 
            "desc": "Lớp kem muối mặn béo ngậy hài hòa tuyệt đối cùng cốt cà phê nguyên chất"
        },
        {
            "id": "CM03", 
            "name": "Bạc Xỉu Sài Gòn", 
            "price": 32000, 
            "img": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=500&q=80", 
            "desc": "Nhiều sữa ngọt thơm thanh mát, chỉ một chút nhấn nhá đắng nhẹ của cà phê"
        },
        {
            "id": "CM04", 
            "name": "Cà Phê Trứng Béo Mịn", 
            "price": 39000, 
            "img": "https://images.unsplash.com/photo-1541167760496-1628856ab772?auto=format&fit=crop&w=500&q=80", 
            "desc": "Kem trứng gà tươi đánh bông kem mịn, thơm phức phủ trên cà phê phin nóng"
        },
        {
            "id": "CM05", 
            "name": "Cà Phê Cốt Dừa Đá Xay", 
            "price": 38000, 
            "img": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?auto=format&fit=crop&w=500&q=80", 
            "desc": "Nước cốt dừa thơm béo dẻo mịn đá xay đượm vị espresso thanh nồng"
        },
        {
            "id": "CM06", 
            "name": "Cold Brew Cam Sả Tươi", 
            "price": 42000, 
            "img": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=500&q=80", 
            "desc": "Cà phê ủ lạnh 16 tiếng kết hợp vị chua ngọt mát lành từ cam tươi và sả"
        }
    ],
    "🍵 Trà & Đồ Uống Mát Lạnh": [
        {
            "id": "TR01", 
            "name": "Trà Đào Cam Sả Tươi", 
            "price": 35000, 
            "img": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=500&q=80", 
            "desc": "Đào miếng giòn rụm, hương thơm đượm sả tươi cùng vị chua ngọt mát dịu"
        },
        {
            "id": "TR02", 
            "name": "Trà Sen Vàng Hạt Sen", 
            "price": 39000, 
            "img": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=500&q=80", 
            "desc": "Trà Oolong thanh khiết kết hợp hạt sen bùi ngọt và lớp kem mặn béo ngậy"
        },
        {
            "id": "TR03", 
            "name": "Matcha Latte Nhật Bản", 
            "price": 42000, 
            "img": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=500&q=80", 
            "desc": "Bột trà xanh Matcha Uji cao cấp pha cùng sữa tươi thơm mịn đậm đà"
        }
    ],
    "🥐 Bánh Ngọt Nhỏ & Snack Mini": [
        {
            "id": "BN01", 
            "name": "Bánh Mì Chuối Nướng Bơ", 
            "price": 25000, 
            "img": "https://images.unsplash.com/photo-1603532648955-039310d9ed75?auto=format&fit=crop&w=500&q=80", 
            "desc": "Bánh mì chuối nướng mềm xốp thơm lừng vị bơ Pháp nhẹ nhàng"
        },
        {
            "id": "BN02", 
            "name": "Croissant Bơ Tỏi Nóng Giòn", 
            "price": 28000, 
            "img": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=500&q=80", 
            "desc": "Bánh sừng bò ngàn lớp nướng nóng giòn tan thơm đượm vị bơ tỏi"
        },
        {
            "id": "BN03", 
            "name": "Bánh Bông Lan Trứng Muối Mini", 
            "price": 30000, 
            "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=500&q=80", 
            "desc": "Sốt phô mai béo ngậy tan chảy cùng chà bông và trứng muối mặn bùi"
        }
    ]
}

# Sidebar điều hướng
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #6F4E37;'>☕ COFFEE MINI</h1>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center;'>Góc Nhỏ Cà Phê & Niềm Vui Lớn</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    sidebar_menu = st.radio(
        "📌 Menu Chức Năng:",
        [
            "🛒 Gọi Món POS & Giỏ Hàng",
            "🎰 Vòng Quay May Mắn Mini",
            "👤 Tích Điểm Khách Hàng",
            "📈 Báo Cáo Doanh Thu Real-Time"
        ]
    )

# Banner chính
st.markdown("""
    <div class="mini-banner">
        <h1>☕ COFFEE MINI - SMALL SIZE, BIG SMILE ☕</h1>
        <p>"Không Gian Tối Giản - Thưởng Thức Cà Phê Chất Lượng Mỗi Ngày"</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU 1: GỌI MÓN POS & GIỎ HÀNG
# ---------------------------------------------------------
if sidebar_menu == "🛒 Gọi Món POS & Giỏ Hàng":
    col_pos, col_cart = st.columns([1.7, 1.3])

    with col_pos:
        st.subheader("📋 Thực Đơn Đồ Uống & Bánh Ngọt")
        
        tab1, tab2, tab3 = st.tabs(["☕ Cà Phê Mini", "🍵 Trà & Mát Lạnh", "🥐 Bánh Ngọt"])
        
        def render_category(items):
            cols = st.columns(2)
            for idx, item in enumerate(items):
                with cols[idx % 2]:
                    st.markdown(f"""
                        <div class="product-card">
                            <img src="{item['img']}" class="product-img" alt="{item['name']}">
                            <h4>{item['name']}</h4>
                            <p style="color:#666; font-size:0.82rem; min-height: 36px; margin-bottom:8px;">{item['desc']}</p>
                            <div class="product-price">{item['price']:,.0f} VNĐ</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"➕ Custom & Chọn Món ({item['name']})"):
                        sugar = st.select_slider("Mức ngọt / Sữa:", options=["0% (Đắng)", "30% (Ít ngọt)", "50% (Vừa)", "100% (Ngọt đậm)"], value="50% (Vừa)", key=f"s_{item['id']}")
                        ice = st.select_slider("Mức đá:", options=["Không đá", "Ít đá", "Vừa", "Nhiều đá"], value="Vừa", key=f"i_{item['id']}")
                        bean = st.selectbox("Hạt cà phê chọn:", ["Robusta Buôn Ma Thuột (Đậm)", "Arabica Cầu Đất (Thơm)", "Blend 70/30 (Đồng Bằng)"], key=f"b_{item['id']}")
                        topping = st.multiselect("Topping kèm:", ["Kem Muối (+8k)", "Kem Trứng (+10k)", "Shot Espresso (+10k)", "Thạch Cà Phê (+5k)"], key=f"t_{item['id']}")
                        
                        qty = st.number_input("Số lượng:", min_value=1, value=1, step=1, key=f"q_{item['id']}")
                        
                        if st.button("🛒 Thêm Vào Giỏ Hàng", key=f"add_{item['id']}", type="primary", use_container_width=True):
                            topping_price = 0
                            if "Kem Muối (+8k)" in topping: topping_price += 8000
                            if "Kem Trứng (+10k)" in topping: topping_price += 10000
                            if "Shot Espresso (+10k)" in topping: topping_price += 10000
                            if "Thạch Cà Phê (+5k)" in topping: topping_price += 5000

                            cart_item = {
                                "id": item["id"],
                                "name": item["name"],
                                "unit_price": item["price"] + topping_price,
                                "qty": qty,
                                "sugar": sugar,
                                "ice": ice,
                                "bean": bean,
                                "topping": ", ".join(topping) if topping else "Không",
                                "total": (item["price"] + topping_price) * qty
                            }
                            st.session_state.cart.append(cart_item)
                            safe_toast(f"Đã thêm {qty}x {item['name']} vào giỏ!", icon="☕")

        with tab1:
            render_category(MENU_DATA["☕ Cà Phê Chữ Ký (Signature Coffee)"])
        with tab2:
            render_category(MENU_DATA["🍵 Trà & Đồ Uống Mát Lạnh"])
        with tab3:
            render_category(MENU_DATA["🥐 Bánh Ngọt Nhỏ & Snack Mini"])

    # CỘT GIỎ HÀNG & THANH TOÁN
    with col_cart:
        st.markdown("<div class='cart-container'>", unsafe_allow_html=True)
        st.markdown("### 🛒 Hóa Đơn POS & Giỏ Hàng")
        
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            order_type = st.selectbox("Hình thức:", ["Tại bàn (In-house)", "Mang đi (Takeaway)"])
        with c_p2:
            table_num = st.text_input("Bàn / Tên khách:", value="Bàn 01")

        cust_phone = st.text_input("📞 SĐT Khách Hàng (Tích Điểm):", placeholder="Nhập SĐT khách...")
        if cust_phone:
            pts = get_customer_points(cust_phone)
            st.info(f"👤 Khách hàng | Điểm tích lũy: **{pts} điểm** (Quy đổi: {pts*1000:,.0f}đ)")

        st.markdown("---")

        if not st.session_state.cart:
            st.warning("Giỏ hàng đang trống. Hãy chọn món từ menu bên trái!")
            raw_total = 0
        else:
            raw_total = 0
            to_remove = None
            for idx, c_item in enumerate(st.session_state.cart):
                raw_total += c_item["total"]
                col_item1, col_item2 = st.columns([3, 1])
                with col_item1:
                    st.write(f"**{idx+1}. {c_item['name']}** x{c_item['qty']}")
                    st.caption(f"⚙️ {c_item['sugar']} | {c_item['ice']} | Hạt: {c_item['bean']}")
                    if c_item['topping'] != "Không":
                        st.caption(f"➕ Topping: {c_item['topping']}")
                    st.write(f"💰 {c_item['total']:,.0f} VNĐ")
                with col_item2:
                    if st.button("❌", key=f"del_cart_{idx}_{c_item['id']}"):
                        to_remove = idx
                st.markdown("---")

            if to_remove is not None:
                st.session_state.cart.pop(to_remove)
                safe_rerun()

            discount_amount = st.session_state.applied_discount
            final_total = max(0, raw_total - discount_amount)

            st.write(f"• Tạm tính: **{raw_total:,.0f} VNĐ**")
            if discount_amount > 0:
                st.write(f"• Giảm giá Voucher / Vòng quay: <span style='color:green;'>- {discount_amount:,.0f} VNĐ</span>", unsafe_allow_html=True)
            st.markdown(f"### 💸 Tổng Thanh Toán: <span style='color:#C85250;'>{final_total:,.0f} VNĐ</span>", unsafe_allow_html=True)

            pay_method = st.radio("Phương thức thanh toán:", ["Tiền mặt 💵", "Chuyển khoản VietQR 📲", "Thẻ ngân hàng 💳"])

            if pay_method == "Chuyển khoản VietQR 📲":
                st.image("https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=COFFEEMINI_PAYMENT", caption="Quét mã VietQR thanh toán")

            if st.button("✅ XÁC NHẬN THANH TOÁN & IN HÓA ĐƠN", type="primary", use_container_width=True):
                success = save_order_to_db(cust_phone, f"{order_type} ({table_num})", st.session_state.cart, raw_total, discount_amount, final_total, pay_method)
                if success:
                    if hasattr(st, "balloons"):
                        st.balloons()
                    st.success("🎉 Thanh toán thành công! Đơn hàng đã được lưu vào CSDL.")
                    st.session_state.cart = []
                    st.session_state.applied_discount = 0
                    safe_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU 2: VÒNG QUAY MAY MẮN MINI
# ---------------------------------------------------------
elif sidebar_menu == "🎰 Vòng Quay May Mắn Mini":
    st.subheader("🎰 Vòng Quay May Mắn Coffee Mini - Trúng Thưởng 100%")
    st.caption("Mỗi hóa đơn tại Coffee Mini đều nhận được 1 lượt quay nhận Voucher ưu đãi!")

    prizes = [
        ("🎉 Voucher Giảm 10.000 VNĐ", 10000),
        ("🔥 Voucher Giảm 15.000 VNĐ", 15000),
        ("☕ Tặng 01 Shot Espresso Kem Muối", 10000),
        ("🥐 Tặng 01 Bánh Mì Chuối Nướng", 25000),
        ("🍀 Chúc bạn may mắn lần sau", 0)
    ]

    col_w1, col_w2 = st.columns([1, 1])

    with col_w1:
        st.image("https://img.icons8.com/color/180/wheel-of-fortune.png", width=180)
        if st.button("🔄 THỰC HIỆN QUAY THƯỞNG", type="primary", use_container_width=True):
            won_prize, won_val = random.choice(prizes)
            st.session_state.won_prize = won_prize
            st.session_state.won_val = won_val
            st.session_state.applied_discount = won_val

    with col_w2:
        if "won_prize" in st.session_state:
            st.success(f"🎁 Kết Quả: **{st.session_state.won_prize}**")
            if st.session_state.won_val > 0:
                st.info(f"Đã tự động áp dụng giảm **-{st.session_state.won_val:,.0f} VNĐ** vào giỏ hàng POS!")

# ---------------------------------------------------------
# MENU 3: TÍCH ĐIỂM KHÁCH HÀNG
# ---------------------------------------------------------
elif sidebar_menu == "👤 Tích Điểm Khách Hàng":
    st.subheader("👤 Tra Cứu & Tích Điểm Thân Thiết")
    
    search_phone = st.text_input("🔍 Nhập Số Điện Thoại Khách Hàng:")
    if search_phone:
        pts = get_customer_points(search_phone)
        st.metric(f"Khách hàng ({search_phone})", f"{pts} Điểm tích lũy")
        st.write(f"• Giá trị quy đổi giảm giá: **{pts*1000:,.0f} VNĐ**")

# ---------------------------------------------------------
# MENU 4: BÁO CÁO DOANH THU REAL-TIME
# ---------------------------------------------------------
else:
    st.subheader("📈 Báo Cáo Doanh Thu Real-Time (Đồng Bộ SQLite)")

    df_orders = load_orders_history()
    
    if df_orders.empty:
        st.warning("Chưa có đơn hàng nào được ghi nhận trong CSDL.")
    else:
        total_rev = df_orders["final_amount"].sum()
        total_orders_cnt = len(df_orders)

        c_r1, c_r2, c_r3 = st.columns(3)
        with c_r1:
            st.metric("💰 Tổng Doanh Thu", f"{total_rev:,.0f} VNĐ")
        with c_r2:
            st.metric("🧾 Tổng Số Đơn Hàng", f"{total_orders_cnt} Đơn")
        with c_r3:
            st.metric("📊 Giá Trị Trung Bình / Đơn", f"{total_rev/total_orders_cnt:,.0f} VNĐ")

        st.markdown("### 📜 Lịch Sử Giao Dịch Đơn Hàng")
        st.dataframe(df_orders, use_container_width=True, hide_index=True)
'''

ast.parse(app_code)
print("Coffee Mini app code parsed successfully!")
