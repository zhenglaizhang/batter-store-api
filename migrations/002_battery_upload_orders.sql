-- 创建电池上传订单表
CREATE TABLE IF NOT EXISTS battery_upload_orders (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(50) NOT NULL,
    store_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    contact_address TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    total_photos INTEGER DEFAULT 0,
    pickup_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建电池上传照片表
CREATE TABLE IF NOT EXISTS battery_upload_photos (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    order_id CHAR(36) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    upload_index INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES battery_upload_orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建索引
CREATE INDEX idx_battery_upload_orders_user_id ON battery_upload_orders(user_id);
CREATE INDEX idx_battery_upload_orders_status ON battery_upload_orders(status);
CREATE INDEX idx_battery_upload_orders_created_at ON battery_upload_orders(created_at);
CREATE INDEX idx_battery_upload_photos_order_id ON battery_upload_photos(order_id);
CREATE INDEX idx_battery_upload_photos_user_id ON battery_upload_photos(user_id);

-- 添加注释
ALTER TABLE battery_upload_orders COMMENT = '电池上传订单表';
ALTER TABLE battery_upload_photos COMMENT = '电池上传照片表';
