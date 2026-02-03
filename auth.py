# -*- coding: utf-8 -*-
"""
Module xác thực người dùng cho ứng dụng Quản Lý Giờ Làm.
Hỗ trợ cả Supabase (cloud) và SQLite (local fallback).
"""

import streamlit as st
import hashlib
import os
import sqlite3
import extra_streamlit_components as stx
from datetime import datetime, timedelta

# Thử import Supabase module
try:
    import supabase_db
    _SUPABASE_MODULE_OK = True
except:
    _SUPABASE_MODULE_OK = False

def _check_supabase() -> bool:
    """Kiểm tra Supabase có sẵn không (gọi mỗi lần, không cache)."""
    if not _SUPABASE_MODULE_OK:
        return False
    try:
        return supabase_db.is_supabase_available()
    except:
        return False

# Đường dẫn thư mục chứa database của users (for SQLite fallback)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data")

# Đảm bảo thư mục tồn tại
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def get_users_db_path() -> str:
    """Lấy đường dẫn database chứa thông tin users."""
    return os.path.join(DATA_DIR, "users.db")


def get_user_db_path(username: str) -> str:
    """Lấy đường dẫn database riêng của user."""
    safe_username = "".join(c for c in username.lower() if c.isalnum() or c == "_")
    return os.path.join(DATA_DIR, f"user_{safe_username}.db")


def init_users_db() -> None:
    """Khởi tạo database users (SQLite)."""
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


def is_using_supabase() -> bool:
    """Kiểm tra có đang dùng Supabase không."""
    return _check_supabase()


def register_user(username: str, password: str, display_name: str = "") -> tuple:
    """
    Đăng ký người dùng mới.
    
    Returns:
        (success, message)
    """
    # Validate input
    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự"
    
    if len(password) < 4:
        return False, "Mật khẩu phải có ít nhất 4 ký tự"
    
    if not username.replace("_", "").isalnum():
        return False, "Tên đăng nhập chỉ được chứa chữ cái, số và gạch dưới"
    
    password_hash = hash_password(password)
    display = display_name if display_name else username
    
    # Thử Supabase trước
    if _check_supabase():
        try:
            # Check if user exists
            existing = supabase_db.get_user_by_username(username)
            if existing:
                return False, "Tên đăng nhập đã tồn tại"
            
            # Create user
            user = supabase_db.create_user(username, password_hash, display)
            if user:
                # Init default data
                supabase_db.init_user_default_data(user['id'])
                return True, "Đăng ký thành công! Bạn có thể đăng nhập ngay."
            else:
                return False, "Lỗi khi tạo tài khoản"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    # Fallback to SQLite
    try:
        init_users_db()
        
        conn = sqlite3.connect(get_users_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE username = ?", (username.lower(),))
        if cursor.fetchone():
            conn.close()
            return False, "Tên đăng nhập đã tồn tại"
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, display_name)
            VALUES (?, ?, ?)
        """, (username.lower(), password_hash, display))
        
        conn.commit()
        conn.close()
        
        return True, "Đăng ký thành công! Bạn có thể đăng nhập ngay."
    
    except Exception as e:
        return False, f"Lỗi: {str(e)}"


def login_user(username: str, password: str) -> tuple:
    """
    Đăng nhập người dùng.
    
    Returns:
        (success, message, user_info)
    """
    password_hash = hash_password(password)
    
    # Thử Supabase trước
    if _check_supabase():
        try:
            user = supabase_db.get_user_by_username(username)
            if user and user['password_hash'] == password_hash:
                supabase_db.update_user_last_login(user['id'])
                return True, "Đăng nhập thành công!", user
            else:
                return False, "Tên đăng nhập hoặc mật khẩu không đúng", None
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    # Fallback to SQLite
    try:
        init_users_db()
        
        conn = sqlite3.connect(get_users_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM users WHERE username = ? AND password_hash = ?
        """, (username.lower(), password_hash))
        
        row = cursor.fetchone()
        
        if row:
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


def is_logged_in() -> bool:
    """Kiểm tra người dùng đã đăng nhập chưa."""
    return st.session_state.get("logged_in", False) and st.session_state.get("user_info") is not None


def get_current_user() -> Optional[Dict]:
    """Lấy thông tin người dùng hiện tại."""
    if is_logged_in():
        return st.session_state.get("user_info")
    return None


def get_current_user_id() -> Optional[int]:
    """Lấy user_id của người dùng hiện tại."""
    user = get_current_user()
    if user:
        return user.get('id')
    return None


@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager():
    return stx.CookieManager(key="auth_cookie_manager")


def set_remember_me_cookie(username: str, password_hash: str):
    """Lưu cookie đăng nhập (30 ngày)."""
    try:
        cookie_manager = get_cookie_manager()
        # Token format: username|password_hash
        token = f"{username}|{password_hash}"
        expires = datetime.now() + timedelta(days=30)
        cookie_manager.set("work_tracker_token", token, expires_at=expires)
    except:
        pass


def check_auto_login() -> bool:
    """Kiểm tra cookie để login tự động."""
    if is_logged_in():
        return True

    try:
        cookie_manager = get_cookie_manager()
        cookies = cookie_manager.get_all()
        token = cookies.get("work_tracker_token")
        
        if token and "|" in token:
            username, pw_hash = token.split("|", 1)
            
            # Verify with DB
            if _check_supabase():
               user = supabase_db.get_user_by_username(username)
               if user and user['password_hash'] == pw_hash:
                   st.session_state["logged_in"] = True
                   st.session_state["user_info"] = user
                   st.session_state["user_db_path"] = None
                   supabase_db.update_user_last_login(user['id'])
                   return True
            else:
                # Local SQLite verification
                init_users_db()
                conn = sqlite3.connect(get_users_db_path())
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, pw_hash))
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    st.session_state["logged_in"] = True
                    st.session_state["user_info"] = dict(row)
                    st.session_state["user_db_path"] = get_user_db_path(username)
                    
                    # Update last login
                    conn = sqlite3.connect(get_users_db_path())
                    conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (row['id'],))
                    conn.commit()
                    conn.close()
                    return True
    except Exception as e:
        print(f"Auto login error: {e}")
        
    return False


def logout():
    """Đăng xuất người dùng."""
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.session_state["user_db_path"] = None
    
    # Xóa Cookie
    try:
        cookie_manager = get_cookie_manager()
        cookie_manager.delete("work_tracker_token")
    except:
        pass


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
            font-size: 3rem;
            background: linear-gradient(to right, #00C6FB, #005BEA);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .db-status {
            text-align: center;
            padding: 0.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="auth-header"><h1>🚀 Quản Lý Giờ Làm</h1></div>', unsafe_allow_html=True)
    
    # Hiển thị trạng thái database
    is_cloud = _check_supabase()
    if is_cloud:
        st.success("☁️ **Cloud Mode** - Dữ liệu được lưu trên Supabase")
    else:
        st.warning("💾 **Local Mode** - Dữ liệu lưu cục bộ (có thể mất khi reboot)")
    
    # Debug info - LUÔN HIỂN THỊ
    with st.expander("🔧 Debug Info - Kiểm tra kết nối", expanded=not is_cloud):
        import os
        st.write("**Kiểm tra Streamlit Secrets:**")
        has_secrets = hasattr(st, 'secrets')
        st.write(f"- hasattr(st, 'secrets'): `{has_secrets}`")
        
        if has_secrets:
            try:
                secrets_keys = list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else "N/A"
                st.write(f"- Secrets keys: `{secrets_keys}`")
            except Exception as e:
                st.write(f"- Secrets keys: Error - `{e}`")
            
            try:
                has_url = "SUPABASE_URL" in st.secrets
                has_key = "SUPABASE_KEY" in st.secrets
                st.write(f"- SUPABASE_URL in secrets: `{has_url}`")
                st.write(f"- SUPABASE_KEY in secrets: `{has_key}`")
                
                if has_url:
                    url_val = st.secrets["SUPABASE_URL"]
                    st.write(f"- SUPABASE_URL value: `{url_val[:30]}...`")
            except Exception as e:
                st.write(f"- Error checking secrets: `{e}`")
        
        st.write("**Kiểm tra Environment Variables:**")
        env_url = os.environ.get("SUPABASE_URL", "")
        env_key = os.environ.get("SUPABASE_KEY", "")
        st.write(f"- ENV SUPABASE_URL: `{'Set (' + env_url[:20] + '...)' if env_url else 'Not set'}`")
        st.write(f"- ENV SUPABASE_KEY: `{'Set' if env_key else 'Not set'}`")
        
        st.write("**Kết quả kiểm tra Supabase:**")
        st.write(f"- _check_supabase(): `{is_cloud}`")
        st.write(f"- _SUPABASE_MODULE_OK: `{_SUPABASE_MODULE_OK}`")
        
        # Show last error if available
        if not is_cloud:
            if _SUPABASE_MODULE_OK:
                try:
                    last_err = supabase_db.get_last_error()
                    st.error(f"**Lỗi Supabase:** `{last_err}`")
                except Exception as ex:
                    st.error(f"**Lỗi khi lấy error:** `{ex}`")
            else:
                st.error("**Lỗi:** Không thể import supabase_db module")
    
    # Tabs đăng nhập / đăng ký
    tab_login, tab_register = st.tabs(["👤 Đăng Nhập", "✨ Đăng Ký"])
    
    with tab_login:
        st.subheader("Chào mừng trở lại 👋")
        
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            remember_me = st.checkbox("Ghi nhớ đăng nhập (30 ngày)")
            
            submit = st.form_submit_button("Đăng Nhập", use_container_width=True, type="primary")
            
            if submit:
                if username and password:
                    success, message, user_info = login_user(username, password)
                    
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["user_info"] = user_info
                        st.session_state["user_db_path"] = get_user_db_path(username)
                        
                        if remember_me:
                            set_remember_me_cookie(username, user_info['password_hash'])
                            st.toast("Đã ghi nhớ đăng nhập!")
                        
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin")
    
    with tab_register:
        st.subheader("Tạo tài khoản mới 🎉")
        
        with st.form("register_form"):
            new_username = st.text_input("Tên đăng nhập", placeholder="Ít nhất 3 ký tự", key="reg_username")
            new_display = st.text_input("Tên hiển thị (tùy chọn)", placeholder="Tên bạn muốn hiển thị", key="reg_display")
            new_password = st.text_input("Mật khẩu", type="password", placeholder="Ít nhất 4 ký tự", key="reg_password")
            new_password2 = st.text_input("Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu", key="reg_password2")
            
            register = st.form_submit_button("Đăng Ký", use_container_width=True, type="primary")
            
            if register:
                if new_password != new_password2:
                    st.error("Mật khẩu không khớp!")
                elif new_username and new_password:
                    success, message = register_user(new_username, new_password, new_display)
                    if success:
                        st.success(message)
                        st.info("Hãy chuyển sang tab Đăng Nhập")
                    else:
                        st.error(message)
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin")
