import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG (Phải đặt ở dòng lệnh Streamlit đầu tiên)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Starbucks Tea & Coffee Lounge",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. TÙY CHỈNH GIAO DIỆN HỆ THỐNG (STARBUCKS GREEN THEME)
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* Màu chủ đạo Starbucks Emerald Green & Warm Cream */
    :root {
        --sb-green: #006241;
        --sb-dark-green: #1E3932;
        --sb-accent-gold: #CBA258;
        --sb-bg-cream: #F2F0EB;
    }
    
    .main {
        background-color: #FAFAFA;
    }
    
    .stAppHeader {
        background-color: var(--sb-dark-green);
    }
    
    /* Header tùy chỉnh */
    .sb-header {
        background: linear-gradient(135deg, #1E3932 0%, #006241 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .sb-header h1 {
        color: #FFFFFF !important;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .sb-header p {
        color: #D4E9E2;
        font-size: 1.1rem;
        margin: 0;
    }

    /* Thẻ Container Hóa Đơn */
    .sb-bill-box {
        background-color: #FFFFFF;
        border: 2px dashed var(--sb-green);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    /* Highlight giá tiền */
    .price-highlight {
        color: var(--sb-green);
        font-size: 1.5rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. DỮ LIỆU SAN PHẨM & CẤU HÌNH MENU STARBUCKS
# ---------------------------------------------------------
MENU_CATEGORIES = {
    "🍵 Trà Sữa & Tea Latte": {
        "Starbucks Black Tea Latte": 55000,
        "Matcha Oat Milk Latte": 65000,
        "Trà Sữa Ô Long Sương Sáo": 50000,
        "Earl Grey Milk Tea Cheese Foam": 60000,
        "Trà Sữa Thái Xanh Cream": 45000,
    },
    "🍓 Trà Trái Cây & Refreshers": {
        "Trà Đào Cam Sả Tươi": 50000,
        "Trà Dâu Hibiscus Refreshers": 55000,
        "Mango Dragonfruit Starlight": 60000,
        "Trà Dâu Tằm Bạc Hà": 48000,
    },
    "☕ Starbucks Reserve & Signature": {
        "Caramel Macchiato Cream": 65000,
        "Cold Brew Trà Sữa Đen": 60000,
        "Trà Sữa Trân Châu Đường Đen Reserve": 62000,
    }
}

SIZE_OPTIONS = {
    "Tall (Vừa)": 0,
    "Grande (Lớn)": 8000,
    "Venti (Đặc biệt)": 15000
}

MILK_OPTIONS = [
    "Sữa tươi nguyên kem",
    "Sữa yến mạch (Oat Milk) (+10k)",
    "Sữa hạnh nhân (+10k)",
    "Sữa tách béo (Skim Milk)",
    "Không dùng sữa"
]

TOPPING_OPTIONS = {
    "Trân châu hoàng gia": 8000,
    "Thạch Espresso Jelly": 10000,
    "Pudding Trứng Custard": 10000,
    "Kem Cheese Foam": 12000,
    "Sốt Caramel Drizzle": 7000
}

SUGAR_LEVELS = ["100% (Tiêu chuẩn)", "70% (Ít ngọt)", "50%", "30%", "0% (Không đường)"]
ICE_LEVELS = ["100% (Tiêu chuẩn)", "70%", "50%", "30%", "0% (Không đá)", "Nóng (Hot)"]

SERVICE_TYPES = ["☕ Uống tại quán (Dine-in)", "🛍️ Mang đi (Takeaway)", "🛵 Giao hàng (Delivery)"]

CUSTOMER_TIERS = {
    "Khách vãng lai / Mới": 0,
    "Thành viên Green ⭐ (Giảm 5%)": 5,
    "Thành viên Gold 🌟 (Giảm 10%)": 10,
    "VIP Starbucks Reserve (Giảm 15%)": 15
}

# ---------------------------------------------------------
# 4. KHỞI TẠO SESSION STATE
# ---------------------------------------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []
if "invoice_paid" not in st.session_state:
    st.session_state.invoice_paid = False

# ---------------------------------------------------------
# 5. HÀM TẠO FILE HÓA ĐƠN TEXT (.TXT)
# ---------------------------------------------------------
def create_txt_invoice(customer_name, tier, service_type, cart, total_amount, discount_percent, final_amount, stars_earned):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    content = f"{'='*45}\n"
    content += f"{'STARBUCKS TEA LOUNGE - RECEIPT':^45}\n"
    content += f"{'='*45}\n"
    content += f"Thời gian   : {now}\n"
    content += f"Khách hàng  : {customer_name if customer_name else 'Khách vãng lai'}\n"
    content += f"Hạng thẻ    : {tier}\n"
    content += f"Hình thức   : {service_type}\n"
    content += f"{'-'*45}\n"
    
    for idx, item in enumerate(cart, 1):
        content += f"{idx}. {item['Tên món']} [{item['Size']}]\n"
        content += f"   - Sữa: {item['Loại sữa']} | Đường: {item['Đường']} | Đá: {item['Đá']}\n"
        if item['Topping'] != "Không":
            content += f"   - Topping: {item['Topping']}\n"
        if item['Ghi chú']:
            content += f"   - Ghi chú: {item['Ghi chú']}\n"
        content += f"   SL: {item['Số lượng']} x {item['Đơn giá']:,} = {item['Thành tiền']:,} VNĐ\n"
        
    content += f"{'-'*45}\n"
    content += f"Tổng tiền món : {total_amount:,} VNĐ\n"
    content += f"Ưu đãi hạng   : {discount_percent}%\n"
    content += f"TỔNG THANH TOÁN: {final_amount:,} VNĐ\n"
    content += f"Sao tích lũy  : +{stars_earned} ⭐ Starbucks Stars\n"
    content += f"{'='*45}\n"
    content += f"{'Cảm ơn bạn đã trải nghiệm tại Starbucks!':^45}\n"
    return content

# ---------------------------------------------------------
# 6. GIAO DIỆN CHÍNH (HEADER & DASHBOARD)
# ---------------------------------------------------------
st.markdown("""
    <div class="sb-header">
        <h1>☕ STARBUCKS TEA & MILK TEA POS</h1>
        <p>Hệ Thống Gọi Món & Tích Điểm Thành Viên Tự Động</p>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.15, 0.85], gap="medium")

# ==================== CỘT TRÁI: ĐẶT MÓN & CẤU HÌNH ====================
with col_left:
    st.subheader("📝 Thông tin đơn hàng & Khách hàng")
    
    c_name, c_tier, c_serv = st.columns([1.2, 1.2, 1])
    with c_name:
        customer_name = st.text_input("Tên khách hàng:", placeholder="Nhập tên khách...")
    with c_tier:
        selected_tier = st.selectbox("Hạng thành viên:", list(CUSTOMER_TIERS.keys()))
    with c_serv:
        service_type = st.selectbox("Phục vụ:", SERVICE_TYPES)

    st.markdown("---")
    st.subheader("🧋 Danh mục Menu Starbucks")
    
    # Lựa chọn danh mục món
    category = st.selectbox("Chọn nhóm thức uống:", list(MENU_CATEGORIES.keys()))
    current_menu = MENU_CATEGORIES[category]

    c_item, c_qty = st.columns([3, 1])
    with c_item:
        selected_tea = st.selectbox("Tên thức uống:", list(current_menu.keys()))
    with c_qty:
        quantity = st.number_input("Số lượng:", min_value=1, value=1, step=1)

    # Tùy chọn Size, Đường, Đá & Sữa
    c_size, c_milk = st.columns(2)
    with c_size:
        selected_size = st.selectbox("Kích cỡ (Size):", list(SIZE_OPTIONS.keys()))
    with c_milk:
        selected_milk = st.selectbox("Tùy chọn Sữa:", MILK_OPTIONS)

    c_sugar, c_ice = st.columns(2)
    with c_sugar:
        selected_sugar = st.selectbox("Mức đường:", SUGAR_LEVELS)
    with c_ice:
        selected_ice = st.selectbox("Mức đá / Nóng:", ICE_LEVELS)

    # Topping & Ghi chú
    selected_toppings = st.multiselect(
        "Topping cao cấp:",
        options=list(TOPPING_OPTIONS.keys())
    )
    custom_note = st.text_input("Ghi chú Barista:", placeholder="Ví dụ: Ít kem cheese, ly mang đi đậy nắp đôi...")

    # Tính toán đơn giá
    base_price = current_menu[selected_tea]
    size_price = SIZE_OPTIONS[selected_size]
    
    # Cộng thêm nếu chọn sữa thực vật
    milk_extra = 10000 if "Oat" in selected_milk or "hạnh nhân" in selected_milk else 0
    topping_price = sum(TOPPING_OPTIONS[t] for t in selected_toppings)
    
    unit_price = base_price + size_price + milk_extra + topping_price
    item_total = unit_price * quantity

    st.info(f"💡 Đơn giá 1 ly (Size + Sữa + Topping): **{unit_price:,} VNĐ**")

    # Nút thêm món vào giỏ
    if st.button("➕ Thêm vào giỏ hàng", type="primary", use_container_width=True):
        topping_str = ", ".join(selected_toppings) if selected_toppings else "Không"
        item_data = {
            "Tên món": selected_tea,
            "Size": selected_size.split()[0], # Lấy tên Size (Tall/Grande/Venti)
            "Loại sữa": selected_milk.split("(")[0].strip(),
            "Đường": selected_sugar.split()[0],
            "Đá": selected_ice.split()[0],
            "Topping": topping_str,
            "Ghi chú": custom_note,
            "Đơn giá": unit_price,
            "Số lượng": quantity,
            "Thành tiền": item_total
        }
        st.session_state.cart.append(item_data)
        st.session_state.invoice_paid = False
        st.toast(f"Đã thêm {quantity}x **{selected_tea}** vào giỏ!", icon="☕")

# ==================== CỘT PHẢI: GIỎ HÀNG & THANH TOÁN ====================
with col_right:
    st.subheader("🛒 Giỏ hàng hiện tại")

    if not st.session_state.cart:
        st.warning("Giỏ hàng đang trống. Vui chọn món từ Menu ở cột bên trái.")
    else:
        df_cart = pd.DataFrame(st.session_state.cart)
        
        # Bảng hiển thị chi tiết giỏ hàng
        st.dataframe(
            df_cart[["Tên món", "Size", "Loại sữa", "Topping", "Số lượng", "Thành tiền"]],
            use_container_width=True,
            hide_index=True
        )

        # Nút xóa giỏ hàng
        if st.button("🗑️ Xóa tất cả món", use_container_width=True):
            st.session_state.cart = []
            st.session_state.invoice_paid = False
            st.rerun()

        st.markdown("---")
        
        # Tính toán chiết khấu & Tổng tiền
        total_price = int(df_cart["Thành tiền"].sum())
        discount_percent = CUSTOMER_TIERS[selected_tier]
        discount_amount = int(total_price * (discount_percent / 100))
        final_price = total_price - discount_amount
        
        # Tích điểm sao Starbucks (Mỗi 50,000 VNĐ = 1 ⭐)
        stars_earned = final_price // 50000

        # Hiển thị tóm tắt chi phí
        st.write(f"**Tạm tính:** {total_price:,} VNĐ")
        if discount_percent > 0:
            st.write(f"**Ưu đãi thành viên ({discount_percent}%):** -{discount_amount:,} VNĐ")
        
        st.markdown(f"### Tổng thanh toán: <span class='price-highlight'>{final_price:,} VNĐ</span>", unsafe_allow_html=True)
        st.caption(f"🌟 Tích lũy dự kiến: **+{stars_earned} Sao Starbucks**")

        st.markdown("---")
        # Nút Bấm Thanh Toán
        if st.button("💳 XÁC NHẬN THANH TOÁN", type="primary", use_container_width=True):
            st.session_state.invoice_paid = True
            st.balloons()

# ---------------------------------------------------------
# 7. XUẤT HÓA ĐƠN & TẠO MÃ VIETQR DỘNG KHI THANH TOÁN
# ---------------------------------------------------------
if st.session_state.get("invoice_paid") and st.session_state.cart:
    st.markdown("---")
    st.success("🎉 Đơn hàng đã được ghi nhận thành công!")

    col_inv, col_qr = st.columns([1.2, 0.8])
    
    with col_inv:
        st.markdown("<div class='sb-bill-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #006241;'>☕ HÓA ĐƠN THANH TOÁN - STARBUCKS</h3>", unsafe_allow_html=True)
        
        st.write(f"**Ngày:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        st.write(f"**Khách hàng:** {customer_name if customer_name else 'Khách vãng lai'} ({selected_tier.split('(')[0]})")
        st.write(f"**Hình thức:** {service_type}")
        
        # Bảng hóa đơn
        st.table(pd.DataFrame(st.session_state.cart)[["Tên món", "Size", "Loại sữa", "Đường", "Đá", "Topping", "Số lượng", "Thành tiền"]])
        
        st.markdown(f"**Tổng tiền ban đầu:** {total_price:,} VNĐ")
        st.markdown(f"**Giảm giá:** {discount_percent}% (-{discount_amount:,} VNĐ)")
        st.markdown(f"### 🎯 CẦN THANH TOÁN: <span style='color:#006241'>{final_price:,} VNĐ</span>", unsafe_allow_html=True)
        st.markdown(f"🌟 **Điểm sao thưởng:** +{stars_earned} ⭐ Starbucks Stars")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_qr:
        st.subheader("📲 Quét VietQR Thanh Toán")
        
        # Tạo mã VietQR động bằng API VietQR công khai
        bank_id = "MB" # Ngân hàng MBBank
        account_no = "09999999999" # Số tài khoản demo
        account_name = "STARBUCKS COFFEE"
        qr_url = f"https://img.vietqr.io/image/{bank_id}-{account_no}-compact2.png?amount={final_price}&addInfo=Thanh%20toan%20Starbucks%20{customer_name}&accountName={account_name}"
        
        st.image(qr_url, caption="Quét mã bằng app ngân hàng hoặc MoMo để thanh toán", use_container_width=True)

    st.markdown("---")
    
    # Nút Download TXT & Tạo Đơn Mới
    txt_data = create_txt_invoice(
        customer_name, selected_tier, service_type, 
        st.session_state.cart, total_price, discount_percent, final_price, stars_earned
    )
    
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        st.download_button(
            label="📥 Tải Hóa Đơn Văn Bản (.TXT)",
            data=txt_data,
            file_name=f"Starbucks_Receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with c_dl2:
        if st.button("🔄 Tạo đơn mới / Tiếp tục bán hàng", use_container_width=True):
            st.session_state.cart = []
            st.session_state.invoice_paid = False
            st.rerun()
