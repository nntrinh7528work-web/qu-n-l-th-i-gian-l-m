# -*- coding: utf-8 -*-
"""
Module xác thực người dùng đơn giản cho ứng dụng Quản Lý Giờ Làm.
Mỗi người dùng sẽ có database riêng biệt.
"""

import streamlit as st
import hashlib
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict

# Đường dẫn thư mục chứa database của users
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data")

# Đảm bảo thư mục tồn tại
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def get_users_db_path() -> str:
    """Lấy đường dẫn database chứa thông tin users."""
    return os.path.join(DATA_DIR, "users.db")


def init_users_db() -> None:
    """Khởi tạo database users."""
    conn = sqlite3.connect(get_users_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Mã hóa mật khẩu."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username: str, password: str, display_name: str = "") -> tuple[bool, str]:
    """
    Đăng ký người dùng mới.
    
    Returns:
        (success, message)
    """
    init_users_db()
    
    # Kiểm tra độ dài username
    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự"
    
    if len(password) < 4:
        return False, "Mật khẩu phải có ít nhất 4 ký tự"
    
    # Chỉ cho phép chữ cái, số và gạch dưới
    if not username.replace("_", "").isalnum():
        return False, "Tên đăng nhập chỉ được chứa chữ cái, số và gạch dưới"
    
    try:
        conn = sqlite3.connect(get_users_db_path())
        cursor = conn.cursor()
        
        # Kiểm tra username đã tồn tại
        cursor.execute("SELECT id FROM users WHERE username = ?", (username.lower(),))
        if cursor.fetchone():
            conn.close()
            return False, "Tên đăng nhập đã tồn tại"
        
        # Thêm user mới
        password_hash = hash_password(password)
        display = display_name if display_name else username
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, display_name)
            VALUES (?, ?, ?)
        """, (username.lower(), password_hash, display))
        
        conn.commit()
        conn.close()
        
        return True, "Đăng ký thành công! Bạn có thể đăng nhập ngay."
    
    except Exception as e:
        return False, f"Lỗi: {str(e)}"


def login_user(username: str, password: str) -> tuple[bool, str, Optional[Dict]]:
    """
    Đăng nhập người dùng.
    
    Returns:
        (success, message, user_info)
    """
    init_users_db()
    
    try:
        conn = sqlite3.connect(get_users_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute("""
            SELECT * FROM users 
            WHERE username = ? AND password_hash = ?
        """, (username.lower(), password_hash))
        
        row = cursor.fetchone()
        
        if row:
            # Cập nhật last_login
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (row['id'],))
            conn.commit()
            
            user_info = dict(row)
            conn.close()
            
            return True, "Đăng nhập thành công!", user_info
        else:
            conn.close()
            return False, "Tên đăng nhập hoặc mật khẩu không đúng", None
    
    except Exception as e:
        return False, f"Lỗi: {str(e)}", None


def get_user_db_path(username: str) -> str:
    """Lấy đường dẫn database riêng của user."""
    safe_username = username.lower().replace(" ", "_")
    return os.path.join(DATA_DIR, f"user_{safe_username}.db")


def is_logged_in() -> bool:
    """Kiểm tra người dùng đã đăng nhập chưa."""
    return st.session_state.get("logged_in", False)


def get_current_user() -> Optional[Dict]:
    """Lấy thông tin người dùng hiện tại."""
    if is_logged_in():
        return st.session_state.get("user_info")
    return None


def logout():
    """Đăng xuất người dùng."""
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.session_state["user_db_path"] = None


def show_login_page():
    """Hiển thị trang đăng nhập/đăng ký."""
    
    st.markdown("""
    <style>
        .auth-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .auth-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .auth-header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="auth-header"><h1>🌷 Quản Lý Giờ Làm</h1></div>', unsafe_allow_html=True)
    
    # Tabs đăng nhập / đăng ký
    tab_login, tab_register = st.tabs(["🔐 Đăng Nhập", "📝 Đăng Ký"])
    
    with tab_login:
        st.subheader("Đăng Nhập")
        
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            
            submit = st.form_submit_button("Đăng Nhập", use_container_width=True, type="primary")
            
            if submit:
                if username and password:
                    success, message, user_info = login_user(username, password)
                    
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["user_info"] = user_info
                        st.session_state["user_db_path"] = get_user_db_path(username)
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin")
    
    with tab_register:
        st.subheader("Đăng Ký Tài Khoản Mới")
        
        with st.form("register_form"):
            new_username = st.text_input(
                "Tên đăng nhập", 
                placeholder="Ít nhất 3 ký tự (chữ, số, _)",
                key="reg_username"
            )
            new_display = st.text_input(
                "Tên hiển thị (tùy chọn)", 
                placeholder="Tên bạn muốn hiển thị",
                key="reg_display"
            )
            new_password = st.text_input(
                "Mật khẩu", 
                type="password", 
                placeholder="Ít nhất 4 ký tự",
                key="reg_password"
            )
            confirm_password = st.text_input(
                "Xác nhận mật khẩu", 
                type="password", 
                placeholder="Nhập lại mật khẩu",
                key="reg_confirm"
            )
            
            register = st.form_submit_button("Đăng Ký", use_container_width=True, type="primary")
            
            if register:
                if new_username and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Mật khẩu xác nhận không khớp!")
                    else:
                        success, message = register_user(new_username, new_password, new_display)
                        if success:
                            st.success(message)
                            st.info("👆 Chuyển sang tab Đăng Nhập để đăng nhập")
                        else:
                            st.error(message)
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.9rem;">
        💡 <strong>Mỗi tài khoản có dữ liệu riêng biệt.</strong><br>
        Bạn có thể chia sẻ link ứng dụng này cho người khác,<br>
        họ tạo tài khoản riêng và dữ liệu của bạn sẽ không bị ảnh hưởng.
    </div>
    """, unsafe_allow_html=True)


def show_user_info_sidebar():
    """Hiển thị thông tin user ở sidebar."""
    user = get_current_user()
    if user:
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"👤 **{user.get('display_name', user['username'])}**")
            if st.button("🚪 Đăng xuất", use_container_width=True):
                logout()
                st.rerun()
