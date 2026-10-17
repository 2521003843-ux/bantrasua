import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import random
import streamlit.components.v1 as components

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
# 2. HÀM TƯƠNG THÍCH BẢO VỆ STREAMLIT
# =========================================================
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def safe_toast(msg):
    if hasattr(st, "toast"):
        st.toast(msg)
    else:
        st.success(msg)

DB_FILE = "coffee_mini_v4.db"

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
        c.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT UNIQUE,
                quantity REAL,
                unit TEXT,
                min_limit REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS vouchers (
                code TEXT PRIMARY KEY,
                discount_value REAL,
                min_order REAL
            )
        """)

        c.execute("SELECT COUNT(*) FROM inventory")
        if c.fetchone()[0] == 0:
            sample_inv = [
                ("Hạt Cà Phê Robusta Buôn Ma Thuột (Kg)", 18.0, "Kg", 4.0),
                ("Hạt Cà Phê Arabica Cầu Đất (Kg)", 10.0, "Kg", 2.5),
                ("Sữa Đặc Nhập Khẩu (Hộp)", 60.0, "Hộp", 12.0),
                ("Sữa Tươi Thanh Trùng (Lít)", 35.0, "Lít", 6.0),
                ("Kem Béo Kem Muối Mini (Lít)", 15.0, "Lít", 3.0),
                ("Trà Oolong Thượng Hạng (Kg)", 6.0, "Kg", 1.5),
                ("Ly Giấy Logo Coffee Mini (Cái)", 650.0, "Cái", 100.0)
            ]
            c.executemany("INSERT INTO inventory (item_name, quantity, unit, min_limit) VALUES (?, ?, ?, ?)", sample_inv)

        c.execute("SELECT COUNT(*) FROM vouchers")
        if c.fetchone()[0] == 0:
            sample_vouchers = [
                ("MINI10", 10000.0, 30000.0),
                ("MINI20", 20000.0, 50000.0),
                ("XINCHAO", 15000.0, 0.0),
                ("VIPCOFFEE", 30000.0, 100000.0)
            ]
            c.executemany("INSERT INTO vouchers (code, discount_value, min_order) VALUES (?, ?, ?)", sample_vouchers)

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Lỗi CSDL: {e}")

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
                c.execute("INSERT INTO customers (phone, name, points) VALUES (?, 'Khách Hàng Mini', ?)", (phone, earned_pts))

        total_qty = sum(it.get('qty', 1) for it in items)
        c.execute("UPDATE inventory SET quantity = MAX(0, quantity - ?) WHERE item_name LIKE '%Ly Giấy%'", (total_qty,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Lỗi lưu đơn hàng: {e}")
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
        df = pd.read_sql("SELECT id, order_time, customer_phone, order_type, total_amount, discount_amount, final_amount, payment_method FROM orders ORDER BY id DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def load_inventory():
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        df = pd.read_sql("SELECT * FROM inventory", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def update_inventory_item(item_id, new_qty):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()
        c.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, item_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def check_voucher(code, order_total):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()
        c.execute("SELECT discount_value, min_order FROM vouchers WHERE code = ?", (code.strip().upper(),))
        row = c.fetchone()
        conn.close()
        if row:
            disc_val, min_ord = row
            if order_total >= min_ord:
                return True, disc_val, f"Đã áp dụng mã {code.upper()}: -{disc_val:,.0f} VNĐ!"
            else:
                return False, 0, f"Mã {code.upper()} cần đơn tối thiểu {min_ord:,.0f} VNĐ!"
        else:
            return False, 0, "Mã không hợp lệ!"
    except Exception:
        return False, 0, "Lỗi voucher!"

# Session states
if "cart" not in st.session_state:
    st.session_state.cart = []
if "applied_discount" not in st.session_state:
    st.session_state.applied_discount = 0
if "discount_reason" not in st.session_state:
    st.session_state.discount_reason = ""
if "table_status" not in st.session_state:
    st.session_state.table_status = {f"Bàn {i:02d}": "Trống 🟢" for i in range(1, 11)}

# =========================================================
# 3. CSS TRANG TRÍ CAO CẤP DÀNH CHO COFFEE MINI ☕🎨
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: #FAF6F0;
    }

    /* HEADER HERO BANNER */
    .hero-header {
        background: linear-gradient(135deg, #2E1F18 0%, #4A3326 40%, #7A5230 100%);
        border-radius: 24px;
        padding: 35px 30px;
        color: #FFF9F2;
        box-shadow: 0 15px 35px rgba(46, 31, 24, 0.25);
        border: 2px solid #E6BA85;
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
    }

    .hero-header h1 {
        font-weight: 800 !important;
        font-size: 2.8rem !important;
        color: #FCE3C1 !important;
        letter-spacing: 1.5px;
        margin-bottom: 8px !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.4);
    }

    .hero-header p {
        font-size: 1.15rem;
        color: #E8D3C0;
        margin: 0;
        font-weight: 500;
    }

    .hero-badge {
        display: inline-block;
        background: #D97706;
        color: #FFFFFF;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 50px;
        font-size: 0.82rem;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* PRODUCT CARD STYLING */
    .item-card {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 16px;
        border: 1px solid #EAE0D5;
        box-shadow: 0 6px 18px rgba(74, 51, 38, 0.05);
        transition: all 0.3s ease;
        text-align: center;
        margin-bottom: 18px;
    }

    .item-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 28px rgba(74, 51, 38, 0.12);
        border-color: #D97706;
    }

    .item-title {
        color: #2E1F18;
        font-weight: 700;
        font-size: 1.1rem;
        margin-top: 10px;
        margin-bottom: 4px;
    }

    .item-desc {
        color: #786C62;
        font-size: 0.83rem;
        min-height: 38px;
        line-height: 1.35;
        margin-bottom: 10px;
    }

    .item-price {
        color: #B91C1C;
        font-size: 1.25rem;
        font-weight: 800;
        background: #FEF2F2;
        padding: 4px 12px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 8px;
    }

    /* CART POS PANEL */
    .cart-box {
        background: #FFFFFF;
        border-radius: 24px;
        padding: 22px;
        border-top: 6px solid #4A3326;
        box-shadow: 0 8px 30px rgba(0,0,0,0.06);
    }

    /* SIDEBAR CUSTOM STYLING */
    [data-testid="stSidebar"] {
        background-color: #251812 !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #F5EBE1 !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        padding: 10px 14px;
        border-radius: 12px;
        margin-bottom: 4px;
        transition: all 0.2s;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(217, 119, 6, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Menu data
MENU_DATA = {
    "☕ Cà Phê Chữ Ký": [
        {"id": "CM01", "name": "Cà Phê Sữa Đá Phin Mini", "price": 29000, "img": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=400", "desc": "Robusta Buôn Ma Thuột đậm đà, vị đắng thơm lừng quyện sữa đặc."},
        {"id": "CM02", "name": "Cà Phê Muối Kem Béo Mini", "price": 35000, "img": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400", "desc": "Lớp kem muối mặn béo ngậy kết hợp cà phê phin nguyên chất."},
        {"id": "CM03", "name": "Bạc Xỉu Sài Gòn", "price": 32000, "img": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=400", "desc": "Nhiều sữa ngọt thơm thanh mát, đắng nhẹ vị cà phê."},
        {"id": "CM04", "name": "Cà Phê Trứng Béo Mịn", "price": 39000, "img": "https://images.unsplash.com/photo-1541167760496-1628856ab772?w=400", "desc": "Kem trứng gà đánh bông béo ngậy phủ trên cà phê phin nóng."}
    ],
    "🍵 Trà & Mát Lạnh": [
        {"id": "TR01", "name": "Trà Đào Cam Sả Tươi", "price": 35000, "img": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400", "desc": "Đào miếng giòn rụm, hương thơm đượm sả tươi mát dịu."},
        {"id": "TR02", "name": "Trà Sen Vàng Hạt Sen", "price": 39000, "img": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400", "desc": "Trà Oolong thanh khiết, hạt sen bùi ngọt và kem mặn béo."}
    ],
    "🥐 Bánh Ngọt Mini": [
        {"id": "BN01", "name": "Bánh Mì Chuối Nướng Bơ", "price": 25000, "img": "https://images.unsplash.com/photo-1603532648955-039310d9ed75?w=400", "desc": "Bánh mì chuối nướng mềm xốp thơm lừng vị bơ Pháp."},
        {"id": "BN02", "name": "Croissant Bơ Tỏi Nóng Giòn", "price": 28000, "img": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400", "desc": "Bánh sừng bò ngàn lớp nướng giòn tan thơm bơ tỏi."}
    ]
}

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #FCE3C1; font-weight:800;'>☕ COFFEE MINI</h1>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center; color: #D1C2B4;'>Cà Phê Nhỏ - Niềm Vui Lớn 🌿</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu_choice = st.radio(
        "📌 Menu Chức Năng:",
        [
            "🛒 Gọi Món POS & Giỏ Hàng",
            "🎰 Vòng Quay Tròn May Mắn",
            "🪑 Sơ Đồ & Quản Lý Bàn",
            "📦 Quản Lý Kho Nguyên Liệu",
            "🎟️ Mã Giảm Giá & Voucher",
            "👤 Tích Điểm Khách Hàng",
            "📈 Báo Cáo & Doanh Thu"
        ]
    )

# Hero Header
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">✨ PREMIUM MINI COFFEE POS</div>
    <h1>☕ COFFEE MINI - SMALL SIZE, BIG SMILE</h1>
    <p>"Hương vị cà phê phin nguyên bản trong không gian hiện đại, tinh tế"</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU 1: GỌI MÓN POS
# ---------------------------------------------------------
if menu_choice == "🛒 Gọi Món POS & Giỏ Hàng":
    col_menu, col_cart = st.columns([1.6, 1.4])

    with col_menu:
        st.subheader("📋 Danh Sách Món & Custom Đồ Uống")
        tab1, tab2, tab3 = st.tabs(["☕ Cà Phê Chữ Ký", "🍵 Trà & Mát Lạnh", "🥐 Bánh Ngọt Mini"])

        def show_items(item_list):
            cols = st.columns(2)
            for i, item in enumerate(item_list):
                with cols[i % 2]:
                    st.markdown(f"""
                        <div class="item-card">
                            <img src="{item['img']}" style="width:100%; height:130px; object-fit:cover; border-radius:14px;">
                            <div class="item-title">{item['name']}</div>
                            <div class="item-desc">{item['desc']}</div>
                            <div class="item-price">{item['price']:,.0f} VNĐ</div>
                        </div>
                    """, unsafe_allow_html=True)

                    with st.expander(f"➕ Custom & Thêm ({item['name']})"):
                        sugar = st.select_slider("Mức Đường/Sữa:", ["0%", "30%", "50%", "100%"], value="50%", key=f"sug_{item['id']}")
                        ice = st.select_slider("Mức Đá:", ["Không đá", "Ít đá", "Vừa", "Nhiều đá"], value="Vừa", key=f"ice_{item['id']}")
                        topping = st.multiselect("Topping:", ["Kem Muối (+8k)", "Kem Trứng (+10k)", "Shot Espresso (+10k)"], key=f"top_{item['id']}")
                        qty = st.number_input("Số lượng:", min_value=1, value=1, key=f"qty_{item['id']}")

                        if st.button("🛒 Thêm Vào Giỏ", key=f"btn_add_{item['id']}"):
                            add_price = 0
                            if "Kem Muối (+8k)" in topping: add_price += 8000
                            if "Kem Trứng (+10k)" in topping: add_price += 10000
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
                            safe_toast(f"Đã thêm {qty}x {item['name']} vào giỏ!")

        with tab1: show_items(MENU_DATA["☕ Cà Phê Chữ Ký"])
        with tab2: show_items(MENU_DATA["🍵 Trà & Mát Lạnh"])
        with tab3: show_items(MENU_DATA["🥐 Bánh Ngọt Mini"])

    with col_cart:
        st.markdown('<div class="cart-box">', unsafe_allow_html=True)
        st.subheader("🛒 Hóa Đơn & Giỏ Hàng POS")
        
        c1, c2 = st.columns(2)
        with c1: order_type = st.selectbox("Hình thức:", ["Tại bàn", "Mang đi"])
        with c2: 
            table_options = list(st.session_state.table_status.keys())
            table_num = st.selectbox("Chọn Bàn:", table_options)

        phone = st.text_input("📞 SĐT Khách Tích Điểm:", placeholder="Nhập số điện thoại khách...")
        if phone:
            p = get_pts(phone)
            st.info(f"👤 Khách Hàng | Điểm tích lũy: **{p} điểm** (Quy đổi: {p*1000:,.0f}đ)")

        st.markdown("---")
        c_v1, c_v2 = st.columns([2, 1])
        with c_v1:
            v_code_input = st.text_input("🏷️ Mã Khuyến Mãi / Voucher:", placeholder="Nhập MINI10, XINCHAO...")
        with c_v2:
            st.write("")
            if st.button("Áp Dụng"):
                raw_sum = sum(ci["total"] for ci in st.session_state.cart)
                valid, d_val, msg = check_voucher(v_code_input, raw_sum)
                if valid:
                    st.session_state.applied_discount = d_val
                    st.session_state.discount_reason = f"Voucher {v_code_input.upper()}"
                    st.success(msg)
                else:
                    st.error(msg)

        st.markdown("---")

        if not st.session_state.cart:
            st.warning("Giỏ hàng đang trống. Hãy chọn món bên trái!")
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
                st.write(f"• Giảm giá ({st.session_state.discount_reason}): <span style='color:green;'>-{disc:,.0f} VNĐ</span>", unsafe_allow_html=True)
            st.markdown(f"### 💸 Tổng Thanh Toán: <span style='color:#B91C1C; font-weight:800;'>{final_total:,.0f} VNĐ</span>", unsafe_allow_html=True)

            pay_method = st.radio("Phương thức thanh toán:", ["Tiền mặt 💵", "Chuyển khoản VietQR 📲", "Thẻ ngân hàng 💳"])

            if pay_method == "Chuyển khoản VietQR 📲":
                st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=COFFEEMINI_POS_PAYMENT", caption="Quét mã VietQR thanh toán")

            if st.button("✅ HOÀN TẤT THANH TOÁN & IN HÓA ĐƠN"):
                if save_order(phone, f"{order_type} ({table_num})", st.session_state.cart, raw_total, disc, final_total, pay_method):
                    if order_type == "Tại bàn":
                        st.session_state.table_status[table_num] = "Có Khách 🔴"

                    if hasattr(st, "balloons"):
                        st.balloons()
                    st.success("🎉 Thanh toán thành công!")
                    st.session_state.cart = []
                    st.session_state.applied_discount = 0
                    st.session_state.discount_reason = ""
                    safe_rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# MENU 2: VÒNG QUAY TRÒN MAY MẮN (CANVAS / INTERACTIVE JS)
# ---------------------------------------------------------
elif menu_choice == "🎰 Vòng Quay Tròn May Mắn":
    st.subheader("🎰 Vòng Quay Tròn Trúng Thưởng Interactive 100%")
    st.caption("Hãy xoay vòng quay bên dưới để nhận các phần quà & Voucher hấp dẫn áp dụng ngay vào đơn hàng!")

    wheel_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; text-align: center; background: transparent; margin: 0; }
        .wheel-container { position: relative; width: 340px; height: 340px; margin: 10px auto; }
        #canvas { border-radius: 50%; box-shadow: 0 10px 25px rgba(0,0,0,0.2); border: 8px solid #4A3326; }
        .pointer {
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 16px solid transparent;
            border-right: 16px solid transparent;
            border-top: 32px solid #B91C1C;
            z-index: 10;
        }
        .spin-btn {
            background: linear-gradient(135deg, #D97706, #B45309);
            color: white;
            font-weight: bold;
            font-size: 1.1rem;
            padding: 12px 35px;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 6px 15px rgba(217,119,6,0.4);
            margin-top: 15px;
            transition: transform 0.2s;
        }
        .spin-btn:active { transform: scale(0.95); }
        #result-text { font-size: 1.25rem; font-weight: bold; color: #2E1F18; margin-top: 15px; min-height: 30px; }
    </style>
    </head>
    <body>

    <div class="wheel-container">
        <div class="pointer"></div>
        <canvas id="canvas" width="340" height="340"></canvas>
    </div>

    <button class="spin-btn" onclick="spinWheel()">🔄 QUAY NGAY</button>
    <div id="result-text">👉 Nhấp "QUAY NGAY" để thử vận may!</div>

    <script>
        const canvas = document.getElementById("canvas");
        const ctx = canvas.getContext("2d");

        const segments = [
            { label: "Giảm 10k", color: "#FBBF24" },
            { label: "Giảm 15k", color: "#F59E0B" },
            { label: "Trứng Kem", color: "#D97706" },
            { label: "Giảm 20k", color: "#B45309" },
            { label: "Kem Muối", color: "#78350F" },
            { label: "May Mắn", color: "#92400E" }
        ];

        const numSegments = segments.length;
        const arc = (2 * Math.PI) / numSegments;
        let startAngle = 0;
        let isSpinning = false;

        function drawWheel() {
            const radius = canvas.width / 2;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            for (let i = 0; i < numSegments; i++) {
                const angle = startAngle + i * arc;
                ctx.beginPath();
                ctx.fillStyle = segments[i].color;
                ctx.moveTo(radius, radius);
                ctx.arc(radius, radius, radius, angle, angle + arc);
                ctx.lineTo(radius, radius);
                ctx.fill();

                ctx.save();
                ctx.translate(radius, radius);
                ctx.rotate(angle + arc / 2);
                ctx.textAlign = "right";
                ctx.fillStyle = "#FFFFFF";
                ctx.font = "bold 15px 'Plus Jakarta Sans', sans-serif";
                ctx.fillText(segments[i].label, radius - 20, 5);
                ctx.restore();
            }

            ctx.beginPath();
            ctx.arc(radius, radius, 30, 0, 2 * Math.PI);
            ctx.fillStyle = "#FFF9F2";
            ctx.fill();
            ctx.lineWidth = 4;
            ctx.strokeStyle = "#4A3326";
            ctx.stroke();
        }

        drawWheel();

        function spinWheel() {
            if (isSpinning) return;
            isSpinning = true;
            document.getElementById("result-text").innerHTML = "⏳ Đang xoay vòng quay...";

            let spinAngleStart = Math.random() * 10 + 20;
            let spinTime = 0;
            let spinTimeTotal = Math.random() * 3000 + 4000;

            function rotateWheel() {
                spinTime += 30;
                if (spinTime >= spinTimeTotal) {
                    stopRotateWheel();
                    return;
                }
                const spinAngle = spinAngleStart - easeOut(spinTime, 0, spinAngleStart, spinTimeTotal);
                startAngle += (spinAngle * Math.PI) / 180;
                drawWheel();
                requestAnimationFrame(rotateWheel);
            }

            rotateWheel();
        }

        function stopRotateWheel() {
            isSpinning = false;
            const degrees = (startAngle * 180) / Math.PI + 90;
            const arcd = (arc * 180) / Math.PI;
            const index = Math.floor((360 - (degrees % 360)) / arcd) % numSegments;
            const wonLabel = segments[index].label;
            document.getElementById("result-text").innerHTML = "🎉 Chúc mừng bạn trúng: <span style='color:#B91C1C;'>" + wonLabel + "</span>!";
        }

        function easeOut(t, b, c, d) {
            const ts = (t /= d) * t;
            const tc = ts * t;
            return b + c * (tc + -3 * ts + 3 * t);
        }
    </script>

    </body>
    </html>
    """

    components.html(wheel_html, height=500)

    st.markdown("---")
    st.write("💡 **Áp dụng ưu đãi nhanh vào giỏ hàng:**")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        if st.button("🎁 Áp Dụng Voucher Giảm 10.000 VNĐ"):
            st.session_state.applied_discount = 10000
            st.session_state.discount_reason = "Vòng Quay (Giảm 10k)"
            st.success("Đã áp dụng Voucher 10k vào giỏ hàng!")
    with col_v2:
        if st.button("🔥 Áp Dụng Voucher Giảm 20.000 VNĐ"):
            st.session_state.applied_discount = 20000
            st.session_state.discount_reason = "Vòng Quay (Giảm 20k)"
            st.success("Đã áp dụng Voucher 20k vào giỏ hàng!")

# ---------------------------------------------------------
# MENU 3: SƠ ĐỒ BÀN
# ---------------------------------------------------------
elif menu_choice == "🪑 Sơ Đồ & Quản Lý Bàn":
    st.subheader("🪑 Sơ Đồ Bàn Thực Tế Quán COFFEE MINI")
    col_t1, col_t2 = st.columns([2, 1])

    with col_t1:
        st.markdown("### 📌 Trạng Thái Bàn Phục Vụ")
        t_cols = st.columns(5)
        for idx, (t_name, t_stat) in enumerate(st.session_state.table_status.items()):
            with t_cols[idx % 5]:
                st.markdown(f"**{t_name}**")
                st.caption(t_stat)

    with col_t2:
        st.markdown("### ⚙️ Cập Nhật Trạng Thái Bàn")
        sel_table = st.selectbox("Chọn Bàn:", list(st.session_state.table_status.keys()))
        new_stat = st.radio("Trạng Thái Mới:", ["Trống 🟢", "Có Khách 🔴", "Đã Đặt 🟡"])
        if st.button("🔄 Cập Nhật Bàn"):
            st.session_state.table_status[sel_table] = new_stat
            safe_toast(f"Đã đổi {sel_table} thành '{new_stat}'!")
            safe_rerun()

# ---------------------------------------------------------
# MENU 4: KHO NGUYÊN LIỆU
# ---------------------------------------------------------
elif menu_choice == "📦 Quản Lý Kho Nguyên Liệu":
    st.subheader("📦 Quản Lý Kho Nguyên Liệu Phin Việt")
    df_inv = load_inventory()
    if df_inv.empty:
        st.info("Chưa có dữ liệu kho.")
    else:
        low_stock = df_inv[df_inv["quantity"] <= df_inv["min_limit"]]
        if not low_stock.empty:
            st.error(f"🚨 CẢNH BÁO: Có {len(low_stock)} nguyên liệu cần nhập kho thêm!")

        st.dataframe(df_inv)

        st.markdown("---")
        c_i1, c_i2, c_i3 = st.columns([2, 1, 1])
        with c_i1:
            item_to_update = st.selectbox("Chọn Nguyên Liệu:", df_inv["item_name"].tolist())
        with c_i2:
            row_item = df_inv[df_inv["item_name"] == item_to_update].iloc[0]
            new_qty_val = st.number_input("Số Lượng Tồn Mới:", min_value=0.0, value=float(row_item["quantity"]), step=1.0)
        with c_i3:
            st.write("")
            if st.button("💾 Cập Nhật Kho"):
                if update_inventory_item(int(row_item["id"]), new_qty_val):
                    safe_toast("Đã cập nhật tồn kho!")
                    safe_rerun()

# ---------------------------------------------------------
# MENU 5: VOUCHER
# ---------------------------------------------------------
elif menu_choice == "🎟️ Mã Giảm Giá & Voucher":
    st.subheader("🎟️ Danh Sách Voucher Khuyến Mãi")
    st.markdown("""
        • **MINI10**: Giảm `10,000 VNĐ` cho đơn từ `30,000 VNĐ`  
        • **MINI20**: Giảm `20,000 VNĐ` cho đơn từ `50,000 VNĐ`  
        • **XINCHAO**: Giảm `15,000 VNĐ` cho mọi đơn hàng  
        • **VIPCOFFEE**: Giảm `30,000 VNĐ` cho đơn từ `100,000 VNĐ`
    """)

# ---------------------------------------------------------
# MENU 6: TÍCH ĐIỂM
# ---------------------------------------------------------
elif menu_choice == "👤 Tích Điểm Khách Hàng":
    st.subheader("👤 Tra Cứu Điểm Tích Lũy")
    s_phone = st.text_input("🔍 Nhập SĐT Khách Hàng:")
    if s_phone:
        pts = get_pts(s_phone)
        st.metric(f"Khách hàng ({s_phone})", f"{pts} Điểm")

# ---------------------------------------------------------
# MENU 7: BÁO CÁO DOANH THU
# ---------------------------------------------------------
else:
    st.subheader("📈 Báo Cáo Doanh Thu Bán Hàng")
    df_ord = load_orders()
    if df_ord.empty:
        st.warning("Chưa có đơn hàng nào.")
    else:
        tot_revenue = df_ord["final_amount"].sum()
        st.metric("💰 Tổng Doanh Thu", f"{tot_revenue:,.0f} VNĐ")
        st.dataframe(df_ord)
