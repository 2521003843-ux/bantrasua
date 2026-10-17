import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import random

# =========================================================
# 1. CẤU HÌNH TRANG (BẮT BUỘC ĐẶT TRÊN CÙNG TRƯỚC MỌI LỆNH ST)
# =========================================================
st.set_page_config(
    page_title="Phin Việt Coffee - Cà Phê Đất Việt ☕",
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
# 3. KHỞI TẠO VÀ THAO TÁC CƠ SỞ DỮ LIỆU SQLITE (AN TOÀN)
# =========================================================
DB_FILE = "viet_coffee_pos.db"

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
        print("Lỗi khởi tạo CSDL:", e)

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
        st.error(f"Lỗi khi lưu đơn hàng vào CSDL: {e}")
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
# 4. GIAO DIỆN & CSS PHIN VIỆT COFFEE
# =========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #FDFBF7;
    }

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
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 8px;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
    }
    
    .coffee-banner p {
        color: #F3E8DC;
        font-size: 1.1rem;
        margin: 0;
        font-weight: 500;
    }

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
        {"id": "CF02", "name": "Cà Phê Đen Đá Nguyên Chất", "price": 28000, "img": "☕", "desc": "Đắng thanh, thơm nồng đậm vị đặc trưng của hạt Robusta Tây Nguyên"},
        {"id": "CF03", "name": "Bạc Xỉu Sài Gòn", "price": 35000, "img": "🥛", "desc": "Hương vị chuẩn Sài Gòn - nhiều sữa thơm ngậy, vị cà phê đắng nhẹ"},
        {"id": "CF04", "name": "Cà Phê Trứng Hà Nội", "price": 45000, "img": "🥚", "desc": "Lớp kem trứng đánh bông béo ngậy phủ trên cốt cà phê phin nóng"},
        {"id": "CF05", "name": "Cà Phê Muối Kem Béo", "price": 39000, "img": "🧂", "desc": "Sự kết hợp giữa lớp kem muối mặn nhẹ béo ngậy và vị đắng cà phê"},
        {"id": "CF06", "name": "Cà Phê Dừa Đá Xay", "price": 42000, "img": "🥥", "desc": "Nước cốt dừa dẻo mịn đá xay kết hợp cùng shot cà phê phin thơm lừng"}
    ],
    "🌿 Trà Việt & Giải Nhiệt": [
        {"id": "TR01", "name": "Trà Sen Vàng Củ Năng", "price": 45000, "img": "🍵", "desc": "Trà Oolong thanh mát kết hợp hạt sen bùi ngậy và củ năng giòn ngọt"},
        {"id": "TR02", "name": "Trà Đào Cam Sả Tươi", "price": 39000, "img": "🍑", "desc": "Đào miếng giòn rụm, vị thơm đượm nồng của sả tươi và cam sành"},
        {"id": "TR03", "name": "Trà Quất Mật Ong Tắc", "price": 32000, "img": "🍋", "desc": "Vị chua dịu lành từ quả tắc tươi hòa quyện mật ong rừng"}
    ],
    "🍰 Bánh Đi Kèm Cà Phê": [
        {"id": "BN01", "name": "Bánh Mì Chà Bông Trứng Muối", "price": 35000, "img": "🧁", "desc": "Sốt phô mai tan chảy kết hợp chà bông gà và trứng muối đậm đà"},
        {"id": "BN02", "name": "Bánh Mì Chuối Nướng Bơ", "price": 28000, "img": "🍌", "desc": "Bánh mì chuối thơm lừng mùi bơ tươi, vỏ giòn ruột mềm dẻo"},
        {"id": "BN03", "name": "Bánh Bông Lan Phô Mai Cà Phê", "price": 35000, "img": "🍰", "desc": "Bánh mềm mịn thơm đượm hương cà phê đắng nhẹ và phô mai"}
    ]
}

# Sidebar điều hướng
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

# Banner chính
st.markdown("""
    <div class="coffee-banner">
        <h1>☕ PHIN VIỆT COFFEE - ĐẬM VỊ ĐẤT VIỆT 🇻🇳</h1>
        <p>"Thưởng Thức Hương Vị Cà Phê Nguyên Bản Từ Đồi Núi Tây Nguyên"</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU 1: GỌI MÓN POS & GIỎ HÀNG
# ---------------------------------------------------------
if sidebar_menu == "🛒 Gọi Món POS & Giỏ Hàng":
    col_pos, col_cart = st.columns([1.7, 1.3])

    with col_pos:
        st.subheader("📋 Thực Đơn Cà Phê & Đồ Uống")
        
        tab1, tab2, tab3 = st.tabs(["☕ Cà Phê Phin", "🌿 Trà Việt", "🍰 Bánh Đi Kèm"])
        
        def render_category(items):
            cols = st.columns(2)
            for idx, item in enumerate(items):
                with cols[idx % 2]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div style="font-size: 2.5rem;">{item['img']}</div>
                            <h4>{item['name']}</h4>
                            <p style="color:#666; font-size:0.85rem; height: 38px;">{item['desc']}</p>
                            <div class="product-price">{item['price']:,.0f} VNĐ</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"➕ Custom & Chọn Món ({item['name']})"):
                        sugar = st.select_slider("Mức ngọt / Sữa đặc:", options=["0% (Đắng)", "30% (Ít ngọt)", "50% (Vừa)", "100% (Đậm ngọt)"], value="50% (Vừa)", key=f"s_{item['id']}")
                        ice = st.select_slider("Mức đá:", options=["Không đá", "Ít đá", "Vừa", "Nhiều đá"], value="Vừa", key=f"i_{item['id']}")
                        bean = st.selectbox("Loại hạt cà phê:", ["Robusta Đậm Đà (Buôn Ma Thuột)", "Arabica Thơm Thanh (Cầu Đất)", "Blend 70/30 Tây Nguyên"], key=f"b_{item['id']}")
                        topping = st.multiselect("Topping kèm theo:", ["Kem Muối (+8k)", "Kem Trứng (+10k)", "Shot Espresso (+10k)", "Thạch Cà Phê (+5k)"], key=f"t_{item['id']}")
                        
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
                            safe_toast(f"Đã thêm {qty}x {item['name']} vào giỏ hàng!", icon="☕")

        with tab1:
            render_category(MENU_DATA["☕ Cà Phê Phin Truyền Thống"])
        with tab2:
            render_category(MENU_DATA["🌿 Trà Việt & Giải Nhiệt"])
        with tab3:
            render_category(MENU_DATA["🍰 Bánh Đi Kèm Cà Phê"])

    # CỘT GIỎ HÀNG & THANH TOÁN
    with col_cart:
        st.markdown("<div class='cart-container'>", unsafe_allow_html=True)
        st.markdown("### 🛒 Hóa Đơn & Giỏ Hàng POS")
        
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            order_type = st.selectbox("Hình thức:", ["Tại bàn (In-house)", "Mang đi (Takeaway)"])
        with c_p2:
            table_num = st.text_input("Số bàn / Tên khách:", value="Bàn 01")

        cust_phone = st.text_input("📞 SĐT Khách Hàng (Tích Điểm):", placeholder="Nhập SĐT để tích điểm...")
        if cust_phone:
            pts = get_customer_points(cust_phone)
            st.info(f"👤 Khách hàng thân thiết | Điểm tích lũy: **{pts} điểm** (Giá trị quy đổi: {pts*1000:,.0f}đ)")

        st.markdown("---")

        if not st.session_state.cart:
            st.warning("Giỏ hàng hiện tại đang trống. Vui lòng chọn món từ menu bên trái!")
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
            st.markdown(f"### 💸 Tổng Thanh Toán: <span style='color:#B91C1C;'>{final_total:,.0f} VNĐ</span>", unsafe_allow_html=True)

            pay_method = st.radio("Phương thức thanh toán:", ["Tiền mặt 💵", "Chuyển khoản VietQR 📲", "Thẻ ngân hàng 💳"])

            if pay_method == "Chuyển khoản VietQR 📲":
                st.image("https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=PHINVIETCOFFEE_PAYMENT", caption="Quét mã VietQR để thanh toán")

            if st.button("✅ XÁC NHẬN THANH TOÁN & IN HÓA ĐƠN", type="primary", use_container_width=True):
                success = save_order_to_db(cust_phone, f"{order_type} ({table_num})", st.session_state.cart, raw_total, discount_amount, final_total, pay_method)
                if success:
                    if hasattr(st, "balloons"):
                        st.balloons()
                    st.success("🎉 Thanh toán thành công! Đơn hàng đã được lưu vào CSDL SQLite vĩnh viễn.")
                    st.session_state.cart = []
                    st.session_state.applied_discount = 0
                    safe_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU 2: VÒNG QUAY MAY MẮN CÀ PHÊ
# ---------------------------------------------------------
elif sidebar_menu == "🎰 Vòng Quay May Mắn Cà Phê":
    st.subheader("🎰 Vòng Quay May Mắn Cà Phê - Trúng Thưởng 100%")
    st.caption("Mỗi hóa đơn tại Phin Việt Coffee đều nhận được 1 lượt quay trúng Voucher hấp dẫn!")

    prizes = [
        ("🎉 Voucher Giảm 10.000 VNĐ", 10000),
        ("🔥 Voucher Giảm 20.000 VNĐ", 20000),
        ("☕ Tặng 01 Shot Espresso Kem Muối", 10000),
        ("🍌 Tặng 01 Bánh Mì Chuối Nướng Bơ", 28000),
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
                st.info(f"Đã tự động áp dụng ưu đãi **-{st.session_state.won_val:,.0f} VNĐ** vào giỏ hàng POS!")

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
