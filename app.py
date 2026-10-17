import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG (Bắt buộc là câu lệnh Streamlit đầu tiên)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Starbucks Reserve & Tea Lounge",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. HÀM HỖ TRỢ TƯƠNG THÍCH MỌI PHIÊN BẢN STREAMLIT
# ---------------------------------------------------------
def safe_rerun():
    """Hỗ trợ làm mới trang tương thích cả Streamlit cũ & mới"""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def safe_toast(msg, icon="✅"):
    """Hiển thị thông báo tương thích mọi phiên bản"""
    if hasattr(st, "toast"):
        st.toast(msg, icon=icon)
    else:
        st.success(f"{icon} {msg}")

# ---------------------------------------------------------
# 3. CSS TRANG TRÍ CHUẨN STARBUCKS RESERVE
# ---------------------------------------------------------
st.markdown("""
    <style>
    :root {
        --sb-green: #006241;
        --sb-dark-green: #1E3932;
        --sb-gold: #CBA258;
        --sb-light-bg: #F9F9F8;
    }

    .stApp {
        background-color: var(--sb-light-bg);
    }

    /* Hero Banner */
    .hero-container {
        position: relative;
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    
    .hero-text {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(0deg, rgba(30,57,50,0.95) 0%, rgba(30,57,50,0.6) 70%, transparent 100%);
        color: white;
        padding: 25px 20px 15px 20px;
    }
    
    .hero-text h1 {
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 2rem;
        margin: 0 0 4px 0;
    }

    .hero-text p {
        color: var(--sb-gold);
        font-size: 1rem;
        margin: 0;
    }

    /* Thẻ Signature Drink */
    .signature-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #E5E5E5;
        box-shadow: 0 4px 10px rgba(0,0,0,0.04);
        text-align: center;
    }
    .signature-title {
        font-weight: 700;
        color: var(--sb-dark-green);
        margin-top: 6px;
        font-size: 0.9rem;
    }
    .signature-price {
        color: var(--sb-green);
        font-weight: 800;
        font-size: 1rem;
    }
    .badge-star {
        background-color: var(--sb-gold);
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    /* Thẻ Hóa Đơn */
    .sb-bill-box {
        background-color: #FFFFFF;
        border: 2px dashed var(--sb-green);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. DỮ LIỆU SẢN PHẨM & MENU STARBUCKS
# ---------------------------------------------------------
