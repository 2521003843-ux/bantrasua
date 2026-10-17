import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import random

# ---------------------------------------------------------
# 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE (LƯU VĨNH VIỄN)
# ---------------------------------------------------------
DB_FILE = "autumn_coffee.db"

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

# Các hàm thao tác CSDL
def save_order_to_db(phone, order_type, items, total, discount, final, pay_method):
    conn = sqlite3.connect(DB_FILE, timeout=15)
    c = conn.cursor()
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    items_str = json.dumps(items, ensure_ascii=False)
    c.execute("""
        INSERT INTO orders (order_time, customer_phone, order_type, items_json, total_amount, discount_amount, final_amount, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now_str, phone, order_type, items_str, total, discount, final, pay_method))
    
    # Cộng điểm tích lũy cho khách hàng (10.000đ = 1 điểm)
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
# 2. CẤU HÌNH GIAO DIỆN AUTUMN COFFEE 🍂☕
# ---------------------------------------------------------
st.set_page_config(
    page_title="Autumn Coffee - Hương Vị Cà Phê Việt 🍂☕",
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
        background-color: #FAF6F0;
    }

    /* BANNER AUTUMN COFFEE */
    .coffee-banner {
        background: linear-gradient(135deg, #3E2723 0%, #4E342E 50%, #8D6E63 100%);
        border-radius: 20px;
        padding: 30px 20px;
        color: #FFF8E1;
        text-align: center;
        box-shadow: 0 10px 25px rgba(62, 39, 35, 0.25);
        margin-bottom: 25px;
        border: 2px solid #D7CCC8;
    }
    
    .coffee-banner h1 {
        color: #FFB300 !important;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 8px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .coffee-banner p {
        color: #E0D5C1;
        font-size: 1.1rem;
        margin: 0;
        font-style: italic;
    }

    /* CARD MÓN ĂN / ĐỒ UỐNG */
    .product-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1px solid #E0D5C1;
        text-align: center;
        margin-bottom: 15px;
    }

    .product-card h4 {
        color: #3E2723;
        margin-bottom: 5px;
        font-weight: 700;
    }

    .product-price {
        color: #D84315;
        font-size: 1.2rem;
        font-weight: 800;
        margin-bottom: 10px;
    }

    /* KHUNG GIỎ HÀNG */
    .cart-container {
        background-color: #FFFFFF;
        border-radius: 18px;
        padding: 20px;
        border-top: 6px solid #8D6E63;
        box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo giỏ hàng trong session state
if "cart" not in st.session_state:
    st.session_state.cart = []
if "applied_discount" not in st.session_state:
    st.session_state.applied_discount = 0

# ---------------------------------------------------------
# 3. DANH MỤC THỰC ĐƠN CÀ PHÊ VIỆT NAM (MENU)
# ---------------------------------------------------------
MENU_DATA = {
    "☕ Cà Phê Phin Việt": [
        {"id": "CF01", "name": "Cà Phê Sữa Đá Phin", "price": 32000, "img": "☕", "desc": "Cà phê Robusta Buôn Ma Thuột nguyên chất pha phin cùng sữa đặc đậm đà"},
        {"id": "CF02", "name": "Cà Phê Đen Đá Phin", "price": 28000, "img": "☕", "desc": "Hương vị đắng thanh, thơm nồng đặc trưng của hạt Robusta rang đậm"},
        {"id": "CF03", "name": "Bạc Xỉu Sài Gòn", "price": 35000, "img": "🥛", "desc": "Nhiều sữa ít cà phê, béo ngậy thơm ngon ngọt ngào"},
        {"id": "CF04", "name": "Cà Phê Trứng Hà Nội", "price": 45000, "img": "🥚", "desc": "Lớp kem trứng đánh bông mịn màng béo ngậy phủ trên cà phê phin nóng"},
        {"id": "CF05", "name": "Cà Phê Muối Xứ Huế", "price": 39000, "img": "🧂", "desc": "Sự kết hợp hoàn hảo giữa vị mặn nhẹ của kem muối và đắng thơm cà phê"},
        {"id": "CF06", "name": "Cà Phê Dừa Bến Tre", "price": 42000, "img": "🥥", "desc": "Cà phê phin hòa quyện cùng cốt dừa đá xay thơm béo dẻo mịn"}
    ],
    "🌿 Trà Việt & Giải Nhiệt": [
        {"id": "TR01", "name": "Trà Sen Vàng Kem Khúc Bạch", "price": 45000, "img": "🍵", "desc": "Trà oolong thanh mát, hạt sen bùi bùi cùng củ năng giòn sần sật"},
        {"id": "TR02", "name": "Trà Đào Cam Sả Hà Thành", "price": 39000, "img": "🍑", "desc": "Đào miếng giòn ngọt, vị cam sả thơm nức giải nhiệt ngày thu"},
        {"id": "TR03", "name": "Trà Quất Mật Ong Rừng", "price": 32000, "img": "🍋", "desc": "Vị chua thanh mát lành của quất tươi và mật ong hoa rừng"}
    ],
    "🍰 Bánh Ngọt Đi Kèm": [
        {"id": "BN01", "name": "Bánh Bông Lan Trứng Muối", "price": 35000, "img": "🧁", "desc": "Sốt phô mai béo ngậy, chà bông và trứng muối đậm đà"},
        {"id": "BN02", "name": "Bánh Mì Chuối Nướng Thu Hà Nội", "price": 28000, "img": "🍌", "desc": "Thơm lừng mùi chuối chín và bơ Pháp, giòn rụm bên ngoài"},
        {"id": "BN03", "name": "Croissant Bơ Tỏi", "price": 32000, "img": "🥐", "desc": "Bánh sừng bò ngàn lớp thơm nức vị bơ tỏi lá thơm"}
    ]
}

# Sidebar điều hướng
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #8D6E63;'>🍂 AUTUMN COFFEE</h1>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center;'>Hương Vị Cà Phê Việt Nam Nguyên Bản</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    sidebar_menu = st.radio(
        "📌 Menu Chức Năng:",
        [
            "🛒 Gọi Món POS & Giỏ Hàng",
            "🎰 Vòng Quay May Mắn Autumn",
            "👤 Tích Điểm Khách Hàng",
            "📈 Báo Cáo Doanh Thu Real-Time"
        ]
    )

# Banner chính
st.markdown("""
    <div class="coffee-banner">
        <h1>🍂 AUTUMN COFFEE - VIETNAM SPECIALTY ☕</h1>
        <p>"Tách Cà Phê Mùa Thu - Đậm Đà Hương Vị Đất Việt"</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU 1: GỌI MÓN POS & GIỎ HÀNG
# ---------------------------------------------------------
if sidebar_menu == "🛒 Gọi Món POS & Giỏ Hàng":
    col_pos, col_cart = st.columns([1.7, 1.3])

    with col_pos:
        st.subheader("📋 Thực Đơn Cà Phê & Đồ Uống")
        
        tab1, tab2, tab3 = st.tabs(["☕ Cà Phê Phin Việt", "🌿 Trà Việt", "🍰 Bánh Ngọt"])
        
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
                        bean = st.selectbox("Hạt cà phê chọn thêm:", ["Robusta Đậm Đà (Buôn Ma Thuột)", "Arabica Thơm Thanh (Cầu Đất)", "Blend 70/30 Đắc Lắc"], key=f"b_{item['id']}")
                        topping = st.multiselect("Topping ngon kèm:", ["Kem Muối (+8k)", "Kem Trừng (+10k)", "Shot Espresso (+10k)", "Thạch Cà Phê (+5k)"], key=f"t_{item['id']}")
                        
                        qty = st.number_input("Số lượng:", min_value=1, value=1, step=1, key=f"q_{item['id']}")
                        
                        if st.button("🛒 Thêm Vào Giỏ Hàng", key=f"add_{item['id']}", type="primary", use_container_width=True):
                            topping_price = 0
                            if "Kem Muối (+8k)" in topping: topping_price += 8000
                            if "Kem Trừng (+10k)" in topping: topping_price += 10000
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
                            st.toast(f"Đã thêm {qty}x {item['name']} vào giỏ hàng!", icon="☕")

        with tab1:
            render_category(MENU_DATA["☕ Cà Phê Phin Việt"])
        with tab2:
            render_category(MENU_DATA["🌿 Trà Việt & Giải Nhiệt"])
        with tab3:
            render_category(MENU_DATA["🍰 Bánh Ngọt Đi Kèm"])

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
            st.info(f"👤 Khách hàng thân thiết | Điểm hiện có: **{pts} điểm** (Quy đổi: {pts*1000:,.0f}đ)")

        st.markdown("---")

        if not st.session_state.cart:
            st.warning("Giỏ hàng hiện tại đang trống. Vui lòng chọn món từ menu bên trái!")
            raw_total = 0
        else:
            raw_total = 0
            for idx, c_item in enumerate(st.session_state.cart):
                raw_total += c_item["total"]
                col_item1, col_item2 = st.columns([3, 1])
                with col_item1:
                    st.write(f"**{idx+1}. {c_item['name']}** x{c_item['qty']}")
                    st.caption(f"⚙️ {c_item['sugar']} | {c_item['ice']} | Topping: {c_item['topping']}")
                    st.write(f"💰 {c_item['total']:,.0f} VNĐ")
                with col_item2:
                    if st.button("❌", key=f"del_{idx}"):
                        st.session_state.cart.pop(idx)
                        st.rerun()
                st.markdown("---")

            discount_amount = st.session_state.applied_discount
            final_total = max(0, raw_total - discount_amount)

            st.write(f"• Tạm tính: **{raw_total:,.0f} VNĐ**")
            if discount_amount > 0:
                st.write(f"• Giảm giá Voucher / Vòng quay: <span style='color:green;'>- {discount_amount:,.0f} VNĐ</span>", unsafe_allow_html=True)
            st.markdown(f"### 💸 Tổng Thanh Toán: <span style='color:#D84315;'>{final_total:,.0f} VNĐ</span>", unsafe_allow_html=True)

            pay_method = st.radio("Phương thức thanh toán:", ["Tiền mặt 💵", "Chuyển khoản VietQR 📲", "Thẻ ngân hàng 💳"])

            if pay_method == "Chuyển khoản VietQR 📲":
                st.image("https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=AUTUMNCOFFEE_PAYMENT", caption="Quét mã VietQR để thanh toán")

            if st.button("✅ XÁC NHẬN THANH TOÁN & IN HÓA ĐƠN", type="primary", use_container_width=True):
                save_order_to_db(cust_phone, f"{order_type} ({table_num})", st.session_state.cart, raw_total, discount_amount, final_total, pay_method)
                st.balloons()
                st.success("🎉 Thanh toán thành công! Đơn hàng đã được lưu vào CSDL SQLite.")
                st.session_state.cart = []
                st.session_state.applied_discount = 0
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU 2: VÒNG QUAY MAY MẮN AUTUMN DAY
# ---------------------------------------------------------
elif sidebar_menu == "🎰 Vòng Quay May Mắn Autumn":
    st.subheader("🎰 Vòng Quay May Mắn Autumn Day - Trúng Thưởng 100%")
    st.caption("Mỗi hóa đơn tại Autumn Coffee đều nhận được 1 lượt quay trúng Voucher hấp dẫn!")

    prizes = [
        ("🎉 Voucher Giảm 10.000 VNĐ", 10000),
        ("🔥 Voucher Giảm 20.000 VNĐ", 20000),
        ("☕ Tặng 01 Shot Espresso Kem Muối", 10000),
        ("🍌 Tặng 01 Bánh Mì Chuối Nướng", 28000),
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
                st.info(f"Đã tự động áp dụng ưu đãi **-{st.session_state.won_val:,.0f} VNĐ** vào giỏ hàng POS của bạn!")

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
