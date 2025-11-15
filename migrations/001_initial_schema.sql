-- 用户注册表
CREATE TABLE user_registrations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    registration_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    business_type_id VARCHAR(20) NOT NULL,
    business_type_name VARCHAR(50) NOT NULL,
    user_role_id VARCHAR(20) NOT NULL,
    user_role_name VARCHAR(50) NOT NULL,
    store_name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(50) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    address VARCHAR(300) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    submit_time DATETIME NOT NULL,
    review_time DATETIME NULL,
    review_comment TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_status CHECK (status IN ('pending', 'approved', 'rejected'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建索引
CREATE INDEX idx_user_registrations_registration_id ON user_registrations(registration_id);
CREATE INDEX idx_user_registrations_user_id ON user_registrations(user_id);
CREATE INDEX idx_user_registrations_status ON user_registrations(status);
CREATE INDEX idx_user_registrations_submit_time ON user_registrations(submit_time);

-- 业务类型表
CREATE TABLE business_types (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认业务类型数据
INSERT INTO business_types (id, name, description) VALUES
('electric_bike', '电动自行车', '电动自行车电池回收业务'),
('forklift', '叉车', '叉车电池回收业务'),
('other', '其他', '其他类型电池回收业务');

-- 用户角色表
CREATE TABLE user_roles (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    permissions JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认用户角色数据
INSERT INTO user_roles (id, name, description, permissions) VALUES
('dealer', '经销商', '从事电池销售和回收业务', '["销售", "回收", "库存管理"]'),
('repair_point', '维修点', '提供电池维修和回收服务', '["维修", "回收", "检测"]');
