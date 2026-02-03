-- =============================================
-- SQL để tạo bảng trên Supabase
-- Chạy trong SQL Editor của Supabase Dashboard
-- =============================================

-- Bảng Users (lưu thông tin đăng nhập)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Bảng Jobs (công việc và lương)
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_name TEXT NOT NULL,
    hourly_rate DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    color TEXT DEFAULT '#667eea',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng Work Shifts (ca làm việc)
CREATE TABLE IF NOT EXISTS work_shifts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    work_date DATE NOT NULL,
    shift_name TEXT NOT NULL,
    job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    break_hours DECIMAL(4,2) DEFAULT 0,
    total_hours DECIMAL(5,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng Holidays (ngày nghỉ)
CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    holiday_date DATE NOT NULL,
    description TEXT,
    UNIQUE(user_id, holiday_date)
);

-- Bảng Settings (cài đặt người dùng)
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, key)
);

-- Tạo Index để tăng tốc query
CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_shifts_user_date ON work_shifts(user_id, work_date);
CREATE INDEX IF NOT EXISTS idx_holidays_user ON holidays(user_id);
CREATE INDEX IF NOT EXISTS idx_settings_user ON settings(user_id);

-- Enable Row Level Security (RLS) - Bảo mật dữ liệu
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_shifts ENABLE ROW LEVEL SECURITY;
ALTER TABLE holidays ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Tạo policy cho phép service_role truy cập tất cả
CREATE POLICY "Service role can do all" ON users FOR ALL USING (true);
CREATE POLICY "Service role can do all" ON jobs FOR ALL USING (true);
CREATE POLICY "Service role can do all" ON work_shifts FOR ALL USING (true);
CREATE POLICY "Service role can do all" ON holidays FOR ALL USING (true);
CREATE POLICY "Service role can do all" ON settings FOR ALL USING (true);
