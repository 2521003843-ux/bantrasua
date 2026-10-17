import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import random

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG (ĐẶT ĐẦU FILE BẮT BUỘC)
# ---------------------------------------------------------
st.set_page_config(
    page_title="COFFEE MINI ☕",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. HÀM TƯƠNG THÍCH VÀ XỬ LÝ CSDL
# ---------------------------------------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

DB_FILE = "coffee_mini_pos_clean.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
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
        st.error(f"Lỗi khởi tạo CSDL: {e}")

init_db()

def save_order(phone, order_type, items, total, discount, final, pay_method):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        items_str = json.dumps(items, ensure_ascii=False)
        c.execute("""
            INSERT INTO orders (order_time, customer_phone, order_type, items_json, total_amount, discount_amount, final_amount, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now_str, phone, order_type, items_str, total, discount, final, pay_method))
        
        if phone:
            earned_pts = int(final // 10000)
            c.execute("SELECT points FROM customers WHERE phone = ?", (phone,))
            row = c.fetchone()
            if row:
                c.execute("UPDATE customers SET points = points + ? WHERE phone = ?", (earned_pts, phone))
            else:
                c.execute("INSERT INTO customers (phone, name, points) VALUES (?, 'Khách hàng', ?)", (phone, earned_pts))
                
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi lưu đơn: {e}")
        return False

def get_pts(phone):
    if not phone: return 0
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()
        c.execute("SELECT points FROM customers WHERE phone = ?", (phone,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0

def load_orders():
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        df = pd.read_sql("SELECT id, order_time, customer_phone, order_type, final_amount, payment_method FROM orders ORDER BY id DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# 3. SESSION STATE
# ---------------------------------------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []
if "applied_discount" not in st.session_state:
    st.session_state.applied_discount = 0

# ---------------------------------------------------------
# 4. DANH MỤC THỰC ĐƠN
# ---------------------------------------------------------
MENU_DATA = {
    "☕ Cà Phê Chữ Ký": [
        {"id": "CM01", "name": "Cà Phê Sữa Đá Phin Mini", "price": 29000, "img": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=400", "desc": "Robusta Buôn Ma Thuột đậm đà, vị đắng thơm lừng quyện sữa đặc."},
        {"id": "CM02", "name": "Cà Phê Muối Kem Béo Mini", "price": 35000, "img": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400", "desc": "Lớp kem muối mặn béo ngậy kết hợp cà phê phin nguyên chất."},
        {"id": "CM03", "name": "Bạc Xỉu Sài Gòn", "price": 32000, "img": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=400", "desc": "Nhiều sữa ngọt thơm thanh mát, đắng nhẹ vị cà phê."},
        {"id": "CM04", "name": "Cà Phê Trứng Béo Mịn", "price": 39000, "img": "https://images.unsplash.com/photo-1541167760496-1628856ab772?w=400", "desc": "Kem trứng gà đánh bông béo ngậy phủ trên cà phê phin nóng."}
    ],
    "🍵 Trà & Đồ Uống Mát Lạnh": [
        {"id": "TR01", "name": "Trà Đào Cam Sả Tươi", "price": 35000, "img": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400", "desc": "Đào miếng giòn rụm, hương thơm đượm sả tươi mát dịu."},
        {"id": "TR02", "name": "Trà Sen Vàng Hạt Sen", "price": 39000, "img": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400", "desc": "Trà Oolong thanh khiết, hạt sen bùi ngọt và kem mặn béo."}
    ],
    "🥐 Bánh Ngọt Mini": [
        {"id": "BN01", "name": "Bánh Mì Chuối Nướng Bơ", "price": 25000, "img": "https://images.unsplash.com/photo-1603532648955-039310d9ed75?w=400", "desc": "Bánh mì chuối nướng mềm xốp thơm lừng vị bơ Pháp."},
        {"id": "BN02", "name": "Croissant Bơ Tỏi Nóng Giòn", "price": 28000, "img": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400", "desc": "Bánh sừng bò ngàn lớp nướng giòn tan thơm bơ tỏi."}
    ]
}

# ---------------------------------------------------------
# 5. GIAO DIỆN CHÍNH
# ---------------------------------------------------------
with st.sidebar:
    st.title("☕ COFFEE MINI")
    st.caption("Góc Nhỏ Cà Phê & Niềm Vui Lớn")
    st.markdown("---")
    menu_choice = st.radio("📌 Điều Hướng Chức Năng:", ["🛒 Gọi Món POS", "🎰 Vòng Quay May Mắn", "👤 Tích Điểm Khách Hàng", "📈 Báo Cáo Doanh Thu"])

st.markdown("# ☕ COFFEE MINI - SMALL SIZE, BIG SMILE")
st.caption("Ứng dụng quản lý bán hàng POS tối giản & hiệu quả")
st.markdown("---")

if menu_choice == "🛒 Gọi Món POS":
    col_menu, col_cart = st.columns([1.6, 1.4])

    with col_menu:
        st.subheader("📋 Danh Sách Món")
        tab1, tab2, tab3 = st.tabs(["☕ Cà Phê Mini", "🍵 Trà & Mát Lạnh", "🥐 Bánh Ngọt"])

        def show_items(item_list):
            cols = st.columns(2)
            for i, item in enumerate(item_list):
                with cols[i % 2]:
                    st.image(item["img"], use_container_width=True)
                    st.markdown(f"**{item['name']}**")
                    st.caption(item["desc"])
                    st.markdown(f"💰 <span style='color:red; font-weight:bold;'>{item['price']:,.0f} VNĐ</span>", unsafe_allow_html=True)

                    with st.expander(f"➕ Thêm {item['name']}"):
                        sugar = st.select_slider("Đường / Sữa:", ["0%", "30%", "50%", "100%"], value="50%", key=f"sugar_{item['id']}")
                        ice = st.select_slider("Đá:", ["Không đá", "Ít đá", "Vừa", "Nhiều đá"], value="Vừa", key=f"ice_{item['id']}")
                        topping = st.multiselect("Topping:", ["Kem Muối (+8k)", "Kem Trừng (+10k)", "Shot Espresso (+10k)"], key=f"top_{item['id']}")
                        qty = st.number_input("Số lượng:", min_value=1, value=1, key=f"qty_{item['id']}")

                        if st.button("🛒 Thêm Vào Giỏ", key=f"btn_add_{item['id']}", type="primary", use_container_width=True):
                            add_price = 0
                            if "Kem Muối (+8k)" in topping: add_price += 8000
                            if "Kem Trừng (+10k)" in topping: add_price += 10000
                            if "Shot Espresso (+10k)" in topping: add_price += 10000

                            cart_item = {
                                "id": item["id"],
                                "name": item["name"],
                                "unit_price": item["price"] + add_price,
                                "qty": qty,
                                "sugar": sugar,
                                "ice": ice,
                                "topping": ", ".join(topping) if topping else "Không",
                                "total": (item["price"] + add_price) * qty
                            }
                            st.session_state.cart.append(cart_item)
                            st.success(f"Đã thêm {qty}x {item['name']}!")

        with tab1: show_items(MENU_DATA["☕ Cà Phê Chữ Ký"])
        with tab2: show_items(MENU_DATA["🍵 Trà & Đồ Uống Mát Lạnh"])
        with tab3: show_items(MENU_DATA["🥐 Bánh Ngọt Mini"])

    with col_cart:
        st.subheader("🛒 Giỏ Hàng & Thanh Toán")
        c1, c2 = st.columns(2)
        with c1: order_type = st.selectbox("Hình thức:", ["Tại bàn", "Mang đi"])
        with c2: table_num = st.text_input("Bàn/Số phòng:", value="Bàn 01")

        phone = st.text_input("📞 SĐT Tích Điểm Khách Hàng:", placeholder="Nhập SĐT...")
        if phone:
            p = get_pts(phone)
            st.info(f"👤 Điểm tích lũy: **{p} điểm** (Quy đổi: {p*1000:,.0f}đ)")

        st.markdown("---")

        if not st.session_state.cart:
            st.warning("Giỏ hàng đang trống.")
            raw_total = 0
        else:
            raw_total = 0
            remove_idx = None
            for idx, c_item in enumerate(st.session_state.cart):
                raw_total += c_item["total"]
                col_i1, col_i2 = st.columns([3, 1])
                with col_i1:
                    st.write(f"**{idx+1}. {c_item['name']}** x{c_item['qty']}")
                    st.caption(f"⚙️ Đường: {c_item['sugar']} | Đá: {c_item['ice']} | Topping: {c_item['topping']}")
                    st.write(f"💰 {c_item['total']:,.0f} VNĐ")
                with col_i2:
                    if st.button("❌", key=f"del_{idx}_{c_item['id']}"):
                        remove_idx = idx
                st.markdown("---")

            if remove_idx is not None:
                st.session_state.cart.pop(remove_idx)
                safe_rerun()

            disc = st.session_state.applied_discount
            final_total = max(0, raw_total - disc)

            st.write(f"• Tạm tính: **{raw_total:,.0f} VNĐ**")
            if disc > 0:
                st.write(f"• Giảm giá: **-{disc:,.0f} VNĐ**")
            st.markdown(f"### 💸 Tổng Cần Thanh Toán: <span style='color:red;'>{final_total:,.0f} VNĐ</span>", unsafe_allow_html=True)

            pay_method = st.radio("Phương thức thanh toán:", ["Tiền mặt 💵", "Chuyển khoản VietQR 📲", "Thẻ 💳"])

            if pay_method == "Chuyển khoản VietQR 📲":
                st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=COFFEEMINI", caption="Mã QR Thanh Toán VietQR")

            if st.button("✅ HOÀN TẤT THANH TOÁN", type="primary", use_container_width=True):
                if save_order(phone, f"{order_type} ({table_num})", st.session_state.cart, raw_total, disc, final_total, pay_method):
                    st.balloons()
                    st.success("🎉 Thanh toán thành công!")
                    st.session_state.cart = []
                    st.session_state.applied_discount = 0
                    safe_rerun()

elif menu_choice == "🎰 Vòng Quay May Mắn":
    st.subheader("🎰 Vòng Quay Trúng Thưởng Voucher 100%")
    prizes = [("Giảm 10.000 VNĐ", 10000), ("Giảm 15.000 VNĐ", 15000), ("Tặng Shot Kem Muối", 8000), ("Chúc may mắn lần sau", 0)]
    if st.button("🔄 THỬ VẬN MAY", type="primary"):
        p, v = random.choice(prizes)
        st.session_state.applied_discount = v
        st.success(f"🎁 Bạn trúng: **{p}**! Đã áp dụng giảm giá vào giỏ hàng.")

elif menu_choice == "👤 Tích Điểm Khách Hàng":
    st.subheader("👤 Tra Cứu Điểm Tích Lũy")
    s_phone = st.text_input("Nhập SĐT Khách Hàng:")
    if s_phone:
        pts = get_pts(s_phone)
        st.metric(f"Khách hàng {s_phone}", f"{pts} Điểm")

else:
    st.subheader("📈 Báo Cáo Doanh Thu Bán Hàng")
    df = load_orders()
    if df.empty:
        st.warning("Chưa có dữ liệu đơn hàng.")
    else:
        st.metric("💰 Tổng Doanh Thu", f"{df['final_amount'].sum():,.0f} VNĐ")
        st.dataframe(df, use_container_width=True)
