# ---------------------------------------------------------
    # BỔ SUNG: VINTAGE RADIO PLAYER TRONG SIDEBAR
    # ---------------------------------------------------------

    st.markdown("### 📻 Vintage Autumn Radio")
    
    # Link nhạc Jazz Vintage Mùa Thu (File MP3 trực tuyến)
    vintage_music_url = "https://ia801503.us.archive.org/15/items/chill-lofi-song/Chill%20Lofi%20Song.mp3"
    
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #FAF5E8 0%, #F3E8D5 100%);
            border: 2px solid #D96B27;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            margin-bottom: 15px;
        ">
            <p style="margin: 0 0 8px 0; font-size: 0.9rem; color: #5C2C16; font-weight: bold;">
                🎷 Autumn Vintage Lounge Radio
            </p>
            <audio controls loop style="width: 100%; height: 36px; border-radius: 6px;">
                <source src="{vintage_music_url}" type="audio/mp3">
                Trình duyệt của bạn không hỗ trợ phát âm thanh.
            </audio>
            <p style="margin: 6px 0 0 0; font-size: 0.75rem; color: #8C5A3C; font-style: italic;">
                🍁 Phát nhạc Jazz/Lo-Fi tạo không khí cho quán
            </p>
        </div>
    """, unsafe_allow_html=True)
