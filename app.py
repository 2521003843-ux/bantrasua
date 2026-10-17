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
# 2. BỘ TRANG TRÍ GIAO DIỆN CHUẨN STARBUCKS RESERVE (CUSTOM CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* Bảng màu chuẩn Starbucks Reserve & Green Lounge */
    :root {
        --sb-green: #006241;
        --sb-dark-green: #1E3932;
        --sb-gold: #CBA258;
        --sb-cream: #F3F1E7;
        --sb-light-bg: #F9F9F8;
    }

    /* Đổi nền trang */
    .stApp {
        background-color: var(--sb-light-bg);
    }

    /* Top Hero Banner */
    .hero-container {
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 25px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    .hero-text {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(0deg, rgba(30,57,50,0.95) 0%, rgba(30,57,50,0.6) 70%, transparent 100%);
        color: white;
        padding: 30px 25px 20px 25px;
        text-align: left;
    }
    
    .hero-text h1 {
        color: #FFFFFF !important;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0 0 5px 0;
        letter-spacing: 1px;
    }

    .hero-text p {
        color: var(--sb-gold);
        font-size: 1.1rem;
        margin: 0;
        font-weight: 500;
    }

    /* Thẻ hiển thị món Signature */
    .signature-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 12px;
        border: 1px solid #E5E5E5;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.2s ease;
    }
    .signature-card:hover {
        transform: translateY(-4px);
        border-color: var(--sb-gold);
    }
    .signature-title {
        font-weight: 700;
        color: var(--sb-dark-green);
        margin-top: 8px;
        font-size: 0.95rem;
    }
    .signature-price {
        color: var(--sb-green);
        font-weight: 800;
        font-size: 1.05rem;
    }

    /* Hóa đơn phong cách Vintage Bill */
    .sb-bill-box {
        background-color: #FFFFFF;
        border: 2px dashed var(--sb-green);
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }
    
    .badge-star {
        background-color: var(--sb-gold);
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }

