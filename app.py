import streamlit as st
import pandas as pd
from datetime import datetime
import json
import random

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG (Đầu tiên)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Autumn Tea & Bakery Lounge 🍁 (All-in-One POS)",
    page_icon="🧋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. HÀM TƯƠNG THÍCH STREAMLIT
# ---------------------------------------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def safe_toast(msg, icon="🍁"):
    if hasattr(st, "toast"):
        st.toast(msg, icon=icon)
    else:
        st.success(f"{icon} {msg}")

# ---------------------------------------------------------
# 3. CUSTOM CSS: TONE MÙA THU CỦA QUÁN 🍁
# ---------------------------------------------------------
st.markdown("""
    <style>
    :root {
        --autumn-orange: #D96B27;
        --autumn-brown: #5C2C16;
        --autumn-gold: #F59E0B;
        --autumn-bg: #FDFBF7;
    }

    .stApp {
        background-color: var(--autumn-bg);
    }

    /* BANNER TIÊU ĐỀ CÓ ẢNH NỀN TONE MÙA THU */
    .hero-banner-img {
        position: relative;
        background-image: linear-gradient(rgba(44, 19, 9, 0.75), rgba(92, 44, 22, 0.85)), 
                          url('https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center;
        border-radius: 16px;
        padding: 30px 20px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    }
    
    .hero-banner-img h1 {
        color: #FFFFFF !important;
        font-family: 'Georgia', serif;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 6px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .hero-banner-img p {
        color: #FBBF24;
        font-size: 1.1rem;
        margin: 0;
        font-style: italic;
        font-weight: 500;
    }

    /* KDS Card */
    .kds-card-pending {
        background-color: #FFFBEB;
        border-left: 6px solid #F59E0B;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .kds-card-doing {
        background-color: #EFF6FF;
        border-left: 6px solid #3B82F6;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .kds-card-done {
        background-color: #ECFDF5;
        border-left: 6px solid #10B981;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* Sơ đồ bàn */
    .table-free {
        background-color: #ECFDF5;
        border: 2px solid #10B981;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        font-weight: bold;
        color: #065F46;
        margin-bottom: 10px;
    }

    .table-occupied {
        background-color: #FEF2F2;
        border: 2px solid #EF4444;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        font-weight: bold;
        color: #991B1B;
        margin-bottom: 10px;
    }

    /* Thẻ Hóa Đơn Thermal POS */
    .bill-thermal {
        background-color: #FFFFFF;
        border: 2px dashed #D96B27;
        border-radius: 12px;
        padding: 20px;
        font-family: 'Courier New', Courier, monospace;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    /* AI Box */
    .ai-box {
        background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%);
        border: 1px solid #F59E0B;
        border-radius: 10px;
        padding: 12px;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* Lucky Wheel Box */
    .wheel-container {
        background: linear-gradient(135deg, #5C2C16 0%, #D96B27 100%);
        color: white;
        border-radius: 16px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. KHỞI TẠO SESSION STATE DỮ LIỆU TOÀN DIỆN
# ---------------------------------------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []
if "invoice_paid" not in st.session_state:
    st.session_state.invoice_paid = False
if "order_counter" not in st.session_state:
    st.session_state.order_counter = 103

if "sales_history" not in st.session_state:
    st.session_state.sales_history = [
        {
            "Mã đơn": "ORD-101",
            "Thời gian": "17/10/2026 14:15:20",
            "Khách hàng": "Anh Minh",
            "Vị trí": "Bàn 02",
            "Số lượng": 3,
            "Thành tiền": 146300,
            "Chi tiết": "Trà Sữa Quế Hoa (1), Bánh Mì Bơ Tỏi (1), Latte Hạt Dẻ (1)"
        },
        {
            "Mã đơn": "ORD-102",
            "Thời gian": "17/10/2026 15:30:10",
            "Khách hàng": "Chị Hoàng Yến",
            "Vị trí": "Mang đi",
            "Số lượng": 1,
            "Thành tiền": 49500,
            "Chi tiết": "Trà Hồng Trà Táo Mật Maple (1)"
        }
    ]

if "kds_orders" not in st.session_state:
    st.session_state.kds_orders = [
        {
            "id": "ORD-101",
            "time": "14:15",
            "customer": "Anh Minh",
            "location": "Bàn 02",
            "items": [
                {"name": "Trà Sữa Quế Hoa Mùa Thu", "qty": 1, "note": "70% đường, Ít đá"},
                {"name": "Bánh Mì Bơ Tỏi Phô Mai Nướng", "qty": 1, "note": "Hâm nóng"},
                {"name": "Latte Hạt Dẻ Nướng Hazelnut", "qty": 1, "note": "Nóng"}
            ],
            "status": "Hoàn thành"
        },
        {
            "id": "ORD-102",
            "time": "15:30",
            "customer": "Chị Hoàng Yến",
            "location": "Mang đi",
            "items": [
                {"name": "Trà Hồng Trà Táo Mật Maple", "qty": 1, "note": "Sữa Oat milk"}
            ],
            "status": "Đang chế biến"
        }
    ]

if "tables" not in st.session_state:
    st.session_state.tables = {f"Bàn {i:02d}": {"status": "Trống", "order_id": None, "guests": 0} for i in range(1, 13)}
    st.session_state.tables["Bàn 02"] = {"status": "Đang ngồi", "order_id": "ORD-101", "guests": 2}
    st.session_state.tables["Bàn 05"] = {"status": "Đang ngồi", "order_id": None, "guests": 4}

if "inventory" not in st.session_state:
    st.session_state.inventory = {
        "Trà Cốt Ô Long (g)": 4500,
        "Trà Cốt Đen (g)": 3800,
        "Sữa Tươi Kem Béo (ml)": 15000,
        "Sữa Yến Mạch Oat Milk (ml)": 4200,
        "Trân Châu Hoàng Gia (g)": 2500,
        "Bánh Mì Sandwich BBQ (Cái)": 18,
        "Bánh Mì Bơ Tỏi (Cái)": 12,
        "Bánh Croissant Bơ (Cái)": 20,
        "Bánh Tiramisu Hạt Dẻ (Cái)": 8,
        "Bánh Cheesecake Chanh Dây (Cái)": 10
    }

if "wheel_prize" not in st.session_state:
    st.session_state.wheel_prize = None

# ---------------------------------------------------------
# 5. DỮ LIỆU THỰC ĐƠN & DANH SÁCH NHẠC VINTAGE
# ---------------------------------------------------------
DRINK_MENU = {
    "🍵 Trà Sữa Mùa Thu 🍁": {
        "Trà Sữa Quế Hoa Mùa Thu": {
            "price": 58000,
            "img": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Trà Cốt Ô Long (g)": 30, "Sữa Tươi Kem Béo (ml)": 100},
            "upsell_recommend": "🥐 Bánh Croissant Bơ Thụy Sĩ"
        },
        "Latte Hạt Dẻ Nướng Hazelnut": {
            "price": 62000,
            "img": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Trà Cốt Đen (g)": 25, "Sữa Tươi Kem Béo (ml)": 120},
            "upsell_recommend": "🍰 Bánh Tiramisu Hạt Dẻ Autumn"
        },
        "Trà Sữa Ô Long Lúa Mạch": {
            "price": 52000,
            "img": "https://images.unsplash.com/photo-1485808191679-5f86510681a2?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Trà Cốt Ô Long (g)": 30, "Sữa Tươi Kem Béo (ml)": 100},
            "upsell_recommend": "🧄 Bánh Mì Bơ Tỏi Phô Mai Nướng"
        },
        "Trà Sữa Trân Châu Đường Đen Maple": {
            "price": 55000,
            "img": "https://images.unsplash.com/photo-1558857563-b371033873b8?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Trà Cốt Đen (g)": 30, "Sữa Tươi Kem Béo (ml)": 100, "Trân Châu Hoàng Gia (g)": 50},
            "upsell_recommend": "🥐 Bánh Croissant Bơ Thụy Sĩ"
        }
    },
    "🍎 Trà Trái Cây Refreshers 🍂": {
        "Trà Hồng Trà Táo Mật Maple": {
            "price": 55000,
            "img": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Trà Cốt Đen (g)": 30},
            "upsell_recommend": "🧀 Bánh Cheesecake Chanh Dây"
        },
        "Trà Đào Cam Sả Mật Ô Long": {
            "price": 50000,
            "img": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Trà Cốt Ô Long (g)": 30},
            "upsell_recommend": "🥪 Bánh Mì Sandwich Thịt Nướng BBQ"
        },
        "Trà Dâu Tằm Bạc Hà Mùa Thu": {
            "price": 48000,
            "img": "https://images.unsplash.com/photo-1499638673689-79a0b5115d87?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Trà Cốt Đen (g)": 30},
            "upsell_recommend": "🧀 Bánh Cheesecake Chanh Dây"
        }
    },
    "☕ Coffee & Cream Special 🌾": {
        "Caramel Macchiato Hạt Dẻ": {
            "price": 65000,
            "img": "https://images.unsplash.com/photo-1541167760496-1628856ab772?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Sữa Tươi Kem Béo (ml)": 120},
            "upsell_recommend": "🥐 Bánh Croissant Bơ Thụy Sĩ"
        },
        "Cold Brew Trà Đen Macchiato": {
            "price": 60000,
            "img": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Trà Cốt Đen (g)": 40},
            "upsell_recommend": "🍰 Bánh Tiramisu Hạt Dẻ Autumn"
        },
        "Matcha Frappuccino Kem Béo": {
            "price": 68000,
            "img": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=600&q=80",
            "ingredients": {"Sữa Tươi Kem Béo (ml)": 150},
            "upsell_recommend": "🧄 Bánh Mì Bơ Tỏi Phô Mai Nướng"
        }
    }
}

BAKERY_MENU = {
    "🥪 Bánh Mì Sandwich Thịt Nướng BBQ": {
        "price": 45000,
        "img": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=600&q=80",
        "desc": "Bánh mì Sandwich giòn kẹp thịt nướng sốt BBQ đậm đà",
        "stock_key": "Bánh Mì Sandwich BBQ (Cái)"
    },
    "🧄 Bánh Mì Bơ Tỏi Phô Mai Nướng": {
        "price": 38000,
        "img": "https://images.unsplash.com/photo-1573140247632-f8fd74997d5c?auto=format&fit=crop&w=600&q=80",
        "desc": "Bánh mì sốt bơ tỏi thơm lừng ngập tràn phô mai kéo sợi",
        "stock_key": "Bánh Mì Bơ Tỏi (Cái)"
    },
    "🥐 Bánh Croissant Bơ Thụy Sĩ": {
        "price": 35000,
        "img": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=600&q=80",
        "desc": "Bánh sừng bò nướng giòn xốp thơm bơ ngậy",
        "stock_key": "Bánh Croissant Bơ (Cái)"
    },
    "🍰 Bánh Tiramisu Hạt Dẻ Autumn": {
        "price": 48000,
        "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=600&q=80",
        "desc": "Bánh Tiramisu mềm mịn thơm vị cà phê & hạt dẻ nướng",
        "stock_key": "Bánh Tiramisu Hạt Dẻ (Cái)"
    },
    "🧀 Bánh Cheesecake Chanh Dây": {
        "price": 45000,
        "img": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=600&q=80",
        "desc": "Cheesecake chua ngọt thanh mát hòa quyện vị chanh dây",
        "stock_key": "Bánh Cheesecake Chanh Dây (Cái)"
    }
}

SIZE_OPTIONS = {"S (Vừa)": 0, "M (Lớn)": 8000, "L (Đặc biệt)": 15000}
MILK_OPTIONS = ["Sữa nguyên kem", "Sữa yến mạch Oat Milk (+10k)", "Sữa hạnh nhân (+10k)", "Không dùng sữa"]
TOPPING_OPTIONS = {
    "Trân châu hoàng gia": 8000,
    "Thạch Quế Hoa": 8000,
    "Thạch Espresso Jelly": 10000,
    "Pudding Trứng Custard": 10000,
    "Kem Cheese Foam": 12000
}
CUSTOMER_TIERS = {
    "Khách vãng lai": 0,
    "Thành viên Maple 🍁 (Giảm 5%)": 5,
    "Thành viên Gold Leaf 🍂 (Giảm 10%)": 10,
    "VIP Autumn Reserve 👑 (Giảm 15%)": 15
}

PRIZES = [
    "🎟️ Voucher giảm 20% cho đơn tiếp theo",
    "🥐 Tặng 1 Bánh Croissant Bơ Thụy Sĩ",
    "🧋 Tặng 1 Topping Trân Châu Hoàng Gia",
    "🌟 Tặng +500 Điểm Thưởng Thành Viên",
    "🎁 Tặng 1 Ly Trà Sữa Quế Hoa Mùa Thu",
    "🍀 Chúc bạn may mắn lần sau!"
]

MUSIC_PLAYLIST = {
    "🎷 Jazz Vintage Mùa Thu": "file:///D:/Relax%20And%20Unwind%20In%20A%20Vintage%20Cafe%20With%20Smooth%20Jazz%20-%205%20Minute%20Calming%20Break.mp3",
    "☕ Lofi Cafe Chill": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "🍁 Autumn Piano Melodies": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
}

# ---------------------------------------------------------
# 6. SIDEBAR ĐIỀU HƯỚNG TỔNG HỢP
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=500&q=80", use_container_width=True)
    st.markdown("<h2 style='text-align:center; color:#5C2C16;'>🍁 AUTUMN LOUNGE</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    selected_nav = st.radio(
        "📌 Chức Năng Hệ Thống:",
        [
            "🧋 Order Bán Hàng & POS",
            "👨‍🍳 Màn Hình Bếp / Barista (KDS)",
            "🗺️ Sơ Đồ Quản Lý Bàn",
            "📦 Quản Lý Tồn Kho",
            "🎁 Vòng Quay May Mắn",
            "📊 Doanh Thu Real-Time",
            "⚙️ Quản Lý Ca"
        ]
    )
    
    st.markdown("---")
    st.caption("👤 **Thu ngân:** Nguyễn Văn Bình")
    st.caption("⏰ **Ca:** Ca Sáng (07:00 - 15:00)")
    
    df_sales_quick = pd.DataFrame(st.session_state.sales_history)
    quick_rev = int(df_sales_quick["Thành tiền"].sum()) if not df_sales_quick.empty else 0
    st.markdown("### 📈 Doanh Thu Ca")
    st.metric("Tổng doanh thu", f"{quick_rev:,} VNĐ")

    # 📻 VINTAGE RADIO PLAYER IN SIDEBAR (CHUẨN STREAMLIT NATIVE)
    st.markdown("---")
    st.markdown("### 📻 Vintage Radio Player")
    selected_music_name = st.selectbox("🎵 Chọn Giai Điệu:", list(MUSIC_PLAYLIST.keys()))
    current_music_url = MUSIC_PLAYLIST[selected_music_name]
    
    st.caption("👇 **Nhấn nút ▶️ bên dưới để bật nhạc:**")
    st.audio(current_music_url, format="audio/mp3")

# ---------------------------------------------------------
# 7. BANNER HERO TIÊU ĐỀ
# ---------------------------------------------------------
st.markdown("""
    <div class="hero-banner-img">
        <h1>🍁 AUTUMN TEA & BAKERY LOUNGE 🍞</h1>
        <p>"Thưởng Thức Hương Vị Trà Sữa Mùa Thu & Bánh Mì Nướng Nóng Giòn"</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 8. XỬ LÝ THEO TỪNG CHỨC NĂNG CỦA SIDEBAR
# ---------------------------------------------------------

# =========================================================
# CHỨC NĂNG 1: ORDER BÁN HÀNG & POS
# =========================================================
if selected_nav == "🧋 Order Bán Hàng & POS":
    col_left, col_right = st.columns([1.2, 0.8], gap="large")

    with col_left:
        st.subheader("📝 Thông Tin Order & Vị Trí")
        
        c1, c2, c3 = st.columns([1.2, 1.2, 1])
        with c1:
            customer_name = st.text_input("Tên khách hàng:", placeholder="Nhập tên khách...")
        with c2:
            selected_tier = st.selectbox("Hạng thành viên:", list(CUSTOMER_TIERS.keys()))
        with c3:
            table_options = ["Mang đi", "Giao hàng"] + list(st.session_state.tables.keys())
            selected_location = st.selectbox("Vị trí / Bàn:", table_options)

        st.markdown("---")
        item_type = st.radio("🎯 Chọn Sản Phẩm:", ["🧋 Thức Uống Mùa Thu", "🍞 Bánh Mì & Bánh Ngọt"], horizontal=True)

        if item_type == "🧋 Thức Uống Mùa Thu":
            category = st.selectbox("Nhóm thức uống:", list(DRINK_MENU.keys()))
            current_category_menu = DRINK_MENU[category]

            c_item, c_qty = st.columns([2.5, 1])
            with c_item:
                selected_drink = st.selectbox("Món nước:", list(current_category_menu.keys()))
            with c_qty:
                drink_qty = st.number_input("Số lượng:", min_value=1, value=1, step=1, key="drink_qty")

            drink_info = current_category_menu[selected_drink]
            
            c_img, c_opts = st.columns([1, 1.8])
            with c_img:
                st.image(drink_info["img"], caption=selected_drink, use_container_width=True)
            with c_opts:
                sz_col, mlk_col = st.columns(2)
                with sz_col:
                    selected_size = st.selectbox("Size:", list(SIZE_OPTIONS.keys()))
                with mlk_col:
                    selected_milk = st.selectbox("Tùy chọn Sữa:", MILK_OPTIONS)

                sug_col, ice_col = st.columns(2)
                with sug_col:
                    selected_sugar = st.selectbox("Đường:", ["100%", "70%", "50%", "30%", "0%"])
                with ice_col:
                    selected_ice = st.selectbox("Đá:", ["100%", "70%", "50%", "30%", "🔥 Uống Nóng"])

            selected_toppings = st.multiselect("Topping:", options=list(TOPPING_OPTIONS.keys()))
            
            # AI SMART UPSELL & RECOMMENDATION BOX
            rec_bakery = drink_info.get("upsell_recommend", "🥐 Bánh Croissant Bơ Thụy Sĩ")
            st.markdown(f"""
                <div class="ai-box">
                    <strong>🤖 AI Gợi Ý Combo Mùa Thu:</strong> Thức uống <em>{selected_drink}</em> cực kỳ hợp vị khi dùng kèm <strong>{rec_bakery}</strong>!
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"➕ Thêm Combo Gợi Ý ({rec_bakery})", type="secondary"):
                bakery_match = None
                for b_name in BAKERY_MENU.keys():
                    if rec_bakery in b_name or b_name in rec_bakery:
                        bakery_match = b_name
                        break
                if not bakery_match:
                    bakery_match = list(BAKERY_MENU.keys())[0]
                
                b_info = BAKERY_MENU[bakery_match]
                st.session_state.cart.append({
                    "Tên món": bakery_match,
                    "Loại": "Bánh (AI Combo)",
                    "Size": "Standard",
                    "Ghi chú": "Hâm nóng | AI Combo Discount -10,000đ",
                    "Đơn giá": b_info["price"] - 10000,
                    "Số lượng": 1,
                    "Thành tiền": b_info["price"] - 10000,
                    "ingredients": {b_info["stock_key"]: 1}
                })
                safe_toast(f"Đã thêm bánh Combo {bakery_match} với giá ưu đãi!", icon="🤖")

            unit_price = drink_info["price"] + SIZE_OPTIONS[selected_size] + (10000 if "Oat" in selected_milk or "hạnh nhân" in selected_milk else 0) + sum(TOPPING_OPTIONS[t] for t in selected_toppings)
            total_item_price = unit_price * drink_qty

            st.info(f"💡 Đơn giá 1 ly: **{unit_price:,} VNĐ** | Tổng: **{total_item_price:,} VNĐ**")

            if st.button("➕ Thêm Thức Uống Vào Giỏ", type="primary", use_container_width=True):
                topping_str = ", ".join(selected_toppings) if selected_toppings else "Không"
                item_data = {
                    "Tên món": selected_drink,
                    "Loại": "Thức uống",
                    "Size": selected_size.split()[0],
                    "Ghi chú": f"Sữa: {selected_milk.split('(')[0].strip()} | Đường: {selected_sugar} | Đá: {selected_ice} | Topping: {topping_str}",
                    "Đơn giá": unit_price,
                    "Số lượng": drink_qty,
                    "Thành tiền": total_item_price,
                    "ingredients": drink_info.get("ingredients", {})
                }
                st.session_state.cart.append(item_data)
                st.session_state.invoice_paid = False
                safe_toast(f"Đã thêm {drink_qty}x {selected_drink}!", icon="🧋")

        else: # BAKERY
            c_bakery, c_qty_b = st.columns([2.5, 1])
            with c_bakery:
                selected_bakery = st.selectbox("Chọn loại bánh mì / bánh ngọt:", list(BAKERY_MENU.keys()))
            with c_qty_b:
                bakery_qty = st.number_input("Số lượng bánh:", min_value=1, value=1, step=1, key="bakery_qty")

            bakery_info = BAKERY_MENU[selected_bakery]
            
            c_b_img, c_b_opts = st.columns([1, 1.8])
            with c_b_img:
                st.image(bakery_info["img"], caption=selected_bakery, use_container_width=True)
            with c_b_opts:
                st.write(f"**Mô tả:** {bakery_info['desc']}")
                heat_option = st.checkbox("🔥 Hâm nóng bánh trước khi giao", value=True)
                extra_cheese = st.checkbox("🧀 Thêm Phô Mai Nướng (+10,000 VNĐ)", value=False)

            bakery_unit_price = bakery_info["price"] + (10000 if extra_cheese else 0)
            total_bakery_price = bakery_unit_price * bakery_qty

            st.info(f"💡 Đơn giá 1 phần bánh: **{bakery_unit_price:,} VNĐ** | Tổng: **{total_bakery_price:,} VNĐ**")

            if st.button("➕ Thêm Bánh Vào Giỏ", type="primary", use_container_width=True):
                note_heat = "Hâm nóng" if heat_option else "Không hâm"
                note_cheese = "Có phô mai" if extra_cheese else ""
                note_final = f"{note_heat} | {note_cheese}".strip(" |")
                item_data = {
                    "Tên món": selected_bakery,
                    "Loại": "Bánh",
                    "Size": "Standard",
                    "Ghi chú": note_final,
                    "Đơn giá": bakery_unit_price,
                    "Số lượng": bakery_qty,
                    "Thành tiền": total_bakery_price,
                    "ingredients": {bakery_info["stock_key"]: bakery_qty}
                }
                st.session_state.cart.append(item_data)
                st.session_state.invoice_paid = False
                safe_toast(f"Đã thêm {bakery_qty}x {selected_bakery}!", icon="🍞")

    # ----- CỘT PHẢI: GIỎ HÀNG & THANH TOÁN -----
    with col_right:
        st.subheader("🛒 Giỏ Hàng Chi Tiết")

        if not st.session_state.cart:
            st.warning("Giỏ hàng đang trống.")
        else:
            df_cart = pd.DataFrame(st.session_state.cart)
            st.dataframe(
                df_cart[["Tên món", "Loại", "Ghi chú", "Số lượng", "Thành tiền"]],
                use_container_width=True,
                hide_index=True
            )

            if st.button("🗑️ Xóa toàn bộ giỏ hàng", use_container_width=True):
                st.session_state.cart = []
                st.session_state.invoice_paid = False
                safe_rerun()

            st.markdown("---")
            total_price = int(df_cart["Thành tiền"].sum())
            discount_percent = CUSTOMER_TIERS[selected_tier]
            discount_amount = int(total_price * (discount_percent / 100))
            final_price = total_price - discount_amount

            st.write(f"**Tạm tính:** {total_price:,} VNĐ")
            if discount_percent > 0:
                st.write(f"**Ưu đãi thành viên ({discount_percent}%):** -{discount_amount:,} VNĐ")
            
            st.markdown(f"### Cần thanh toán: <span style='color:#D96B27; font-weight:800; font-size:1.6rem;'>{final_price:,} VNĐ</span>", unsafe_allow_html=True)

            if final_price >= 100000:
                st.success("🎉 Đơn hàng >= 100k! Khách hàng nhận được 1 Lượt Quay Vòng Quay May Mắn!")

            st.markdown("---")
            if st.button("💳 XÁC NHẬN THANH TOÁN & GỬI BẾP", type="primary", use_container_width=True):
                order_id = f"ORD-{st.session_state.order_counter}"
                st.session_state.order_counter += 1
                
                st.session_state.invoice_paid = True
                
                # 1. Trừ kho nguyên liệu
                for item in st.session_state.cart:
                    ing_map = item.get("ingredients", {})
                    for ing_name, amount in ing_map.items():
                        if ing_name in st.session_state.inventory:
                            st.session_state.inventory[ing_name] = max(0, st.session_state.inventory[ing_name] - (amount * item["Số lượng"]))

                # 2. Cập nhật sơ đồ bàn
                if selected_location in st.session_state.tables:
                    st.session_state.tables[selected_location]["status"] = "Đang ngồi"
                    st.session_state.tables[selected_location]["order_id"] = order_id

                # 3. Gửi đơn sang KDS Màn Hình Bếp
                kds_item_list = [{"name": i["Tên món"], "qty": i["Số lượng"], "note": i["Ghi chú"]} for i in st.session_state.cart]
                st.session_state.kds_orders.append({
                    "id": order_id,
                    "time": datetime.now().strftime("%H:%M"),
                    "customer": customer_name if customer_name else "Khách vãng lai",
                    "location": selected_location,
                    "items": kds_item_list,
                    "status": "Chờ chế biến"
                })

                # 4. Lưu báo cáo doanh thu real-time
                item_summary = ", ".join([f"{item['Tên món']} ({item['Số lượng']})" for item in st.session_state.cart])
                new_sale = {
                    "Mã đơn": order_id,
                    "Thời gian": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Khách hàng": customer_name if customer_name else "Khách vãng lai",
                    "Vị trí": selected_location,
                    "Số lượng": sum(item['Số lượng'] for item in st.session_state.cart),
                    "Thành tiền": final_price,
                    "Chi tiết": item_summary
                }
                st.session_state.sales_history.append(new_sale)
                st.session_state.last_completed_order = new_sale
                
                if hasattr(st, "balloons"):
                    st.balloons()

    # HIỂN THỊ HÓA ĐƠN THERMAL POS & MÃ VIETQR
    if st.session_state.get("invoice_paid") and st.session_state.cart:
        st.markdown("---")
        st.success("🎉 Đơn hàng đã được thanh toán & chuyển xuống màn hình Bếp KDS!")

        df_inv = pd.DataFrame(st.session_state.cart)
        tot_p = int(df_inv["Thành tiền"].sum())
        disc_p = CUSTOMER_TIERS[selected_tier]
        fin_p = tot_p - int(tot_p * (disc_p / 100))

        col_inv, col_qr = st.columns([1.1, 0.9])
        with col_inv:
            st.markdown("<div class='bill-thermal'>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;'>🍁 AUTUMN LOUNGE</h3>", unsafe_allow_html=True)
            current_ord_id = st.session_state.last_completed_order['Mã đơn'] if st.session_state.last_completed_order else 'ORD-NEW'
            st.markdown(f"<p style='text-align:center;'>Mã đơn: <strong>{current_ord_id}</strong></p>", unsafe_allow_html=True)
            st.write(f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            st.write(f"Khách: {customer_name if customer_name else 'Khách vãng lai'} | {selected_location}")
            st.markdown("---------------------------------")
            for idx, item in enumerate(st.session_state.cart, 1):
                st.write(f"{idx}. {item['Tên món']} (x{item['Số lượng']})")
                st.caption(f"   {item['Ghi chú']} -> {item['Thành tiền']:,}đ")
            st.markdown("---------------------------------")
            st.write(f"Tạm tính: {tot_p:,} VNĐ")
            st.write(f"Giảm giá ({disc_p}%): -{int(tot_p * disc_p / 100):,} VNĐ")
            st.markdown(f"#### TỔNG CẦN THU: {fin_p:,} VNĐ")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_qr:
            st.subheader("📲 VietQR Autopay")
            qr_url = f"https://img.vietqr.io/image/MB-09999999999-compact2.png?amount={fin_p}&addInfo=AUTUMN%20TEA%20{customer_name}&accountName=AUTUMN%20LOUNGE"
            st.image(qr_url, caption="Quét VietQR tự động hoàn tất thanh toán", use_container_width=True)

        if st.button("🔄 Tiếp tục tạo đơn bán tiếp theo", use_container_width=True):
            st.session_state.cart = []
            st.session_state.invoice_paid = False
            safe_rerun()

# =========================================================
# CHỨC NĂNG 2: MÀN HÌNH BẾP / BARISTA (KDS)
# =========================================================
elif selected_nav == "👨‍🍳 Màn Hình Bếp / Barista (KDS)":
    st.subheader("👨‍🍳 Màn Hình Chế Biến Real-Time Bếp & Barista (KDS)")
    st.info("💡 Màn hình tự động cập nhật đơn từ quầy POS. Barista nhấn chuyển trạng thái để báo hoàn thành đơn.")

    if not st.session_state.kds_orders:
        st.warning("Hiện tại không có đơn hàng nào chờ chế biến.")
    else:
        kds_col1, kds_col2, kds_col3 = st.columns(3)

        pending_orders = [o for o in st.session_state.kds_orders if o["status"] == "Chờ chế biến"]
        doing_orders = [o for o in st.session_state.kds_orders if o["status"] == "Đang chế biến"]
        done_orders = [o for o in st.session_state.kds_orders if o["status"] == "Hoàn thành"]

        with kds_col1:
            st.markdown("### ⏳ Chờ Chế Biến")
            for order in pending_orders:
                st.markdown(f"""
                    <div class="kds-card-pending">
                        <h4>Mã đơn: {order['id']} ({order['time']})</h4>
                        <p><strong>Khách:</strong> {order['customer']} | <strong>Vị trí:</strong> {order['location']}</p>
                    </div>
                """, unsafe_allow_html=True)
                for item in order["items"]:
                    st.write(f"• **{item['name']}** x{item['qty']}")
                    st.caption(f"  Ghi chú: {item['note']}")
                
                if st.button(f"👉 Chuyển Đang Làm ({order['id']})", key=f"btn_doing_{order['id']}"):
                    order["status"] = "Đang chế biến"
                    safe_toast(f"Đã chuyển đơn {order['id']} sang Đang chế biến!", icon="👨‍🍳")
                    safe_rerun()
                st.markdown("---")

        with kds_col2:
            st.markdown("### ☕ Đang Chế Biến")
            for order in doing_orders:
                st.markdown(f"""
                    <div class="kds-card-doing">
                        <h4>Mã đơn: {order['id']} ({order['time']})</h4>
                        <p><strong>Khách:</strong> {order['customer']} | <strong>Vị trí:</strong> {order['location']}</p>
                    </div>
                """, unsafe_allow_html=True)
                for item in order["items"]:
                    st.write(f"• **{item['name']}** x{item['qty']}")
                    st.caption(f"  Ghi chú: {item['note']}")
                
                if st.button(f"✅ Hoàn Thành Bếp ({order['id']})", key=f"btn_done_{order['id']}"):
                    order["status"] = "Hoàn thành"
                    safe_toast(f"Đơn {order['id']} đã hoàn thành chế biến!", icon="✅")
                    safe_rerun()
                st.markdown("---")

        with kds_col3:
            st.markdown("### 🎉 Sẵn Sàng Giao Khách")
            for order in done_orders:
                st.markdown(f"""
                    <div class="kds-card-done">
                        <h4>Mã đơn: {order['id']} ({order['time']})</h4>
                        <p><strong>Khách:</strong> {order['customer']} | <strong>Vị trí:</strong> {order['location']}</p>
                        <p><span style="color:#10B981; font-weight:bold;">Status: Đã Hoàn Thành</span></p>
                    </div>
                """, unsafe_allow_html=True)

# =========================================================
# CHỨC NĂNG 3: SƠ ĐỒ QUẢN LÝ BÀN
# =========================================================
elif selected_nav == "🗺️ Sơ Đồ Quản Lý Bàn":
    st.subheader("🗺️ Sơ Đồ Quản Lý Bàn Tại Quán")
    
    table_names = list(st.session_state.tables.keys())
    t_cols = st.columns(4)
    for idx, t_name in enumerate(table_names):
        t_data = st.session_state.tables[t_name]
        with t_cols[idx % 4]:
            if t_data["status"] == "Trống":
                st.markdown(f"""
                    <div class="table-free">
                        <h3>{t_name}</h3>
                        <p>Trạng thái: 🟢 Trống</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🪑 Mở Bàn ({t_name})", key=f"open_{t_name}"):
                    st.session_state.tables[t_name]["status"] = "Đang ngồi"
                    safe_toast(f"Đã mở {t_name}!", icon="🪑")
                    safe_rerun()
            else:
                st.markdown(f"""
                    <div class="table-occupied">
                        <h3>{t_name}</h3>
                        <p>Trạng thái: 🔴 Đang Ngồi</p>
                        <p>Mã đơn: {t_data['order_id'] if t_data['order_id'] else 'Đang chọn món'}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🧹 Dọn Bàn / Trả Bàn ({t_name})", key=f"clear_{t_name}"):
                    st.session_state.tables[t_name]["status"] = "Trống"
                    st.session_state.tables[t_name]["order_id"] = None
                    safe_toast(f"Đã dọn dẹp {t_name} về trạng thái trống!", icon="🧹")
                    safe_rerun()

# =========================================================
# CHỨC NĂNG 4: QUẢN LÝ TỒN KHO & NGUYÊN LIỆU
# =========================================================
elif selected_nav == "📦 Quản Lý Tồn Kho":
    st.subheader("📦 Bảng Quản Lý Tồn Kho & Nguyên Liệu Tự Động")
    st.info("💡 Hệ thống tự động trừ kho nguyên liệu mỗi khi hoàn tất đơn hàng bán lẻ.")

    inv_df = pd.DataFrame([
        {"Tên nguyên liệu / Bánh": k, "Số lượng còn lại": v, "Cảnh báo": "🔴 Sắp hết" if v < 15 else "🟢 Đạt chuẩn"}
        for k, v in st.session_state.inventory.items()
    ])

    st.dataframe(inv_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📥 Nhập Thêm Hàng / Cập Nhật Kho")
    c_inv1, c_inv2, c_inv3 = st.columns([2, 1.5, 1])
    with c_inv1:
        inv_item = st.selectbox("Chọn món / nguyên liệu:", list(st.session_state.inventory.keys()))
    with c_inv2:
        add_amount = st.number_input("Số lượng nhập thêm:", min_value=1, value=100, step=10)
    with c_inv3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Nhập Kho", type="primary"):
            st.session_state.inventory[inv_item] += add_amount
            safe_toast(f"Đã nhập thêm +{add_amount} vào {inv_item}!", icon="📦")
            safe_rerun()

# =========================================================
# CHỨC NĂNG 5: VÒNG QUAY MAY MẮN (GAMIFICATION)
# =========================================================
elif selected_nav == "🎁 Vòng Quay May Mắn":
    st.subheader("🎁 Vòng Quay May Mắn Mùa Thu (Loyalty Rewards)")
    
    st.markdown("""
        <div class="wheel-container">
            <h2>🎰 VÒNG QUAY MAY MẮN AUTUMN REWARDS 🍂</h2>
            <p>Dành cho khách hàng có đơn hàng từ 100,000 VNĐ trở lên</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
    with col_w2:
        if st.button("🎡 QUAY VÒNG QUAY MAY MẮN NGAY", type="primary", use_container_width=True):
            selected_prize = random.choice(PRIZES)
            st.session_state.wheel_prize = selected_prize
            if hasattr(st, "balloons"):
                st.balloons()

        if st.session_state.wheel_prize:
            st.markdown(f"""
                <div style="background-color:#FEF3C7; border:2px dashed #D96B27; border-radius:12px; padding:20px; text-align:center; margin-top:20px;">
                    <h3>🎉 CHÚC MỪNG QUÝ KHÁCH TRÚNG THƯỞNG!</h3>
                    <h2 style="color:#D96B27;">{st.session_state.wheel_prize}</h2>
                    <p>Mã trúng thưởng đã được lưu vào hệ thống tích điểm!</p>
                </div>
            """, unsafe_allow_html=True)

# =========================================================
# CHỨC NĂNG 6: DOANH THU REAL-TIME
# =========================================================
elif selected_nav == "📊 Doanh Thu Real-Time":
    st.subheader("📊 Báo Cáo Doanh Thu Real-Time (Cập Nhật Tự Động)")
    
    if not st.session_state.sales_history:
        st.info("Chưa có giao dịch phát sinh.")
    else:
        df_sales = pd.DataFrame(st.session_state.sales_history)
        
        total_rev = int(df_sales["Thành tiền"].sum())
        total_orders = len(df_sales)
        total_items = int(df_sales["Số lượng"].sum())
        avg_order = int(total_rev / total_orders) if total_orders > 0 else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("💰 Tổng Doanh Thu", f"{total_rev:,} VNĐ")
        with kpi2:
            st.metric("📦 Tổng Đơn Hàng", f"{total_orders} đơn")
        with kpi3:
            st.metric("🧋 Bánh & Ly Bán Ra", f"{total_items} phần")
        with kpi4:
            st.metric("📈 Trung Bình / Đơn", f"{avg_order:,} VNĐ")

        st.markdown("---")

        col_c1, col_c2 = st.columns([1.2, 0.8])
        with col_c1:
            st.subheader("📈 Biểu Đồ Doanh Thu Dạng Chuỗi Thời Gian")
            st.bar_chart(df_sales, x="Thời gian", y="Thành tiền", color="#D96B27")

        with col_c2:
            st.subheader("📜 Nhật Ký Đơn Hàng Bán Ra")
            st.dataframe(
                df_sales[["Mã đơn", "Thời gian", "Khách hàng", "Thành tiền"]],
                use_container_width=True,
                hide_index=True
            )

        csv_data = df_sales.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Tải Báo Cáo Doanh Thu CSV",
            data=csv_data,
            file_name=f"Autumn_Revenue_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            type="primary"
        )

# =========================================================
# CHỨC NĂNG 7: QUẢN LÝ CA
# =========================================================
else:
    st.subheader("⚙️ Quản Lý Ca Làm Việc & Cấu Hình")
    c_staff1, c_staff2 = st.columns(2)
    with c_staff1:
        st.text_input("Tên Thu Ngân Ca Trực:", value="Nguyễn Văn Bình")
        st.selectbox("Chọn Ca Làm:", ["Ca Sáng (07:00 - 15:00)", "Ca Chiều (15:00 - 23:00)"])
    with c_staff2:
        st.text_input("Mã Máy POS:", value="POS-AUTUMN-01")
        st.number_input("Tiền Mặt Đầu Ca (VNĐ):", value=1000000, step=100000)
