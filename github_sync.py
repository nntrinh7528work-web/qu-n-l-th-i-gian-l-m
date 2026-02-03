# -*- coding: utf-8 -*-
"""
Module đồng bộ dữ liệu với GitHub.
Tự động tải/upload database SQLite từ repository GitHub.
"""

import os
import streamlit as st
from github import Github, GithubException
import base64

# Tên file database chứa thông tin users
USERS_DB_NAME = "users.db"
DATA_DIR = "user_data"

def get_github_client():
    """Lấy GitHub client từ token trong secrets."""
    # Kiểm tra xem có token trong secrets không
    if "GITHUB_TOKEN" not in st.secrets:
        return None
    return Github(st.secrets["GITHUB_TOKEN"])

def get_repo():
    """Lấy repository object."""
    g = get_github_client()
    if not g:
        return None
    
    # 1. Ưu tiên lấy từ config repo_name
    if "GITHUB_REPO" in st.secrets:
        return g.get_repo(st.secrets["GITHUB_REPO"])
    
    # 2. Nếu không, thử đoán repo hiện tại (chỉ hoạt động nếu user own repo)
    # Cách đơn giản nhất: Users tự điền tên repo dạng "username/repo" vào secrets
    return None

def download_file(file_path_in_repo: str, local_path: str) -> bool:
    """
    Tải file từ GitHub về local.
    
    Args:
        file_path_in_repo: Đường dẫn file trên repo (vd: user_data/users.db)
        local_path: Đường dẫn lưu file ở local
    """
    try:
        repo = get_repo()
        if not repo:
            print("⚠️ Chưa cấu hình GITHUB_TOKEN hoặc GITHUB_REPO trong secrets.")
            return False
            
        try:
            contents = repo.get_contents(file_path_in_repo)
            file_content = base64.b64decode(contents.content)
            
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, "wb") as f:
                f.write(file_content)
            
            print(f"✅ Đã tải {file_path_in_repo} từ GitHub.")
            return True
        except GithubException as e:
            if e.status == 404:
                print(f"ℹ️ File {file_path_in_repo} chưa tồn tại trên GitHub.")
            else:
                print(f"❌ Lỗi khi tải file: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi download: {e}")
        return False

def upload_file(local_path: str, file_path_in_repo: str, message: str) -> bool:
    """
    Upload file từ local lên GitHub.
    """
    try:
        repo = get_repo()
        if not repo:
            return False
        
        if not os.path.exists(local_path):
            print(f"❌ File local không tồn tại: {local_path}")
            return False
            
        with open(local_path, "rb") as f:
            content = f.read()
            
        try:
            # Kiểm tra file đã tồn tại chưa để update hay create
            contents = repo.get_contents(file_path_in_repo)
            repo.update_file(contents.path, message, content, contents.sha)
            print(f"✅ Đã cập nhật {file_path_in_repo} lên GitHub.")
        except GithubException as e:
            if e.status == 404:
                # File chưa tồn tại -> Create
                repo.create_file(file_path_in_repo, message, content)
                print(f"✅ Đã tạo mới {file_path_in_repo} trên GitHub.")
            else:
                print(f"❌ Lỗi GitHub khi upload: {e}")
                return False
                
        return True
    except Exception as e:
        print(f"❌ Lỗi upload: {e}")
        return False

def sync_pull_users_db():
    """Kéo users.db về."""
    local_path = os.path.join(DATA_DIR, USERS_DB_NAME)
    download_file(f"{DATA_DIR}/{USERS_DB_NAME}", local_path)

def sync_push_users_db():
    """Đẩy users.db lên."""
    local_path = os.path.join(DATA_DIR, USERS_DB_NAME)
    upload_file(local_path, f"{DATA_DIR}/{USERS_DB_NAME}", "Update users.db")

def sync_pull_user_db(username: str):
    """Kéo DB riêng của user về."""
    safe_name = username.lower().replace(" ", "_")
    filename = f"user_{safe_name}.db"
    local_path = os.path.join(DATA_DIR, filename)
    download_file(f"{DATA_DIR}/{filename}", local_path)

def sync_push_user_db(username: str):
    """Đẩy DB riêng của user lên."""
    safe_name = username.lower().replace(" ", "_")
    filename = f"user_{safe_name}.db"
    local_path = os.path.join(DATA_DIR, filename)
    upload_file(local_path, f"{DATA_DIR}/{filename}", f"Update data for user {username}")
