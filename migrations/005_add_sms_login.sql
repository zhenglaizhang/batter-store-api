-- 用户表（用于短信验证码登录）
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(11) UNIQUE NOT NULL COMMENT '手机号',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 短信验证码表（用于存储验证码，可选，也可以使用Redis）
CREATE TABLE IF NOT EXISTS sms_codes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(11) NOT NULL COMMENT '手机号',
    code VARCHAR(6) NOT NULL COMMENT '验证码',
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
    used_at DATETIME NULL COMMENT '使用时间',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    INDEX idx_phone (phone),
    INDEX idx_sent_at (sent_at),
    INDEX idx_phone_code (phone, code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

