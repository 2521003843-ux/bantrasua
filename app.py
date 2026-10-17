import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import random

# =========================================================
# 1. CẤU HÌNH TRANG (ĐẶT ĐẦU FILE BẮT BUỘC)
# =========================================================
st.set_page_config(
    page_title="COFFEE MINI - Super POS ☕ Pro",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. HÀM TƯƠNG THÍCH BẢO VỆ LỖI STREAMLIT
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

# Dùng tên Database mới để tránh vướng dữ liệu cũ
DB_FILE = "coffee_mini_pos_v3.db"

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

        # Khởi tạo kho mẫu
        c.execute("SELECT COUNT(*) FROM inventory")
        if c.fetchone()[0] == 0:
            sample_inv = [
                ("Hạt Cà Phê Robusta (Kg)", 15.0, "Kg", 3.0),
                ("Hạt Cà Phê Arabica (Kg)", 8.0, "Kg", 2.0),
                ("Sữa Đặc (Hộp 380g)", 50.0, "Hộp", 10.0),
                ("Sữa Tươi Thanh Trùng (Lít)", 30.0, "Lít", 5.0),
                ("Kem Béo Kem Muối (Lít)", 12.0, "Lít", 2.0),
                ("Trà Oolong (Kg)", 5.0, "Kg", 1.0),
                ("Đào Đóng Hộp (Hộp)", 20.0, "Hộp", 4.0),
                ("Ly Giấy Coffee Mini", 500.0, "Ly", 50.0)
            ]
            c.executemany("INSERT INTO inventory (item_name, quantity, unit, min_limit) VALUES (?, ?, ?, ?)", sample_inv)

        # Khởi tạo Voucher mẫu
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
                c.execute("INSERT INTO customers (phone, name, points) VALUES (?, 'Khách Hàng', ?)", (phone, earned_pts))

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
                return True, disc_val, f"Áp dụng thành công mã {code.upper()}: -{disc_val:,.0f} VNĐ!"
            else:
                return False, 0, f"Mã {code.upper()} yêu cầu đơn hàng tối thiểu {min_ord:,.0f} VNĐ!"
        else:
            return False, 0, "Mã giảm giá không hợp lệ!"
    except Exception:
        return False, 0, "Lỗi kiểm tra mã giảm giá!"

if "cart" not in st.session_state:
    st.session_state.cart = []
if "applied_discount" not in st.session_state:
    st.session_state.applied_discount = 0
if "discount_reason" not in st.session_state:
    st.session_state.discount_reason = ""
if "table_status" not in st.session_state:
    st.session_state.table_status = {f"Bàn {i:02d}": "Trống 🟢" for i in range(1, 11)}

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

with st.sidebar:
    st.title("☕ COFFEE MINI")
    st.caption("Góc Nhỏ Cà Phê & Niềm Vui Lớn")
    st.markdown("---")
    
    menu_choice = st.radio(
        "📌 Menu Chức Năng:",
        [
            "🛒 Gọi Món POS & Giỏ Hàng",
            "🪑 Sơ Đồ & Quản Lý Bàn",
            "📦 Quản Lý Kho Nguyên Liệu",
            "🎟️ Mã Giảm Giá & Voucher",
            "🎰 Vòng Quay May Mắn",
            "👤 Tích Điểm Khách Hàng",
            "📈 Báo Cáo & Phân Tích Doanh Thu"
        ]
    )

st.title("☕ COFFEE MINI - SUPER POS PRO")
st.caption("Hệ Thống Bán Hàng & Quản Lý Quán Cà Phê Thông Minh")
st.markdown("---")

if menu_choice == "🛒 Gọi Món POS & Giỏ Hàng":
    col_menu, col_cart = st.columns([1.6, 1.4])

    with col_menu:
        st.subheader("📋 Thực Đơn Món")
        tab1, tab2, tab3 = st.tabs(["☕ Cà Phê Mini", "🍵 Trà & Mát Lạnh", "🥐 Bánh Ngọt"])

        def show_items(item_list):
            cols = st.columns(2)
            for i, item in enumerate(item_list):
                with cols[i % 2]:
                    try:
                        st.image(item["img"])
                    except Exception:
                        pass
                    st.markdown(f"**{item['name']}**")
                    st.caption(item["desc"])
                    st.markdown(f"💰 **{item['price']:,.0f} VNĐ**")

                    with st.expander(f"➕ Chọn {item['name']}"):
                        sugar = st.select_slider("Mức Đường / Sữa:", ["0%", "30%", "50%", "100%"], value="50%", key=f"sug_{item['id']}")
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
                            safe_toast(f"Đã thêm {qty}x {item['name']}!")

        with tab1: show_items(MENU_DATA["☕ Cà Phê Chữ Ký"])
        with tab2: show_items(MENU_DATA["🍵 Trà & Đồ Uống Mát Lạnh"])
        with tab3: show_items(MENU_DATA["🥐 Bánh Ngọt Mini"])

    with col_cart:
        st.subheader("🛒 Giỏ Hàng & Thanh Toán")
        c1, c2 = st.columns(2)
        with c1: order_type = st.selectbox("Hình thức:", ["Tại bàn", "Mang đi"])
        with c2: 
            table_options = list(st.session_state.table_status.keys())
            table_num = st.selectbox("Chọn Bàn:", table_options)

        phone = st.text_input("📞 SĐT Khách Hàng (Tích Điểm):", placeholder="Nhập SĐT khách hàng...")
        if phone:
            p = get_pts(phone)
            st.info(f"👤 Điểm tích lũy: **{p} điểm** (Quy đổi: {p*1000:,.0f}đ)")

        st.markdown("---")
        c_v1, c_v2 = st.columns([2, 1])
        with c_v1:
            v_code_input = st.text_input("🏷️ Mã Khuyến Mãi / Voucher:", placeholder="Nhập MINI10, XINCHAO...")
        with c_v2:
            st.write("")
            if st.button("Áp Dụng Mã"):
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
                st.write(f"• Ưu đãi ({st.session_state.discount_reason}): **-{disc:,.0f} VNĐ**")
            st.markdown(f"### 💸 Tổng Thanh Toán: **{final_total:,.0f} VNĐ**")

            pay_method = st.radio("Phương thức thanh toán:", ["Tiền mặt 💵", "Chuyển khoản VietQR 📲", "Thẻ ngân hàng 💳"])

            if pay_method == "Chuyển khoản VietQR 📲":
                try:
                    st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=COFFEEMINI_POS_PAYMENT", caption="Mã QR Thanh Toán VietQR")
                except Exception:
                    st.warning("Không thể tải ảnh VietQR.")

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

elif menu_choice == "🪑 Sơ Đồ & Quản Lý Bàn":
    st.subheader("🪑 Sơ Đồ Bàn Thực Tế & Trạng Thái Sức Chứa")
    col_t1, col_t2 = st.columns([2, 1])

    with col_t1:
        st.markdown("### 📌 Trạng Thái Các Bàn")
        t_cols = st.columns(5)
        for idx, (t_name, t_stat) in enumerate(st.session_state.table_status.items()):
            with t_cols[idx % 5]:
                st.markdown(f"**{t_name}**")
                st.caption(t_stat)

    with col_t2:
        st.markdown("### ⚙️ Thao Tác Nhanh")
        sel_table = st.selectbox("Chọn Bàn Cần Thay Đổi:", list(st.session_state.table_status.keys()))
        new_stat = st.radio("Đổi Trạng Thái:", ["Trống 🟢", "Có Khách 🔴", "Đã Đặt 🟡"])
        if st.button("🔄 Cập Nhật Trạng Thái Bàn"):
            st.session_state.table_status[sel_table] = new_stat
            safe_toast(f"Đã đổi {sel_table} thành '{new_stat}'!")
            safe_rerun()

elif menu_choice == "📦 Quản Lý Kho Nguyên Liệu":
    st.subheader("📦 Quản Lý Tồn Kho Nguyên Liệu")
    df_inv = load_inventory()
    if df_inv.empty:
        st.info("Chưa có dữ liệu kho nguyên liệu.")
    else:
        low_stock = df_inv[df_inv["quantity"] <= df_inv["min_limit"]]
        if not low_stock.empty:
            st.error(f"🚨 CẢNH BÁO: Có {len(low_stock)} nguyên liệu cần nhập thêm ngay!")

        st.dataframe(df_inv)

        st.markdown("---")
        st.markdown("### ✏️ Cập Nhật Kho Nguyên Liệu")
        c_i1, c_i2, c_i3 = st.columns([2, 1, 1])
        with c_i1:
            item_to_update = st.selectbox("Chọn Nguyên Liệu:", df_inv["item_name"].tolist())
        with c_i2:
            row_item = df_inv[df_inv["item_name"] == item_to_update].iloc[0]
            new_qty_val = st.number_input("Số Lượng Mới:", min_value=0.0, value=float(row_item["quantity"]), step=1.0)
        with c_i3:
            st.write("")
            if st.button("💾 Lưu Kho"):
                if update_inventory_item(int(row_item["id"]), new_qty_val):
                    safe_toast("Đã cập nhật số lượng tồn kho!")
                    safe_rerun()

elif menu_choice == "🎟️ Mã Giảm Giá & Voucher":
    st.subheader("🎟️ Danh Sách Mã Giảm Giá Đang Hoạt Động")
    st.markdown("""
        • **MINI10**: Giảm `10,000 VNĐ` cho đơn từ `30,000 VNĐ`  
        • **MINI20**: Giảm `20,000 VNĐ` cho đơn từ `50,000 VNĐ`  
        • **XINCHAO**: Giảm `15,000 VNĐ` cho mọi đơn hàng  
        • **VIPCOFFEE**: Giảm `30,000 VNĐ` cho đơn từ `100,000 VNĐ`
    """)

elif menu_choice == "🎰 Vòng Quay May Mắn":
    st.subheader("🎰 Vòng Quay Trúng Thưởng Voucher 100%")
    prizes = [
        ("Voucher Giảm 10.000 VNĐ", 10000), 
        ("Voucher Giảm 15.000 VNĐ", 15000), 
        ("Tặng 01 Shot Kem Muối", 8000), 
        ("Chúc may mắn lần sau", 0)
    ]
    if st.button("🔄 THỰC HIỆN QUAY THƯỞNG"):
        p_name, p_val = random.choice(prizes)
        st.session_state.applied_discount = p_val
        st.session_state.discount_reason = f"Vòng quay ({p_name})"
        st.success(f"🎁 Bạn nhận được: **{p_name}**!")

elif menu_choice == "👤 Tích Điểm Khách Hàng":
    st.subheader("👤 Tra Cứu Điểm Tích Lũy Khách Hàng")
    s_phone = st.text_input("🔍 Nhập SĐT Khách Hàng:")
    if s_phone:
        pts = get_pts(s_phone)
        st.metric(f"Khách hàng ({s_phone})", f"{pts} Điểm")

else:
    st.subheader("📈 Báo Cáo Doanh Thu Bán Hàng")
    df_ord = load_orders()
    if df_ord.empty:
        st.warning("Chưa có dữ liệu đơn hàng nào được ghi nhận.")
    else:
        tot_revenue = df_ord["final_amount"].sum()
        st.metric("💰 Tổng Doanh Thu", f"{tot_revenue:,.0f} VNĐ")
        st.dataframe(df_ord)
